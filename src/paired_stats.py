"""Inferência pareada A × B com a imagem como unidade de reamostragem.

Plano estatístico de 13/10/2026 (docs/plano_estatistico.md):
- intervalos percentis por bootstrap reamostrando imagens inteiras, com os
  mesmos IDs para A e B em cada réplica (pareamento preservado);
- reamostragem estratificada por classe da imagem (positiva/negativa), para
  que cada réplica mantenha o tamanho de cada grupo;
- McNemar exato (binomial nos pares discordantes) para a decisão por imagem.

Regiões, pontos e sementes nunca são tratados como unidades independentes.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

import numpy as np

POSITIVE_DECISIONS = {"1", "suspeita", "true", "True"}
NEGATIVE_DECISIONS = {"0", "sem_suspeita", "false", "False"}


def decision_value(value) -> int | None:
    """Normaliza a decisão por imagem; erro/ausência continua None."""
    text = "" if value is None else str(value).strip()
    if text in POSITIVE_DECISIONS:
        return 1
    if text in NEGATIVE_DECISIONS:
        return 0
    return None


def paired_table(rows: Sequence[Mapping]) -> dict:
    """Converte per_image.csv (uma linha por imagem e sistema) em vetores pareados.

    Exige exatamente os mesmos IDs para A e B. Mantém None para erros.
    """
    by_system: dict[str, dict[str, Mapping]] = {"A": {}, "B": {}}
    for row in rows:
        system = str(row["system"])
        if system not in by_system:
            raise ValueError(f"Sistema inesperado: {system}")
        if row["image_id"] in by_system[system]:
            raise ValueError(f"Imagem repetida para {system}: {row['image_id']}")
        by_system[system][row["image_id"]] = row
    if set(by_system["A"]) != set(by_system["B"]):
        raise ValueError("A e B precisam dos mesmos IDs de imagem.")
    ids = sorted(by_system["A"])
    if not ids:
        raise ValueError("Nenhuma imagem pareada.")
    a, b = by_system["A"], by_system["B"]
    classes = []
    for image_id in ids:
        if a[image_id]["image_class"] != b[image_id]["image_class"]:
            raise ValueError(f"Classe diverge entre sistemas: {image_id}")
        classes.append(1 if a[image_id]["image_class"] == "positive" else 0)

    def number(row, key):
        value = row.get(key, "")
        return 0.0 if value in ("", None) else float(value)

    return {
        "image_id": ids,
        "label": np.asarray(classes, dtype=int),
        "decision_a": [decision_value(a[i]["original_decision"]) for i in ids],
        "decision_b": [decision_value(b[i]["original_decision"]) for i in ids],
        "points": np.asarray([number(a[i], "reference_points") for i in ids]),
        "matched_a": np.asarray([number(a[i], "matched_positive_regions") for i in ids]),
        "matched_b": np.asarray([number(b[i], "matched_positive_regions") for i in ids]),
        "positive_regions_a": np.asarray([number(a[i], "positive_regions") for i in ids]),
        "positive_regions_b": np.asarray([number(b[i], "positive_regions") for i in ids]),
    }


def _ratio(numerator, denominator):
    total = float(np.sum(denominator))
    return None if total == 0 else float(np.sum(numerator)) / total


def _rate(values):
    values = [v for v in values if v is not None]
    return None if not values else float(np.mean(values))


def point_metrics(table: Mapping, index: np.ndarray) -> dict:
    """Métricas calculáveis de per_image.csv para um conjunto de índices de imagens."""
    label = table["label"][index]
    pos = index[label == 1]
    neg = index[label == 0]
    da, db = table["decision_a"], table["decision_b"]
    out = {
        # Razão de somas: imagens com mais pontos pesam mais, como na cobertura global.
        "coverage_A": _ratio(table["matched_a"][pos], table["points"][pos]),
        "coverage_B": _ratio(table["matched_b"][pos], table["points"][pos]),
        "sensitivity_A": _rate([da[i] for i in pos]),
        "sensitivity_B": _rate([db[i] for i in pos]),
        "specificity_A": _rate([None if da[i] is None else 1 - da[i] for i in neg]),
        "specificity_B": _rate([None if db[i] is None else 1 - db[i] for i in neg]),
        "false_regions_per_negative_A": (float(np.mean(table["positive_regions_a"][neg])) if len(neg) else None),
        "false_regions_per_negative_B": (float(np.mean(table["positive_regions_b"][neg])) if len(neg) else None),
    }
    for name in ("coverage", "sensitivity", "specificity", "false_regions_per_negative"):
        a, b = out[f"{name}_A"], out[f"{name}_B"]
        out[f"{name}_diff_B_minus_A"] = None if a is None or b is None else b - a
    return out


def stratified_bootstrap(table: Mapping, statistic: Callable[[Mapping, np.ndarray], dict], *,
                         n_resamples: int = 10000, seed: int = 20261013,
                         confidence: float = 0.95) -> dict:
    """Bootstrap percentil reamostrando imagens dentro de cada classe.

    O mesmo vetor de índices alimenta A e B em cada réplica, preservando o pareamento.
    Réplicas em que uma estatística fica indefinida (denominador zero) são contadas
    e excluídas apenas daquela estatística.
    """
    if n_resamples < 1 or not 0 < confidence < 1:
        raise ValueError("n_resamples >= 1 e confiança em (0,1).")
    labels = np.asarray(table["label"])
    strata = [np.flatnonzero(labels == value) for value in (0, 1)]
    strata = [s for s in strata if len(s)]
    full = np.arange(len(labels))
    estimate = statistic(table, full)
    rng = np.random.default_rng(seed)
    samples: dict[str, list[float]] = {key: [] for key in estimate}
    undefined = {key: 0 for key in estimate}
    for _ in range(n_resamples):
        index = np.concatenate([rng.choice(s, size=len(s), replace=True) for s in strata])
        replicate = statistic(table, index)
        for key in estimate:
            value = replicate.get(key)
            if value is None:
                undefined[key] += 1
            else:
                samples[key].append(value)
    alpha = (1 - confidence) / 2
    result = {}
    for key, value in estimate.items():
        values = np.asarray(samples[key], dtype=float)
        low, high = ((None, None) if value is None or not len(values)
                     else (float(np.quantile(values, alpha)), float(np.quantile(values, 1 - alpha))))
        result[key] = {"estimate": value, "ci_low": low, "ci_high": high,
                       "undefined_resamples": undefined[key]}
    return {"method": "bootstrap_percentil_estratificado_por_classe_reamostrando_imagens",
            "paired": True, "n_resamples": n_resamples, "seed": seed, "confidence": confidence,
            "n_images": int(len(labels)), "n_positive": int(labels.sum()),
            "n_negative": int(len(labels) - labels.sum()), "metrics": result}


def mcnemar_exact(correct_a: Sequence[bool | None], correct_b: Sequence[bool | None]) -> dict:
    """McNemar exato bilateral: binomial(b, b+c, 0,5) nos pares discordantes.

    Pares com erro de execução (None) em qualquer sistema saem do teste e são relatados.
    """
    from scipy.stats import binomtest

    if len(correct_a) != len(correct_b):
        raise ValueError("Vetores pareados de tamanhos diferentes.")
    pairs = [(bool(x), bool(y)) for x, y in zip(correct_a, correct_b) if x is not None and y is not None]
    both = sum(x and y for x, y in pairs)
    only_a = sum(x and not y for x, y in pairs)
    only_b = sum(y and not x for x, y in pairs)
    neither = sum(not x and not y for x, y in pairs)
    discordant = only_a + only_b
    p_value = 1.0 if discordant == 0 else float(binomtest(only_b, discordant, 0.5).pvalue)
    return {"test": "mcnemar_exato_bilateral", "n_pairs": len(pairs),
            "excluded_pairs_with_error": len(correct_a) - len(pairs),
            "both_correct": both, "only_A_correct": only_a, "only_B_correct": only_b,
            "both_wrong": neither, "discordant": discordant, "p_value": p_value}


def image_decision_tests(table: Mapping) -> dict:
    """McNemar por grupo (positivas, negativas) e no conjunto, decisão correta por imagem."""
    label = np.asarray(table["label"])

    def correct(decisions, index):
        return [None if decisions[i] is None else decisions[i] == label[i] for i in index]

    groups = {"positivas": np.flatnonzero(label == 1), "negativas": np.flatnonzero(label == 0),
              "todas": np.arange(len(label))}
    return {name: mcnemar_exact(correct(table["decision_a"], index), correct(table["decision_b"], index))
            for name, index in groups.items() if len(index)}


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    """Correção de Holm para a família de testes declarada no plano."""
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted, running = {}, 0.0
    m = len(ordered)
    for rank, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[name] = running
    return adjusted


def reviewed_precision(sample_rows: Sequence[Mapping], *, n_resamples: int = 10000,
                       seed: int = 20261013, confidence: float = 0.95) -> dict:
    """Precisão estimada por amostra aleatória simples de regiões positivas revisadas.

    Cada linha: image_id e decision em {"parasita", "nao_parasita", "incerto"}.
    Estimativa principal exclui incertos; limites de sensibilidade os tratam como
    todos errados (pior caso) e todos certos (melhor caso). O IC reamostra imagens
    (cluster bootstrap), pois regiões da mesma imagem são correlacionadas.
    """
    allowed = {"parasita", "nao_parasita", "incerto"}
    by_image: dict[str, list[str]] = {}
    for row in sample_rows:
        decision = row["decision"]
        if decision not in allowed:
            raise ValueError(f"Decisão inválida: {decision}")
        by_image.setdefault(str(row["image_id"]), []).append(decision)
    if not by_image:
        raise ValueError("Amostra revisada vazia.")
    images = sorted(by_image)
    counts = np.asarray([[d.count("parasita"), d.count("nao_parasita"), d.count("incerto")]
                         for d in (by_image[i] for i in images)], dtype=float)

    def estimates(c):
        tp, fp, unsure = c.sum(axis=0)
        decided = tp + fp
        return {"precision": None if decided == 0 else tp / decided,
                "precision_worst_case": None if decided + unsure == 0 else tp / (decided + unsure),
                "precision_best_case": None if decided + unsure == 0 else (tp + unsure) / (decided + unsure)}

    point = estimates(counts)
    rng = np.random.default_rng(seed)
    draws = {key: [] for key in point}
    for _ in range(n_resamples):
        replicate = estimates(counts[rng.integers(0, len(images), len(images))])
        for key, value in replicate.items():
            if value is not None:
                draws[key].append(value)
    alpha = (1 - confidence) / 2
    tp, fp, unsure = counts.sum(axis=0)
    return {"method": "amostra_aleatoria_simples_de_regioes_ic_bootstrap_por_imagem",
            "n_regions": int(counts.sum()), "n_images": len(images),
            "parasita": int(tp), "nao_parasita": int(fp), "incerto": int(unsure),
            "n_resamples": n_resamples, "seed": seed, "confidence": confidence,
            "metrics": {key: {"estimate": value,
                              "ci_low": float(np.quantile(draws[key], alpha)) if draws[key] else None,
                              "ci_high": float(np.quantile(draws[key], 1 - alpha)) if draws[key] else None}
                        for key, value in point.items()}}
