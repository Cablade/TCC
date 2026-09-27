import copy
import csv
import hashlib

import numpy as np
from PIL import Image

from src.prediction_exports import export_saved_predictions, write_review_csvs


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def prediction():
    boxes = [[1, 2, 8, 9], [12, 13, 18, 19]]
    return {'image_id': 'field/unsafe', 'status': 'predicao_positiva', 'original_decision': 1,
            'candidates': [{'bbox': box} for box in boxes],
            'regions': [{'bbox': box, 'class_id': index, 'scores': [.9, .1] if index == 0 else [.2, .8]}
                        for index, box in enumerate(boxes)],
            'timings': {'total_seconds': 2.5, 'io_and_inference_seconds': 3.0}}


def test_original_pixels_and_region_decisions_preserved(tmp_path):
    pixels = np.random.default_rng(42).integers(0, 256, (24, 28, 3), dtype=np.uint8)
    source = tmp_path / 'source.png'
    Image.fromarray(pixels).save(source)
    payload = {'images': [prediction()]}
    before = copy.deepcopy(payload)
    manifest = [{'image_id': 'field/unsafe', 'path': str(source), 'width': 28, 'height': 24,
                 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}]
    out = tmp_path / 'review'
    exported = export_saved_predictions(payload, manifest, out)
    assert payload == before
    with Image.open(out / exported['field/unsafe']['image_file']) as actual:
        np.testing.assert_array_equal(np.asarray(actual), pixels)
    summary = read_csv(out / 'images.csv')[0]
    assert list(summary)[:7] == ['image_id', 'status', 'original_decision', 'candidates', 'classified', 'seconds', 'error']
    assert summary['original_decision'] == 'suspeita'
    assert summary['positive_regions'] == summary['negative_regions'] == '1'
    assert summary['seconds'] == '2.5'
    details = read_csv(out / 'regions.csv')
    assert [r['classification'] for r in details] == ['sem_suspeita', 'suspeita']
    assert [r['candidate_id'] for r in details] == ['1', '2']
    assert details[1]['x1'] == '12' and details[1]['score_suspect'] == '0.8'


def test_no_regions_and_failed_classification_are_not_negative_regions(tmp_path):
    empty = dict(prediction(), image_id='empty', status='sem_regioes', original_decision=0, candidates=[], regions=[])
    failed = dict(prediction(), image_id='failed', status='erro', original_decision=None,
                  regions=[], error='classification failed')
    write_review_csvs([empty, failed], tmp_path)
    images = read_csv(tmp_path / 'images.csv')
    assert images[0]['status'] == 'sem_regioes' and images[0]['negative_regions'] == '0'
    assert images[1]['classified'] == '0' and images[1]['original_decision'] == ''
    details = read_csv(tmp_path / 'regions.csv')
    assert len(details) == 2
    assert all(r['status'] == 'nao_classificado' and r['class_id'] == '' for r in details)


def test_export_error_does_not_replace_model_result(tmp_path):
    source = tmp_path / 'changed.png'
    Image.new('RGB', (24, 28)).save(source)
    result = prediction()
    out = tmp_path / 'review'
    export_saved_predictions({'images': [result]}, [{'image_id': result['image_id'], 'path': str(source),
                             'sha256': 'wrong', 'width': 24, 'height': 28}], out)
    summary = read_csv(out / 'images.csv')[0]
    assert summary['status'] == 'predicao_positiva' and summary['error'] == ''
    assert 'Hash' in summary['export_error'] and summary['image_file'] == ''
    assert not list(out.rglob('*.png'))
