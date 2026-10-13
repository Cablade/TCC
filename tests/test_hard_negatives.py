import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mine_hard_negatives import eligible_regions, sample_regions  # noqa: E402
from prepare_hard_negative_dataset import add_negative_regions  # noqa: E402
from sample_precision_review import sample_positive_regions  # noqa: E402
from src import data_protocol as dp  # noqa: E402
from src.region_review import load_decisions, save_region_views, write_queue, write_review_page  # noqa: E402


def annotation():
    return {"image_id": "m1", "width": 400, "height": 400, "review_status": "reviewed", "reviewer": "pub",
            "reference_complete": False, "whole_image_label": 1,
            "positives": [{"annotation_id": "p1", "point": [50, 50]}],
            "negative_regions": [{"annotation_id": "n1", "bbox": [300, 300, 400, 400],
                                  "review_status": "reviewed", "reviewer": "Caio"}]}


def test_eligible_regions_skip_points_known_negatives_and_low_scores():
    result = {"regions": [
        {"bbox": [0, 0, 100, 100], "class_id": 1, "scores": [0.1, 0.9]},      # contém ponto
        {"bbox": [150, 150, 250, 250], "class_id": 1, "scores": [0.2, 0.8]},  # elegível
        {"bbox": [300, 300, 400, 400], "class_id": 1, "scores": [0.1, 0.9]},  # já negativo revisado
        {"bbox": [150, 0, 250, 100], "class_id": 0, "scores": [0.7, 0.3]},    # negativo do modelo
        {"bbox": [0, 150, 100, 250], "class_id": 1, "scores": [0.45, 0.55]},  # abaixo do mínimo
    ]}
    out = eligible_regions(result, annotation(), min_score=0.6)
    assert [r["candidate_index"] for r in out] == [1]


def test_sampling_is_uniform_capped_and_reproducible():
    regions = {f"i{k}": [{"candidate_index": j, "bbox": [0, 0, 1, 1], "score_suspect": 0.9} for j in range(10)]
               for k in range(5)}
    a = sample_regions(regions, per_image=3, max_total=8, seed=1)
    b = sample_regions(regions, per_image=3, max_total=8, seed=1)
    assert a == b and len(a) == 8
    assert max(sum(1 for i, _ in a if i == k) for k in regions) <= 3


def test_confirmed_negatives_enter_reference_only_for_train():
    reference = {"schema_version": 1, "coordinate_convention": "xyxy_half_open", "images": [annotation()]}
    queue = {"checkpoint_sha256": "x", "items": [
        {"candidate_id": "c1", "image_id": "m1", "bbox": [150, 150, 250, 250]},
        {"candidate_id": "c2", "image_id": "m1", "bbox": [150, 0, 250, 100]}]}
    decisions = {"c1": {"decision": "negativo", "reviewer": "Caio"}, "c2": {"decision": "parasita", "reviewer": "Caio"}}
    accepted = add_negative_regions(reference, queue, decisions, {"m1"})
    assert [i["candidate_id"] for i in accepted] == ["c1"]
    checked = dp.validate_annotations(reference)
    assert dp.candidate_label([150, 150, 250, 250], checked["m1"]) == 0
    assert dp.candidate_label([150, 0, 250, 100], checked["m1"]) is None
    with pytest.raises(ValueError):
        add_negative_regions(json.loads(json.dumps(reference)), queue, decisions, set())


def test_review_queue_roundtrip_binds_decisions(tmp_path):
    image = np.full((400, 400, 3), 200, dtype=np.uint8)
    views = save_region_views(image, [150, 150, 250, 250], tmp_path, "c1")
    assert (tmp_path / views["crop_file"]).exists() and (tmp_path / views["context_file"]).exists()
    items = [{"candidate_id": "c1", "image_id": "m1", **views}]
    sha = write_queue(tmp_path, {"purpose": "t"}, items)
    page = write_review_page(tmp_path, sha, items, title="t", instructions="i",
                             options=[("negativo", "Neg"), ("parasita", "Par")])
    assert sha in page.read_text(encoding="utf-8")
    good = tmp_path / "d.json"
    good.write_text(json.dumps({"queue_sha256": sha, "reviewer": "Caio",
                                "decisions": [{"candidate_id": "c1", "decision": "negativo"}]}))
    _, decisions = load_decisions(tmp_path / "queue.json", good, {"negativo", "parasita"})
    assert decisions["c1"]["reviewer"] == "Caio"
    bad = tmp_path / "e.json"
    bad.write_text(json.dumps({"queue_sha256": "outra", "reviewer": "Caio", "decisions": []}))
    with pytest.raises(ValueError):
        load_decisions(tmp_path / "queue.json", bad, {"negativo"})


def test_precision_sample_uses_only_positive_regions_of_eligible_images():
    regions = [{"image_id": "a", "candidate_id": str(i), "class_id": str(i % 2)} for i in range(10)]
    regions += [{"image_id": "b", "candidate_id": "1", "class_id": "1"}]
    chosen, pool = sample_positive_regions(regions, {"a"}, n=3, seed=0)
    assert pool == 5 and len(chosen) == 3 and all(r["class_id"] == "1" and r["image_id"] == "a" for r in chosen)
