"""Importa pontos publicados do conjunto 5123062, sem inventar caixas/negativos.

Os arquivos de origem são fixados por commit e SHA-256. Os pixels originais
usam x/y; new_x/new_y pertencem à imagem reduzida e só conferem a escala.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp  # noqa: E402

COMMIT = "b0b8f4d74dc679756bca4c5569c3f8abbe0d10d5"
SOURCE = "https://doi.org/10.5281/zenodo.5123062"
REVIEWER = "Anotações publicadas por Morais et al. (2022), doi:10.7717/peerj.13470/supp-1"
BASE = f"https://raw.githubusercontent.com/csbl-br/chagas_detection/{COMMIT}/"
FILES = {
    "position_data.csv": ("main/position_data.csv", "e53861f400e84bde199fb941ff1a8e8784ab49f5a5a03837ce37dfa73e070064"),
    "images_info.csv": ("main/images_info.csv", "af3bfa6dab35cb8811bf135eeba0c44c0f2452addef85c8235ad84dae40af5fa"),
    "features_data.csv": ("main/features_data.csv", "88f183b566616b06194dd94bb86702a1b48714a8dafd7463a17c88092d4f6c06"),
    "my_tools.py": ("main/my_tools.py", "f57a2ddcff5a13ae61f79b73bad70cc52514be24ca3650823cde111e108dd6bd"),
    "README.md": ("README.md", "eafa4b11427caadf8721e41fd060fc0ebb79df47e170bd108c43f8300cd00ffa"),
}
POSITIVE_STRUCTURES = {"NUCLEUS", "NUCLEUS_CELL_BODY", "T_CRUZI"}
KNOWN_STRUCTURES = POSITIVE_STRUCTURES | {"KINETOPLAST", "KINETOPLAST_CELL_BODY"}


def download_sources(destination: Path) -> list[dict]:
    """Reusa apenas cópias com hash correto; nunca executa código da fonte."""
    destination.mkdir(parents=True, exist_ok=True)
    provenance = []
    for name, (remote, digest) in FILES.items():
        path = destination / name
        url = BASE + remote
        data = path.read_bytes() if path.exists() else urllib.request.urlopen(url, timeout=60).read()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"Checksum da fonte não corresponde: {name}")
        if not path.exists():
            path.write_bytes(data)
        provenance.append({"name": name, "url": url, "sha256": digest, "bytes": len(data)})
    return provenance


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def import_points(inventory: list[dict], positions: list[dict], info: list[dict]) -> tuple[dict, dict, list[dict]]:
    """Aceita somente associação inequívoca e conferida por dimensões/escala.

    A revisão é explicitamente a publicada pelos autores, não nova revisão do
    TCC. Não converte ausência de ponto em negativo ou completude da referência.
    """
    by_name = {}
    for image in inventory:
        name = image["path"].replace("\\", "/").rsplit("/", 1)[-1]
        if name in by_name or image.get("duplicate_of"):
            raise ValueError("Inventário ambíguo ou com duplicatas")
        if image.get("source") != SOURCE:
            raise ValueError("Inventário não está associado à fonte 5123062 verificada")
        by_name[name] = image
    if len({row["filename"] for row in info}) != len(info):
        raise ValueError("Metadados de origem com filename repetido")
    metadata = {row["filename"]: row for row in info}
    if set(metadata) != set(by_name):
        raise ValueError("Metadados publicados e inventário devem conter exatamente as mesmas imagens")
    for name, image in by_name.items():
        item = metadata[name]
        width, height = int(image["width"]), int(image["height"])
        if (width, height) != (int(item["width"]), int(item["height"])):
            raise ValueError(f"Dimensões incompatíveis: {name}")
        factor = float(item["resize_factor"])
        if not math.isfinite(factor) or not math.isclose(factor, 1024 / height, abs_tol=1e-12):
            raise ValueError(f"Fator de redução incompatível: {name}")
        # Somente conferência; esta divisão NÃO se torna a partição do TCC.
        member = image["path"].split("!", 1)[-1]
        if member.split("/")[0] != item["set"] or item["set"] not in {"train", "test"}:
            raise ValueError(f"Pasta original não corresponde aos metadados: {name}")

    grouped = defaultdict(dict)
    raw_counts = Counter()
    selected = duplicate_points = 0
    for csv_row, point in enumerate(positions, 2):
        name = point["filename"]
        if name not in by_name or point["structure"] not in KNOWN_STRUCTURES:
            raise ValueError(f"Anotação fora do esquema/fonte: linha {csv_row}")
        image, meta = by_name[name], metadata[name]
        x, y = float(point["x"]), float(point["y"])
        nx, ny, scale = float(point["new_x"]), float(point["new_y"]), float(meta["resize_factor"])
        if not all(math.isfinite(v) for v in (x, y, nx, ny)):
            raise ValueError(f"Coordenada não finita: linha {csv_row}")
        if not (0 <= x < int(image["width"]) and 0 <= y < int(image["height"])):
            raise ValueError(f"Ponto fora dos pixels originais: linha {csv_row}")
        if abs(x * scale - nx) > 0.501 or abs(y * scale - ny) > 0.501:
            raise ValueError(f"Escala das coordenadas incompatível: linha {csv_row}")
        if point["set"] != meta["set"]:
            raise ValueError(f"Divisão publicada contraditória: linha {csv_row}")
        raw_counts[name] += 1
        if point["structure"] not in POSITIVE_STRUCTURES:
            continue
        selected += 1
        key = (x, y)
        if key in grouped[name]:
            duplicate_points += 1
            grouped[name][key]["source_csv_rows"].append(csv_row)
            grouped[name][key]["source_structures"].append(point["structure"])
            continue
        grouped[name][key] = {
            "annotation_id": f"public_point_{csv_row:06d}", "point": [x, y],
            "source_csv_rows": [csv_row], "source_structures": [point["structure"]],
            "source_coordinate_columns": ["x", "y"],
        }
    payload = dp.annotation_template(inventory)
    payload["provenance"] = {
        "source": SOURCE, "publication": "https://doi.org/10.7717/peerj.13470",
        "source_commit": COMMIT, "review_basis": "published_author_annotations",
        "new_tcc_human_review": False,
        "reference_completeness": "not_asserted",
        "positive_filter": sorted(POSITIVE_STRUCTURES),
        "negative_policy": "No segmented-object False label is converted into a negative image or RGB crop.",
    }
    by_id = {row["image_id"]: name for name, row in by_name.items()}
    mapping, count_discrepancies = [], []
    for image in payload["images"]:
        name = by_id[image["image_id"]]
        if raw_counts[name] != int(metadata[name]["n_structures"]):
            count_discrepancies.append({"filename": name,
                "images_info_n_structures": int(metadata[name]["n_structures"]),
                "position_data_rows": raw_counts[name]})
        if not grouped[name]:
            raise ValueError(f"Imagem sem positivo publicado; não assumir negativa: {name}")
        image.update(review_status="reviewed", reviewer=REVIEWER, reference_complete=False,
                     whole_image_label=1, positives=list(grouped[name].values()),
                     source_filename=name, review_basis="published_author_annotations",
                     new_tcc_human_review=False)
        mapping.append({**by_name[name], "source_filename": name,
                        "source_split": metadata[name]["set"],
                        "positive_points": len(grouped[name]),
                        "biological_group_available": False})
    dp.validate_annotations(payload, inventory)
    report = {"images": len(inventory), "source_structure_rows": len(positions),
              "selected_structure_rows": selected, "unique_positive_points": selected - duplicate_points,
              "identical_points_merged": duplicate_points, "negative_regions": 0,
              "whole_negative_images": 0, "reference_complete_images": 0,
              "source_splits": dict(Counter(row["set"] for row in info)),
              "animal_or_slide_ids_available": False,
              "source_structure_count_discrepancies": count_discrepancies,
              "train_ready_alone": False,
              "remaining": ["Negativos adequados ao recorte RGB e ao campo completo",
                            "Partições por grupo biológico ou limitação declarada",
                            "Referência completa/caixas para métricas que as exijam"]}
    return payload, report, mapping


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=ROOT / "data/protocol/trypomastigote_verified/eligible_inventory.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/annotations/public_import")
    args = parser.parse_args()
    destinations = [args.output_dir / name for name in ("public_points.json", "import_report.json", "source_mapping.csv")]
    if any(path.exists() for path in destinations):
        parser.error("Saída já existe. Escolha outro --output-dir para preservar a versão atual.")
    sources = download_sources(args.output_dir / "raw")
    payload, report, mapping = import_points(dp.read_manifest(args.inventory),
        read_csv(args.output_dir / "raw/position_data.csv"), read_csv(args.output_dir / "raw/images_info.csv"))
    features = read_csv(args.output_dir / "raw/features_data.csv")
    report.update(source_files=sources, source_feature_rows=len(features),
                  source_feature_labels=dict(Counter(row["structure"] for row in features)),
                  inventory_sha256=hashlib.sha256(args.inventory.read_bytes()).hexdigest())
    payload["provenance"]["source_files"] = sources
    for path, value in zip(destinations[:2], (payload, report)):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dp.write_manifest(mapping, destinations[2], fields=list(mapping[0]))
    print(json.dumps({key: value for key, value in report.items() if key != "source_files"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
