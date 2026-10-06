"""Variações determinísticas de desenvolvimento, com referência derivada."""
from copy import deepcopy
from functools import lru_cache
import io

import numpy as np
from PIL import Image

TRANSFORMS = ('rotation90', 'flip_horizontal', 'brightness85')
DESCRIPTIONS = {
    'original': 'Original', 'rotation90': 'Rotação 90°',
    'flip_horizontal': 'Espelho horizontal', 'brightness85': 'Brilho × 0,85',
}


def transform_pixels(pixels, transform):
    if transform == 'rotation90':
        return np.rot90(pixels).copy()
    if transform == 'flip_horizontal':
        return pixels[:, ::-1].copy()
    if transform == 'brightness85':
        return np.rint(pixels.astype(np.float64) * .85).astype(np.uint8)
    raise ValueError('Variação desconhecida: ' + transform)


@lru_cache(maxsize=1)
def variant_bytes(raw, transform):
    with Image.open(io.BytesIO(raw)) as image:
        pixels = transform_pixels(np.asarray(image.convert('RGB')), transform)
    stream = io.BytesIO()
    Image.fromarray(pixels).save(stream, format='PNG', compress_level=1)
    return stream.getvalue()


def transform_bbox(box, width, height, transform):
    x1, y1, x2, y2 = box
    if transform == 'rotation90':
        return [y1, width-x2, y2, width-x1]
    if transform == 'flip_horizontal':
        return [width-x2, y1, width-x1, y2]
    if transform == 'brightness85':
        return list(box)
    raise ValueError('Variação desconhecida: ' + transform)


def transform_point(point, width, height, transform):
    # Pontos publicados indicam índices de pixels. Rejeitar coordenadas
    # fracionárias: exigiriam uma convenção explícita de centro de pixel.
    x, y = point
    if any(float(v) != int(v) for v in point):
        raise ValueError('Variações geométricas exigem pontos em índices inteiros de pixels.')
    if transform == 'rotation90':
        return [y, width-1-x]
    if transform == 'flip_horizontal':
        return [width-1-x, y]
    if transform == 'brightness85':
        return list(point)
    raise ValueError('Variação desconhecida: ' + transform)


def transform_annotation(annotation, image_id, transform):
    result = deepcopy(annotation)
    width, height = annotation['width'], annotation['height']
    result['image_id'] = image_id
    if transform == 'rotation90':
        result['width'], result['height'] = height, width
    for positive in result['positives']:
        if 'point' in positive:
            positive['point'] = transform_point(positive['point'], width, height, transform)
        else:
            positive['bbox'] = transform_bbox(positive['bbox'], width, height, transform)
    for negative in result['negative_regions']:
        negative['bbox'] = transform_bbox(negative['bbox'], width, height, transform)
    result['derived_reference'] = dict(original_image_id=annotation['image_id'],
        transform=transform, new_human_review=False,
        note='Referência e rótulo herdados do original; não há nova anotação humana nem inferência de rótulo pelo modelo.')
    return result
