"""Monta o conjunto de treino com negativos difíceis confirmados na revisão humana.

Entrada: conjunto atual (data/processed/b_next), fila de mine_hard_negatives.py e
decisions.json exportado da página de revisão. Saída: nova pasta com images.csv,
annotations.json (negativos confirmados acrescentados como negative_regions
revisadas), crops.csv (recortes antigos + novos negativos) e assembly.json.

Regras:
- só entram regiões marcadas "negativo"; "parasita" e "incerto" ficam fora e
  são listadas no relatório;
- só imagens de treino; validação, desenvolvimento e teste não mudam;
- a região é recalculada pela localização e o recorte precisa ter os mesmos
  pixels revisados (SHA-256 igual ao da fila);
- a validação de recortes do treino (validate_crop_manifest) roda no final.

Exemplo:
  python scripts/prepare_hard_negative_dataset.py ^
      --queue data/annotations/hard_negatives_20261013/queue.json ^
      --decisions data/annotations/hard_negatives_20261013/decisions.json ^
      --destination data/processed/b_hardneg
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ALLOWED = {"negativo", "parasita", "incerto"}


def add_negative_regions(reference: dict, queue: dict, decisions: dict, train_ids: set[str]) -> list[dict]:
    """Acrescenta os negativos confirmados à referência (cópia) e devolve os itens aceitos."""
    by_id = {entry["image_id"]: entry for entry in reference["images"]}
    accepted = []
    for item in queue["items"]:
        decision = decisions.get(item["candidate_id"])
        if not decision or decision["decision"] != "negativo":
            continue
        if item["image_id"] not in train_ids:
            raise ValueError(f"Negativo difícil fora do treino: {item['image_id']}")
        entry = by_id[item["image_id"]]
        entry.setdefault("negative_regions", []).append({
            "annotation_id": f"hard_negative_{item['candidate_id']}", "bbox": item["bbox"],
            "review_status": "reviewed", "reviewer": decision["reviewer"],
            "reviewed_at": decision.get("reviewed_at"),
            "review_basis": "human_visual_review_of_model_b_false_alarm",
            "review_usage": "train_hard_negative",
            "mined_with_checkpoint_sha256": queue["checkpoint_sha256"],
        })
        accepted.append(item)
    return accepted


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-dir", type=Path, default=ROOT / "data/processed/b_next")
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/model_b_cpu_original_negatives.yaml")
    parser.add_argument("--supplementary-policy", type=Path, default=ROOT / "configs/negative_sources_originals.json")
    parser.add_argument("--allow-partial", action="store_true",
                        help="Aceita fila com regiões ainda sem decisão (ficam fora do treino).")
    args = parser.parse_args()
    if args.destination.exists():
        raise FileExistsError("Destino já existe; não sobrescrever.")

    from PIL import Image
    from src import data_protocol as dp
    from src.data_pipeline import file_sha256, load_split, validate_crop_manifest
    from src.dataset_policy import validate_active_images, validate_supplementary_crops
    from src.region_review import load_decisions
    from src.segmentation import crop_region, localization_hash, propose_regions
    from src.train import load_config
    from notebooks.gerar_rois import CROP_FIELDS

    queue, decisions = load_decisions(args.queue, args.decisions, ALLOWED)
    missing = [i["candidate_id"] for i in queue["items"] if i["candidate_id"] not in decisions]
    if missing and not args.allow_partial:
        raise ValueError(f"{len(missing)} regiões sem decisão; termine a revisão ou use --allow-partial.")
    images_path, annotations_path, crops_path = (args.source_dir / n for n in
                                                 ("images.csv", "annotations.json", "crops.csv"))
    if file_sha256(images_path) != queue["image_manifest_sha256"]:
        raise ValueError("images.csv mudou desde a mineração.")
    if file_sha256(annotations_path) != queue["annotations_sha256"]:
        raise ValueError("annotations.json mudou desde a mineração.")
    cfg = load_config(args.config)
    loc_hash = localization_hash(cfg["localization"])
    if loc_hash != queue["localization_sha256"]:
        raise ValueError("Localização da configuração difere da usada na mineração.")
    protected = {p: file_sha256(ROOT / p) for p in
                 ("models/model_a/model_trained.keras", "experiments/runs/b_atual/best.keras")
                 if (ROOT / p).exists()}

    images = dp.read_manifest(images_path)
    dp.validate_partitions(images)
    validate_active_images(images, supplementary_policy=args.supplementary_policy)
    by_row = {r["image_id"]: r for r in images}
    train_ids = {r["image_id"] for r in images if r["split"] == "train"}
    old_annotations = dp.load_annotations(annotations_path, images)
    old_crops = load_split(crops_path)
    validate_crop_manifest(old_crops, images, old_annotations, loc_hash, file_sha256(annotations_path))

    reference = deepcopy(json.loads(annotations_path.read_text(encoding="utf-8-sig")))
    accepted = add_negative_regions(reference, queue, decisions, train_ids)
    if not accepted:
        raise ValueError("Nenhuma região confirmada como negativa.")
    reference.setdefault("review_imports", []).append({
        "purpose": "train_hard_negatives", "queue_sha256": hashlib.sha256(args.queue.read_bytes()).hexdigest(),
        "decisions_sha256": file_sha256(args.decisions), "accepted": len(accepted),
        "created_at": datetime.now(timezone.utc).isoformat()})
    annotations = dp.validate_annotations(reference, images)

    args.destination.mkdir(parents=True)
    dp.write_manifest(images, args.destination / "images.csv", list(dict.fromkeys(k for r in images for k in r)))
    (args.destination / "annotations.json").write_text(
        json.dumps(reference, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    annotation_sha = file_sha256(args.destination / "annotations.json")
    crops = old_crops.to_dict("records")
    for crop in crops:
        crop["annotation_sha256"] = annotation_sha
    known_ids = {c["crop_id"] for c in crops}
    pending = {}
    for item in accepted:
        pending.setdefault(item["image_id"], []).append(item)
    for image_id, items in sorted(pending.items()):
        row = by_row[image_id]
        if hashlib.sha256(dp.read_image_bytes(row["path"])).hexdigest() != row["sha256"]:
            raise ValueError(f"Imagem mudou: {image_id}")
        pixels = dp.read_image_rgb(row["path"])
        candidates, _ = propose_regions(pixels, cfg["localization"])
        for item in items:
            index = item["candidate_index"]
            if index >= len(candidates) or candidates[index]["bbox"] != item["bbox"]:
                raise ValueError(f"Localização não reproduz a região revisada: {item['candidate_id']}")
            if dp.candidate_label(item["bbox"], annotations[image_id]) != 0:
                raise ValueError(f"Região revisada não recebe rótulo negativo: {item['candidate_id']}")
            crop_id = hashlib.sha256(f"{image_id}:{index}:{loc_hash}".encode()).hexdigest()[:24]
            if crop_id in known_ids:
                raise ValueError(f"crop_id já existe no conjunto: {crop_id}")
            path = args.destination / "train/0" / f"{crop_id}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(crop_region(pixels, item["bbox"])).save(path)
            if file_sha256(path) != item["crop_sha256"]:
                raise ValueError(f"Pixels do recorte diferem dos revisados: {item['candidate_id']}")
            known_ids.add(crop_id)
            crops.append(dict(crop_id=crop_id, image_id=image_id, path=str(path.resolve()), label=0,
                              split="train", group_id=row["group_id"], source_sha256=row["sha256"],
                              crop_sha256=item["crop_sha256"], bbox=json.dumps(item["bbox"]),
                              localization_sha256=loc_hash, annotation_sha256=annotation_sha,
                              review_status="reviewed"))
    dp.write_manifest(crops, args.destination / "crops.csv", CROP_FIELDS)
    final = load_split(args.destination / "crops.csv")
    validate_crop_manifest(final, images, annotations, loc_hash, annotation_sha)
    validate_supplementary_crops(final, args.supplementary_policy)
    if any(file_sha256(ROOT / p) != h for p, h in protected.items()):
        raise ValueError("Checkpoint protegido mudou durante o preparo.")
    counts = Counter(decision["decision"] for decision in decisions.values())
    mouse = {i for i, r in by_row.items() if r["source"] == queue["source"]}
    neg = final[final["label"].astype(int) == 0]
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(), "training_started": False,
        "source_dir": str(args.source_dir), "queue": str(args.queue), "decisions": str(args.decisions),
        "decisions_sha256": file_sha256(args.decisions), "reviewer": next(iter(decisions.values()))["reviewer"],
        "review_counts": dict(counts), "undecided": len(missing), "added_negative_crops": len(accepted),
        "possible_unannotated_parasites": [
            {"image_id": i["image_id"], "bbox": i["bbox"], "candidate_id": i["candidate_id"]}
            for i in queue["items"] if decisions.get(i["candidate_id"], {}).get("decision") == "parasita"],
        "crop_counts": dict(Counter(f"{r['split']}/{r['label']}" for r in final.to_dict("records"))),
        "negative_crops_by_domain": {
            split: {"murino": int(neg[(neg.split == split) & neg.image_id.isin(mouse)].shape[0]),
                    "humano_externo": int(neg[(neg.split == split) & ~neg.image_id.isin(mouse)].shape[0])}
            for split in ("train", "val")},
        "validation_unchanged": True, "test_105_unchanged": True, "protected_sha256": protected,
    }
    (args.destination / "assembly.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("review_counts", "added_negative_crops", "crop_counts",
                                             "negative_crops_by_domain")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
