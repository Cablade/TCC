"""
Loop de treino reutilizável para Modelo A e Modelo B.

Carrega config YAML, executa fit() com callbacks de logging e
early stopping, e salva o modelo + métricas em experiments/.
"""

from __future__ import annotations

from pathlib import Path

import tensorflow as tf
import yaml


def load_config(config_path: str | Path) -> dict:
    """Carrega arquivo YAML de configuração."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_callbacks(
    checkpoint_path: str | Path,
    log_dir: str | Path,
    patience: int = 5,
    extra_callbacks: list | None = None,
) -> list:
    """Callbacks padrão: checkpoint + early stopping + tensorboard."""
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(checkpoint_path),
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=patience,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.TensorBoard(log_dir=str(log_dir)),
    ]
    if extra_callbacks:
        callbacks.extend(extra_callbacks)
    return callbacks


def train_model(
    model: tf.keras.Model,
    train_ds: tf.data.Dataset,
    val_ds: tf.data.Dataset,
    config: dict,
    run_name: str,
) -> tf.keras.callbacks.History:
    """
    Executa o treino e retorna o histórico.

    Espera em config:
        epochs, batch_size, patience, class_weights (opcional)
    """
    exp_root = Path("experiments")
    checkpoint_path = exp_root / "checkpoints" / f"{run_name}.keras"
    log_dir = exp_root / "logs" / run_name

    callbacks = get_callbacks(
        checkpoint_path=checkpoint_path,
        log_dir=log_dir,
        patience=config.get("patience", 5),
    )

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["epochs"],
        callbacks=callbacks,
        class_weight=config.get("class_weights"),
    )
    return history
