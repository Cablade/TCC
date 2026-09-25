"""Bloqueios do lançador e integridade do transporte, sem treinar TensorFlow."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import zipfile

from PIL import Image
import pytest

from scripts import relocate_experiment as relocation
from scripts import start_training as launcher
from src import data_protocol as dp


def experiment(tmp_path):
    config = {
        "image_manifest": str(tmp_path / "images.csv"),
        "crop_manifest": str(tmp_path / "crops.csv"),
        "annotations": str(tmp_path / "reference.json"),
        "model_config": str(tmp_path / "custom_cpu.yaml"),
        "output_dir": str(tmp_path / "runs"),
        "run_name": "b_custom_cpu", "require_gpu": False,
    }
    path = tmp_path / "experiment.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path, config


@pytest.mark.parametrize("ready_data,runtime_ok", [(False, True), (True, False), (False, False)])
def test_launcher_blocks_training_until_data_and_runtime_ready(tmp_path, monkeypatch, ready_data, runtime_ok):
    path, _ = experiment(tmp_path)
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher.sys, "argv", ["start_training.py", "--experiment", str(path)])
    monkeypatch.setattr(launcher, "check_data", lambda cfg: {
        "ready_data": ready_data, "checks": [], "warnings": []})
    monkeypatch.setattr(launcher, "check_runtime", lambda require_gpu: {"ok": runtime_ok})
    monkeypatch.setattr(launcher.subprocess, "run", lambda *a, **k: pytest.fail("Treino indevido"))
    assert launcher.main() == 2
    report = json.loads((tmp_path / "data/protocol/readiness_experiment.json").read_text())
    assert report["ready_to_train"] is False


@pytest.mark.parametrize("check_only", [True, False])
def test_launcher_passes_exact_validated_experiment_to_training(tmp_path, monkeypatch, check_only):
    path, config = experiment(tmp_path)
    checks, calls = [], []
    monkeypatch.setattr(launcher, "ROOT", tmp_path)
    monkeypatch.setattr(launcher.sys, "argv", ["start_training.py", "--experiment", str(path)]
                        + (["--check-only"] if check_only else []))

    def check_data(received):
        checks.append(deepcopy(received))
        return {"ready_data": True, "checks": [], "warnings": ["Referência de teste pendente"]}

    def check_runtime(require_gpu):
        assert require_gpu is config["require_gpu"]
        return {"ok": True}

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(launcher, "check_data", check_data)
    monkeypatch.setattr(launcher, "check_runtime", check_runtime)
    monkeypatch.setattr(launcher.subprocess, "run", run)
    assert launcher.main() == (0 if check_only else 7)
    assert checks == [config]
    if check_only:
        assert not calls
    else:
        command, kwargs = calls[0]
        assert command[:2] == [launcher.sys.executable, str(tmp_path / "scripts/train_model_b.py")]
        arguments = dict(zip(command[2::2], command[3::2]))
        assert arguments == {
            "--image-manifest": config["image_manifest"],
            "--crop-manifest": config["crop_manifest"],
            "--annotations": config["annotations"],
            "--config": config["model_config"],
            "--run-name": config["run_name"],
            "--output-dir": config["output_dir"],
        }
        assert kwargs == {"cwd": tmp_path}


def test_remap_obeys_path_boundaries_and_most_specific_prefix(tmp_path):
    old = (tmp_path / "old").as_posix()
    new = (tmp_path / "new").as_posix()
    special = (tmp_path / "special").as_posix()
    mappings = [(old, new), (old + "/images", special)]
    assert relocation.remap(old + "/images/a.png", mappings) == special + "/a.png"
    assert relocation.remap(old + "/crops/a.png", mappings) == new + "/crops/a.png"
    assert relocation.remap(old + "_other/a.png", mappings) == old + "_other/a.png"
    assert relocation.remap("zip://" + old + "/raw.zip!old/images/a.png", mappings) == (
        "zip://" + new + "/raw.zip!old/images/a.png")


def png_bytes(color):
    stream = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(stream, format="PNG")
    return stream.getvalue()


def transfer_fixture(tmp_path):
    """O local antigo nem existe: somente bytes na máquina nova estão disponíveis."""
    old, new = tmp_path / "old", tmp_path / "new"
    new.mkdir()
    pixels, crop_pixels = png_bytes("red"), png_bytes("blue")
    with zipfile.ZipFile(new / "raw.zip", "w") as archive:
        archive.writestr("train/field.png", pixels)
    (new / "crop.png").write_bytes(crop_pixels)
    image = {"image_id": "fixed-image-id", "path": f"zip://{old.as_posix()}/raw.zip!train/field.png",
             "sha256": hashlib.sha256(pixels).hexdigest(), "width": "8", "height": "8",
             "source": "synthetic", "group_id": "animal-fixed", "group_level": "animal",
             "duplicate_of": "", "split": "train"}
    crop = {"crop_id": "fixed-crop-id", "image_id": image["image_id"],
            "path": (old / "crop.png").as_posix(), "crop_sha256": hashlib.sha256(crop_pixels).hexdigest(),
            "source_sha256": image["sha256"], "annotation_sha256": "a" * 64,
            "localization_sha256": "b" * 64, "review_status": "reviewed",
            "group_id": image["group_id"], "split": "train", "label": "0", "bbox": "[0,0,8,8]"}
    images, crops = tmp_path / "images.csv", tmp_path / "crops.csv"
    dp.write_manifest([image], images, list(image))
    dp.write_manifest([crop], crops, list(crop))
    output = tmp_path / "transported"
    argv = ["relocate_experiment.py", "--images", str(images), "--crops", str(crops),
            "--output-dir", str(output), "--map", f"{old}={new}"]
    return new, images, crops, output, argv


def test_relocate_zip_and_crops_preserves_identity_labels_and_originals(tmp_path, monkeypatch):
    new, images, crops, output, argv = transfer_fixture(tmp_path)
    original_bytes = [images.read_bytes(), crops.read_bytes()]
    monkeypatch.setattr(relocation.sys, "argv", argv)
    assert relocation.main() == 0
    for source, destination in [(images, output / "images.csv"), (crops, output / "crops.csv")]:
        before, after = dp.read_manifest(source)[0], dp.read_manifest(destination)[0]
        assert {k: v for k, v in before.items() if k != "path"} == {
            k: v for k, v in after.items() if k != "path"}
        assert after["path"] != before["path"]
    assert dp.read_manifest(output / "images.csv")[0]["path"] == f"zip://{new.as_posix()}/raw.zip!train/field.png"
    assert dp.read_manifest(output / "crops.csv")[0]["path"] == (new / "crop.png").as_posix()
    assert [images.read_bytes(), crops.read_bytes()] == original_bytes
    report = json.loads((output / "relocation.json").read_text(encoding="utf-8"))
    assert report["images"] == report["crops"] == 1


@pytest.mark.parametrize("corrupt", ["image", "crop"])
def test_relocate_rejects_changed_image_or_crop_before_writing(tmp_path, monkeypatch, corrupt):
    new, _, _, output, argv = transfer_fixture(tmp_path)
    if corrupt == "image":
        with zipfile.ZipFile(new / "raw.zip", "w") as archive:
            archive.writestr("train/field.png", png_bytes("green"))
    else:
        (new / "crop.png").write_bytes(png_bytes("green"))
    monkeypatch.setattr(relocation.sys, "argv", argv)
    with pytest.raises(ValueError, match="Conteúdo diferente"):
        relocation.main()
    assert not output.exists()


def test_relocate_refuses_existing_output_without_changes(tmp_path, monkeypatch):
    _, _, _, output, argv = transfer_fixture(tmp_path)
    output.mkdir()
    existing = output / "images.csv"
    existing.write_text("preserve me", encoding="utf-8")
    monkeypatch.setattr(relocation.sys, "argv", argv)
    with pytest.raises(FileExistsError, match="pasta nova"):
        relocation.main()
    assert existing.read_text() == "preserve me"
    assert list(output.iterdir()) == [existing]


def test_relocate_resolves_relative_crop_at_project_root(tmp_path, monkeypatch):
    monkeypatch.setattr(relocation, "ROOT", tmp_path)
    crop = tmp_path / "data" / "crop.png"
    crop.parent.mkdir()
    crop.write_bytes(png_bytes("red"))
    row = {"path": "data/crop.png", "crop_sha256": hashlib.sha256(crop.read_bytes()).hexdigest(),
           "image_id": "unchanged", "split": "val", "label": "1"}
    changed = relocation.relocate([row], [], crop=True)[0]
    assert changed == {**row, "path": crop.as_posix()}
