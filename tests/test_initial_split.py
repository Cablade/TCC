from collections import Counter

import pytest

from scripts.prepare_initial_split import build_assignments


def test_split_preserves_original_test_and_stratifies_review_availability():
    images, annotations = [], {}
    for index in range(25):
        image_id = f"image_{index:02d}"
        images.append({"image_id": image_id, "group_id": image_id, "group_level": "imagem_original",
                       "path": f"zip://public.zip!{'train' if index < 20 else 'test'}/{index}.jpg"})
        annotations[image_id] = {"negative_regions": [{"bbox": [0, 0, 10, 10]}] if index < 8 else []}
    result = build_assignments(images, annotations)
    assert Counter(result.values()) == {"train": 16, "val": 4, "test": 5}
    assert Counter(result[f"image_{i:02d}"] for i in range(8)) == {"train": 6, "val": 2}
    assert all(result[f"image_{i:02d}"] == "test" for i in range(20, 25))
    assert build_assignments(list(reversed(images)), annotations) == result
    assert build_assignments(images, annotations, seed=99) != result
    images[0]["group_level"] = "animal"
    with pytest.raises(ValueError, match="grupos por imagem"):
        build_assignments(images, annotations)
