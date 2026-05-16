"""
Testes estatísticos para comparar Modelo A e Modelo B.

Como as métricas por fold não são necessariamente normais e os modelos
são avaliados nos mesmos folds (amostras pareadas), usamos o teste
de Wilcoxon pareado como teste primário.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def wilcoxon_paired(
    metric_a: list[float] | np.ndarray,
    metric_b: list[float] | np.ndarray,
    alpha: float = 0.05,
) -> dict:
    """
    Teste de Wilcoxon pareado.

    H0: as duas distribuições de métrica têm a mesma mediana.
    H1: bilateral (diferentes).

    Args:
        metric_a: métricas por fold/seed do Modelo A.
        metric_b: métricas por fold/seed do Modelo B.
        alpha: nível de significância.

    Returns:
        Dict com statistic, p_value, significant (bool), effect_size.
    """
    a = np.array(metric_a)
    b = np.array(metric_b)
    statistic, p_value = stats.wilcoxon(a, b)
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": bool(p_value < alpha),
        "alpha": alpha,
        "median_a": float(np.median(a)),
        "median_b": float(np.median(b)),
        "delta_median": float(np.median(b) - np.median(a)),
        "n": len(a),
    }


def confidence_interval_mean(
    values: list[float] | np.ndarray,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Intervalo de confiança da média via t-Student."""
    arr = np.array(values)
    mean = arr.mean()
    sem = stats.sem(arr)
    h = sem * stats.t.ppf((1 + confidence) / 2, len(arr) - 1)
    return float(mean - h), float(mean + h)
