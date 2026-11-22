"""Checagem do A no domínio original (imagens de exemplo do VisionCruzi).

Objetivo: mostrar que a reprodução do A funciona nas imagens para as quais ele
foi feito, de modo que "o A não se transfere para a aquisição do Zenodo" seja
um resultado, não uma suspeita sobre a reprodução.

Roda o mesmo fluxo congelado (src/model_a.py, sem alterar limites) em:
  --images: arquivos ou pastas com exemplos do VisionCruzi (domínio original);
  --zenodo-manifest/--zenodo-limit (opcional): algumas imagens murinas de
    validação, para comparar lado a lado onde o fluxo perde candidatos.

Além do status por imagem, mede a área dos componentes de núcleo ANTES do filtro
de área do A (450–1100 px), para verificar se a perda no Zenodo vem da escala
da imagem. O recálculo dessa máscara é conferido contra a contagem do próprio
locate_original em cada imagem.

Exemplo:
  python scripts/check_model_a_original_domain.py ^
      --images C:\\caminho\\VisionCruzi\\exemplos ^
      --zenodo-manifest experiments/comparison/a_vs_b_barcelona20_20261006/images.csv --zenodo-limit 10 ^
      --output-dir experiments/validation/model_a_original_domain_20261013
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import cv2 as cv
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
MOUSE_SOURCE = "https://doi.org/10.5281/zenodo.5123062"
AREA_MIN, AREA_MAX = 450, 1100  # limites literais de locate_original


def nucleus_component_areas(image_bgr: np.ndarray) -> list[int]:
    """Mesmas operações de locate_original até a máscara de núcleo; devolve áreas antes do filtro."""
    hsv = cv.cvtColor(image_bgr, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, np.array([145, 100, 30]), np.array([165, 255, 120]))
    kernel = np.ones((30, 30), np.uint8)
    mask = cv.morphologyEx(cv.dilate(mask, kernel, iterations=2), cv.MORPH_OPEN, kernel)
    num_labels, labels_im = cv.connectedComponents(mask)
    for lab in range(1, num_labels):
        area = np.sum(labels_im == lab)
        if area < 3450 or area > 15300:
            mask[labels_im == lab] = 0
    result = cv.bitwise_and(image_bgr, image_bgr, mask=mask)
    nucleus = cv.inRange(cv.cvtColor(result, cv.COLOR_BGR2HSV), np.array([120, 50, 30]), np.array([170, 255, 150]))
    _, nucleus = cv.threshold(nucleus, 127, 255, cv.THRESH_BINARY)
    n, _, stats, _ = cv.connectedComponentsWithStats(nucleus)
    return [int(stats[lab][4]) for lab in range(1, n)]


def image_files(paths):
    out = []
    for item in map(Path, paths):
        if item.is_dir():
            out += sorted(p for p in item.rglob("*") if p.suffix.lower() in EXTENSIONS)
        elif item.suffix.lower() in EXTENSIONS:
            out.append(item)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--images", nargs="+", required=True)
    parser.add_argument("--zenodo-manifest", type=Path)
    parser.add_argument("--zenodo-limit", type=int, default=10)
    parser.add_argument("--model", default=str(ROOT / "models/model_a/model_trained.keras"))
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--label", default="visioncruzi", help="Nome do domínio das imagens de --images no resumo.")
    parser.add_argument("--no-overlays", action="store_true",
                        help="Não grava overlays (imagens de terceiros que não podem ser salvas).")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("Pasta de saída já existe.")
    from src.data_protocol import read_image_bytes
    from src.model_a import draw_overlay, infer_image, load_original_model

    jobs = [(args.label, str(p), p.stem) for p in image_files(args.images)]
    if not jobs:
        raise ValueError("Nenhuma imagem encontrada em --images.")
    if args.zenodo_manifest:
        with open(args.zenodo_manifest, encoding="utf-8-sig", newline="") as stream:
            rows = [r for r in csv.DictReader(stream) if r["source"] == MOUSE_SOURCE and r["split"] != "test"]
        jobs += [("zenodo", r["path"], r["image_id"]) for r in rows[:args.zenodo_limit]]
    model, artifact = load_original_model(args.model)
    args.output_dir.mkdir(parents=True)
    if not args.no_overlays:
        (args.output_dir / "overlays").mkdir()
    records = []
    for domain, path, name in jobs:
        raw = read_image_bytes(path)
        image = cv.imdecode(np.frombuffer(raw, np.uint8), cv.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Não decodificou: {path}")
        result = infer_image(image, model, name)
        areas = nucleus_component_areas(image)
        if len(areas) != result["instrumentation"].get("components_before_area_filter"):
            raise AssertionError(f"Recálculo das áreas diverge do fluxo do A em {name}.")
        within = sum(AREA_MIN <= a <= AREA_MAX for a in areas)
        overlay = args.output_dir / "overlays" / f"{domain}_{hashlib.sha256(name.encode()).hexdigest()[:12]}.png"
        if not args.no_overlays:
            cv.imwrite(str(overlay), draw_overlay(image, result))
        records.append({
            "domain": domain, "image": name, "path": path, "sha256": hashlib.sha256(raw).hexdigest(),
            "width": image.shape[1], "height": image.shape[0], "status": result["status"],
            "candidates": len(result["candidates"]),
            "positive_regions": sum(r["class_id"] == 1 for r in result["regions"]),
            "nucleus_components": len(areas), "components_in_area_range": within,
            "area_median": float(np.median(areas)) if areas else None,
            "area_p10": float(np.percentile(areas, 10)) if areas else None,
            "area_p90": float(np.percentile(areas, 90)) if areas else None,
            "overlay": "" if args.no_overlays else overlay.name, "error": result.get("error", ""),
            **{f"inst_{k}": v for k, v in result["instrumentation"].items()},
        })
        print(f"{domain} {name}: {result['status']}, {len(areas)} componentes, {within} na faixa de área", flush=True)
    fields = list(dict.fromkeys(k for r in records for k in r))
    with (args.output_dir / "per_image.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    summary = {"model_sha256": artifact["sha256"], "area_filter_px": [AREA_MIN, AREA_MAX], "domains": {}}
    for domain in sorted({r["domain"] for r in records}):
        rs = [r for r in records if r["domain"] == domain]
        summary["domains"][domain] = {
            "images": len(rs), "status": {s: sum(r["status"] == s for r in rs) for s in {r["status"] for r in rs}},
            "images_with_candidates": sum(r["candidates"] > 0 for r in rs),
            "median_nucleus_area": (float(np.median([r["area_median"] for r in rs if r["area_median"] is not None]))
                                    if any(r["area_median"] is not None for r in rs) else None),
            "median_image_width": float(np.median([r["width"] for r in rs]))}
    summary["note"] = ("Execução diagnóstica do A congelado; não altera limites nem pesos. "
                       "Sem referência anotada no domínio original, mede só se o fluxo gera e classifica regiões.")
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
