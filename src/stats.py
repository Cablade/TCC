"""
Testes estatísticos para comparar Modelo A e Modelo B.

Utilitários legados para vetores já agregados por grupos independentes.
Não são um protocolo automático: folds sobrepostos e sementes não representam
unidades independentes. A metodologia atual não exige significância.
"""

from __future__ import annotations

import numpy as np
from scipy import stats


def wilcoxon_paired(
    metric_a: list[float] | np.ndarray,
    metric_b: list[float] | np.ndarray,
    alpha: float = 0.05,
    *, independent_group_ids: list[str] | None = None,
) -> dict:
    """
    Teste de Wilcoxon pareado.

    H0: diferenças pareadas centradas em zero, sob pressupostos do teste.
    H1: bilateral (diferentes).

    Args:
        metric_a: métricas por grupo independente do Modelo A.
        metric_b: métricas pelos mesmos grupos, na mesma ordem, do Modelo B.
        alpha: nível de significância.

    Returns:
        Dict com statistic, p_value, significant (bool) e medianas descritivas.
    """
    a = np.asarray(metric_a, dtype=float)
    b = np.asarray(metric_b, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or len(a) < 2 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Vetores pareados finitos exigidos; planeje tamanho amostral por grupos.')
    if independent_group_ids is None or len(independent_group_ids) != len(a) or len(set(independent_group_ids)) != len(a):
        raise ValueError('Identifique uma observação por grupo independente; não use recortes/folds/sementes.')
    if np.array_equal(a,b):
        return {'statistic':0.0,'p_value':1.0,'significant':False,'alpha':alpha,
                'median_a':float(np.median(a)),'median_b':float(np.median(b)),
                'delta_median':0.0,'n':len(a)}
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
    *, independent_group_ids: list[str] | None = None,
) -> tuple[float, float]:
    """Intervalo de confiança da média via t-Student."""
    arr = np.asarray(values,dtype=float)
    if arr.ndim != 1 or len(arr)<2 or not np.isfinite(arr).all() or not 0<confidence<1:
        raise ValueError('Exige pelo menos dois valores finitos e nível em (0,1).')
    if independent_group_ids is None or len(independent_group_ids)!=len(arr) or len(set(independent_group_ids))!=len(arr):
        raise ValueError('Informe uma observação por grupo independente; viabilidade requer planejamento.')
    mean = arr.mean()
    sem = stats.sem(arr)
    h = sem * stats.t.ppf((1 + confidence) / 2, len(arr) - 1)
    return float(mean - h), float(mean + h)
