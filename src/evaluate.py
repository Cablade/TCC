"""
Métricas auxiliares de recortes; não substituem detecção em imagem inteira.

Calcula acurácia, precisão, recall, F1-score, matriz de confusão e AUC.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None = None,
) -> dict:
    """
    Calcula um dicionário completo de métricas.

    Args:
        y_true: rótulos verdadeiros (shape [N]).
        y_pred: rótulos preditos (shape [N]).
        y_proba: escores da classe positiva (shape [N]), sem assumir calibração.

    Returns:
        Dict com chaves: accuracy, precision, recall, f1, auc (se y_proba),
        confusion_matrix.
    """
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    if y_true.ndim != 1 or y_true.shape != y_pred.shape or not y_true.size:
        raise ValueError('Rótulos/predições devem ser vetores não vazios do mesmo tamanho.')
    if not set(np.unique(y_true)).issubset({0,1}) or not set(np.unique(y_pred)).issubset({0,1}):
        raise ValueError('A avaliação de recortes é binária: 0 ou 1.')
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0,1]).tolist(),
    }
    if y_proba is not None:
        scores = np.asarray(y_proba)
        if scores.shape != y_true.shape or not np.isfinite(scores).all():
            raise ValueError('Escores devem ser finitos e alinhados aos rótulos.')
        metrics['auc'] = None
        metrics['roc'] = None
        if len(np.unique(y_true)) == 2:
            metrics["auc"] = roc_auc_score(y_true, scores)
            fpr, tpr, _ = roc_curve(y_true, scores)
            metrics["roc"] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
    return metrics


def metrics_to_dataframe(per_fold_metrics: list[dict]) -> pd.DataFrame:
    """Converte lista de métricas por fold em DataFrame com média e std."""
    df = pd.DataFrame(per_fold_metrics)
    summary = pd.DataFrame({
        "mean": df.mean(numeric_only=True),
        "std": df.std(numeric_only=True),
    })
    return summary
