"""Aumentos geométricos conservadores do B, somente no treino.

Rotações de 90 graus e reflexões preservam pixels, sem apagar o alvo ou
alterar a coloração. Adequação biológica ainda requer revisão da equipe.
"""

import numpy as np


def get_train_augmentations(image_size: int = 224, seed: int = 42):
    rng = np.random.default_rng(seed)

    def augment(image):
        if image.shape[:2] != (image_size, image_size):
            raise ValueError("Faça resize ao tamanho configurado antes do aumento.")
        out = np.rot90(image, int(rng.integers(0, 4)))
        if rng.random() < 0.5:
            out = out[:, ::-1]
        if rng.random() < 0.5:
            out = out[::-1]
        return np.ascontiguousarray(out, dtype=np.float32)

    return augment


def get_eval_augmentations(image_size: int = 224):
    return lambda image: np.asarray(image, dtype=np.float32)


def apply(transform, image: np.ndarray) -> np.ndarray:
    return transform(image)
