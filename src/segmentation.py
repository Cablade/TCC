"""
Pipeline de segmentação por cor (HSV + morfologia + connected components).

Replica fielmente o pipeline do Modelo A da Fuzzylab/FIOCRUZ para garantir
que ambos os modelos recebam a mesma entrada na etapa de classificação.

Referência: classification.py / decision_predictor.py do repo Fuzzylab.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import cv2 as cv
import numpy as np

# =============================================================================
# Constantes do pipeline original do Modelo A
# =============================================================================
MIN_AREA_COLOR: int = 3450
MAX_AREA_COLOR: int = 15300

MIN_AREA_COMPONENT: int = 450
MAX_AREA_COMPONENT: int = 1100

LOWER_COLOR_HSV: np.ndarray = np.array([145, 100, 30])
UPPER_COLOR_HSV: np.ndarray = np.array([165, 255, 120])

LOWER_NUCLEUS_HSV: np.ndarray = np.array([120, 50, 30])
UPPER_NUCLEUS_HSV: np.ndarray = np.array([170, 255, 150])

MORPH_KERNEL_SIZE: int = 30


def segment_smear(image_bgr: np.ndarray) -> np.ndarray:
    """
    Primeira etapa: isolar regiões coradas (células) e remover componentes
    com área fora do intervalo [MIN_AREA_COLOR, MAX_AREA_COLOR].

    Args:
        image_bgr: imagem original em BGR (saída do cv.imread).

    Returns:
        Imagem mascarada onde apenas as regiões celulares válidas restam.
    """
    # TODO: implementar (ver classification.py original)
    raise NotImplementedError


def extract_nuclei_rois(image_filtered_bgr: np.ndarray) -> Iterator[tuple[int, np.ndarray]]:
    """
    Segunda etapa: encontrar núcleos roxos dentro das células e gerar
    recortes (ROIs) para classificação.

    Args:
        image_filtered_bgr: saída de `segment_smear`.

    Yields:
        Tuplas (label_id, roi_bgr) para cada núcleo válido encontrado.
    """
    # TODO: implementar
    raise NotImplementedError


def process_image(image_path: str | Path, output_dir: str | Path) -> int:
    """
    Pipeline completo: imagem original -> ROIs salvas em disco.

    Returns:
        Número de ROIs salvas.
    """
    # TODO: orquestrar segment_smear + extract_nuclei_rois e salvar
    raise NotImplementedError
