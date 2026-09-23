"""Preparação de dados não pode incluir arquivos corrompidos ou apagar revisão."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from PIL import Image

from src import data_protocol as dp


def test_active_archive_excludes_corruption_and_preserves_outputs(tmp_path):
    buffer = io.BytesIO()
    Image.new("RGB", (12, 8), "white").save(buffer, format="JPEG")
    archive = tmp_path / "images.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("train/valid.jpg", buffer.getvalue())
        stream.writestr("train/copy.jpg", buffer.getvalue())
        stream.writestr("test/broken.jpg", b"not an image")
    raw = archive.read_bytes()
    output, annotations = tmp_path / "audit", tmp_path / "pending.json"
    config = {
        "dataset_id": "synthetic", "archive": str(archive), "source": "synthetic",
        "expected_md5": hashlib.md5(raw).hexdigest(),
        "expected_sha256": hashlib.sha256(raw).hexdigest(),
        "output_dir": str(output), "annotations": str(annotations),
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    script = Path(__file__).resolve().parents[1] / "scripts/prepare_active_dataset.py"
    command = [sys.executable, str(script), "--config", str(config_path)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    assert report["inventory"]["files"] == 3
    assert report["eligible"]["files"] == 1
    assert report["integrity_excluded"] == 1
    assert len(dp.read_manifest(output / "duplicate_exclusions.csv")) == 1
    rows = dp.read_manifest(output / "eligible_inventory.csv")
    assert all(row["source"] == "synthetic" for row in rows)
    reference = dp.load_annotations(annotations, rows)
    assert all(item["review_status"] == "pending" and item["whole_image_label"] is None
               for item in reference.values())
    assert "split" not in rows[0]
    before = annotations.read_bytes()
    assert subprocess.run(command, cwd=tmp_path, capture_output=True).returncode != 0
    assert annotations.read_bytes() == before
    config["expected_sha256"] = "0" * 64
    config["output_dir"] = str(tmp_path / "wrong_archive")
    config["annotations"] = str(tmp_path / "wrong_pending.json")
    config_path.write_text(json.dumps(config), encoding="utf-8")
    assert subprocess.run(command, cwd=tmp_path, capture_output=True).returncode != 0
    assert not Path(config["output_dir"]).exists()
