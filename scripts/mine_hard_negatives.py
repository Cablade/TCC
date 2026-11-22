"""Minera candidatos a negativos difíceis nas imagens de TREINO de camundongo (Zenodo).

Roda o B atual nas imagens de treino murinas, guarda as regiões que o B marcou
como suspeitas e que não contêm nenhum ponto publicado, sorteia uma amostra por
imagem e prepara uma página de revisão humana. Nenhuma região vira negativo
aqui: só as confirmadas na revisão entram no treino, via
scripts/prepare_hard_negative_dataset.py.

Recusa validação, desenvolvimento e teste: a mineração usa só a partição de
treino, para que a seleção não use imagens de avaliação.

Exemplo (na raiz do TCC):
  python scripts/mine_hard_negatives.py ^
      --image-manifest data/processed/b_next/images.csv ^
      --annotations data/processed/b_next/annotations.json ^
      --checkpoint experiments/runs/b_atual/best.keras ^
      --output-dir data/annotations/hard_negatives_20261013
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MOUSE_SOURCE = "https://doi.org/10.5281/zenodo.5123062"
REVIEW_OPTIONS = [("negativo", "Sem parasita (negativo)"), ("parasita", "Contém parasita"),
                  ("incerto", "Incerto")]


def eligible_regions(result: dict, annotation: dict, min_score: float) -> list[dict]:
    """Regiões classificadas como suspeitas, sem ponto publicado e ainda sem rótulo.

    Exclui regiões que já estão dentro de um negativo revisado, pois essas já
    viram recorte negativo pela regra de candidate_label.
    """
    from src.data_protocol import annotation_intersects_box

    positives = annotation.get("positives", []) if annotation else []
    reviewed_negatives = [n["bbox"] for n in (annotation or {}).get("negative_regions", [])
                          if n.get("review_status") == "reviewed"]
    out = []
    for index, region in enumerate(result.get("regions", [])):
        score = float(region["scores"][1])
        bbox = region["bbox"]
        if region["class_id"] != 1 or score < min_score:
            continue
        if any(annotation_intersects_box(p, bbox) for p in positives):
            continue
        if any(n[0] <= bbox[0] and n[1] <= bbox[1] and bbox[2] <= n[2] and bbox[3] <= n[3]
               for n in reviewed_negatives):
            continue
        out.append({"candidate_index": index, "bbox": list(map(int, bbox)), "score_suspect": score})
    return out


def sample_regions(regions_by_image: dict[str, list[dict]], per_image: int, max_total: int | None,
                   seed: int) -> list[tuple[str, dict]]:
    """Amostra aleatória (não pelos maiores escores) com teto por imagem e teto global.

    Sorteio uniforme mantém a amostra representativa dos alarmes do modelo; escolher
    os maiores escores concentraria a fila em parasitas não anotados.
    """
    rng = random.Random(seed)
    chosen = []
    for image_id in sorted(regions_by_image):
        regions = sorted(regions_by_image[image_id], key=lambda r: r["candidate_index"])
        chosen += [(image_id, r) for r in rng.sample(regions, min(per_image, len(regions)))]
    if max_total is not None and len(chosen) > max_total:
        chosen = sorted(rng.sample(chosen, max_total), key=lambda c: (c[0], c[1]["candidate_index"]))
    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--image-manifest", required=True, type=Path)
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--per-image", type=int, default=2, help="Máximo de regiões sorteadas por imagem.")
    parser.add_argument("--max-total", type=int, default=600, help="Tamanho máximo da fila de revisão.")
    parser.add_argument("--min-score", type=float, default=0.5, help="Escore mínimo de suspeita (argmax=1 já implica >= 0,5).")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--limit-images", type=int, help="Só para teste rápido do fluxo.")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("Pasta de saída já existe; use outra para preservar a fila anterior.")

    import tensorflow as tf
    from src.data_protocol import read_manifest, validate_partitions, load_annotations, read_image_rgb, read_image_bytes
    from src.data_pipeline import file_sha256
    from src.model_b import predict_image_b
    from src.segmentation import localization_hash
    from src.region_review import save_region_views, write_queue, write_review_page

    tf.config.threading.set_inter_op_parallelism_threads(2)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    cfg = json.loads((args.checkpoint.parent / "config.json").read_text(encoding="utf-8"))
    rows = read_manifest(args.image_manifest)
    validate_partitions(rows)
    annotations = load_annotations(args.annotations, rows)
    selected = [r for r in rows if r["split"] == "train" and r["source"] == MOUSE_SOURCE
                and not r.get("duplicate_of")]
    if any(r["split"] != "train" for r in selected):
        raise AssertionError("Mineração restrita ao treino.")
    if args.limit_images:
        selected = selected[:args.limit_images]
    if not selected:
        raise ValueError("Nenhuma imagem murina de treino no manifesto.")
    print(f"{len(selected)} imagens de treino murinas.", flush=True)
    classifier = tf.keras.models.load_model(args.checkpoint)
    eligible, per_image_report, sources = {}, [], {}
    start = time.perf_counter()
    for i, row in enumerate(selected, 1):
        raw = read_image_bytes(row["path"])
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"Hash difere do manifesto: {row['image_id']}")
        image = read_image_rgb(row["path"])
        result = predict_image_b(image, classifier, cfg, row["image_id"])
        if result["status"] == "erro":
            raise RuntimeError(f"Falha do B em {row['image_id']}: {result.get('error')}")
        regions = eligible_regions(result, annotations.get(row["image_id"]), args.min_score)
        eligible[row["image_id"]] = regions
        sources[row["image_id"]] = row
        positive = sum(r["class_id"] == 1 for r in result["regions"])
        per_image_report.append({"image_id": row["image_id"], "candidates": len(result["candidates"]),
                                 "positive_regions": positive, "eligible_without_point": len(regions)})
        print(f"[{i}/{len(selected)}] {row['image_id']}: {positive} positivas, "
              f"{len(regions)} sem ponto", flush=True)
    chosen = sample_regions(eligible, args.per_image, args.max_total, args.seed)
    args.output_dir.mkdir(parents=True)
    items = []
    by_image = {}
    for image_id, region in chosen:
        by_image.setdefault(image_id, []).append(region)
    loc_hash = localization_hash(cfg["localization"])
    for image_id, regions in by_image.items():
        image = read_image_rgb(sources[image_id]["path"])
        for region in regions:
            candidate_id = hashlib.sha256(f"{image_id}:{region['candidate_index']}:{loc_hash}".encode()).hexdigest()[:24]
            views = save_region_views(image, region["bbox"], args.output_dir, candidate_id)
            items.append({"candidate_id": candidate_id, "image_id": image_id,
                          "source_sha256": sources[image_id]["sha256"], **region, **views})
    metadata = {
        "purpose": "negativos_dificeis_treino_murino", "created_at": datetime.now(timezone.utc).isoformat(),
        "split": "train", "source": MOUSE_SOURCE,
        "image_manifest": str(args.image_manifest), "image_manifest_sha256": file_sha256(args.image_manifest),
        "annotations": str(args.annotations), "annotations_sha256": file_sha256(args.annotations),
        "checkpoint": str(args.checkpoint), "checkpoint_sha256": file_sha256(args.checkpoint),
        "localization": cfg["localization"], "localization_sha256": loc_hash,
        "selection": {"rule": "class_id==1, sem ponto publicado, fora de negativo revisado",
                      "sampling": "uniforme por imagem, depois teto global", "per_image": args.per_image,
                      "max_total": args.max_total, "min_score": args.min_score, "seed": args.seed},
        "images_processed": len(selected), "eligible_regions": sum(map(len, eligible.values())),
        "queued_regions": len(items), "seconds": time.perf_counter() - start,
        "per_image": per_image_report, "review_options": [v for v, _ in REVIEW_OPTIONS],
        "unreviewed_is_negative": False,
    }
    queue_sha = write_queue(args.output_dir, metadata, items)
    page = write_review_page(
        args.output_dir, queue_sha, items, title="Negativos difíceis — treino",
        instructions=("Cada região foi marcada como suspeita pelo B e não contém ponto publicado. "
                      "Marque 'Sem parasita' só quando não houver nenhuma parte de tripomastigota no recorte. "
                      "Na dúvida, use 'Incerto': incertos não entram no treino."),
        options=REVIEW_OPTIONS)
    print(json.dumps({"queued": len(items), "eligible": metadata["eligible_regions"],
                      "per_image_counts": dict(Counter(i["image_id"] for i in items).most_common(3)),
                      "review_page": str(page), "queue_sha256": queue_sha}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
