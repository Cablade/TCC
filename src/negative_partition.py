"""Reserva originais negativos por imagem, sem consultar previsões dos modelos."""
from collections import Counter
import random


def split_barcelona(rows, training_count=20, seed=42):
    if training_count != 20 or len(rows) != 200:
        raise ValueError("Esta reserva exige exatamente 20 de 200 originais.")
    for key in ("image_id", "sha256", "group_id", "decoded_sha256"):
        values = [r.get(key) for r in rows]
        if not all(values) or len(set(values)) != len(rows):
            raise ValueError("IDs, pixels ou grupos repetidos/ausentes: " + key)
    types = sorted({r["cell_type"] for r in rows})
    if len(types) != 8 or set(Counter(r["cell_type"] for r in rows).values()) != {25}:
        raise ValueError("A reserva exige os oito tipos com 25 originais cada.")
    rng = random.Random(seed)
    extra = set(rng.sample(types, 4))
    selected = set()
    for cell_type in types:
        candidates = sorted((r for r in rows if r["cell_type"] == cell_type),
                            key=lambda r: r["image_id"])
        selected.update(r["image_id"] for r in rng.sample(candidates, 3 if cell_type in extra else 2))
    return [dict(r, split="train" if r["image_id"] in selected else "development",
                 review_status="reviewed", usage="next_training_negative" if r["image_id"] in selected
                 else "comparison_negative") for r in rows]


def assert_disjoint_training_comparison(training, comparison):
    """Impede vazamento por ID, bytes, pixels, grupo ou descendente de um original."""
    for key in ("image_id", "sha256", "decoded_sha256", "group_id", "path"):
        left = {r[key] for r in training if r.get(key)}
        right = {r[key] for r in comparison if r.get(key)}
        if left & right:
            raise ValueError("Treino e comparação compartilham " + key)
    trained_ids = {r["image_id"] for r in training}
    if any(r.get("original_image_id") in trained_ids for r in comparison):
        raise ValueError("Versão de uma imagem de treino incluída na comparação.")
