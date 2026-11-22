"""Extrai candidatos do B após particionar imagens; rótulos apenas revisados.

Não sorteia negativos nem inventa rótulos de regiões não anotadas.
O crop contextual é exatamente o usado em src.model_b.predict_image_b.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CROP_FIELDS = ["crop_id", "image_id", "path", "label", "split", "group_id",
               "source_sha256", "crop_sha256", "bbox", "localization_sha256",
               "annotation_sha256", "review_status"]


def generate_crops(image_manifest, annotations_path, config, output_dir, dry_run=False,
                   splits=("train", "val", "development")):
    from PIL import Image
    from src.data_protocol import (read_manifest, load_annotations, validate_partitions,
                                   read_image_rgb, read_image_bytes, candidate_label,
                                   annotation_intersects_box)
    from src.data_pipeline import file_sha256
    from src.segmentation import propose_regions, crop_region, localization_hash

    images = read_manifest(image_manifest)
    validate_partitions(images)
    annotations = load_annotations(annotations_path, images)
    if not splits or set(splits) - {"train", "val", "development"}:
        raise ValueError("Extração para treinamento aceita somente train, val e development.")
    selected = [row for row in images if row["split"] in splits]
    if not selected:
        raise ValueError("Nenhuma imagem nas partições selecionadas para extração.")
    localization = config["localization"]
    config_hash = localization_hash(localization)
    annotation_hash = file_sha256(annotations_path)
    output_dir = Path(output_dir).resolve()
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        if (output_dir / "crops.csv").exists():
            raise FileExistsError("crops.csv já existe; use outro --output-dir para preservar a extração.")
    rows, reports = [], []
    for source in selected:
        if hashlib.sha256(read_image_bytes(source["path"])).hexdigest() != source["sha256"]:
            raise ValueError(f"Conteúdo da origem mudou: {source['image_id']}")
        image = read_image_rgb(source["path"])
        if image.shape[:2] != (int(source["height"]), int(source["width"])):
            raise ValueError("Dimensões da imagem diferem do inventário.")
        candidates, diagnostics = propose_regions(image, localization)
        annotation = annotations.get(source["image_id"])
        if annotation and (int(annotation["height"]), int(annotation["width"])) != image.shape[:2]:
            raise ValueError("Dimensões da anotação diferem da imagem.")
        labels = Counter()
        for index, candidate in enumerate(candidates):
            bbox = candidate["bbox"]
            label = candidate_label(bbox, annotation) if annotation is not None else None
            labels["unlabeled" if label is None else str(label)] += 1
            if label is None:
                continue
            crop_id = hashlib.sha256(f"{source['image_id']}:{index}:{config_hash}".encode()).hexdigest()[:24]
            crop_path = output_dir / source["split"] / str(label) / f"{crop_id}.png"
            if not dry_run:
                crop_path.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(crop_region(image, bbox)).save(crop_path)
            rows.append({
                "crop_id": crop_id, "image_id": source["image_id"], "path": str(crop_path),
                "label": label, "split": source["split"], "group_id": source["group_id"],
                "source_sha256": source["sha256"],
                "crop_sha256": file_sha256(crop_path) if not dry_run else "",
                "bbox": json.dumps(bbox), "localization_sha256": config_hash,
                "annotation_sha256": annotation_hash, "review_status": "reviewed",
            })
        reviewed = annotation is not None and annotation.get("review_status") == "reviewed"
        positives = annotation.get("positives", []) if reviewed else []
        missed = [p["annotation_id"] for p in positives
                  if not any(annotation_intersects_box(p, c["bbox"]) for c in candidates)]
        reports.append({
            "image_id": source["image_id"], "split": source["split"], **diagnostics,
            "labels": dict(labels), "reviewed_positives": len(positives) if reviewed else None,
            "missed_positive_ids": missed if reviewed else None,
            "coverage_note": "Diagnóstico de interseção de crops; avaliação final usa associação um a um.",
        })
    report = {"image_manifest_sha256": file_sha256(image_manifest),
              "annotation_sha256": annotation_hash, "localization_sha256": config_hash,
              "localization": localization, "dry_run": dry_run, "images": reports,
              "processed_splits": sorted(set(splits)),
              "excluded_images": len(images) - len(selected),
              "labeled_crops": len(rows), "unlabeled_is_negative": False}
    if not dry_run:
        with (output_dir / "crops.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=CROP_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        (output_dir / "extraction_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-manifest", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--config", default=str(ROOT / "configs/model_b_cpu_original_negatives.yaml"))
    parser.add_argument("--output-dir", default=str(ROOT / "data/processed/b"))
    parser.add_argument("--dry-run", action="store_true", help="Diagnostica candidatos sem salvar recortes.")
    parser.add_argument("--splits", nargs="+", choices=["train", "val", "development"],
                        default=["train", "val", "development"], help="Teste nunca é extraído para treinamento.")
    args = parser.parse_args()
    from src.dataset_policy import validate_active_images
    from src.data_protocol import read_manifest
    validate_active_images(read_manifest(args.image_manifest))
    from src.train import load_config
    report = generate_crops(args.image_manifest, args.annotations, load_config(args.config),
                            args.output_dir, args.dry_run, splits=args.splits)
    print(json.dumps({"images": len(report["images"]), "labeled_crops": report["labeled_crops"],
                      "dry_run": args.dry_run, "output_dir": args.output_dir}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
