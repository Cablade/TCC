"""
Modelo B — proposta do TCC.

Diferenças em relação ao Modelo A:
    - Arquitetura: EfficientNet-B0 (em vez de ResNet-50)
    - Fine-tuning: últimas N camadas convolucionais descongeladas
    - Otimizador: AdamW com weight decay
    - Scheduler: Cosine Annealing
    - Regularização: Label Smoothing + Dropout
    - (Augmentation aplicada via tf.data, ver augmentation.py)
"""

from __future__ import annotations

import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.losses import CategoricalCrossentropy
from tensorflow.keras.models import Model


def build_model_b(
    num_classes: int = 2,
    input_shape: tuple[int, int, int] = (224, 224, 3),
    dropout_rate: float = 0.3,
    unfreeze_last_n: int = 30,
    label_smoothing: float = 0.1,
    learning_rate: float = 1e-4,
    weight_decay: float = 1e-4,
) -> Model:
    """
    Constrói o Modelo B.

    Args:
        num_classes: número de classes.
        input_shape: shape da entrada.
        dropout_rate: dropout antes da camada final.
        unfreeze_last_n: quantas das últimas camadas da base descongelar.
        label_smoothing: alpha do label smoothing.
        learning_rate: LR inicial (será ajustado pelo scheduler).
        weight_decay: weight decay do AdamW.

    Returns:
        Modelo Keras compilado pronto para `.fit()`.
    """
    base_model = EfficientNetB0(
        weights="imagenet",
        include_top=False,
        input_shape=input_shape,
    )

    # Fine-tuning parcial: congela tudo, depois descongela as últimas N
    base_model.trainable = True
    for layer in base_model.layers[:-unfreeze_last_n]:
        layer.trainable = False

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(dropout_rate)(x)
    outputs = Dense(num_classes, activation="softmax")(x)

    model = Model(inputs=base_model.input, outputs=outputs)
    model.compile(
        optimizer=tf.keras.optimizers.AdamW(
            learning_rate=learning_rate,
            weight_decay=weight_decay,
        ),
        loss=CategoricalCrossentropy(label_smoothing=label_smoothing),
        metrics=["accuracy"],
    )
    return model


def get_cosine_scheduler(
    initial_lr: float = 1e-4,
    total_epochs: int = 30,
) -> tf.keras.callbacks.Callback:
    """Scheduler de Cosine Annealing como callback."""
    return tf.keras.callbacks.LearningRateScheduler(
        lambda epoch: 0.5 * initial_lr * (1 + tf.math.cos(
            tf.constant(epoch / total_epochs * 3.141592653589793)
        )).numpy()
    )
