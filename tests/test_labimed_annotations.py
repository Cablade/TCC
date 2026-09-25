"""Regression checks for published field labels and patient independence."""
import hashlib
import importlib.util
from pathlib import Path

from PIL import Image
import pytest

from src import data_protocol as dp


spec = importlib.util.spec_from_file_location(
    "labimed_import", Path(__file__).parents[1] / "scripts/import_labimed_annotations.py")
labimed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(labimed)


@pytest.fixture
def published_subset(tmp_path, monkeypatch):
    images = tmp_path / "images"
    images.mkdir()
    assets, selection = [], []
    for index, name in enumerate(("positive.jpg", "negative.jpg")):
        path = images / name
        Image.new("RGB", (4128, 3096), (index * 50, 10, 20)).save(path)
        asset = dict(assetFile=name, caseId="same_positive_donor", sampleId=f"slide_{index}",
                     sample_type="Blood_thin")
        assets.append(asset)
        selection.append(dict(asset, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                              width=4128, height=3096, parasite_bbox_count=1-index))
    boxes = [dict(assetFile="positive.jpg", xmin=20, ymin=30, xmax=80, ymax=100,
                  label_str="Tripanosoma")]
    for name, rows in (("assets.csv", assets), ("bboxes.csv", boxes), ("selection.csv", selection)):
        dp.write_manifest(rows, tmp_path / name, fields=list(rows[0]))
    monkeypatch.setattr(labimed, "HASHES", {
        name: hashlib.md5((tmp_path / name).read_bytes()).hexdigest()
        for name in ("assets.csv", "bboxes.csv")})
    return tmp_path


def test_field_negative_retains_positive_donor_and_single_group(published_subset):
    rows, annotations, report = labimed.import_reference(published_subset)
    assert [r["whole_image_label"] for r in rows] == [1, 0]
    assert {r["donor_status"] for r in rows} == {"positive"}
    assert len({r["group_id"] for r in rows}) == 1
    assert annotations["images"][0]["positives"][0]["bbox"] == [20, 30, 80, 100]
    assert annotations["provenance"]["new_tcc_human_review"] is False
    assert report["independent_negative_cases"] == 1
    assert report["split_created"] is False
    assert report["three_way_patient_split_with_both_classes_possible"] is False


def test_changed_image_is_rejected(published_subset):
    with (published_subset / "images/negative.jpg").open("ab") as handle:
        handle.write(b"changed")
    with pytest.raises(ValueError, match="Imagem modificada"):
        labimed.import_reference(published_subset)


def test_changed_published_metadata_is_rejected(published_subset):
    with (published_subset / "bboxes.csv").open("a", encoding="utf-8") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="Metadados publicados alterados"):
        labimed.import_reference(published_subset)
