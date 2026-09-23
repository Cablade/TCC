"""Audita o único ZIP ativo; não cria rótulos nem partições experimentais."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp  # noqa: E402


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/dataset.json")
    parser.add_argument("--archive", type=Path, help="Caminho alternativo para o mesmo ZIP.")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--annotations", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    archive = (args.archive or Path(config["archive"])).resolve()
    output = args.output_dir or ROOT / config["output_dir"]
    annotations = args.annotations or ROOT / config["annotations"]
    if output.exists() or annotations.exists():
        raise FileExistsError("Saída já existe. Para repetir a auditoria, escolha --output-dir e --annotations novos; anotações existentes são preservadas.")
    digests = {name: hashlib.new(name) for name in ("md5", "sha256")}
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            for digest in digests.values():
                digest.update(block)
    hashes = {name: digest.hexdigest() for name, digest in digests.items()}
    for name, actual in hashes.items():
        if actual != config[f"expected_{name}"]:
            raise ValueError(f"ZIP diferente do configurado: {name} não confere.")
    with zipfile.ZipFile(archive) as stream:
        members = [item.filename for item in stream.infolist() if not item.is_dir()]
    image_members = [name for name in members if Path(name).suffix.lower() in dp.IMAGE_EXTENSIONS]
    metadata = [{"path": f"zip://{archive.as_posix()}!{name}", "source": config["source"]}
                for name in image_members]
    result = dp.build_inventory([archive], metadata)
    header_errors = {row["image_id"]: row["error"] for row in result["errors"]}
    eligible, integrity_exclusions, checks = [], [], []
    for index, row in enumerate(result["images"], 1):
        error = header_errors.get(row["image_id"])
        try:
            pixels = dp.read_image_rgb(row["path"])
            if pixels.shape[:2] != (int(row["height"]), int(row["width"])):
                raise ValueError("Dimensões decodificadas não correspondem ao inventário")
            del pixels
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        checks.append({"image_id": row["image_id"], "decode_ok": error is None, "error": error})
        if error:
            integrity_exclusions.append({**row, "reason": error})
        elif not row["duplicate_of"]:
            eligible.append(row)
        if index % 100 == 0:
            print(f"Decodificação: {index}/{len(result['images'])}", flush=True)
    dp.write_manifest(result["images"], output / "inventory.csv")
    dp.write_manifest(eligible, output / "eligible_inventory.csv")
    dp.write_manifest(result["exclusions"], output / "duplicate_exclusions.csv", [*dp.INVENTORY_FIELDS, "reason"])
    dp.write_manifest(integrity_exclusions, output / "integrity_exclusions.csv", [*dp.INVENTORY_FIELDS, "reason"])
    save_json(annotations, dp.annotation_template(eligible))
    report = {
        "dataset_id": config["dataset_id"], "archive": archive.as_posix(),
        "source": config["source"], "bytes": archive.stat().st_size, **hashes,
        "archive_folders": dict(Counter(name.split("/")[0] for name in image_members)),
        "non_image_members": [name for name in members if name not in image_members],
        "inventory": result["summary"], "eligible": dp.inventory_summary(eligible),
        "integrity_excluded": len(integrity_exclusions), "checks": checks,
        "annotations": str(annotations), "split_status": "pending",
        "note": "Elegível significa decodificável e único; revisão biológica e agrupamento ainda pendentes. Pastas originais não definem o teste do TCC."
    }
    save_json(output / "audit.json", report)
    print(json.dumps({"files": len(checks), "eligible": len(eligible),
                      "integrity_excluded": len(integrity_exclusions), "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
