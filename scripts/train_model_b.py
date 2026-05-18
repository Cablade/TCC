"""Treino do Modelo B via linha de comando.

Fluxo:
1) (Opcional) Gera splits em data/splits/ a partir de data/processed/
2) Monta tf.data para treino/val/teste
3) Treina EfficientNetB0 (Modelo B) e salva checkpoint em experiments/checkpoints/
4) Avalia no conjunto de teste e salva métricas em experiments/results/

Uso:
    python scripts/train_model_b.py
    python scripts/train_model_b.py --config configs/model_b.yaml --run-name b_seed42

Pré-requisitos:
    - Rode antes: python notebooks/gerar_rois.py (gera data/processed/...)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src import augmentation, data_pipeline, evaluate, model_b, train  # noqa: E402


def _one_hot_if_needed(ds: tf.data.Dataset, loss_name: str, num_classes: int) -> tf.data.Dataset:
    if "categorical" not in loss_name.lower():
        return ds

    def _map(x, y):
        return x, tf.one_hot(y, depth=num_classes)

    return ds.map(_map, num_parallel_calls=tf.data.AUTOTUNE)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Treina o Modelo B (EfficientNetB0).")
    parser.add_argument(
        "--config", default="configs/model_b.yaml", help="Caminho do YAML de config")
    parser.add_argument("--run-name", default=None,
                        help="Nome da execução (default: model_b)")
    parser.add_argument("--no-augment", action="store_true",
                        help="Desliga augmentation (mesmo se config diz true)")
    parser.add_argument("--no-splits", action="store_true",
                        help="Não gera splits automaticamente")
    args = parser.parse_args()

    cfg = train.load_config(ROOT / args.config)
    run_name = args.run_name or "model_b"

    # Diretórios
    processed_dir = ROOT / "data" / "processed"
    splits_dir = ROOT / "data" / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)

    # Gera splits se necessário
    train_csv = splits_dir / "train.csv"
    val_csv = splits_dir / "val.csv"
    test_csv = splits_dir / "test.csv"

    if not args.no_splits and (not train_csv.exists() or not val_csv.exists() or not test_csv.exists()):
        data_cfg = cfg.get("data", {})
        data_pipeline.build_splits(
            processed_dir=processed_dir,
            output_dir=splits_dir,
            test_size=float(data_cfg.get("test_size", 0.15)),
            val_size=float(data_cfg.get("val_size", 0.15)),
            seed=int(data_cfg.get("seed", 42)),
        )

    if not train_csv.exists() or not val_csv.exists() or not test_csv.exists():
        raise FileNotFoundError(
            "Splits não encontrados em data/splits/. "
            "Rode scripts/train_model_b.py (sem --no-splits) ou gere manualmente."
        )

    train_df = data_pipeline.load_split(train_csv)
    val_df = data_pipeline.load_split(val_csv)
    test_df = data_pipeline.load_split(test_csv)

    # Configs
    data_cfg = cfg.get("data", {})
    train_cfg = cfg.get("training", {})
    model_cfg = cfg.get("model", {})

    image_size = tuple(int(x) for x in data_cfg.get("image_size", [224, 224]))
    batch_size = int(train_cfg.get("batch_size", 32))

    use_augment = bool(train_cfg.get("augmentation", True)
                       ) and (not args.no_augment)

    train_aug_fn = None
    if use_augment:
        aug = augmentation.get_train_augmentations(image_size=image_size[0])
        def train_aug_fn(img_u8): return augmentation.apply(aug, img_u8)

    # Datasets
    train_ds = data_pipeline.make_dataset(
        train_df,
        image_size=image_size,
        batch_size=batch_size,
        augment_fn=train_aug_fn,
        shuffle=True,
        seed=int(data_cfg.get("seed", 42)),
    )
    val_ds = data_pipeline.make_dataset(
        val_df,
        image_size=image_size,
        batch_size=batch_size,
        augment_fn=None,
        shuffle=False,
    )
    test_ds = data_pipeline.make_dataset(
        test_df,
        image_size=image_size,
        batch_size=batch_size,
        augment_fn=None,
        shuffle=False,
    )

    loss_name = str(train_cfg.get("loss", "categorical_crossentropy"))
    num_classes = int(model_cfg.get("num_classes", 2))

    train_ds = _one_hot_if_needed(
        train_ds, loss_name=loss_name, num_classes=num_classes)
    val_ds = _one_hot_if_needed(
        val_ds, loss_name=loss_name, num_classes=num_classes)

    # Modelo
    model = model_b.build_model_b(
        num_classes=num_classes,
        input_shape=tuple(int(x)
                          for x in model_cfg.get("input_shape", [224, 224, 3])),
        dropout_rate=float(model_cfg.get("dropout_rate", 0.3)),
        unfreeze_last_n=int(model_cfg.get("unfreeze_last_n", 30)),
        label_smoothing=float(model_cfg.get("label_smoothing", 0.1)),
        learning_rate=float(train_cfg.get("learning_rate", 1e-4)),
        weight_decay=float(train_cfg.get("weight_decay", 1e-4)),
    )

    # Class weights
    class_weight = None
    if cfg.get("class_weights") == "auto":
        classes = np.array([0, 1])
        weights = compute_class_weight(
            class_weight="balanced",
            classes=classes,
            y=train_df["label"].astype(int).to_numpy(),
        )
        class_weight = {int(c): float(w) for c, w in zip(classes, weights)}

    # Callbacks
    exp_root = ROOT / "experiments"
    ckpt_dir = exp_root / "checkpoints"
    logs_dir = exp_root / "logs"
    results_dir = exp_root / "results"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = ckpt_dir / f"{run_name}.keras"
    log_dir = logs_dir / run_name

    extra_callbacks = []
    if str(train_cfg.get("scheduler", "")).lower() in {"cosine", "cosine_annealing", "cosine-annealing"}:
        extra_callbacks.append(
            model_b.get_cosine_scheduler(
                initial_lr=float(train_cfg.get("learning_rate", 1e-4)),
                total_epochs=int(train_cfg.get("epochs", 40)),
            )
        )

    callbacks = train.get_callbacks(
        checkpoint_path=checkpoint_path,
        log_dir=log_dir,
        patience=int(train_cfg.get("patience", 7)),
        extra_callbacks=extra_callbacks,
    )

    # Treino
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=int(train_cfg.get("epochs", 40)),
        callbacks=callbacks,
        class_weight=class_weight,
    )

    # Avaliação
    probs = model.predict(test_ds, verbose=0)
    probs = np.asarray(probs)
    y_true = test_df["label"].astype(int).to_numpy()
    y_pred = probs.argmax(axis=1)
    y_proba = probs[:, 1] if probs.shape[1] > 1 else None

    metrics = evaluate.compute_metrics(
        y_true=y_true, y_pred=y_pred, y_proba=y_proba)

    out = {
        "run_name": run_name,
        "config": args.config,
        "n_train": int(len(train_df)),
        "n_val": int(len(val_df)),
        "n_test": int(len(test_df)),
        "use_augmentation": bool(use_augment),
        "history_keys": list(history.history.keys()),
        "metrics": metrics,
    }

    out_path = results_dir / f"{run_name}_metrics.json"
    out_path.write_text(json.dumps(
        out, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 60)
    print(f"Treino finalizado: {run_name}")
    print(f"Checkpoint: {checkpoint_path}")
    print(f"Métricas:   {out_path}")
    print("=" * 60)
    print({k: metrics[k] for k in metrics if k != "roc"})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
