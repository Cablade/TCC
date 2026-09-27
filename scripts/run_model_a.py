"""Inferência do A em imagens inteiras de manifesto com partições persistidas."""
from __future__ import annotations
import argparse
import csv
import json
import sys
import time
from pathlib import Path
import cv2
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.model_a import load_original_model, infer_image, draw_overlay, file_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--model', default=str(ROOT / 'models/model_a/model_trained.keras'),
                        help='Modelo A congelado; padrão: models/model_a/model_trained.keras no TCC.')
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--split', default='development')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--overlays', action='store_true')
    parser.add_argument('--threads', type=int, default=0, help='Threads intra/inter-op do TensorFlow; 0 mantém automático.')
    args = parser.parse_args()
    if args.threads < 0:
        parser.error('--threads deve ser >= 0')
    if args.threads:
        import tensorflow as tf
        tf.config.threading.set_intra_op_parallelism_threads(args.threads)
        tf.config.threading.set_inter_op_parallelism_threads(args.threads)
    from src.data_protocol import read_image_bytes, validate_partitions
    with open(args.manifest, encoding='utf-8-sig', newline='') as file:
        rows = list(csv.DictReader(file))
    if any('split' not in row for row in rows):
        raise ValueError('Use manifesto com partições persistidas')
    validate_partitions(rows)
    rows = [row for row in rows if row['split']==args.split and not row.get('duplicate_of')]
    if args.limit is not None:
        rows = rows[:args.limit]
    if not rows:
        raise ValueError('Nenhuma imagem única na partição solicitada')
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if (output/'predictions.json').exists():
        raise FileExistsError('Resultado existente; escolha outro --output-dir para preservar a execução')
    start = time.perf_counter()
    model, artifact = load_original_model(args.model)
    artifact['load_seconds'] = time.perf_counter()-start
    artifact['tensorflow_threads'] = {'intra_op': args.threads, 'inter_op': args.threads}
    artifact['overlays_saved'] = args.overlays
    results = []
    for row in rows:
        start = time.perf_counter()
        try:
            raw = read_image_bytes(row['path'])
            if row.get('sha256') and __import__('hashlib').sha256(raw).hexdigest()!=row['sha256']:
                raise ValueError('Conteúdo da imagem difere do manifesto')
            image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
            if image is None or image.shape[:2] != (int(row['height']), int(row['width'])):
                raise ValueError('Decodificação/dimensões diferem do inventário')
            decode_seconds = time.perf_counter()-start
            result = infer_image(image, model, row['image_id'])
            result['timings']['decode_seconds'] = decode_seconds
            result['timings']['pipeline_seconds'] = time.perf_counter()-start
            if args.overlays and image is not None:
                overlay = output/'overlays'/(row['image_id']+'.png')
                overlay.parent.mkdir(exist_ok=True)
                ok, encoded = cv2.imencode('.png', draw_overlay(image, result))
                if not ok:
                    raise RuntimeError('Falha ao salvar sobreposição')
                overlay.write_bytes(encoded.tobytes())
        except Exception as error:
            result = {'image_id': row['image_id'], 'status': 'erro', 'regions': [], 'candidates': [],
                      'original_decision': None, 'error': str(error), 'timings': {'total_seconds': time.perf_counter()-start}}
        results.append(result)
        print(row['image_id'], result['status'], flush=True)
    payload = {'schema_version': 1, 'system': 'A', 'split': args.split,
               'manifest_sha256': file_sha256(args.manifest), 'artifact': artifact,
               'images': results, 'note': 'Diagnóstico de execução; escores não calibrados.'}
    (output/'predictions.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    with (output/'images.csv').open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['image_id','status','original_decision','candidates','classified','seconds','error'])
        writer.writeheader()
        for result in results:
            writer.writerow({'image_id':result['image_id'], 'status':result['status'],
                             'original_decision':result['original_decision'], 'candidates':len(result['candidates']),
                             'classified':len(result['regions']), 'seconds':result['timings']['total_seconds'],
                             'error':result.get('error','')})
    return int(any(result['status']=='erro' for result in results))


if __name__=='__main__':
    raise SystemExit(main())
