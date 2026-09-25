"""Transporta caminhos sem alterar IDs, rótulos, grupos ou partições; valida bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp


def remap(locator, mappings):
    value = str(locator).replace("\\", "/")
    is_zip = value.startswith("zip://")
    if is_zip:
        value, separator, member = value[6:].partition("!")
        if not separator:
            raise ValueError("Localizador ZIP inválido")
    matches = [(old, new) for old, new in mappings
               if value.casefold() == old.casefold() or value.casefold().startswith(old.casefold() + "/")]
    if matches:
        old, new = max(matches, key=lambda pair: len(pair[0]))
        value = new + value[len(old):]
    # Caminhos de recortes relativos são relativos à raiz do projeto, como no treino.
    if not Path(value).is_absolute():
        value = (ROOT / value).as_posix()
    return f"zip://{value}!{member}" if is_zip else value


def relocate(rows, mappings, *, crop=False):
    result = []
    digest_key = "crop_sha256" if crop else "sha256"
    for row in rows:
        changed = {**row, "path": remap(row["path"], mappings)}
        digest = hashlib.sha256(dp.read_image_bytes(changed["path"])).hexdigest()
        if digest != row[digest_key]:
            raise ValueError(f"Conteúdo diferente após transporte: {changed['path']}")
        result.append(changed)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--crops", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--map", action="append", default=[], metavar="ANTIGO=NOVO")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("Use uma pasta nova; manifestos existentes são preservados.")
    mappings = []
    for entry in args.map:
        old, separator, new = entry.partition("=")
        if not separator or not old or not new:
            parser.error("Cada --map exige CAMINHO_ANTIGO=CAMINHO_NOVO")
        mappings.append((old.replace("\\", "/").rstrip("/"), new.replace("\\", "/").rstrip("/")))
    images = relocate(dp.read_manifest(args.images), mappings)
    if not images:
        raise ValueError("Manifesto de imagens vazio")
    if "split" in images[0]:
        dp.validate_partitions(images)
    crops = relocate(dp.read_manifest(args.crops), mappings, crop=True) if args.crops else None
    args.output_dir.mkdir(parents=True)
    dp.write_manifest(images, args.output_dir / "images.csv", list(images[0]))
    if crops:
        dp.write_manifest(crops, args.output_dir / "crops.csv", list(crops[0]))
    report = {"images": len(images), "crops": len(crops) if crops is not None else None,
              "mappings": mappings, "image_manifest_source": str(args.images),
              "source_manifest_sha256": hashlib.sha256(args.images.read_bytes()).hexdigest(),
              "note": "IDs, grupos, partições e rótulos preservados; todos os conteúdos conferidos por SHA-256. Copie o JSON de anotações sem alterá-lo e atualize os caminhos da configuração de experimento. Manifestos alterados exigem novas inferências A/B."}
    (args.output_dir / "relocation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
