"""Exportações de revisão, sem executar modelos ou alterar suas decisões."""
from __future__ import annotations

import csv
import hashlib
import io
import time
from pathlib import Path

from PIL import Image

IMAGE_FIELDS = ['image_id', 'status', 'original_decision', 'candidates', 'classified',
                'seconds', 'error', 'positive_regions', 'negative_regions',
                'image_file', 'export_seconds', 'export_error']
REGION_FIELDS = ['image_id', 'candidate_id', 'status', 'classification', 'class_id',
                 'x1', 'y1', 'x2', 'y2', 'score_negative', 'score_suspect',
                 'image_seconds', 'error']


def image_seconds(result):
    """Tempo do algoritmo, excluindo leitura e gravação de arquivos."""
    return result['timings'].get('total_seconds', '')


def decision_label(result):
    if result['status'] == 'erro':
        return ''
    value = result.get('original_decision')
    return {0: 'sem_suspeita', 1: 'suspeita'}.get(value, value)


def save_original_png(image_rgb, output_dir, image_id):
    """PNG RGB inteiro: mesmos pixels decodificados, sem caixas ou recortes."""
    output_dir = Path(output_dir)
    token = hashlib.sha256(str(image_id).encode('utf-8')).hexdigest()
    relative = Path('images') / f'{token}.png'
    target = output_dir / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image_rgb).save(target)
    return relative.as_posix()


def write_review_csvs(results, output_dir, exports=None):
    """Resumo compatível com A e detalhes dos candidatos, inclusive não classificados."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    exports = exports or {}
    with (output_dir / 'images.csv').open('w', newline='', encoding='utf-8-sig') as summary, \
         (output_dir / 'regions.csv').open('w', newline='', encoding='utf-8-sig') as regions_file:
        images_writer = csv.DictWriter(summary, fieldnames=IMAGE_FIELDS)
        regions_writer = csv.DictWriter(regions_file, fieldnames=REGION_FIELDS)
        images_writer.writeheader()
        regions_writer.writeheader()
        for result in results:
            regions = result['regions']
            exported = exports.get(result['image_id'], {})
            images_writer.writerow({
                'image_id': result['image_id'], 'status': result['status'],
                'original_decision': decision_label(result), 'candidates': len(result['candidates']),
                'classified': len(regions), 'seconds': image_seconds(result),
                'error': result.get('error', ''),
                'positive_regions': sum(r['class_id'] == 1 for r in regions),
                'negative_regions': sum(r['class_id'] == 0 for r in regions),
                **exported,
            })
            # A e B preservam a ordem dos candidatos na lista de regiões.
            for index, candidate in enumerate(result['candidates']):
                region = regions[index] if index < len(regions) else None
                if region is not None and region['bbox'] != candidate['bbox']:
                    raise ValueError('Ordem das regiões difere dos candidatos.')
                scores = region['scores'] if region is not None else ['', '']
                class_id = region['class_id'] if region is not None else ''
                x1, y1, x2, y2 = candidate['bbox']
                regions_writer.writerow({
                    'image_id': result['image_id'], 'candidate_id': index + 1,
                    'status': 'classificado' if region is not None else 'nao_classificado',
                    'classification': {0: 'sem_suspeita', 1: 'suspeita'}.get(class_id, ''),
                    'class_id': class_id, 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'score_negative': scores[0], 'score_suspect': scores[1],
                    'image_seconds': image_seconds(result), 'error': result.get('error', ''),
                })


def export_saved_predictions(payload, manifest_rows, output_dir):
    """Reexporta A/B concluído sem inferência; confere origem, hashes e dimensões."""
    import numpy as np
    from .data_protocol import read_image_bytes
    rows = {row['image_id']: row for row in manifest_rows}
    results = payload['images']
    ids = [result['image_id'] for result in results]
    if len(ids) != len(set(ids)) or any(image_id not in rows for image_id in ids):
        raise ValueError('IDs duplicados ou ausentes no manifesto.')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    exports = {}
    for result in results:
        start = time.perf_counter()
        entry = {'image_file': '', 'export_error': ''}
        try:
            row = rows[result['image_id']]
            raw = read_image_bytes(row['path'])
            if hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('Hash da imagem difere do manifesto.')
            with Image.open(io.BytesIO(raw)) as source:
                pixels = np.asarray(source.convert('RGB'))
            if pixels.shape[:2] != (int(row['height']), int(row['width'])):
                raise ValueError('Dimensões diferem do inventário.')
            entry['image_file'] = save_original_png(pixels, output_dir, result['image_id'])
        except Exception as exc:
            entry['export_error'] = f'{type(exc).__name__}: {exc}'
        entry['export_seconds'] = time.perf_counter() - start
        exports[result['image_id']] = entry
    write_review_csvs(results, output_dir, exports)
    return exports
