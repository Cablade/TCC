"""Ajusta o pacote recebido para este computador, preservando a divisão e os bytes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.relocate_experiment import relocate
from src import data_protocol as dp
from src.dataset_policy import validate_active_images


def prepare(archive, *, root=ROOT):
    archive = Path(archive).resolve(strict=True)
    output = root / "data/protocol/experimento_neste_pc"
    config_path = root / "configs/experiment_cpu_local.json"
    if output.exists() or config_path.exists():
        raise FileExistsError("Este computador já foi preparado; use configs/experiment_cpu_local.json.")
    config = json.loads((root / "configs/experiment_cpu.json").read_text(encoding="utf-8-sig"))
    images = dp.read_manifest(root / config["image_manifest"])
    crops = dp.read_manifest(root / config["crop_manifest"])
    archives = {row["path"].replace("\\", "/")[6:].split("!", 1)[0] for row in images
                if row["path"].startswith("zip://")}
    if len(archives) != 1:
        raise ValueError("O pacote deve usar exatamente um ZIP público.")
    old_roots = set()
    for row in crops:
        old_root, separator, _ = row["path"].replace("\\", "/").partition("/data/processed/")
        if not separator:
            raise ValueError("Caminho de recorte não pertence à estrutura esperada do pacote.")
        old_roots.add(old_root)
    if len(old_roots) != 1:
        raise ValueError("Recortes devem pertencer à mesma raiz de projeto.")
    mappings = [(next(iter(archives)), archive.as_posix()),
                (next(iter(old_roots)), root.resolve().as_posix())]
    moved_images = relocate(images, mappings)
    dp.validate_partitions(moved_images)
    validate_active_images(moved_images, root=root)
    moved_crops = relocate(crops, mappings, crop=True)
    output.mkdir(parents=True)
    dp.write_manifest(moved_images, output / "images.csv", list(moved_images[0]))
    dp.write_manifest(moved_crops, output / "crops.csv", list(moved_crops[0]))
    config.update(image_manifest="data/protocol/experimento_neste_pc/images.csv",
                  crop_manifest="data/protocol/experimento_neste_pc/crops.csv")
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "relocation.json").write_text(json.dumps({"mappings": mappings, "images": len(images),
        "crops": len(crops), "preserved": ["image_id", "group_id", "split", "label", "sha256"],
        "note": "Todos os arquivos conferidos por SHA-256. Referência e configuração de localização preservadas."},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return config_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Caminho local do trypoastigote_images.zip recebido.")
    args = parser.parse_args()
    config = prepare(args.archive)
    print(f"Caminhos preparados: {config}")
    print("Próximo passo: scripts/start_training.py --experiment configs/experiment_cpu_local.json --check-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
