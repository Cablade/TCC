"""Divisão inicial por imagem: preserva test do ZIP e separa treino/validação.

Não presume independência entre animais. Estratifica a disponibilidade de regiões
negativas revisadas; não utiliza resultados do classificador nem pixels do teste.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp
from src.data_pipeline import file_sha256


def build_assignments(images, annotations, seed=42):
    if any(row["group_level"] != "imagem_original" or row["group_id"] != row["image_id"]
           for row in images):
        raise ValueError("Este protocolo inicial exige grupos por imagem; grupos biológicos precisam de outra divisão.")
    pool, test = [], []
    for row in images:
        member = row["path"].replace("\\", "/").split("!", 1)[-1]
        parts = Path(member).parts
        if "train" in parts and "test" not in parts:
            pool.append(row)
        elif "test" in parts and "train" not in parts:
            test.append(row)
        else:
            raise ValueError("Não foi possível identificar a partição original do ZIP.")
    if not pool or not test:
        raise ValueError("O ZIP deve ter imagens de train e test.")
    negative = sorted(row["image_id"] for row in pool
                      if annotations[row["image_id"]].get("negative_regions"))
    other = sorted(row["image_id"] for row in pool if row["image_id"] not in set(negative))
    if len(negative) < 4:
        raise ValueError("Revisar negativos em pelo menos quatro imagens para esta divisão inicial.")
    rng = random.Random(seed)
    rng.shuffle(negative)
    rng.shuffle(other)
    n_val = round(len(pool) * 0.2)
    n_negative_val = max(1, round(len(negative) * 0.2))
    n_other_val = n_val - n_negative_val
    if not 0 <= n_other_val <= len(other):
        raise ValueError("Quantidade de imagens incompatível com a estratificação.")
    val = set(negative[:n_negative_val] + other[:n_other_val])
    return {**{row["group_id"]: "val" if row["image_id"] in val else "train" for row in pool},
            **{row["group_id"]: "test" for row in test}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT / "data/protocol/trypomastigote_verified/eligible_inventory.csv")
    parser.add_argument("--annotations", type=Path, default=ROOT / "data/annotations/experimento_reference_v2.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/splits/experimento")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("Partições existentes; não sobrescrever a divisão congelada.")
    images = dp.read_manifest(args.inventory)
    annotations = dp.load_annotations(args.annotations, images)
    assignments = build_assignments(images, annotations, args.seed)
    partitions = dp.assign_splits(images, assignments=assignments, seed=args.seed)
    from src.dataset_policy import validate_active_images
    validate_active_images(partitions)
    dp.write_manifest(partitions, args.output_dir / "images.csv")
    for name in dp.SPLITS:
        dp.write_manifest([row for row in partitions if row["split"] == name],
                          args.output_dir / (name + ".csv"), [*dp.INVENTORY_FIELDS, "split"])
    dp.write_manifest([{"group_id": key, "split": value} for key, value in sorted(assignments.items())],
                      args.output_dir / "grupos.csv", ["group_id", "split"])
    report = {"seed": args.seed, "counts": dict(Counter(row["split"] for row in partitions)),
              "inventory_sha256": file_sha256(args.inventory), "annotation_sha256": file_sha256(args.annotations),
              "negative_review_images": dict(Counter(row["split"] for row in partitions
                  if annotations[row["image_id"]].get("negative_regions"))),
              "method": "Test original preservado; 80/20 das imagens train, estratificado por disponibilidade de negativos revisados.",
              "group_level": "imagem_original", "biological_independence_confirmed": False,
              "limitations": ["Espécie camundongo não identifica animal ou lâmina individual.",
                  "Negativos revisados disponíveis em apenas oito imagens; treinamento inicial exploratório.",
                  "Teste contém somente campos positivos, sem referência exaustiva; avaliação final ainda não liberada."]}
    (args.output_dir / "split_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
