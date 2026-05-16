"""
Carregamento de dados e construção de pipelines tf.data para treino,
validação e teste, com suporte a Stratified K-Fold.

Esperado:
    - data/processed/positivo/*.png
    - data/processed/negativo/*.png
    - data/splits/{train,val,test}.csv
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import StratifiedKFold


def build_splits(
    processed_dir: str | Path,
    output_dir: str | Path,
    test_size: float = 0.15,
    val_size: float = 0.15,
    seed: int = 42,
) -> None:
    """Gera CSVs train.csv, val.csv, test.csv com colunas [path, label]."""
    # TODO: listar arquivos, estratificar por classe, salvar splits
    raise NotImplementedError


def load_split(csv_path: str | Path) -> pd.DataFrame:
    """Carrega um split como DataFrame [path, label]."""
    return pd.read_csv(csv_path)


def make_dataset(
    df: pd.DataFrame,
    image_size: tuple[int, int] = (224, 224),
    batch_size: int = 32,
    augment_fn=None,
    shuffle: bool = True,
    seed: int = 42,
) -> tf.data.Dataset:
    """
    Constrói um tf.data.Dataset a partir de DataFrame [path, label].

    Args:
        df: DataFrame com colunas 'path' e 'label'.
        image_size: dimensão de saída (height, width).
        batch_size: tamanho do batch.
        augment_fn: função callable(image) -> image, ou None.
        shuffle: embaralha o dataset.

    Returns:
        tf.data.Dataset preparado e prefetched.
    """
    # TODO: implementar parsing + augmentation + prefetch
    raise NotImplementedError


def kfold_splits(
    df: pd.DataFrame,
    k: int = 5,
    seed: int = 42,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Gera índices de Stratified K-Fold para cross-validation."""
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    yield from skf.split(df["path"], df["label"])
