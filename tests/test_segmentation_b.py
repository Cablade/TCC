"""Regressões de coordenadas, contexto e ausência de candidatos do B."""

import numpy as np
import pytest

from src.model_b import predict_image_b
from src.segmentation import contextual_box, crop_region, localization_hash, propose_regions


def test_no_regions_never_calls_classifier():
    def forbidden(*args, **kwargs):
        raise AssertionError("Não se deve classificar imagem sem regiões.")

    result = predict_image_b(np.full((64, 64, 3), 230, dtype=np.uint8), forbidden)
    assert result["status"] == "sem_regioes"
    assert result["regions"] == result["candidates"] == []
    assert result["original_decision"] == 0
    assert result["timings"]["classification_seconds"] == 0


def test_context_clips_borders_and_maps_original_pixels():
    image = np.arange(20 * 30 * 3, dtype=np.uint8).reshape(20, 30, 3)
    box = contextual_box([0, 0, 4, 4], image.shape, {"min_crop_size": 11})
    assert box == (0, 0, 7, 7)
    np.testing.assert_array_equal(crop_region(image, box), image[:7, :7])
    box = contextual_box([27, 17, 30, 20], image.shape, {"min_crop_size": 11})
    assert box == (23, 13, 30, 20)


def test_candidates_have_valid_context_and_original_bbox():
    image = np.full((80, 100, 3), 240, dtype=np.uint8)
    image[35:41, 45:51] = 25
    candidates, diagnostics = propose_regions(image, {"min_crop_size": 20})
    assert candidates and diagnostics["selected_pixels"] > 0
    for candidate in candidates:
        x1, y1, x2, y2 = candidate["bbox"]
        assert 0 <= x1 < x2 <= 100 and 0 <= y1 < y2 <= 80
        assert crop_region(image, candidate["bbox"]).shape == (y2 - y1, x2 - x1, 3)
    assert candidates[0]["proposal_bbox"] == [45, 35, 51, 41]


def test_invalid_rgb_and_config_are_not_silently_accepted():
    with pytest.raises(ValueError, match="uint8"):
        propose_regions(np.zeros((20, 20, 3), dtype=np.float32))
    with pytest.raises(ValueError, match="ímpar"):
        propose_regions(np.zeros((20, 20, 3), dtype=np.uint8), {"kernel_size": 4})
    assert localization_hash({}) == localization_hash(None)
    assert localization_hash({"min_crop_size": 101}) != localization_hash({})


def test_reviewed_crops_preserve_partitions_and_reject_wrong_labels(tmp_path):
    import hashlib
    import json
    import pandas as pd
    from PIL import Image
    from notebooks.gerar_rois import generate_crops
    from src.data_pipeline import file_sha256, validate_crop_manifest
    from src.data_protocol import write_manifest, load_annotations

    sources, entries = [], []
    for index, (split, label) in enumerate([("train", 0), ("train", 1), ("val", 0), ("val", 1)]):
        image = np.full((80, 100, 3), 230 + index, dtype=np.uint8)
        image[35:41, 45:51] = 25
        path = tmp_path / f"source_{index}.png"
        Image.fromarray(image).save(path)
        source = {"image_id": f"synthetic_{index}", "path": str(path), "sha256": file_sha256(path),
                  "width": 100, "height": 80, "source": "synthetic", "group_id": f"group_{index}",
                  "group_level": "imagem_original", "duplicate_of": "", "split": split}
        sources.append(source)
        entries.append({"image_id": source["image_id"], "width": 100, "height": 80,
                        "review_status": "reviewed", "reviewer": "synthetic_fixture",
                        "reference_complete": True, "whole_image_label": label,
                        "positives": [{"annotation_id": "p1", "point": [48, 38]}] if label else [],
                        "negative_regions": []})
    manifest = tmp_path / "images.csv"
    write_manifest(sources, manifest)
    annotation_path = tmp_path / "annotations.json"
    annotation_path.write_text(json.dumps({"schema_version": 1, "coordinate_convention": "xyxy_half_open",
                                            "images": entries}), encoding="utf-8")
    cfg = {"localization": {"min_crop_size": 20}}
    output = tmp_path / "crops"
    report = generate_crops(manifest, annotation_path, cfg, output)
    assert report["labeled_crops"] == 4
    crops = pd.read_csv(output / "crops.csv", keep_default_na=False)
    annotations = load_annotations(annotation_path, sources)
    validate_crop_manifest(crops, sources, annotations, localization_hash(cfg["localization"]),
                           file_sha256(annotation_path))
    assert set(crops[crops["split"] == "train"]["image_id"]) == {"synthetic_0", "synthetic_1"}
    assert set(crops[crops["split"] == "val"]["image_id"]) == {"synthetic_2", "synthetic_3"}
    crops.loc[0, "label"] = 1 - int(crops.loc[0, "label"])
    with pytest.raises(ValueError, match="rótulo"):
        validate_crop_manifest(crops, sources, annotations, localization_hash(cfg["localization"]),
                               file_sha256(annotation_path))
