"""Modelo B: localização configurável e EfficientNet-B0, ainda sem qualidade demonstrada."""

from __future__ import annotations

import math
import time

import numpy as np


def build_model_b(
    num_classes=2, input_shape=(224, 224, 3), dropout_rate=0.3,
    unfreeze_last_n=30, label_smoothing=0.1, learning_rate=1e-4,
    weight_decay=1e-4, weights="imagenet",
):
    """Recebe RGB float32 [0,255]; o Keras 2.15 inclui a reescala na base.

    N conta as últimas camadas da base, incluindo camadas sem parâmetros.
    BatchNormalization permanece congelada, inclusive durante fine-tuning.
    weights=None permite teste sintético sem baixar pesos.
    """
    import tensorflow as tf

    if int(unfreeze_last_n) != unfreeze_last_n or unfreeze_last_n < 0:
        raise ValueError("unfreeze_last_n deve ser inteiro não negativo.")
    if num_classes != 2:
        raise ValueError("O protocolo atual usa 0=negativo e 1=suspeito.")
    base = tf.keras.applications.EfficientNetB0(
        weights=weights, include_top=False, input_shape=input_shape,
    )
    for layer in base.layers:
        layer.trainable = False
    if unfreeze_last_n > 0:
        for layer in base.layers[-unfreeze_last_n:]:
            layer.trainable = not isinstance(layer, tf.keras.layers.BatchNormalization)
    inputs = tf.keras.Input(shape=input_shape, name="rgb_0_255")
    features = base(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(features)
    x = tf.keras.layers.Dropout(dropout_rate)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="class_scores")(x)
    model = tf.keras.Model(inputs, outputs, name="model_b")
    model.compile(
        optimizer=tf.keras.optimizers.AdamW(learning_rate=learning_rate, weight_decay=weight_decay),
        loss=tf.keras.losses.CategoricalCrossentropy(label_smoothing=label_smoothing),
        metrics=["accuracy"],
    )
    return model


def get_cosine_scheduler(initial_lr=1e-4, total_epochs=30):
    import tensorflow as tf

    if total_epochs < 1:
        raise ValueError("total_epochs deve ser >= 1.")
    return tf.keras.callbacks.LearningRateScheduler(
        lambda epoch: float(0.5 * initial_lr * (1 + math.cos(math.pi * epoch / total_epochs)))
    )


def compiled_inference(classifier, input_shape):
    """Mesmo classificador em grafo; lote variável evita retraçar o último lote."""
    import tensorflow as tf
    compiled = tf.function(lambda batch: classifier(batch, training=False),
                           input_signature=[tf.TensorSpec((None, *input_shape), tf.float32)])

    def call(batch, training=False):
        if training:
            raise ValueError("Execução compilada é exclusiva para inferência.")
        return compiled(tf.convert_to_tensor(batch, dtype=tf.float32))
    return call


def predict_image_b(image_rgb, classifier, config=None, image_id="unknown") -> dict:
    """Inferência em imagem inteira, mantendo sem_regioes e erros explícitos."""
    from .segmentation import propose_regions, crop_region

    config = config or {}
    result = {
        "image_id": image_id, "status": "erro", "regions": [], "candidates": [],
        "original_decision": None, "timings": {},
    }
    start = time.perf_counter()
    try:
        t0 = time.perf_counter()
        candidates, diagnostics = propose_regions(image_rgb, config.get("localization"))
        result["candidates"] = candidates
        result["localization"] = diagnostics
        result["timings"]["localization_seconds"] = time.perf_counter() - t0
        result["timings"]["classification_seconds"] = 0.0
        result["timings"]["preprocessing_seconds"] = 0.0
        if not candidates:
            result.update(status="sem_regioes", original_decision=0)
            return result
        from .data_pipeline import resize_rgb_for_model

        shape = config.get("model", {}).get("input_shape", [224, 224, 3])
        batch_size = int(config.get("training", {}).get("batch_size", 32))
        if batch_size < 1:
            raise ValueError("batch_size deve ser positivo.")
        scores_all = []
        for offset in range(0, len(candidates), batch_size):
            subset = candidates[offset:offset + batch_size]
            t0 = time.perf_counter()
            batch = np.stack([resize_rgb_for_model(crop_region(image_rgb, c["bbox"]), shape[:2]) for c in subset])
            result["timings"]["preprocessing_seconds"] += time.perf_counter() - t0
            t0 = time.perf_counter()
            scores = np.asarray(classifier(batch, training=False))
            result["timings"]["classification_seconds"] += time.perf_counter() - t0
            if scores.shape != (len(subset), 2) or not np.isfinite(scores).all():
                raise ValueError("Saída esperada do B: Nx2 escores finitos.")
            scores_all.extend(scores.tolist())
        result["regions"] = [
            {**c, "class_id": int(np.argmax(scores)), "scores": scores}
            for c, scores in zip(candidates, scores_all)
        ]
        positive = any(region["class_id"] == 1 for region in result["regions"])
        result.update(
            status="predicao_positiva" if positive else "regioes_sem_predicao_positiva",
            original_decision=int(positive),
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        result["timings"]["total_seconds"] = time.perf_counter() - start
    return result
