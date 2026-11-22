"""Une as amostras de precisão de A e B em uma única página cega e separa as decisões depois.

A revisão do teste final deve ser cega quanto ao sistema (docs/plano_estatistico.md, 4.2).
As amostras continuam sendo sorteadas por scripts/sample_precision_review.py, uma pasta por
sistema; este script apenas:

  merge — copia recortes/contexto das duas filas para uma pasta neutra, embaralha os itens
          (semente fixa) e grava uma página de revisão sem indicação de sistema;
  split — divide o decisions.json exportado da página cega em um decisions.json por sistema,
          citando o SHA-256 da fila original de cada um, para o "estimate" congelado.

Exemplo:
  python scripts/blind_merge_review.py merge --queues A=data/.../A/queue.json B=data/.../B/queue.json ^
      --output-dir data/.../revisao_cega
  python scripts/blind_merge_review.py split --blind-dir data/.../revisao_cega ^
      --decisions data/.../revisao_cega/decisions.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OPTIONS = [("parasita", "Contém parasita (acerto)"), ("nao_parasita", "Sem parasita (falso alarme)"),
           ("incerto", "Incerto")]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def merge(args):
    from src.region_review import write_queue, write_review_page

    if args.output_dir.exists():
        raise FileExistsError("Pasta de saída já existe.")
    sources, items = {}, []
    for spec in args.queues:
        system, _, path = spec.partition("=")
        path = Path(path)
        queue = json.loads(path.read_text(encoding="utf-8-sig"))
        sources[system] = {"queue": str(path), "queue_sha256": sha(path), "n": len(queue["items"])}
        for item in queue["items"]:
            items.append((system, path.parent, item))
    ids = [item["candidate_id"] for _, _, item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate_id repetido entre sistemas.")
    random.Random(args.seed).shuffle(items)
    args.output_dir.mkdir(parents=True)
    public, mapping = [], {}
    for system, folder, item in items:
        copied = {}
        for key in ("crop_file", "context_file"):
            target = args.output_dir / item[key]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(folder / item[key], target)
            copied[key] = item[key]
        public.append({"candidate_id": item["candidate_id"], "image_id": item["image_id"], **copied})
        mapping[item["candidate_id"]] = system
    metadata = {"purpose": "revisao_cega_precisao_teste_final", "shuffle_seed": args.seed,
                "sources": sources, "blind_to_system": True}
    queue_sha = write_queue(args.output_dir, metadata, public)
    write_review_page(args.output_dir, queue_sha, public, title="Precisão — amostra de regiões positivas",
                      instructions=("Cada recorte foi sinalizado como suspeito por um dos sistemas. Marque "
                                    "'Contém parasita' quando houver tripomastigota (ou parte inequívoca dele)."),
                      options=OPTIONS)
    # O mapeamento fica fora da página e fora da fila exibida; o revisor não precisa abri-lo.
    (args.output_dir / "_mapa_sistemas_nao_abrir.json").write_text(
        json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(public), "sources": sources}, indent=2, ensure_ascii=False))
    return 0


def split(args):
    from src.region_review import load_decisions

    queue, decisions = load_decisions(args.blind_dir / "queue.json", args.decisions, {v for v, _ in OPTIONS})
    mapping = json.loads((args.blind_dir / "_mapa_sistemas_nao_abrir.json").read_text(encoding="utf-8"))
    payload = json.loads(args.decisions.read_text(encoding="utf-8-sig"))
    for system, source in queue["sources"].items():
        queue_path = Path(source["queue"])
        if sha(queue_path) != source["queue_sha256"]:
            raise ValueError(f"Fila de {system} mudou desde a união.")
        entries = [{k: v for k, v in d.items() if k != "reviewer"}
                   for cid, d in decisions.items() if mapping[cid] == system]
        out = queue_path.parent / "decisions.json"
        if out.exists():
            raise FileExistsError(out)
        out.write_text(json.dumps({
            "queue_sha256": source["queue_sha256"], "reviewer": payload["reviewer"],
            "exported_at": payload.get("exported_at"), "total_items": source["n"], "decisions": entries,
            "derived_from_blind_review": {"decisions": str(args.decisions), "decisions_sha256": sha(args.decisions),
                                          "blind_queue_sha256": sha(args.blind_dir / "queue.json")},
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{system}: {len(entries)} de {source['n']} decisões -> {out}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--queues", nargs="+", required=True, help="SISTEMA=caminho/queue.json")
    m.add_argument("--output-dir", required=True, type=Path)
    m.add_argument("--seed", type=int, default=20261014)
    s = sub.add_parser("split")
    s.add_argument("--blind-dir", required=True, type=Path)
    s.add_argument("--decisions", required=True, type=Path)
    args = parser.parse_args()
    return merge(args) if args.command == "merge" else split(args)


if __name__ == "__main__":
    raise SystemExit(main())
