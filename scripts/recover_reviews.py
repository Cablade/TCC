"""Reconstrói galerias estáticas e registra declarações da conversa com proveniência.

Não recupera os bytes dos JSONs perdidos nem executa redes neurais.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import html
import json
import os
from datetime import datetime, timezone

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def save_new(path, payload):
    if path.exists():
        raise FileExistsError(f"Arquivo já existe: {path}")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_crop(path, expected_hash):
    if sha(path) != expected_hash:
        raise ValueError(f"Recorte alterado: {path}")


def gallery(folder, title, note, cards):
    target = folder / "index.html"
    if target.exists():
        raise FileExistsError(target)
    chunks = []
    for key, image, caption in cards:
        if not image.is_file():
            raise FileNotFoundError(image)
        relative = Path(os.path.relpath(image, folder)).as_posix()
        chunks.append(f'<article id="{html.escape(key)}"><h2>{html.escape(key)}</h2>'
                      f'<a href="{html.escape(relative, quote=True)}"><img loading="lazy" '
                      f'src="{html.escape(relative, quote=True)}" alt="{html.escape(key)}"></a>'
                      f'<p>{html.escape(caption)}</p></article>')
    target.write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,initial-scale=1">'
                     f'<title>{html.escape(title)}</title><style>'
                     'body{font:16px system-ui;background:#f2f4f6;color:#192c40;margin:24px}'
                     'main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}'
                     'article{background:white;padding:16px;border-radius:10px;overflow-wrap:anywhere}'
                     'img{width:100%;height:260px;object-fit:contain}p{line-height:1.5}'
                     '</style>' + f'<h1>{html.escape(title)}</h1><p>{html.escape(note)}</p>'
                     f'<p>{len(cards)} cartões. Clique na imagem para abrir o arquivo original do cartão.</p>'
                     '<main>' + ''.join(chunks) + '</main></html>', encoding="utf-8")


def recover(root):
    base = root / "experiments/reviews"
    external = base / "ab_external_negatives_20260927"
    focused = base / "b_external_false_positives_20260927_v2"
    reference = base / "ab_reference_20260927"
    # Verificar destinos antes de iniciar: jamais substituir um original recuperado.
    targets = [external / "index.html", focused / "index.html", reference / "index.html",
               external / "review_reconstructed.json", focused / "review_reconstructed.json"]
    if any(p.exists() for p in targets):
        raise FileExistsError("Uma reconstrução já existe; preserve-a antes de repetir.")
    manifest = root / "data/protocol/labimed_external_20260927/images.csv"
    fields = rows(manifest)
    field_ids = [r["image_id"] for r in fields]
    if len(fields) != 33 or len(set(field_ids)) != 33:
        raise ValueError("A declaração da conversa se refere exatamente aos 33 campos desta rodada.")
    crop_csv = external / "crop_predictions.csv"
    central = rows(crop_csv)
    if {r["image_id"] for r in central} != set(field_ids) or len(central) != 33:
        raise ValueError("Campos e recortes centrais não correspondem.")
    prediction_file = root / "experiments/runs/b_labimed_neg_20260927/predictions.json"
    payload = json.loads(prediction_file.read_text(encoding="utf-8-sig"))
    predictions = {r["image_id"]: r for r in payload["images"]}
    if set(predictions) != set(field_ids) or len(payload["images"]) != 33:
        raise ValueError("Predições externas não correspondem ao manifesto.")
    expected = payload.get("manifest_sha256") or payload["artifact"]["manifest_sha256"]
    if expected != sha(manifest):
        raise ValueError("Hash do manifesto externo alterado.")
    restored = []
    cards = []
    for field in fields:
        original = Path(field["path"])
        check_crop(original, field["sha256"])
        with Image.open(original) as im:
            image = np.array(im.convert("RGB"))
        candidates = sorted(enumerate(predictions[field["image_id"]]["regions"]),
                            key=lambda item: (-item[1]["scores"][1], item[0]))[:3]
        if len(candidates) != 3 or any(r["class_id"] != 1 for _, r in candidates):
            raise ValueError("Seleção não corresponde aos três candidatos positivos por campo.")
        for rank, (index, region) in enumerate(candidates, 1):
            key = f"FP{len(restored)+1:03d}"
            crop_path = focused / "crops" / f"{key}.png"
            x1, y1, x2, y2 = region["bbox"]
            if any(int(v) != v for v in (x1, y1, x2, y2)) or not (0 <= x1 < x2 <= image.shape[1] and 0 <= y1 < y2 <= image.shape[0]):
                raise ValueError("Coordenadas inválidas.")
            x1,y1,x2,y2 = map(int, (x1,y1,x2,y2))
            with Image.open(crop_path) as im:
                pixels = np.array(im.convert("RGB"))
            if not np.array_equal(pixels, image[y1:y2, x1:x2]):
                raise ValueError(f"Não foi possível provar o vínculo por pixels de {key}.")
            restored.append({"id": key, "image_id": field["image_id"], "bbox": region["bbox"],
                             "region_index": index, "candidate_rank": rank, "score_B": region["scores"][1],
                             "decision": "no_visible_parasite", "decision_basis": "user_global_statement",
                             "crop_sha256": sha(crop_path), "pixels_match_source_bbox": True,
                             "individual_artifact_category": None})
            cards.append((key, crop_path, f'{field["image_id"]} | escore B: {region["scores"][1]:.4f} | '
                          'sem parasita visível, conforme declaração geral de Caio. Categoria individual não anotada.'))
    external_cards = []
    for row in central:
        crop = external / row["crop_path"]
        check_crop(crop, row["crop_sha256"])
        external_cards.append((row["id"], crop, f'{row["image_id"]} | recorte central ilustrativo. '
                               f'Campo sinalizado: A={row["field_A"]}, B={row["field_B"]}. '
                               'Caio relatou ausência de parasita visível no campo.'))
    common = rows(reference / "predictions.csv")
    common_cards = []
    for row in common:
        crop = reference / "crops" / (row["crop_id"] + ".png")
        check_crop(crop, row["crop_sha256"])
        common_cards.append((row["crop_id"], crop,
            f'{row["image_id"]} | referência={row["label"]}, A={row["A_predicted"]}, B={row["B_predicted"]}. '
            'Diagnóstico em recortes comuns; não é inferência dos sistemas completos.'))
    provenance = {"schema_version": 1, "reconstructed_at": datetime.now(timezone.utc).isoformat(),
                  "original_review_file_recovered": False, "basis": "explicit_user_statements_in_conversation",
                  "reviewer": "Caio", "new_expert_review": False,
                  "manifest_sha256": sha(manifest), "predictions_B_sha256": sha(prediction_file),
                  "training_changed": False, "annotations_changed": False}
    save_new(focused / "review_reconstructed.json", dict(provenance, regions=restored,
        user_statement="Nenhuma dessas regioes tem parasita, so temos celulas, alguns com borda escura e algumas com sujeira/artefato somente",
        general_findings=["células", "borda escura", "sujeira/artefato"],
        selection="Três maiores escores B por campo; empate por ordem original. 99 recortes conferidos pixel a pixel."))
    save_new(external / "review_reconstructed.json", dict(provenance,
        user_statement="nenhum desses 33 campos tem parasita!",
        images=[{"image_id": key, "decision": "no_visible_parasite", "decision_basis": "user_global_statement"} for key in field_ids]))
    gallery(focused, "99 regiões sinalizadas por B — revisão reconstruída",
            "Vínculos confirmados pixel a pixel com as imagens originais. A declaração geral de Caio foi registrada novamente a partir da conversa; o JSON original não foi recuperado. Seleção por escore alto, sem contagem por categoria de artefato.", cards)
    gallery(external, "33 campos externos — revisão reconstruída",
            "Os cartões mostram recortes centrais ilustrativos, não o campo inteiro. Decisões indicadas são dos campos completos. Referência visual relatada por Caio na conversa; domínio humano externo, somente desenvolvimento.", external_cards)
    gallery(reference, "Recortes comuns A × B — galeria reconstruída",
            "Imagens e predições recuperadas dos CSVs preservados; hashes de todos os recortes conferidos. Rótulos são da referência existente, não de uma nova revisão humana.", common_cards)
    return dict(provenance, focused_regions=len(restored), external_fields=len(fields),
                common_crops=len(common_cards), static_galleries=3,
                recovered_original_jsons=0, reconstructed_records=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    report = recover(ROOT)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    save_new(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
