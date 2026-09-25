"""Treino exclusivo do B; seleção e reabertura do mesmo best.keras por val_loss."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
import json
from pathlib import Path
import platform
import shutil
import time

import numpy as np

from .data_pipeline import file_sha256


def load_config(config_path):
    import yaml

    with open(config_path, encoding="utf-8-sig") as stream:
        return yaml.safe_load(stream)


def versions():
    packages = {}
    for name in ("tensorflow", "tensorflow-intel", "keras", "numpy", "opencv-python", "pandas"):
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": platform.python_version(), "platform": platform.platform(), "packages": packages}


def get_callbacks(checkpoint_path, log_dir, patience=5, extra_callbacks=None):
    import tensorflow as tf

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(str(checkpoint_path), monitor="val_loss",
                                           mode="min", save_best_only=True),
        # O único artefato selecionado será reaberto; não há restauração divergente em memória.
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", mode="min", patience=patience,
                                         restore_best_weights=False),
        tf.keras.callbacks.CSVLogger(str(Path(log_dir) / "epochs.csv")),
    ]
    return callbacks + list(extra_callbacks or [])


@dataclass
class TrainingResult:
    loaded_model: object
    history: dict
    checkpoint_path: Path
    run_dir: Path


def train_model(model, train_ds, val_ds, config, run_name, *, output_dir=None,
                manifest_paths=None, extra_callbacks=None, synthetic=False):
    import tensorflow as tf

    if not run_name or Path(run_name).name != run_name or run_name in {".", ".."}:
        raise ValueError("run_name deve ser um nome simples de diretório.")
    run_dir = Path(output_dir or Path(__file__).resolve().parents[1] / "experiments" / "runs") / run_name
    run_dir.mkdir(parents=True, exist_ok=False)
    checkpoint = run_dir / "best.keras"
    training = config["training"]
    seed = int(config["data"]["seed"])
    info = {
        "run_name": run_name, "synthetic": bool(synthetic), "seed": seed,
        "selection": {"monitor": "val_loss", "mode": "min", "artifact": "best.keras"},
        "versions": versions(), "manifests": {},
        "hardware": {"processor": platform.processor(),
                     "devices": [device.name for device in tf.config.list_physical_devices()]},
        "input": {"channels": "RGB", "dtype": "float32", "range": [0, 255]},
        "classes": {"0": "negativo", "1": "suspeito"},
        "status": "running",
    }
    (run_dir / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    for name, path in (manifest_paths or {}).items():
        path = Path(path)
        copy_to = run_dir / f"input_{name}{path.suffix}"
        shutil.copyfile(path, copy_to)
        info["manifests"][name] = {"source": str(path.resolve()), "copy": copy_to.name,
                                    "sha256": file_sha256(copy_to)}
    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    callbacks = get_callbacks(checkpoint, run_dir, int(training.get("patience", 5)), extra_callbacks)
    t0 = time.perf_counter()
    try:
        history = model.fit(train_ds, validation_data=val_ds, epochs=int(training["epochs"]),
                            callbacks=callbacks, class_weight=config.get("resolved_class_weights"),
                            verbose=int(training.get("verbose", 2))).history
        history = {key: [float(v) for v in values] for key, values in history.items()}
        (run_dir / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
        losses = np.asarray(history.get("val_loss", []), dtype=float)
        if not losses.size or not np.isfinite(losses).all() or not checkpoint.is_file():
            raise RuntimeError("Treino sem val_loss finita/checkpoint selecionado.")
        info["training_seconds"] = time.perf_counter() - t0
        # Avaliação/inferência sempre recebe o artefato persistido selecionado.
        selected = tf.keras.models.load_model(checkpoint)
        info.update(status="complete", selected_epoch=int(np.argmin(losses)) + 1,
                    selected_val_loss=float(np.min(losses)),
                    checkpoint_sha256=file_sha256(checkpoint), checkpoint_bytes=checkpoint.stat().st_size)
    except (Exception, KeyboardInterrupt) as exc:
        info.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "error",
                    error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        info["elapsed_seconds"] = time.perf_counter() - t0
        metadata_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    return TrainingResult(selected, history, checkpoint, run_dir)
