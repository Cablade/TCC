"""Verifica importação de coordenadas e limites de uso do rótulo publicado."""
from copy import deepcopy

import pytest

from scripts.import_public_annotations import SOURCE, import_points
from src.data_protocol import candidate_label


def fixture_rows():
    inventory = [{"image_id": "img_one", "path": "zip://archive.zip!train/field0001.jpg",
                  "width": "768", "height": "1024", "sha256": "a" * 64,
                  "source": SOURCE, "group_id": "img_one", "group_level": "imagem_original",
                  "duplicate_of": ""}]
    info = [{"filename": "field0001.jpg", "width": "768", "height": "1024",
             "n_structures": "2", "resize_factor": "1", "set": "train"}]
    positions = [{"filename": "field0001.jpg", "x": "100", "y": "200", "new_x": "100",
                  "new_y": "200", "set": "train", "structure": "NUCLEUS"},
                 {"filename": "field0001.jpg", "x": "110", "y": "210", "new_x": "110",
                  "new_y": "210", "set": "train", "structure": "KINETOPLAST"}]
    return inventory, positions, info


def test_published_points_do_not_create_negative_labels_or_complete_reference():
    payload, report, mapping = import_points(*fixture_rows())
    annotation = payload["images"][0]
    assert annotation["positives"][0]["point"] == [100, 200]
    assert annotation["review_basis"] == "published_author_annotations"
    assert annotation["reviewer"].startswith("Anotações publicadas")
    assert annotation["reference_complete"] is False
    assert annotation["negative_regions"] == []
    assert candidate_label([90, 190, 120, 220], annotation) == 1
    assert candidate_label([300, 300, 400, 400], annotation) is None
    assert report["train_ready_alone"] is False
    assert mapping[0]["source_split"] == "train"
    assert "split" not in mapping[0]


def test_original_coordinates_are_not_replaced_with_resized_coordinates():
    inventory, positions, info = fixture_rows()
    inventory[0].update(width="1536", height="2048")
    info[0].update(width="1536", height="2048", resize_factor="0.5")
    for row in positions:
        row["new_x"] = str(float(row["x"]) / 2)
        row["new_y"] = str(float(row["y"]) / 2)
    payload, _, _ = import_points(inventory, positions, info)
    assert payload["images"][0]["positives"][0]["point"] == [100, 200]


def test_duplicate_points_preserve_all_source_rows():
    inventory, positions, info = fixture_rows()
    positions.append(deepcopy(positions[0]))
    info[0]["n_structures"] = "3"
    payload, report, _ = import_points(inventory, positions, info)
    assert report["identical_points_merged"] == 1
    assert payload["images"][0]["positives"][0]["source_csv_rows"] == [2, 4]


@pytest.mark.parametrize("defect", ["dimensions", "scale", "bounds", "source", "ambiguous", "split"])
def test_rejects_unverifiable_mapping(defect):
    inventory, positions, info = fixture_rows()
    if defect == "dimensions":
        info[0]["width"] = "769"
    elif defect == "scale":
        positions[0]["new_x"] = "50"
    elif defect == "bounds":
        positions[0]["x"] = "800"
    elif defect == "source":
        inventory[0]["source"] = "unknown"
    elif defect == "ambiguous":
        inventory.append(deepcopy(inventory[0]))
    else:
        positions[0]["set"] = "test"
    with pytest.raises(ValueError):
        import_points(inventory, positions, info)


def test_source_summary_discrepancy_is_reported_and_never_claimed_complete():
    inventory, positions, info = fixture_rows()
    info[0]["n_structures"] = "3"
    payload, report, _ = import_points(inventory, positions, info)
    assert report["source_structure_count_discrepancies"] == [
        {"filename": "field0001.jpg", "images_info_n_structures": 3, "position_data_rows": 2}]
    assert payload["images"][0]["reference_complete"] is False
