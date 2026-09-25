"""Regressões de perda de revisão, origem não autorizada e vazamento do teste."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

import pytest

from scripts.merge_reviewed_reference import merge
from scripts.review_annotations import ReviewStore
from src import data_protocol as dp
from src.dataset_policy import validate_active_images


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def fixture(tmp_path):
    archive = tmp_path / "public.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("train/a.jpg", b"synthetic fixture, not biological pixels")
    rows = [{"image_id": "one", "path": f"zip://{archive.as_posix()}!train/a.jpg",
             "sha256": "a" * 64, "width": 100, "height": 100, "source": "synthetic",
             "group_id": "one", "group_level": "imagem_original", "duplicate_of": "",
             "split": "train"}]
    write_json(tmp_path / "configs/dataset.json", {
        "output_dir": "data/protocol/verified", "source": "synthetic",
        "expected_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()})
    inventory = tmp_path / "data/protocol/verified/eligible_inventory.csv"
    dp.write_manifest(rows, inventory)
    write_json(tmp_path / "data/annotations/negative_preselection_v1/development_reservation.json",
               {"images": [{"image_id": "one", "sha256": "a" * 64}]})
    return rows, inventory, archive


def test_received_package_relocates_without_changing_split_and_refuses_overwrite(tmp_path):
    from scripts.prepare_received import prepare
    from src.data_pipeline import file_sha256
    rows, inventory, archive = fixture(tmp_path)
    with zipfile.ZipFile(archive) as stream:
        rows[0]["sha256"] = hashlib.sha256(stream.read("train/a.jpg")).hexdigest()
    dp.write_manifest(rows, inventory)
    dp.write_manifest(rows, tmp_path / "data/splits/experimento/images.csv")
    crop = tmp_path / "data/processed/b_real_01/train/0/crop.png"
    crop.parent.mkdir(parents=True)
    crop.write_bytes(b"synthetic crop fixture")
    old_path = (tmp_path / "old_project/data/processed/b_real_01/train/0/crop.png").as_posix()
    crops = [{"crop_id": "crop", "path": old_path, "crop_sha256": file_sha256(crop),
              "label": "0", "split": "train", "image_id": "one"}]
    dp.write_manifest(crops, tmp_path / "data/processed/b_real_01/crops.csv", list(crops[0]))
    write_json(tmp_path / "configs/experiment_cpu.json", {
        "image_manifest": "data/splits/experimento/images.csv",
        "crop_manifest": "data/processed/b_real_01/crops.csv", "run_name": "initial"})
    config = json.loads(prepare(archive, root=tmp_path).read_text(encoding="utf-8"))
    moved = dp.read_manifest(tmp_path / config["crop_manifest"])
    assert Path(moved[0]["path"]) == crop
    assert moved[0]["label"] == "0" and moved[0]["split"] == "train"
    assert dp.read_manifest(tmp_path / config["image_manifest"])[0]["image_id"] == "one"
    assert config["run_name"] == "initial"
    with pytest.raises(FileExistsError, match="já foi preparado"):
        prepare(archive, root=tmp_path)


def test_source_guard_accepts_relocation_but_rejects_other_zip(tmp_path):
    rows, _, archive = fixture(tmp_path)
    relocated = tmp_path / "relocated.zip"
    relocated.write_bytes(archive.read_bytes())
    rows[0]["path"] = f"zip://{relocated.as_posix()}!train/a.jpg"
    assert validate_active_images(rows, root=tmp_path)["images"] == 1
    relocated.write_bytes(b"another dataset under the same filename")
    with pytest.raises(ValueError, match="ZIP não corresponde"):
        validate_active_images(rows, root=tmp_path)


@pytest.mark.parametrize("key,value", [("image_id", "foreign"), ("sha256", "b"*64),
                                       ("path", "zip://other.zip!train/wrong.jpg"),
                                       ("split", "test")])
def test_source_guard_rejects_foreign_identity_or_reviewed_test(tmp_path, key, value):
    rows, _, _ = fixture(tmp_path)
    rows[0][key] = value
    with pytest.raises(ValueError):
        validate_active_images(rows, root=tmp_path)


def review_fixture(tmp_path):
    rows, inventory, _ = fixture(tmp_path)
    base = dp.annotation_template(rows)
    base["images"][0].update(review_status="reviewed", reviewer="synthetic source",
                             positives=[{"annotation_id": "p", "point": [90, 90]}])
    base["images"][0]["negative_regions"] = [{"annotation_id": "original",
        "bbox": [0, 0, 10, 10], "review_status": "reviewed", "reviewer": "synthetic source"}]
    source = tmp_path / "base.json"
    write_json(source, base)
    batch = tmp_path / "batch"
    dp.write_manifest(rows, batch / "inventory.csv")
    write_json(batch / "source_annotations.json", base)
    reviewed = batch / "reviewed.json"
    store = ReviewStore(batch / "inventory.csv", batch / "source_annotations.json", reviewed)
    store.change({"image_id": "one", "bbox": [20, 20, 30, 30], "confirmed": True,
                  "reviewer": "synthetic reviewer"})
    return inventory, source, reviewed, tmp_path / "merged.json"


def test_merge_preserves_old_negatives_and_full_history(tmp_path):
    paths = review_fixture(tmp_path)
    assert merge(*paths)["imported_regions"] == 1
    merged = json.loads(paths[-1].read_text(encoding="utf-8"))
    assert len(merged["images"][0]["negative_regions"]) == 2
    assert merged["review_imports"][0]["history"][0]["action"] == "add"
    # A referência incorporada pode ser aberta para continuar revisando em outro arquivo.
    ReviewStore(paths[0], paths[-1], tmp_path / "next_review.json")


def test_merge_refuses_mismatched_source_and_preserves_output(tmp_path):
    paths = review_fixture(tmp_path)
    source = paths[2].parent / "source_annotations.json"
    payload = json.loads(source.read_text())
    payload["images"][0]["positives"][0]["point"] = [89, 90]
    write_json(source, payload)
    with pytest.raises(ValueError, match="original mudou"):
        merge(*paths)
    assert not paths[-1].exists()


def test_training_interruption_is_recorded(tmp_path):
    from src.train import train_model
    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        train_model(SimpleNamespace(fit=interrupted), None, None,
                    {"data": {"seed": 42}, "training": {"epochs": 1}},
                    "interrupt", output_dir=tmp_path, synthetic=True)
    metadata = json.loads((tmp_path / "interrupt/metadata.json").read_text())
    assert metadata["status"] == "interrupted"
