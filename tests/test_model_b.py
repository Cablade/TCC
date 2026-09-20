"""Regressões B: faixa RGB, congelamento, seleção/persistência do checkpoint."""

import json

import numpy as np
import pandas as pd
import pytest
from PIL import Image

tf = pytest.importorskip("tensorflow")

from src import data_pipeline, model_b, train


def test_rgb_preprocessing_keeps_0_255_and_channels(tmp_path):
    pixels = np.full((9, 11, 3), [17, 129, 255], dtype=np.uint8)
    path = tmp_path / "rgb.png"
    Image.fromarray(pixels).save(path)
    df = pd.DataFrame([{"path": str(path), "label": 1}])
    batch, labels = next(iter(data_pipeline.make_dataset(df, image_size=(32, 32), shuffle=False)))
    assert batch.dtype == tf.float32
    np.testing.assert_allclose(batch[0, 0, 0], [17, 129, 255])
    np.testing.assert_allclose(batch[0], data_pipeline.resize_rgb_for_model(pixels, (32, 32)))
    assert int(labels[0]) == 1


@pytest.mark.parametrize("unfreeze", [0, 30])
def test_freeze_zero_and_batch_norm(unfreeze):
    tf.keras.backend.clear_session()
    model = model_b.build_model_b(input_shape=(32, 32, 3), unfreeze_last_n=unfreeze, weights=None)
    base = model.get_layer("efficientnetb0")
    bn_layers = [layer for layer in base.layers if isinstance(layer, tf.keras.layers.BatchNormalization)]
    assert bn_layers and all(not layer.trainable for layer in bn_layers)
    if unfreeze == 0:
        assert not base.trainable_weights
    else:
        assert base.trainable_weights
        assert all(not layer.trainable for layer in base.layers[:-unfreeze])
    assert model.get_layer("class_scores").trainable_weights


def test_augmentation_rejected_outside_train(tmp_path):
    df = pd.DataFrame([{"path": "unused.png", "label": 0}])
    with pytest.raises(ValueError, match="somente"):
        data_pipeline.make_dataset(df, augment_fn=lambda x: x, partition="val")


def test_split_by_crop_disabled():
    with pytest.raises(ValueError, match="Dividir recortes"):
        data_pipeline.build_splits("unused", "unused")


def test_single_selection_criterion_and_reload(tmp_path):
    tf.keras.utils.set_random_seed(42)
    model = tf.keras.Sequential([
        tf.keras.layers.Input((2,)), tf.keras.layers.Dense(2, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="categorical_crossentropy")
    x = np.asarray([[0, 1], [1, 0]], dtype=np.float32)
    y = np.eye(2, dtype=np.float32)
    options = tf.data.Options()
    options.threading.private_threadpool_size = 1
    ds = tf.data.Dataset.from_tensor_slices((x, y)).batch(2).with_options(options)
    cfg = {"data": {"seed": 42}, "training": {"epochs": 2, "verbose": 0}}
    callbacks = train.get_callbacks(tmp_path / "unused.keras", tmp_path)
    assert callbacks[0].monitor == callbacks[1].monitor == "val_loss"
    assert callbacks[1].restore_best_weights is False
    result = train.train_model(model, ds, ds, cfg, "synthetic", output_dir=tmp_path, synthetic=True)
    reopened = tf.keras.models.load_model(result.checkpoint_path)
    np.testing.assert_allclose(result.loaded_model(x), reopened(x), atol=1e-7)
    metadata = json.loads((result.run_dir / "metadata.json").read_text())
    assert metadata["selected_epoch"] == int(np.argmin(result.history["val_loss"])) + 1
    assert metadata["checkpoint_sha256"] == data_pipeline.file_sha256(result.checkpoint_path)
    assert metadata["synthetic"] is True


def test_whole_image_cli_and_synthetic_test_guard(tmp_path):
    """CLI real com fixture sintética; também verifica o contrato da comparação."""
    from pathlib import Path
    import subprocess
    import sys
    from src.data_protocol import write_manifest, annotation_template, validate_annotations
    from src.detection_evaluation import load_predictions, compare_systems

    root = Path(__file__).resolve().parents[1]
    checkpoint = tmp_path / "best.keras"
    model = model_b.build_model_b(input_shape=(32, 32, 3), weights=None, unfreeze_last_n=0)
    model.save(checkpoint)
    cfg = {"model": {"input_shape": [32, 32, 3]}, "training": {"batch_size": 2},
           "localization": {"min_crop_size": 20}}
    (tmp_path / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    (tmp_path / "metadata.json").write_text(json.dumps({"synthetic": True}), encoding="utf-8")
    sources = []
    for index in range(2):
        image = np.full((80, 100, 3), 240, dtype=np.uint8)
        if index:
            image[35:41, 45:51] = 25
        path = tmp_path / f"image_{index}.png"
        Image.fromarray(image).save(path)
        sources.append({"image_id": f"synthetic_{index}", "path": str(path),
                        "sha256": data_pipeline.file_sha256(path), "width": 100, "height": 80,
                        "source": "synthetic", "group_id": f"group_{index}",
                        "group_level": "imagem_original", "duplicate_of": "", "split": "development"})
    manifest = tmp_path / "images.csv"
    write_manifest(sources, manifest)
    out = tmp_path / "result"
    command = [sys.executable, str(root / "scripts/run_model_b.py"), "--manifest", str(manifest),
               "--checkpoint", str(checkpoint), "--output-dir", str(out)]
    completed = subprocess.run(command + ["--split", "development"], capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads((out / "predictions.json").read_text(encoding="utf-8"))
    assert payload["system"] == "B" and payload["schema_version"] == 1
    assert payload["artifact"]["trained_on_synthetic_data"] is True
    predictions = load_predictions(out / "predictions.json", "B")
    assert [row["image_id"] for row in predictions] == [row["image_id"] for row in sources]
    assert predictions[0]["status"] == "sem_regioes"
    assert predictions[1]["status"] in {"predicao_positiva", "regioes_sem_predicao_positiva"}
    annotations = validate_annotations(annotation_template(sources), sources)
    fixture_a = [dict(row, regions=[], candidates=[], status="sem_regioes", original_decision=0)
                 for row in predictions]
    comparison = compare_systems(sources, annotations, fixture_a, predictions, split="development")
    assert set(comparison["image_ids"]) == {row["image_id"] for row in sources}
    denied = subprocess.run(command + ["--split", "test"], capture_output=True, text=True, timeout=60)
    assert denied.returncode != 0 and "Checkpoint sintético" in denied.stderr
