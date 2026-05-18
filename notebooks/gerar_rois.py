"""
Geração de ROIs (Regions of Interest) a partir do dataset Zenodo + Data S1.

Pipeline:
1. Para cada imagem do Zenodo, lê as anotações positivas do supply.csv
2. Detecta a máscara da área iluminada do microscópio (círculo claro,
   excluindo as bordas pretas)
3. Recorta ROIs 100×100 centradas em cada anotação positiva
4. Amostra coordenadas aleatórias DENTRO da máscara iluminada, com
   distância mínima de MIN_NEG_DIST pixels de qualquer positivo
5. Recorta ROIs 100×100 nas coordenadas amostradas → negativos
6. Salva tudo organizado em data/processed/{train,test}/{positivo,negativo}/
7. Gera um manifest CSV com (rel_path, label, original_image, source_x, source_y, structure)

Uso:
    python notebooks/gerar_rois.py            # processa tudo
    python notebooks/gerar_rois.py --dry-run  # processa só 5 imagens, sem salvar
    python notebooks/gerar_rois.py --preview  # gera preview visual de 1 imagem
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2 as cv
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm

# =============================================================================
# Constantes
# =============================================================================
ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS_CSV = ROOT / "data" / "raw" / "annotations" / "supply.csv"
IMAGES_TRAIN_DIR = ROOT / "data" / "raw" / "train"
IMAGES_TEST_DIR = ROOT / "data" / "raw" / "test"
PROCESSED_DIR = ROOT / "data" / "processed"

ROI_SIZE = 100              # tamanho dos recortes (mesmo do paper original)
MIN_NEG_DIST = 50           # distância mínima entre um negativo e qualquer positivo
SEED = 42                   # determinismo na amostragem de negativos
ILLUMINATED_MIN_V = 60      # pixels com V<60 = fundo preto/escuro do bordo

# Utilitários
def get_illuminated_mask(image_bgr: np.ndarray) -> np.ndarray:
    """
    Retorna máscara booleana onde True = área iluminada do microscópio
    (descarta as bordas pretas circulares).

    Usa o canal V do HSV: pixels com V baixo = escuros (borda).
    """
    hsv = cv.cvtColor(image_bgr, cv.COLOR_BGR2HSV)
    v_channel = hsv[..., 2]
    mask = v_channel > ILLUMINATED_MIN_V
    # Erosão pra evitar amostrar perto da borda
    kernel = np.ones((30, 30), np.uint8)
    mask = cv.erode(mask.astype(np.uint8), kernel).astype(bool)
    return mask


def crop_roi(
    image_bgr: np.ndarray, x: int, y: int, size: int = ROI_SIZE,
) -> np.ndarray | None:
    """
    Recorta uma ROI de `size`×`size` centrada em (x, y).
    """
    h, w = image_bgr.shape[:2]
    half = size // 2
    x1, x2 = x - half, x + half
    y1, y2 = y - half, y + half
    if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
        return None
    return image_bgr[y1:y2, x1:x2].copy()


def sample_negatives(
    mask_illuminated: np.ndarray,
    positives_xy: np.ndarray,
    n_negatives: int,
    min_dist: int = MIN_NEG_DIST,
    rng: np.random.Generator | None = None,
    max_attempts_factor: int = 50,
) -> list[tuple[int, int]]:
    if rng is None:
        rng = np.random.default_rng()

    h, w = mask_illuminated.shape
    half = ROI_SIZE // 2

    #  pixels dentro da máscara E com folga pra recortar ROI
    ys_valid, xs_valid = np.where(mask_illuminated)
    valid_idx = (
        (xs_valid >= half) & (xs_valid < w - half) &
        (ys_valid >= half) & (ys_valid < h - half)
    )
    xs_valid = xs_valid[valid_idx]
    ys_valid = ys_valid[valid_idx]

    if len(xs_valid) == 0:
        return []

    sampled: list[tuple[int, int]] = []
    min_dist_sq = min_dist ** 2
    max_attempts = n_negatives * max_attempts_factor
    attempts = 0

    while len(sampled) < n_negatives and attempts < max_attempts:
        attempts += 1
        idx = rng.integers(0, len(xs_valid))
        x, y = int(xs_valid[idx]), int(ys_valid[idx])

        # Checa distância mínima a positivos
        if len(positives_xy) > 0:
            dx = positives_xy[:, 0] - x
            dy = positives_xy[:, 1] - y
            min_dist_to_pos = (dx * dx + dy * dy).min()
            if min_dist_to_pos < min_dist_sq:
                continue

        # Checa distância mínima a outros negativos já sorteados (evita sobreposição)
        if sampled:
            sampled_arr = np.array(sampled)
            dx = sampled_arr[:, 0] - x
            dy = sampled_arr[:, 1] - y
            min_dist_to_neg = (dx * dx + dy * dy).min()
            if min_dist_to_neg < min_dist_sq:
                continue

        sampled.append((x, y))

    return sampled

# Processamento principal

def process_image(
    image_path: Path,
    annots_for_image: pd.DataFrame,
    out_dir_pos: Path,
    out_dir_neg: Path,
    rng: np.random.Generator,
    dry_run: bool = False,
) -> list[dict]:
    """
    Processa uma imagem: recorta positivos, amostra e recorta negativos.
    Retorna lista de dicts pra o manifest CSV.
    """
    image_bgr = cv.imread(str(image_path))
    if image_bgr is None:
        print(f"  WARN: falha ao abrir {image_path.name}")
        return []

    rows: list[dict] = []
    mask_illuminated = get_illuminated_mask(image_bgr)

    # Positivos
    positives_xy = annots_for_image[["x", "y"]].to_numpy()
    n_skipped = 0

    for i, (_, row) in enumerate(annots_for_image.iterrows()):
        x, y = int(row["x"]), int(row["y"])
        roi = crop_roi(image_bgr, x, y)
        if roi is None:
            n_skipped += 1
            continue
        fname = f"{image_path.stem}_pos_{i:03d}.png"
        out_path = out_dir_pos / fname
        if not dry_run:
            cv.imwrite(str(out_path), roi)
        rows.append({
            "rel_path": str(out_path.relative_to(PROCESSED_DIR)),
            "label": "positivo",
            "original_image": image_path.name,
            "source_x": x, "source_y": y,
            "structure": row["structure"],
        })

    # Negativos: amostra o mesmo número de positivos válidos
    n_negatives_target = len(rows)
    neg_coords = sample_negatives(
        mask_illuminated, positives_xy,
        n_negatives=n_negatives_target, rng=rng,
    )
    for i, (x, y) in enumerate(neg_coords):
        roi = crop_roi(image_bgr, x, y)
        if roi is None:
            continue
        fname = f"{image_path.stem}_neg_{i:03d}.png"
        out_path = out_dir_neg / fname
        if not dry_run:
            cv.imwrite(str(out_path), roi)
        rows.append({
            "rel_path": str(out_path.relative_to(PROCESSED_DIR)),
            "label": "negativo",
            "original_image": image_path.name,
            "source_x": x, "source_y": y,
            "structure": "UNKNOWN",
        })

    return rows


def main(dry_run: bool = False, preview: bool = False):
    # Setup
    df = pd.read_csv(ANNOTATIONS_CSV)
    rng = np.random.default_rng(SEED)
    rows_all: list[dict] = []

    if preview:
        # Gera preview de uma única imagem com positivos+negativos visualizados
        run_preview(df, rng)
        return

    # Estrutura de saída
    for split in ("train", "test"):
        for label in ("positivo", "negativo"):
            (PROCESSED_DIR / split / label).mkdir(parents=True, exist_ok=True)

    # Itera por split 
    for split, source_dir in [("train", IMAGES_TRAIN_DIR), ("test", IMAGES_TEST_DIR)]:
        split_df = df[df["set"] == split]
        image_files = sorted(source_dir.glob("*.jpg"))
        if dry_run:
            image_files = image_files[:5]
            print(f"DRY RUN: processando só {len(image_files)} imagens de '{split}'")

        out_pos = PROCESSED_DIR / split / "positivo"
        out_neg = PROCESSED_DIR / split / "negativo"

        for img_path in tqdm(image_files, desc=f"{split:5s}"):
            annots = split_df[split_df["filename"] == img_path.name]
            if len(annots) == 0:
                continue
            rows = process_image(
                img_path, annots, out_pos, out_neg, rng, dry_run=dry_run,
            )
            rows_all.extend(rows)

    # Manifest
    manifest = pd.DataFrame(rows_all)
    manifest_path = PROCESSED_DIR / "manifest.csv"
    if not dry_run:
        manifest.to_csv(manifest_path, index=False)
        print(f"\nManifest salvo em: {manifest_path}")

    # Relatório
    print("\n" + "=" * 60)
    print("RELATÓRIO DE GERAÇÃO DE ROIs")
    print("=" * 60)
    print(f"Total ROIs geradas: {len(manifest):,}")
    print("\nPor split e label:")
    if len(manifest) > 0:
        ct = pd.crosstab(
            manifest["original_image"].map(
                lambda f: "train" if (IMAGES_TRAIN_DIR / f).exists() else "test"
            ),
            manifest["label"],
            margins=True,
        )
        print(ct.to_string())


def run_preview(df: pd.DataFrame, rng: np.random.Generator):
    """Gera uma imagem mostrando positivos (verde) e negativos (laranja) sorteados."""
    # Imagem com mais anotações
    target = df.groupby("filename").size().sort_values(ascending=False).index[0]
    img_path = IMAGES_TRAIN_DIR / target
    image_bgr = cv.imread(str(img_path))
    if image_bgr is None:
        print(f"ERRO: não foi possível abrir {img_path}")
        return

    annots = df[df["filename"] == target]
    positives_xy = annots[["x", "y"]].to_numpy()
    mask = get_illuminated_mask(image_bgr)
    neg_coords = sample_negatives(
        mask, positives_xy, n_negatives=len(annots), rng=rng,
    )

    # Desenha
    for x, y in positives_xy:
        cv.rectangle(
            image_bgr,
            (int(x) - 50, int(y) - 50), (int(x) + 50, int(y) + 50),
            (0, 255, 0), 6,
        )
    for x, y in neg_coords:
        cv.rectangle(
            image_bgr,
            (x - 50, y - 50), (x + 50, y + 50),
            (0, 128, 255), 6,
        )

    # Preview menor pra abrir fácil
    h, w = image_bgr.shape[:2]
    scale = 0.33
    preview = cv.resize(image_bgr, (int(w * scale), int(h * scale)))
    out = ROOT / "data" / "raw" / "annotations" / f"preview_rois_{img_path.stem}.png"
    cv.imwrite(str(out), preview)
    print(f"\nPreview salvo em: {out}")
    print(f"Verde = positivos ({len(positives_xy)})")
    print(f"Laranja = negativos sorteados ({len(neg_coords)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="processa só 5 imagens, sem salvar")
    parser.add_argument("--preview", action="store_true",
                        help="gera preview visual de uma imagem")
    args = parser.parse_args()
    main(dry_run=args.dry_run, preview=args.preview)
