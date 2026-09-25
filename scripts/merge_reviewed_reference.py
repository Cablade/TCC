"""Incorpora regiões negativas revisadas à referência positiva completa."""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def merge(inventory: Path, base: Path, reviewed: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"A saída já existe; preserve-a e escolha outro destino: {output}")
    rows = dp.read_manifest(inventory)
    base_payload = json.loads(base.read_text(encoding="utf-8-sig"))
    reviewed_payload = json.loads(reviewed.read_text(encoding="utf-8-sig"))
    base_by_id = dp.validate_annotations(base_payload, rows)
    reviewed_rows = dp.read_manifest(reviewed.parent / "inventory.csv")
    reviewed_by_id = dp.validate_annotations(reviewed_payload, reviewed_rows)
    result = deepcopy(base_payload)
    result_by_id = {entry["image_id"]: entry for entry in result["images"]}
    imported = []
    for image_id, reviewed_entry in reviewed_by_id.items():
        if image_id not in result_by_id:
            raise ValueError(f"Imagem revisada ausente na referência completa: {image_id}")
        if reviewed_entry["positives"] != base_by_id[image_id]["positives"]:
            raise ValueError(f"A revisão alterou positivos publicados: {image_id}")
        human_regions = [region for region in reviewed_entry.get("negative_regions", [])
                         if region.get("review_basis") == "human_visual_review"]
        result_by_id[image_id]["negative_regions"] = deepcopy(human_regions)
        imported.extend({"image_id": image_id, "annotation_id": region["annotation_id"],
                         "reviewer": region["reviewer"], "reviewed_at": region.get("reviewed_at")}
                        for region in human_regions)
    result["visual_review"] = {
        "source_annotation_sha256": sha256(base),
        "inventory_sha256_at_start": sha256(inventory),
        "purpose": "merged_development_negative_review",
        "history": imported,
        "reviewed_batch": str(reviewed),
        "reviewed_batch_sha256": sha256(reviewed),
    }
    dp.validate_annotations(result, rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"images": len(result["images"]), "imported_regions": len(imported),
            "reviewers": sorted({item["reviewer"] for item in imported}),
            "output": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path,
                        default=ROOT / "data/protocol/trypomastigote_verified/eligible_inventory.csv")
    parser.add_argument("--base", type=Path,
                        default=ROOT / "data/annotations/public_import/public_points.json")
    parser.add_argument("--reviewed", type=Path,
                        default=ROOT / "data/annotations/negative_preselection_v1/reviewed.json")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "data/annotations/experimento_reference.json")
    args = parser.parse_args()
    print(json.dumps(merge(args.inventory, args.base, args.reviewed, args.output), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
