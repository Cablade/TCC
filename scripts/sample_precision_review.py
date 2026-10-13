"""Estimativa de precisão por amostra revisada de regiões positivas (campos murinos de validação).

Dois passos:

1) sample — sorteia N regiões positivas (amostra aleatória simples, semente fixa)
   de regions.csv de uma execução já feita, grava recortes, contexto e página de
   revisão. A página não mostra escore nem se há ponto publicado (revisão cega).
     python scripts/sample_precision_review.py sample ^
         --regions experiments/comparison/<execucao>/B/regions.csv ^
         --image-manifest experiments/comparison/<execucao>/images.csv ^
         --output-dir data/annotations/precision_B_<execucao> --n 200

2) estimate — lê decisions.json exportado da página e calcula a precisão com IC
   por bootstrap reamostrando imagens; grava decisions.csv para paired_analysis.py.
     python scripts/sample_precision_review.py estimate ^
         --queue data/annotations/precision_B_<execucao>/queue.json ^
         --decisions data/annotations/precision_B_<execucao>/decisions.json

Use só imagens de validação/desenvolvimento antes do congelamento; no teste
final, repita com uma nova amostra das imagens de teste.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MOUSE_SOURCE = "https://doi.org/10.5281/zenodo.5123062"
OPTIONS = [("parasita", "Contém parasita (acerto)"), ("nao_parasita", "Sem parasita (falso alarme)"),
           ("incerto", "Incerto")]


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sample_positive_regions(regions: list[dict], image_ids: set[str], n: int, seed: int) -> tuple[list[dict], int]:
    pool = [r for r in regions if r["image_id"] in image_ids and str(r["class_id"]) == "1"]
    pool.sort(key=lambda r: (r["image_id"], int(r["candidate_id"])))
    rng = random.Random(seed)
    chosen = rng.sample(pool, min(n, len(pool)))
    return sorted(chosen, key=lambda r: (r["image_id"], int(r["candidate_id"]))), len(pool)


def cmd_sample(args):
    from src import data_protocol as dp
    from src.data_pipeline import file_sha256
    from src.region_review import save_region_views, write_queue, write_review_page

    if args.output_dir.exists():
        raise FileExistsError("Pasta de saída já existe.")
    images = {r["image_id"]: r for r in read_csv(args.image_manifest)}
    allowed_splits = {"val", "development"} | ({"test"} if args.final_test else set())
    eligible = {i for i, r in images.items() if r["source"] == MOUSE_SOURCE and r["split"] in allowed_splits}
    if not eligible:
        raise ValueError("Nenhuma imagem murina elegível no manifesto.")
    chosen, pool_size = sample_positive_regions(read_csv(args.regions), eligible, args.n, args.seed)
    if not chosen:
        raise ValueError("Nenhuma região positiva nas imagens elegíveis.")
    args.output_dir.mkdir(parents=True)
    items, cache = [], {}
    for region in chosen:
        image_id = region["image_id"]
        if image_id not in cache:
            row = images[image_id]
            if hashlib.sha256(dp.read_image_bytes(row["path"])).hexdigest() != row["sha256"]:
                raise ValueError(f"Imagem mudou: {image_id}")
            cache = {image_id: dp.read_image_rgb(row["path"])}
        bbox = [int(region[k]) for k in ("x1", "y1", "x2", "y2")]
        candidate_id = hashlib.sha256(f"{image_id}:{region['candidate_id']}:{bbox}".encode()).hexdigest()[:24]
        views = save_region_views(cache[image_id], bbox, args.output_dir, candidate_id)
        items.append({"candidate_id": candidate_id, "image_id": image_id,
                      "region_candidate_id": int(region["candidate_id"]), "bbox": bbox,
                      "score_suspect": float(region["score_suspect"]), **views})
    metadata = {"purpose": "estimativa_de_precisao_por_amostra", "created_at": datetime.now(timezone.utc).isoformat(),
                "regions_csv": str(args.regions), "regions_sha256": file_sha256(args.regions),
                "image_manifest": str(args.image_manifest), "image_manifest_sha256": file_sha256(args.image_manifest),
                "sampling": "amostra_aleatoria_simples_de_regioes_positivas", "seed": args.seed,
                "requested": args.n, "population_positive_regions": pool_size, "eligible_images": len(eligible),
                "blind_review": True, "final_test": bool(args.final_test)}
    queue_sha = write_queue(args.output_dir, metadata, items)
    page = write_review_page(
        args.output_dir, queue_sha, items, title="Precisão do sistema — amostra de regiões positivas",
        instructions=("Cada recorte foi sinalizado como suspeito pelo sistema. Marque 'Contém parasita' "
                      "quando houver tripomastigota (ou parte inequívoca dele) no recorte."),
        options=OPTIONS)
    print(json.dumps({"sampled": len(items), "population": pool_size, "page": str(page)}, ensure_ascii=False))
    return 0


def cmd_estimate(args):
    from src.paired_stats import reviewed_precision
    from src.region_review import load_decisions

    queue, decisions = load_decisions(args.queue, args.decisions, {v for v, _ in OPTIONS})
    missing = [i for i in queue["items"] if i["candidate_id"] not in decisions]
    if missing and not args.allow_partial:
        raise ValueError(f"{len(missing)} regiões sem decisão.")
    rows = [{"image_id": i["image_id"], "candidate_id": i["candidate_id"],
             "decision": decisions[i["candidate_id"]]["decision"]}
            for i in queue["items"] if i["candidate_id"] in decisions]
    out_csv = args.decisions.with_name("decisions.csv")
    with out_csv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["image_id", "candidate_id", "decision"])
        writer.writeheader()
        writer.writerows(rows)
    result = reviewed_precision(rows, n_resamples=args.resamples, seed=args.seed)
    result["population_positive_regions"] = queue["population_positive_regions"]
    result["undecided"] = len(missing)
    out = args.decisions.with_name("precision.json")
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--regions", required=True, type=Path)
    s.add_argument("--image-manifest", required=True, type=Path)
    s.add_argument("--output-dir", required=True, type=Path)
    s.add_argument("--n", type=int, default=200)
    s.add_argument("--seed", type=int, default=20261013)
    s.add_argument("--final-test", action="store_true", help="Permite imagens de teste; só após o congelamento.")
    e = sub.add_parser("estimate")
    e.add_argument("--queue", required=True, type=Path)
    e.add_argument("--decisions", required=True, type=Path)
    e.add_argument("--resamples", type=int, default=10000)
    e.add_argument("--seed", type=int, default=20261013)
    e.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    return cmd_sample(args) if args.command == "sample" else cmd_estimate(args)


if __name__ == "__main__":
    raise SystemExit(main())
