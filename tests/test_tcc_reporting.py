import pytest
from src.tcc_reporting import paired_ids, coverage_rows


def test_pairing_rejects_duplicates_and_missing_images():
    a = [{"image_id": "x"}, {"image_id": "y"}]
    assert paired_ids(a, list(reversed(a)), {"x", "y"}) == ["x", "y"]
    with pytest.raises(ValueError):
        paired_ids(a, [a[0], a[0]], {"x", "y"})
    with pytest.raises(ValueError):
        paired_ids(a, [a[0]], {"x", "y"})


def test_coverage_uses_one_to_one_and_keeps_uncovered_points():
    box = [0, 0, 10, 10]
    references = {"x": {"positives": [{"point": [2, 2]}, {"point": [3, 3]}, {"point": [90, 90]}]}}
    predictions = {"A": {"x": {"candidates": [{"bbox": box}, {"bbox": box}],
        "regions": [{"bbox": box, "class_id": 1}, {"bbox": box, "class_id": 0}]}}}
    row = coverage_rows(predictions, references)[0]
    assert row["reference_points"] == 3
    assert row["matched_proposals"] == 2
    assert row["matched_positive_regions"] == 1


def test_no_proposals_does_not_remove_reference_denominator():
    rows = coverage_rows({"B": {"x": {"candidates": [], "regions": []}}},
                         {"x": {"positives": [{"point": [1, 1]}]}})
    assert rows[0]["reference_points"] == 1
    assert rows[0]["matched_positive_regions"] == 0
