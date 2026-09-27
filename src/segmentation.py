"""Localização experimental do B; nenhum parâmetro do A é usado aqui.

Black-hat na luminância propõe estruturas localmente escuras. Os padrões
iniciais são provisórios e exigem calibração nas imagens de desenvolvimento.
Caixas são xyxy, com limite direito/inferior exclusivo, na imagem original.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math

import cv2 as cv
import numpy as np


@dataclass(frozen=True)
class LocalizationConfig:
    method: str = "blackhat_otsu"
    kernel_size: int = 31
    min_contrast: int = 8
    min_area: int = 8
    max_area: int = 2500
    min_crop_size: int = 100
    context_fraction: float = 0.5
    border_policy: str = "clip"
    merge_max_size: int | None = None

    def __post_init__(self):
        if self.method != "blackhat_otsu" or self.border_policy != "clip":
            raise ValueError("Método/borda não suportado; use blackhat_otsu e clip.")
        if self.kernel_size < 3 or self.kernel_size % 2 != 1:
            raise ValueError("kernel_size deve ser ímpar e >= 3.")
        if not 0 <= self.min_contrast <= 255:
            raise ValueError("min_contrast deve estar em [0,255].")
        if self.min_area < 1 or self.max_area < self.min_area:
            raise ValueError("Intervalo de áreas inválido.")
        if self.min_crop_size < 1 or self.context_fraction < 0:
            raise ValueError("Contexto/tamanho de recorte inválido.")
        if self.merge_max_size is not None and (isinstance(self.merge_max_size, bool)
                or not isinstance(self.merge_max_size, int) or self.merge_max_size < self.min_crop_size):
            raise ValueError("merge_max_size deve ser inteiro >= min_crop_size ou null.")


def localization_config(config: dict | LocalizationConfig | None = None) -> LocalizationConfig:
    if isinstance(config, LocalizationConfig):
        return config
    return LocalizationConfig(**(config or {}))


def localization_hash(config: dict | LocalizationConfig | None = None) -> str:
    values = asdict(localization_config(config))
    # A opção desativada preserva os hashes de todos os recortes/checkpoints antigos.
    if values["merge_max_size"] is None:
        values.pop("merge_max_size")
    content = json.dumps(values, sort_keys=True).encode()
    return hashlib.sha256(content).hexdigest()


def merge_overlapping_regions(candidates, max_size):
    """Agrupa caixas sobrepostas sem descartar a cobertura de nenhuma proposta.

    A união retangular é limitada em largura e altura; caixas originalmente
    maiores são preservadas. Não usa rótulos, escores da rede ou limite top-K.
    A ordem geométrica e os desempates são determinísticos.
    """
    if not candidates:
        return []
    ordered = sorted(candidates, key=lambda row: (*row["bbox"][1::-1], row["bbox"][3], row["bbox"][2]))
    boxes = np.empty((len(ordered), 4), dtype=np.int64)
    groups = []
    for candidate in ordered:
        box = np.asarray(candidate["bbox"], dtype=np.int64)
        current = boxes[:len(groups)]
        lower = np.maximum(current[:, :2], box[:2])
        upper = np.minimum(current[:, 2:], box[2:])
        intersection = np.prod(np.maximum(0, upper - lower), axis=1)
        union_box = np.concatenate((np.minimum(current[:, :2], box[:2]),
                                    np.maximum(current[:, 2:], box[2:])), axis=1)
        feasible = (intersection > 0) & np.all(union_box[:, 2:] - union_box[:, :2] <= max_size, axis=1)
        choices = np.flatnonzero(feasible)
        if len(choices):
            areas = np.prod(current[choices, 2:] - current[choices, :2], axis=1)
            area = np.prod(box[2:] - box[:2])
            scores = intersection[choices] / (areas + area - intersection[choices])
            index = int(choices[int(np.argmax(scores))])
            boxes[index] = union_box[index]
            group = groups[index]
            group["bbox"] = boxes[index].tolist()
            a, b = group["proposal_bbox"], candidate["proposal_bbox"]
            group["proposal_bbox"] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
            group["area"] += candidate["area"]
            group["merged_candidates"] += 1
        else:
            boxes[len(groups)] = box
            groups.append({**candidate, "bbox": list(candidate["bbox"]),
                           "proposal_bbox": list(candidate["proposal_bbox"]), "merged_candidates": 1})
    groups.sort(key=lambda row: (row["bbox"][1], row["bbox"][0], row["bbox"][3], row["bbox"][2]))
    return groups


def validate_rgb(image_rgb: np.ndarray) -> None:
    if image_rgb.ndim != 3 or image_rgb.shape[2] != 3 or not image_rgb.size:
        raise ValueError("Esperada imagem RGB HxWx3 não vazia.")
    if image_rgb.dtype != np.uint8:
        raise ValueError("Localização exige RGB uint8 [0,255].")


def contextual_box(bbox, image_shape, config=None) -> tuple[int, int, int, int]:
    """Amplia em quadrado e limita às bordas; treino e inferência usam isto."""
    cfg = localization_config(config)
    h, w = image_shape[:2]
    x1, y1, x2, y2 = map(float, bbox)
    if not (0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h):
        raise ValueError("Caixa da proposta fora da imagem.")
    side = max(cfg.min_crop_size, math.ceil(max(x2 - x1, y2 - y1) * (1 + 2 * cfg.context_fraction)))
    left = math.floor((x1 + x2 - side) / 2)
    top = math.floor((y1 + y2 - side) / 2)
    return max(0, left), max(0, top), min(w, left + side), min(h, top + side)


def crop_region(image_rgb: np.ndarray, bbox) -> np.ndarray:
    validate_rgb(image_rgb)
    x1, y1, x2, y2 = map(int, bbox)
    h, w = image_rgb.shape[:2]
    if not (0 <= x1 < x2 <= w and 0 <= y1 < y2 <= h):
        raise ValueError("Caixa de recorte fora da imagem.")
    return image_rgb[y1:y2, x1:x2].copy()


def propose_regions(image_rgb: np.ndarray, config=None) -> tuple[list[dict], dict]:
    """Retorna caixas contextuais, caixas dos componentes e contagens diagnósticas."""
    validate_rgb(image_rgb)
    cfg = localization_config(config)
    gray = cv.cvtColor(image_rgb, cv.COLOR_RGB2GRAY)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (cfg.kernel_size, cfg.kernel_size))
    response = cv.morphologyEx(gray, cv.MORPH_BLACKHAT, kernel)
    threshold, _ = cv.threshold(response, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    applied_threshold = max(float(cfg.min_contrast), float(threshold))
    mask = (response > applied_threshold).astype(np.uint8)
    count, _, stats, _ = cv.connectedComponentsWithStats(mask, connectivity=8)
    candidates = []
    seen = set()
    accepted_components = 0
    for x, y, width, height, area in stats[1:]:
        if not cfg.min_area <= int(area) <= cfg.max_area:
            continue
        accepted_components += 1
        proposal_bbox = [int(x), int(y), int(x + width), int(y + height)]
        bbox = contextual_box(proposal_bbox, image_rgb.shape, cfg)
        if bbox in seen:
            continue
        seen.add(bbox)
        candidates.append({"bbox": list(bbox), "proposal_bbox": proposal_bbox, "area": int(area)})
    candidates.sort(key=lambda row: (row["bbox"][1], row["bbox"][0], row["bbox"][3], row["bbox"][2]))
    before_merge = len(candidates)
    if cfg.merge_max_size is not None:
        candidates = merge_overlapping_regions(candidates, cfg.merge_max_size)
    diagnostics = {
        "method": cfg.method,
        "parameters_status": "provisorios_nao_calibrados",
        "threshold": applied_threshold,
        "selected_pixels": int(mask.sum()),
        "components": int(count - 1),
        "accepted_components": accepted_components,
        "candidates": len(candidates),
        "candidates_before_merge": before_merge,
        "merged_redundant_candidates": before_merge - len(candidates),
    }
    return candidates, diagnostics
