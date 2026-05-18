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
from typing import Callable, Iterator

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedKFold


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_splits(
    processed_dir: str | Path,
    output_dir: str | Path,
    test_size: float = 0.15,
    val_size: float = 0.15,
    seed: int = 42,
) -> None:
    """Gera CSVs train.csv, val.csv, test.csv com colunas [path, label]."""
    processed_dir = Path(processed_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def _rows_from_dir(root: Path) -> list[dict]:
        rows: list[dict] = []
        for label_name, label_id in (("negativo", 0), ("positivo", 1)):
            label_dir = root / label_name
            if not label_dir.exists():
                continue
            for img_path in sorted(label_dir.glob("*.png")):
                rows.append({
                    "path": str(img_path.relative_to(REPO_ROOT).as_posix()),
                    "label": int(label_id),
                })
        return rows

    # Caso A: já existe estrutura com train/test separados.
    has_split_dirs = (
        processed_dir / "train").exists() and (processed_dir / "test").exists()
    if has_split_dirs:
        train_rows = _rows_from_dir(processed_dir / "train")
        test_rows = _rows_from_dir(processed_dir / "test")
        if not train_rows or not test_rows:
            raise FileNotFoundError(
                "Nenhuma ROI encontrada em data/processed/{train,test}/{positivo,negativo}. "
                "Rode primeiro o script notebooks/gerar_rois.py."
            )

        train_df_full = pd.DataFrame(train_rows)
        test_df = pd.DataFrame(test_rows)

        # Val split é extraído do train.
        if not (0.0 < val_size < 1.0):
            raise ValueError("val_size deve estar entre 0 e 1")

        train_df, val_df = train_test_split(
            train_df_full,
            test_size=val_size,
            random_state=seed,
            stratify=train_df_full["label"],
        )
    else:
        # Caso B: tudo em processed/{positivo,negativo} (sem splits pré-definidos).
        all_rows = _rows_from_dir(processed_dir)
        if not all_rows:
            raise FileNotFoundError(
                "Nenhuma ROI encontrada em data/processed/{positivo,negativo} (ou em data/processed/train)."
            )
        df_all = pd.DataFrame(all_rows)

        if not (0.0 < test_size < 1.0):
            raise ValueError("test_size deve estar entre 0 e 1")
        if not (0.0 < val_size < 1.0):
            raise ValueError("val_size deve estar entre 0 e 1")
        if test_size + val_size >= 1.0:
            raise ValueError("test_size + val_size deve ser < 1")

        train_val_df, test_df = train_test_split(
            df_all,
            test_size=test_size,
            random_state=seed,
            stratify=df_all["label"],
        )

        # Ajusta val_size relativo ao conjunto restante.
        val_size_rel = val_size / (1.0 - test_size)
        train_df, val_df = train_test_split(
            train_val_df,
            test_size=val_size_rel,
            random_state=seed,
            stratify=train_val_df["label"],
        )

    train_df.to_csv(output_dir / "train.csv", index=False)
    val_df.to_csv(output_dir / "val.csv", index=False)
    test_df.to_csv(output_dir / "test.csv", index=False)


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
    if "path" not in df.columns or "label" not in df.columns:
        raise ValueError("DataFrame deve conter colunas: 'path' e 'label'")

    def _to_abs_path(p: str) -> str:
        pp = Path(p)
        if pp.is_absolute():
            return str(pp)
        return str((REPO_ROOT / pp).resolve())

    paths = df["path"].astype(str).map(_to_abs_path).to_numpy()
    labels = df["label"].astype(int).to_numpy()

    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(df), seed=seed,
                        reshuffle_each_iteration=True)

    target_h, target_w = int(image_size[0]), int(image_size[1])

    def _decode_png(path: tf.Tensor, label: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
        image_bytes = tf.io.read_file(path)
        image = tf.image.decode_png(image_bytes, channels=3)
        image = tf.image.resize(image, (target_h, target_w), method="bilinear")
        image = tf.cast(image, tf.float32) / 255.0
        return image, tf.cast(label, tf.int32)

    ds = ds.map(_decode_png, num_parallel_calls=tf.data.AUTOTUNE)

    if augment_fn is not None:
        if not isinstance(augment_fn, Callable):
            raise TypeError("augment_fn deve ser callable ou None")

        def _augment(image: tf.Tensor, label: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
            def _np_aug(img: np.ndarray) -> np.ndarray:
                # img chega como float32 [0,1]; converte pra uint8 pra albumentations.
                img_u8 = np.clip(img * 255.0, 0, 255).astype(np.uint8)
                aug_u8 = augment_fn(img_u8)
                aug_f = aug_u8.astype(np.float32) / 255.0
                return aug_f

            out = tf.numpy_function(_np_aug, [image], Tout=tf.float32)
            out.set_shape((target_h, target_w, 3))
            return out, label

        ds = ds.map(_augment, num_parallel_calls=tf.data.AUTOTUNE)

    ds = ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds


def kfold_splits(
    df: pd.DataFrame,
    k: int = 5,
    seed: int = 42,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Gera índices de Stratified K-Fold para cross-validation."""
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    yield from skf.split(df["path"], df["label"])
