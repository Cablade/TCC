"""Treina B a partir de manifestos revisados ou executa --smoke sintético curto."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(ROOT / "configs/model_b.yaml"))
    parser.add_argument("--run-name")
    parser.add_argument("--output-dir", default=str(ROOT / "experiments/runs"))
    parser.add_argument("--image-manifest")
    parser.add_argument("--crop-manifest")
    parser.add_argument("--annotations")
    parser.add_argument("--no-augment", action="store_true")
    parser.add_argument("--smoke", action="store_true",
                        help="Uma etapa sintética; pesos aleatórios, sem download e sem desempenho real.")
    args = parser.parse_args()
    if not args.smoke and not all((args.image_manifest, args.crop_manifest, args.annotations)):
        parser.error("Treino real exige --image-manifest, --crop-manifest e --annotations revisadas.")

    import numpy as np
    import tensorflow as tf
    from src import augmentation, data_pipeline, model_b, train
    from src.segmentation import localization_hash

    # Limita recursos do smoke e torna ordem de execução explícita.
    tf.config.threading.set_inter_op_parallelism_threads(2)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    cfg = train.load_config(args.config)
    for key, expected in {"optimizer": "AdamW", "loss": "categorical_crossentropy",
                          "selection_monitor": "val_loss", "selection_mode": "min"}.items():
        if cfg["training"].get(key, expected) != expected:
            raise ValueError(f"Configuração não suportada: training.{key}; esperado {expected}.")
    if cfg["training"].get("scheduler") not in {None, "cosine_annealing"}:
        raise ValueError("Scheduler não suportado; use cosine_annealing ou null.")
    if cfg["model"].get("batch_normalization", "frozen") != "frozen":
        raise ValueError("BatchNormalization deve permanecer frozen neste protocolo.")
    if cfg.get("augmentation", {}).get("policy", "rotations_90_and_flips") != "rotations_90_and_flips":
        raise ValueError("Aumento não suportado; use rotations_90_and_flips.")
    seed = int(cfg["data"]["seed"])
    tf.keras.utils.set_random_seed(seed)
    tf.config.experimental.enable_op_determinism()
    manifests = {"config": args.config}
    cfg["training"]["augmentation"] = bool(cfg["training"].get("augmentation", True)) and not args.no_augment
    run_name = args.run_name or ("b_smoke_" if args.smoke else "b_") + datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.smoke:
        cfg["model"].update(input_shape=[32, 32, 3], weights=None, unfreeze_last_n=0)
        cfg["data"]["image_size"] = [32, 32]
        cfg["training"].update(epochs=1, batch_size=2, augmentation=False, verbose=2)
        cfg["resolved_class_weights"] = None
        rng = np.random.default_rng(seed)
        x_train = rng.integers(0, 256, (2, 32, 32, 3), dtype=np.uint8).astype(np.float32)
        x_val = rng.integers(0, 256, (2, 32, 32, 3), dtype=np.uint8).astype(np.float32)
        labels = np.eye(2, dtype=np.float32)
        options = tf.data.Options()
        options.threading.private_threadpool_size = 1
        train_ds = tf.data.Dataset.from_tensor_slices((x_train, labels)).batch(2).with_options(options)
        val_ds = tf.data.Dataset.from_tensor_slices((x_val, labels)).batch(2).with_options(options)
    else:
        from src.data_protocol import load_annotations, read_manifest
        images = read_manifest(args.image_manifest)
        annotations = load_annotations(args.annotations, images)
        crops = data_pipeline.load_split(args.crop_manifest)
        data_pipeline.validate_crop_manifest(
            crops, images, annotations, localization_hash(cfg["localization"]),
            data_pipeline.file_sha256(args.annotations),
        )
        train_df = crops[crops["split"] == "train"].copy()
        val_df = crops[crops["split"] == "val"].copy()
        if train_df.empty or val_df.empty:
            raise ValueError("Treino e validação precisam de recortes revisados; não se divide crops automaticamente.")
        if set(train_df["label"].astype(int)) != {0, 1} or set(val_df["label"].astype(int)) != {0, 1}:
            raise ValueError("Train e val precisam conter as duas classes revisadas; examine a viabilidade por grupos.")
        image_size = tuple(cfg["data"]["image_size"])
        if tuple(cfg["model"]["input_shape"][:2]) != image_size:
            raise ValueError("image_size deve corresponder à entrada do modelo.")
        aug = None
        if cfg["training"]["augmentation"]:
            if image_size[0] != image_size[1]:
                raise ValueError("Rotações de 90 graus exigem crops redimensionados quadrados.")
            aug = augmentation.get_train_augmentations(image_size[0], seed=seed)
        train_ds = data_pipeline.make_dataset(
            train_df, image_size, cfg["training"]["batch_size"], aug, True, seed, partition="train")
        val_ds = data_pipeline.make_dataset(
            val_df, image_size, cfg["training"]["batch_size"], shuffle=False, partition="val")
        train_ds = train_ds.map(lambda x, y: (x, tf.one_hot(y, 2)), num_parallel_calls=1)
        val_ds = val_ds.map(lambda x, y: (x, tf.one_hot(y, 2)), num_parallel_calls=1)
        if cfg.get("class_weights") == "auto":
            counts = train_df["label"].astype(int).value_counts()
            cfg["resolved_class_weights"] = {int(k): float(len(train_df) / (2 * v)) for k, v in counts.items()}
        else:
            cfg["resolved_class_weights"] = cfg.get("class_weights")
        cfg["dataset_counts"] = {"train": len(train_df), "val": len(val_df)}
        manifests.update(images=args.image_manifest, crops=args.crop_manifest, annotations=args.annotations)

    model_cfg, train_cfg = cfg["model"], cfg["training"]
    model = model_b.build_model_b(
        num_classes=int(model_cfg["num_classes"]), input_shape=tuple(model_cfg["input_shape"]),
        dropout_rate=float(model_cfg["dropout_rate"]), unfreeze_last_n=int(model_cfg["unfreeze_last_n"]),
        label_smoothing=float(model_cfg["label_smoothing"]),
        learning_rate=float(train_cfg["learning_rate"]), weight_decay=float(train_cfg["weight_decay"]),
        weights=model_cfg.get("weights", "imagenet"),
    )
    callbacks = []
    if train_cfg.get("scheduler") == "cosine_annealing":
        callbacks.append(model_b.get_cosine_scheduler(float(train_cfg["learning_rate"]), int(train_cfg["epochs"])))
    result = train.train_model(
        model, train_ds, val_ds, cfg, run_name, output_dir=args.output_dir,
        manifest_paths=manifests, extra_callbacks=callbacks, synthetic=args.smoke,
    )
    if args.smoke:
        scores = np.asarray(result.loaded_model(x_val, training=False))
        again = tf.keras.models.load_model(result.checkpoint_path)
        np.testing.assert_allclose(scores, np.asarray(again(x_val, training=False)), rtol=1e-6, atol=1e-6)
        assert scores.shape == (2, 2) and np.isfinite(scores).all()
        specimen = np.full((128, 128, 3), 240, dtype=np.uint8)
        specimen[55:61, 58:66] = [40, 20, 70]
        whole_image = model_b.predict_image_b(specimen, result.loaded_model, cfg, "synthetic_b_smoke")
        if whole_image["status"] in {"erro", "sem_regioes"}:
            raise RuntimeError(f"Smoke de imagem inteira falhou: {whole_image}")
        smoke = {"synthetic": True, "purpose": "execucao_sem_medida_de_desempenho_real",
                 "reloaded_scores": scores.tolist(), "reload_equal": True, "whole_image": whole_image}
        (result.run_dir / "smoke.json").write_text(json.dumps(smoke, indent=2), encoding="utf-8")
    print(json.dumps({"run_dir": str(result.run_dir), "checkpoint": str(result.checkpoint_path),
                      "synthetic": args.smoke, "selection": "val_loss"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
