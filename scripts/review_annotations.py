"""Revisão humana local de regiões negativas, preservando a referência original."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import secrets
import shutil
import sys
import threading
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ReviewStore:
    def __init__(self, inventory, annotations, output, suggestions=None):
        self.inventory_path, self.source, self.output = map(Path, (inventory, annotations, output))
        if self.output.resolve() in {self.source.resolve(), self.inventory_path.resolve()}:
            raise ValueError("A saída deve ser diferente da referência original e do inventário.")
        self.rows = dp.read_manifest(self.inventory_path)
        self.by_id = {row["image_id"]: row for row in self.rows}
        if len(self.by_id) != len(self.rows):
            raise ValueError("Inventário contém IDs repetidos.")
        source_payload = json.loads(self.source.read_text(encoding="utf-8-sig"))
        original = dp.validate_annotations(source_payload, self.rows)
        if set(original) != set(self.by_id):
            raise ValueError("A referência deve conter exatamente os IDs do inventário.")
        self.source_hash = digest(self.source)
        self.inventory_hash = digest(self.inventory_path)
        self.payload = (json.loads(self.output.read_text(encoding="utf-8-sig"))
                        if self.output.exists() else source_payload)
        checked = dp.validate_annotations(self.payload, self.rows)
        if set(checked) != set(self.by_id):
            raise ValueError("A referência deve conter exatamente os IDs do inventário.")
        metadata = self.payload.get("visual_review", {})
        if metadata and metadata.get("source_annotation_sha256") != digest(self.source):
            raise ValueError("A referência original mudou desde a última revisão.")
        if self.output.exists() and not metadata:
            raise ValueError("Saída existente sem histórico desta ferramenta. Escolha um novo arquivo.")
        if metadata and metadata.get("inventory_sha256_at_start") != self.inventory_hash:
            raise ValueError("O inventário mudou desde a última revisão. Preserve a revisão e use uma nova saída.")
        for image_id, entry in checked.items():
            baseline = original[image_id]
            if ({k: v for k, v in entry.items() if k != "negative_regions"} !=
                    {k: v for k, v in baseline.items() if k != "negative_regions"}):
                raise ValueError("A saída alterou campos da referência original.")
            if any(region not in entry["negative_regions"] for region in baseline["negative_regions"]):
                raise ValueError("A saída removeu ou alterou regiões originais.")
        self.original = original
        self.output_hash = digest(self.output) if self.output.exists() else None
        self.lock = threading.Lock()
        self.token = secrets.token_urlsafe(32)
        self.suggestions = []
        if suggestions is not None:
            queue = json.loads(Path(suggestions).read_text(encoding="utf-8-sig"))
            if queue.get("source_annotation_sha256") != self.source_hash:
                raise ValueError("Sugestões não correspondem à referência original.")
            seen = set()
            for item in queue.get("candidates", []):
                image_id = item.get("image_id")
                row = self.by_id.get(image_id)
                if row is None or row.get("split") != "development":
                    raise ValueError("Sugestões exigem imagens reservadas para desenvolvimento.")
                identifier = item.get("candidate_id")
                if not identifier or identifier in seen:
                    raise ValueError("Identificador de sugestão inválido/repetido.")
                seen.add(identifier)
                if item.get("review_status") != "pending" or item.get("label") is not None:
                    raise ValueError("Sugestões devem permanecer pendentes e sem rótulo.")
                if item.get("source_sha256") != row["sha256"]:
                    raise ValueError("Hash da imagem da sugestão diverge.")
                entry = original[image_id]
                dp.validate_bbox(item.get("bbox"), entry["width"], entry["height"])
                if not dp.validate_negative_box(item["bbox"], entry["positives"]):
                    raise ValueError("Sugestão sobrepõe positivo conhecido.")
                self.suggestions.append(deepcopy(item))

    def list_images(self):
        annotations = {entry["image_id"]: entry for entry in self.payload["images"]}
        return [{"image_id": row["image_id"], "name": row["path"].replace("\\", "/").rsplit("/", 1)[-1],
                 "width": int(row["width"]), "height": int(row["height"]),
                 "split": row.get("split") or "não definido",
                 "negatives": len(annotations[row["image_id"]].get("negative_regions", []))}
                for row in self.rows if row.get("split") != "test"]

    def annotation(self, image_id):
        if image_id not in self.by_id or self.by_id[image_id].get("split") == "test":
            raise ValueError("Imagem indisponível. A revisão de desenvolvimento não abre o teste.")
        return next(item for item in self.payload["images"] if item["image_id"] == image_id)

    def change(self, request):
        with self.lock:
            reviewer = request.get("reviewer")
            if not isinstance(reviewer, str) or not reviewer.strip():
                raise ValueError("Informe o nome real de quem examinou a região.")
            if request.get("confirmed") is not True:
                raise ValueError("Confirme explicitamente a revisão da área antes de salvar.")
            image_id = request.get("image_id")
            if not isinstance(image_id, str):
                raise ValueError("Identificador de imagem inválido.")
            current = self.annotation(image_id)
            payload = deepcopy(self.payload)
            entry = next(item for item in payload["images"] if item["image_id"] == image_id)
            action = request.get("action", "add")
            when = datetime.now(timezone.utc).isoformat()
            if action == "add":
                bbox = request.get("bbox")
                dp.validate_bbox(bbox, current["width"], current["height"])
                if not dp.validate_negative_box(bbox, current.get("positives", [])):
                    raise ValueError("A área cruza uma anotação positiva. Examine outra área.")
                if any(region["bbox"] == bbox for region in entry.get("negative_regions", [])):
                    raise ValueError("Esta região já foi registrada.")
                annotation_id = "visual_negative_" + secrets.token_hex(8)
                entry.setdefault("negative_regions", []).append({
                    "annotation_id": annotation_id, "bbox": bbox,
                    "review_status": "reviewed", "reviewer": reviewer.strip(),
                    "reviewed_at": when, "review_basis": "human_visual_review",
                    "review_usage": "development",
                })
            elif action == "remove":
                annotation_id = request.get("annotation_id", "")
                if not isinstance(annotation_id, str) or not annotation_id.startswith("visual_negative_"):
                    raise ValueError("Só é possível remover regiões criadas nesta ferramenta.")
                if any(r["annotation_id"] == annotation_id for r in self.original[image_id]["negative_regions"]):
                    raise ValueError("Regiões da referência original são preservadas.")
                before = entry.get("negative_regions", [])
                entry["negative_regions"] = [r for r in before if r["annotation_id"] != annotation_id]
                if len(before) == len(entry["negative_regions"]):
                    raise ValueError("Região não encontrada.")
            else:
                raise ValueError("Ação desconhecida.")
            meta = payload.setdefault("visual_review", {
                "source_annotation_sha256": self.source_hash,
                "inventory_sha256_at_start": self.inventory_hash,
                "purpose": "development_negative_region_review", "history": [],
            })
            meta.setdefault("history", []).append({"action": action, "image_id": image_id,
                "annotation_id": annotation_id, "reviewer": reviewer.strip(), "at": when})
            dp.validate_annotations(payload, self.rows)
            if digest(self.source) != self.source_hash or digest(self.inventory_path) != self.inventory_hash:
                raise ValueError("A referência ou o inventário mudou. Reinicie a ferramenta antes de salvar.")
            actual_hash = digest(self.output) if self.output.exists() else None
            if actual_hash != self.output_hash:
                raise ValueError("A saída mudou fora desta janela. Reinicie a ferramenta para carregar a versão atual.")
            self.output.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.output.with_name(self.output.name + ".tmp-" + secrets.token_hex(4))
            try:
                temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                if self.output.exists():
                    shutil.copy2(self.output, self.output.with_name(self.output.name + ".bak"))
                temporary.replace(self.output)
            finally:
                temporary.unlink(missing_ok=True)
            self.payload, self.output_hash = payload, digest(self.output)
            return {"saved": True, "annotation": entry, "output": str(self.output)}


def make_server(store, port=8765):
    class Handler(BaseHTTPRequestHandler):
        def send_content(self, code, content, kind="application/json; charset=utf-8"):
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)

        def local_request(self):
            expected = "127.0.0.1:" + str(self.server.server_port)
            return self.headers.get("Host") == expected

        def do_GET(self):
            if not self.local_request():
                self.send_content(403, {"error": "Use o endereço local informado no terminal."})
                return
            parts = urlsplit(self.path)
            query = parse_qs(parts.query)
            try:
                if parts.path == "/":
                    self.send_content(200, Path(__file__).with_name("review_ui.html").read_bytes(), "text/html; charset=utf-8")
                elif parts.path == "/api/state":
                    self.send_content(200, {"images": store.list_images(), "token": store.token,
                        "output": str(store.output), "unsplit": any(not row.get("split") for row in store.rows),
                        "excluded_test": sum(row.get("split") == "test" for row in store.rows)})
                elif parts.path in {"/api/annotation", "/api/image"}:
                    image_id = query.get("id", [""])[0]
                    with store.lock:
                        annotation = deepcopy(store.annotation(image_id))
                        annotation["suggestions"] = [item for item in store.suggestions if item["image_id"] == image_id]
                    if parts.path == "/api/annotation":
                        self.send_content(200, annotation)
                    else:
                        image_path = store.by_id[image_id]["path"]
                        self.send_content(200, dp.read_image_bytes(image_path),
                            mimetypes.guess_type(image_path)[0] or "application/octet-stream")
                else:
                    self.send_content(404, {"error": "Endereço não encontrado."})
            except (ValueError, OSError, KeyError) as exc:
                self.send_content(400, {"error": str(exc)})

        def do_POST(self):
            if not self.local_request() or self.headers.get("X-Review-Token") != store.token:
                self.send_content(403, {"error": "Sessão inválida. Reabra a página local."})
                return
            if self.path != "/api/review":
                self.send_content(404, {"error": "Endereço não encontrado."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    raise ValueError("Pedido vazio ou grande demais.")
                request = json.loads(self.rfile.read(length))
                if not isinstance(request, dict):
                    raise ValueError("Pedido inválido.")
                self.send_content(200, store.change(request))
            except (ValueError, OSError, KeyError, TypeError) as exc:
                self.send_content(400, {"error": str(exc)})

        def log_message(self, fmt, *args):
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT / "data/protocol/trypomastigote_verified/eligible_inventory.csv")
    parser.add_argument("--annotations", type=Path, default=ROOT / "data/annotations/public_import/public_points.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/annotations/experimento_reference.json")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--suggestions", type=Path)
    parser.add_argument("--batch", type=Path, help="Pasta gerada por preselect_negatives.py.")
    args = parser.parse_args()
    if args.batch:
        args.inventory = args.batch / "inventory.csv"
        args.annotations = args.batch / "source_annotations.json"
        args.output = args.batch / "reviewed.json"
        args.suggestions = args.batch / "suggestions.json"
    store = ReviewStore(args.inventory, args.annotations, args.output, args.suggestions)
    server = make_server(store, args.port)
    print(f"Abra http://127.0.0.1:{server.server_port}/ no navegador.", flush=True)
    print(f"Revisões serão salvas somente após sua confirmação em: {store.output}", flush=True)
    print("Imagens com split=test ficam ocultas. Inventários sem partição exigem planejar a reserva de teste.", flush=True)
    print("Para encerrar, pressione Ctrl+C.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
