"""Dados do B: manifestos por imagem antes dos recortes; RGB float32 [0,255]."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]


def file_sha256(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def build_splits(*args, **kwargs):
    raise ValueError(
        "Dividir recortes foi desativado. Separe imagens/grupos via "
        "scripts/prepare_data.py antes de notebooks/gerar_rois.py."
    )


def kfold_splits(*args, **kwargs):
    raise ValueError("Não dividir recortes. A estratégia por grupos deve ser definida antes da extração.")


def load_split(csv_path):
    return pd.read_csv(csv_path, keep_default_na=False, dtype={
        "crop_id": str, "image_id": str, "group_id": str, "path": str,
        "source_sha256": str, "crop_sha256": str, "localization_sha256": str,
        "annotation_sha256": str,
    })


def validate_crop_manifest(crops, images, annotations, localization_sha256, annotation_sha256):
    """Revalida origem, grupo, rótulo revisado, configuração e conteúdo de cada crop."""
    from .data_protocol import candidate_label, validate_partitions

    validate_partitions(images)
    by_id = {row["image_id"]: row for row in images}
    required = {
        "crop_id", "image_id", "path", "label", "split", "group_id",
        "source_sha256", "crop_sha256", "bbox", "localization_sha256",
        "annotation_sha256", "review_status",
    }
    if not required.issubset(crops.columns):
        raise ValueError(f"Manifesto de recortes incompleto: {sorted(required - set(crops.columns))}")
    if crops["crop_id"].duplicated().any():
        raise ValueError("crop_id duplicado.")
    for row in crops.to_dict("records"):
        source = by_id.get(row["image_id"])
        if source is None:
            raise ValueError(f"Origem ausente no manifesto: {row['image_id']}")
        if row["split"] != source["split"] or str(row["group_id"]) != str(source["group_id"]):
            raise ValueError("Partição/grupo de crop diverge da imagem original.")
        if row["source_sha256"] != source["sha256"]:
            raise ValueError("Hash da imagem de origem diverge.")
        if row["localization_sha256"] != localization_sha256 or row["annotation_sha256"] != annotation_sha256:
            raise ValueError("Recortes usam localização/anotações diferentes; gere-os novamente.")
        annotation = annotations.get(row["image_id"])
        bbox = json.loads(row["bbox"]) if isinstance(row["bbox"], str) else row["bbox"]
        expected = candidate_label(bbox, annotation) if annotation is not None else None
        if row["review_status"] != "reviewed" or expected is None or int(row["label"]) != expected:
            raise ValueError("Crop sem rótulo revisado ou incompatível com as anotações.")
        crop_path = Path(row["path"])
        if not crop_path.is_absolute():
            crop_path = REPO_ROOT / crop_path
        if file_sha256(crop_path) != row["crop_sha256"]:
            raise ValueError(f"Conteúdo do crop mudou: {crop_path}")


def resize_rgb_for_model(image, image_size=(224, 224)):
    """Único resize de treino/inferência, sem divisão por 255."""
    import tensorflow as tf

    image = tf.cast(image, tf.float32)
    return tf.image.resize(image, tuple(image_size), method="bilinear")


def make_dataset(df, image_size=(224, 224), batch_size=32, augment_fn=None,
                 shuffle=True, seed=42, partition=None):
    import tensorflow as tf

    if not {"path", "label"}.issubset(df.columns) or df.empty:
        raise ValueError("Dataset precisa conter pelo menos um recorte e colunas path,label.")
    if augment_fn is not None and partition != "train":
        raise ValueError("Aumento de dados permitido somente com partition='train'.")
    if not set(df["label"].astype(int)).issubset({0, 1}):
        raise ValueError("Rótulos devem ser 0 ou 1.")
    if batch_size < 1:
        raise ValueError("batch_size deve ser positivo.")
    paths = [str(Path(p) if Path(p).is_absolute() else REPO_ROOT / p) for p in df["path"]]
    ds = tf.data.Dataset.from_tensor_slices((paths, df["label"].astype(int).to_numpy()))
    options = tf.data.Options()
    options.experimental_deterministic = True
    options.threading.private_threadpool_size = 1
    ds = ds.with_options(options)
    if shuffle:
        ds = ds.shuffle(len(df), seed=seed, reshuffle_each_iteration=True)

    def decode(path, label):
        image = tf.io.decode_image(tf.io.read_file(path), channels=3, expand_animations=False)
        image.set_shape((None, None, 3))
        return resize_rgb_for_model(image, image_size), tf.cast(label, tf.int32)

    ds = ds.map(decode, num_parallel_calls=1)
    if augment_fn is not None:
        def augment(image, label):
            out = tf.numpy_function(augment_fn, [image], Tout=tf.float32)
            out.set_shape((*image_size, 3))
            return tf.clip_by_value(out, 0.0, 255.0), label
        # Ordem serial também preserva a sequência do RNG do aumento.
        ds = ds.map(augment, num_parallel_calls=1)
    return ds.batch(batch_size).prefetch(1)
