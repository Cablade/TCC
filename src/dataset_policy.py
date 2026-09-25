"""Restringe os comandos reais ao conteúdo do ZIP autorizado neste TCC."""
from pathlib import Path
import json

from . import data_protocol as dp
from .data_pipeline import file_sha256

ROOT = Path(__file__).resolve().parents[1]


def validate_active_images(rows, *, root=ROOT):
    config = json.loads((root / "configs/dataset.json").read_text(encoding="utf-8-sig"))
    inventory = root / config["output_dir"] / "eligible_inventory.csv"
    allowed = {row["image_id"]: row for row in dp.read_manifest(inventory)}
    reservation = json.loads((root / "data/annotations/negative_preselection_v1/development_reservation.json").read_text(encoding="utf-8-sig"))
    reserved_ids = {row["image_id"] for row in reservation["images"]}
    reserved_hashes = {row["sha256"] for row in reservation["images"]}
    reserved_groups = {row["group_id"] for row in rows
                       if row["image_id"] in reserved_ids or row["sha256"] in reserved_hashes}
    archives = set()
    if not rows:
        raise ValueError("Manifesto real vazio.")
    for row in rows:
        original = allowed.get(row["image_id"])
        if original is None or any(str(row.get(key)) != str(original[key])
                                   for key in ("sha256", "width", "height", "source")):
            raise ValueError("Imagem fora do inventário público autorizado ou identidade alterada.")
        locator = row["path"].replace("\\", "/")
        if not locator.startswith("zip://") or "!" not in locator:
            raise ValueError("Imagem real deve apontar para o ZIP público autorizado.")
        archive, member = locator[6:].split("!", 1)
        if member != original["path"].split("!", 1)[1]:
            raise ValueError("Membro do ZIP diverge do inventário autorizado.")
        archives.add(Path(archive))
        if row.get("split") == "test" and (row["image_id"] in reserved_ids
                or row["sha256"] in reserved_hashes or row["group_id"] in reserved_groups):
            raise ValueError("Imagem/grupo examinado no desenvolvimento não pode integrar o teste.")
    # O nome pode mudar durante transporte; somente bytes idênticos são aceitos.
    for archive in archives:
        if file_sha256(archive) != config["expected_sha256"]:
            raise ValueError("ZIP não corresponde ao conteúdo público autorizado.")
    return {"images": len(rows), "archives": len(archives), "source": config["source"]}
