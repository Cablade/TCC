"""
Pipeline de data augmentation para o Modelo B.

Usa Albumentations para aplicar transformações geométricas e de cor
sobre as ROIs antes do treino.
"""

from __future__ import annotations

import albumentations as A
import numpy as np


def get_train_augmentations(image_size: int = 224) -> A.Compose:
    """
    Augmentations aplicadas apenas no treino.

    Cuidado: T. cruzi tem orientação variável no esfregaço, então flips
    e rotações 360° são seguras. Color jitter é leve para preservar a
    coloração Giemsa, que é informativa.
    """
    return A.Compose([
        A.Resize(image_size, image_size),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.Rotate(limit=180, p=0.7),
        A.ColorJitter(
            brightness=0.1,
            contrast=0.1,
            saturation=0.1,
            hue=0.03,
            p=0.5,
        ),
        A.CoarseDropout(  # RandomErasing
            max_holes=2,
            max_height=int(image_size * 0.15),
            max_width=int(image_size * 0.15),
            fill_value=0,
            p=0.3,
        ),
    ])


def get_eval_augmentations(image_size: int = 224) -> A.Compose:
    """Sem augmentation; apenas resize para validação/teste."""
    return A.Compose([
        A.Resize(image_size, image_size),
    ])


def apply(transform: A.Compose, image: np.ndarray) -> np.ndarray:
    """Aplica um pipeline e retorna a imagem transformada."""
    return transform(image=image)["image"]
