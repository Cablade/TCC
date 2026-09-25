"""Importa a referência pública LABIMED; não declara revisão independente local.

Requer o subconjunto verificado por fetch_negative_candidates.py. Os rótulos
descrevem campos microscópicos, nunca o diagnóstico negativo de participantes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp  # noqa: E402

SOURCE = "https://doi.org/10.5281/zenodo.15007339"
PAPER = "https://doi.org/10.1371/journal.pntd.0012955"
REVIEWER = "Referência publicada por Lin et al.; seção Image labeling, doi:10.1371/journal.pntd.0012955"
HASHES = {"assets.csv": "b13a71d6e73c0008041225aa6307c923", "bboxes.csv": "9fa2f1c0025d5c0280c440d5f0be3be5"}


def import_reference(folder: Path) -> tuple[list[dict], dict, dict]:
    for filename, expected in HASHES.items():
        if hashlib.md5((folder / filename).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Metadados publicados alterados: {filename}")
    assets = dp.read_manifest(folder / "assets.csv")
    by_name = {r["assetFile"]: r for r in assets}
    if len(by_name) != len(assets):
        raise ValueError("Identificadores de imagem duplicados")
    boxes = defaultdict(list)
    for number, row in enumerate(dp.read_manifest(folder / "bboxes.csv"), 2):
        if row["assetFile"] not in by_name or row["label_str"] != "Tripanosoma":
            raise ValueError("Anotação fora do esquema publicado")
        boxes[row["assetFile"]].append({"annotation_id": f"labimed_bbox_{number:06d}",
            "bbox": [int(row[k]) for k in ("xmin", "ymin", "xmax", "ymax")],
            "source_csv_row": number})
    selection = dp.read_manifest(folder / "selection.csv")
    rows, seen_names, seen_hashes = [], set(), set()
    for selected in selection:
        name = selected["assetFile"]
        asset = by_name[name]
        if name in seen_names or asset["sample_type"] != "Blood_thin":
            raise ValueError("Seleção duplicada ou fora de esfregaço fino sanguíneo")
        if any(selected[k] != asset[k] for k in ("caseId", "sampleId", "sample_type")):
            raise ValueError("Grupos da seleção diferem da tabela original")
        path = (folder / "images" / name).resolve()
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != selected["sha256"] or digest in seen_hashes:
            raise ValueError("Imagem modificada ou conteúdo duplicado")
        with Image.open(path) as image:
            image.load()
            width, height = image.size
        if (width, height) != (4128, 3096) or (str(width), str(height)) != (selected["width"], selected["height"]):
            raise ValueError("Dimensões diferentes dos pixels originais LABIMED")
        if int(selected["parasite_bbox_count"]) != len(boxes[name]):
            raise ValueError("Contagem de anotações inconsistente")
        image_id = "img_" + hashlib.sha256((path.as_posix() + "\0" + digest).encode()).hexdigest()[:24]
        rows.append(dict(image_id=image_id, path=path.as_posix(), sha256=digest,
            width=width, height=height, source=SOURCE, group_id="labimed_case_" + asset["caseId"],
            group_level="paciente", duplicate_of="", source_filename=name,
            case_id=asset["caseId"], slide_id=asset["sampleId"], sample_type=asset["sample_type"],
            donor_status="positive", whole_image_label=int(bool(boxes[name]))))
        seen_names.add(name)
        seen_hashes.add(digest)
    if not rows:
        raise ValueError("Seleção vazia")
    payload = dp.annotation_template(rows)
    payload["provenance"] = dict(source=SOURCE, publication=PAPER, license="CC-BY-NC-4.0",
        metadata_md5=HASHES, review_basis="published_author_annotations", new_tcc_human_review=False,
        negative_basis="Complete published assets table plus parasite boxes and authors' positive/negative field annotation protocol; not merely a missing local label file.",
        reference_completeness="Published object-detection reference, not independently re-reviewed locally.",
        coordinate_conversion="Original xmin/ymin/xmax/ymax retained in original 4128x3096 pixels; no resizing; interpreted as xyxy half-open.")
    for annotation, row in zip(payload["images"], rows):
        annotation.update(review_status="reviewed", reviewer=REVIEWER,
            review_basis="published_author_annotations", new_tcc_human_review=False,
            reference_complete=True, whole_image_label=row["whole_image_label"],
            positives=boxes[row["source_filename"]], source_filename=row["source_filename"],
            donor_status="positive")
    dp.validate_annotations(payload, rows)
    by_case = defaultdict(Counter)
    for asset in assets:
        if asset["sample_type"] == "Blood_thin":
            by_case[asset["caseId"]]["positive" if boxes[asset["assetFile"]] else "negative"] += 1
    report = dict(source=SOURCE, selected_images=len(rows),
        selected_labels=dict(Counter(str(r["whole_image_label"]) for r in rows)),
        selected_cases=len({r["case_id"] for r in rows}), selected_slides=len({r["slide_id"] for r in rows}),
        selected_positive_boxes=sum(len(a["positives"]) for a in payload["images"]),
        complete_thin_dataset_cases={case: dict(counts) for case, counts in sorted(by_case.items())},
        independent_negative_cases=sum(c["negative"] > 0 for c in by_case.values()),
        three_way_patient_split_with_both_classes_possible=False,
        split_created=False, new_tcc_human_review=False,
        limitation="All negative thin-smear fields belong to one positive participant. Do not distribute this participant across train/validation/test to manufacture independent negative controls.")
    return rows, payload, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=ROOT / "data/external_candidates/labimed")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/annotations/labimed_public")
    args = parser.parse_args()
    output = args.output_dir
    names = ("inventory.csv", "annotations.json", "import_report.json")
    if any((output / name).exists() for name in names):
        parser.error("Saída existente; escolha outro --output-dir para preservar a versão atual.")
    rows, payload, report = import_reference(args.source_dir)
    output.mkdir(parents=True, exist_ok=True)
    dp.write_manifest(rows, output / names[0], fields=list(rows[0]))
    for name, value in zip(names[1:], (payload, report)):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
