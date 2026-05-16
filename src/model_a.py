"""
Modelo A — replicação fiel da arquitetura usada pela Fuzzylab/FIOCRUZ.

Configuração original (do repo Fuzzylab, arquivo traindeddata.py):
    - ResNet-50 com pesos ImageNet
    - Base CONGELADA (transfer learning puro, sem fine-tuning)
    - Top: GlobalAveragePooling2D + Dropout(0.3) + Dense(softmax)
    - Optimizer: Adam, lr=1e-4
    - Loss: sparse_categorical_crossentropy
    - Sem data augmentation
    - 50 epochs com EarlyStopping (patience=3)
"""

from __future__ import annotations

import tensorflow as tf
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Model


def build_model_a(
    num_classes: int = 2,
    input_shape: tuple[int, int, int] = (224, 224, 3),
    dropout_rate: float = 0.3,
    freeze_base: bool = True,
) -> Model:
    """
    Constrói o Modelo A.

    Args:
        num_classes: número de classes (default 2: positivo/negativo).
        input_shape: shape da entrada.
        dropout_rate: taxa de dropout antes da camada final.
        freeze_base: se True (padrão), congela toda a ResNet-50.

    Returns:
        Modelo Keras compilado pronto para `.fit()`.
    """
    base_model = ResNet50(
        weights="imagenet",
        include_top=False,
        input_shape=input_shape,
    )
    base_model.trainable = not freeze_base

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(dropout_rate)(x)
    outputs = Dense(num_classes, activation="softmax")(x)

    model = Model(inputs=base_model.input, outputs=outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model
