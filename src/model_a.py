"""A congelado: inferência do VisionCruzi 59b10244, sem API de treinamento."""
from __future__ import annotations
import hashlib
import io
import json
import platform
import tempfile
import time
import zipfile
from pathlib import Path
import cv2 as cv
import numpy as np

REFERENCE_COMMIT = '59b10244f2ce5cfabff7bece404cb5679668a45d'
REFERENCE_MODEL_SHA256 = '9fd092567f2579ffd283d1796c472230853481de394a81159f312a598440893f'
CLASS_LABELS = ('0', '1')  # confirmado em label_encoder.dat e _build_summary


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def tensor_fingerprints(raw):
    import h5py
    result = {}
    with h5py.File(io.BytesIO(raw), 'r') as handle:
        def visit(name, obj):
            if isinstance(obj, h5py.Dataset):
                key = name.replace('\\', '/')
                if key in result:
                    raise ValueError('Colisão de caminhos normalizados')
                array = np.asarray(obj)
                result[key] = (array.shape, str(array.dtype), hashlib.sha256(array.tobytes()).hexdigest())
        handle.visititems(visit)
    return result


def normalize_keras_copy(source, target):
    """Cópia temporária com caminhos HDF5 portáveis e tensores idênticos."""
    import h5py
    source, target = Path(source), Path(target)
    if source.resolve() == target.resolve() or target.exists():
        raise ValueError('A cópia deve ser nova e distinta do original')
    before = file_sha256(source)
    with zipfile.ZipFile(source) as archive:
        raw = archive.read('model.weights.h5')
        expected = tensor_fingerprints(raw)
        buffer = io.BytesIO()
        with h5py.File(io.BytesIO(raw), 'r') as src, h5py.File(buffer, 'w') as dst:
            for key, value in src.attrs.items():
                dst.attrs[key] = value
            def copy(name, obj):
                name = name.replace('\\', '/')
                if isinstance(obj, h5py.Group):
                    out = dst.require_group(name)
                else:
                    parent, _, leaf = name.rpartition('/')
                    group = dst.require_group(parent) if parent else dst
                    out = group.create_dataset(leaf, data=obj[()], dtype=obj.dtype)
                for key, value in obj.attrs.items():
                    out.attrs[key] = value
            src.visititems(copy)
        converted = buffer.getvalue()
        if tensor_fingerprints(converted) != expected:
            raise RuntimeError('A normalização alterou tensores')
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as output:
            for item in archive.infolist():
                output.writestr(item, converted if item.filename == 'model.weights.h5' else archive.read(item))
    if file_sha256(source) != before:
        raise RuntimeError('O original foi alterado')
    return {'tensor_count': len(expected), 'all_tensors_preserved': True, 'source_sha256': before}


def load_original_model(path):
    import tensorflow as tf
    import keras
    import h5py
    path = Path(path)
    digest = file_sha256(path)
    if digest != REFERENCE_MODEL_SHA256:
        raise ValueError('Artefato diferente do A auditado. Confirme origem e mapeamento antes de atualizar a referência congelada.')
    with zipfile.ZipFile(path) as archive:
        raw = archive.read('model.weights.h5')
        metadata = json.loads(archive.read('metadata.json'))
    names = []
    with h5py.File(io.BytesIO(raw), 'r') as handle:
        handle.visit(names.append)
    normalize = platform.system() != 'Windows' and any('\\' in name for name in names)
    report = {'sha256': digest, 'artifact_bytes': path.stat().st_size, 'keras_metadata': metadata,
              'tensorflow': tf.__version__, 'keras': keras.__version__, 'opencv': cv.__version__,
              'python': platform.python_version(), 'platform': platform.platform(),
              'hardware': {'processor': platform.processor(), 'devices': [device.name for device in tf.config.list_physical_devices()]},
              'reference_repository': 'https://github.com/Cablade/VisionCruzi',
              'reference_commit': REFERENCE_COMMIT, 'class_labels': list(CLASS_LABELS),
              'class_mapping_source': "label_encoder.dat classes_=['0','1']; API _build_summary",
              'normalized_copy': normalize, 'training_time_seconds': None}
    if normalize:
        with tempfile.TemporaryDirectory(prefix='tcc_model_a_') as temp:
            copy = Path(temp)/'normalized.keras'
            report['preservation'] = normalize_keras_copy(path, copy)
            model = tf.keras.models.load_model(copy, compile=False)
    else:
        model = tf.keras.models.load_model(path, compile=False)
        report['preservation'] = {'tensor_count': len(tensor_fingerprints(raw)),
                                  'original_unchanged': file_sha256(path) == digest}
    report['model_weight_count'] = len(model.weights)
    if tuple(model.input_shape[1:]) != (224, 224, 3) or model.output_shape[-1] != 2:
        raise ValueError('Artefato incompatível com a entrada/saída do A de referência')
    model.trainable = False
    return model, report


def locate_original(image_bgr):
    """Reprodução literal das operações e limites do decision_predictor.py."""
    if image_bgr is None or image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError('Imagem BGR inválida')
    hsv = cv.cvtColor(image_bgr, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, np.array([145, 100, 30]), np.array([165, 255, 120]))
    counts = {'hsv_color_pixels': int(np.count_nonzero(mask))}
    kernel = np.ones((30, 30), np.uint8)
    mask = cv.morphologyEx(cv.dilate(mask, kernel, iterations=2), cv.MORPH_OPEN, kernel)
    counts['morphology_pixels'] = int(np.count_nonzero(mask))
    num_labels, labels_im = cv.connectedComponents(mask)
    for lab in range(1, num_labels):
        area = np.sum(labels_im == lab)
        if area < 3450 or area > 15300:
            mask[labels_im == lab] = 0
    counts['area_filtered_pixels'] = int(np.count_nonzero(mask))
    result = cv.bitwise_and(image_bgr, image_bgr, mask=mask)
    hsv_result = cv.cvtColor(result, cv.COLOR_BGR2HSV)
    nucleus = cv.inRange(hsv_result, np.array([120, 50, 30]), np.array([170, 255, 150]))
    _, nucleus = cv.threshold(nucleus, 127, 255, cv.THRESH_BINARY)
    counts['nucleus_pixels'] = int(np.count_nonzero(nucleus))
    n, labels, stats, centroids = cv.connectedComponentsWithStats(nucleus)
    counts['components_before_area_filter'] = int(n-1)
    candidates = []
    for lab in range(1, n):
        x, y, w, h, area = [int(v) for v in stats[lab]]
        if area < 450 or area > 1100:
            continue
        roi = result[y:y+h, x:x+w]
        if roi.size:
            candidates.append({'component_id': lab, 'bbox': [x,y,x+w,y+h], 'area': area, 'roi_bgr': roi})
    counts['candidates'] = len(candidates)
    return candidates, counts


def preprocess_original(roi_bgr):
    from tensorflow.keras.applications.resnet50 import preprocess_input
    rgb = cv.cvtColor(roi_bgr, cv.COLOR_BGR2RGB)
    return preprocess_input(np.expand_dims(cv.resize(rgb, (224,224)).astype('float32'), axis=0))


def infer_image(image_bgr, model, image_id='unknown'):
    start = time.perf_counter()
    result = {'image_id': image_id, 'status': 'erro', 'regions': [], 'candidates': [],
              'original_decision': None, 'timings': {}, 'instrumentation': {}}
    try:
        candidates, counts = locate_original(image_bgr)
        result['timings']['localization_seconds'] = time.perf_counter()-start
        result['instrumentation'] = counts
        result['candidates'] = [{k:v for k,v in item.items() if k!='roi_bgr'} for item in candidates]
        result['timings']['classification_seconds'] = 0.0
        result['timings']['preprocessing_seconds'] = 0.0
        for item in candidates:
            stage_start = time.perf_counter()
            batch = preprocess_original(item['roi_bgr'])
            result['timings']['preprocessing_seconds'] += time.perf_counter()-stage_start
            stage_start = time.perf_counter()
            scores = np.asarray(model.predict(batch, verbose=0))[0]
            result['timings']['classification_seconds'] += time.perf_counter()-stage_start
            if scores.shape != (2,) or not np.isfinite(scores).all():
                raise ValueError('Escores inválidos do classificador A')
            index = int(scores.argmax())
            result['regions'].append({'component_id': item['component_id'], 'bbox': item['bbox'],
                                      'class_id': int(CLASS_LABELS[index]), 'scores': scores.tolist()})
        positive = any(region['class_id']==1 for region in result['regions'])
        result['status'] = 'sem_regioes' if not candidates else ('predicao_positiva' if positive else 'regioes_sem_predicao_positiva')
        result['original_decision'] = 'suspeita' if positive else 'sem_suspeita'
        result['image_prediction'] = int(positive)
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    result['instrumentation']['classified_regions'] = len(result['regions'])
    result['timings']['total_seconds'] = time.perf_counter()-start
    return result


def draw_overlay(image_bgr, result):
    output = image_bgr.copy()
    for region in result['regions']:
        x1,y1,x2,y2 = region['bbox']
        color = (0,0,255) if region['class_id']==1 else (0,170,0)
        cv.rectangle(output, (x1,y1), (x2-1,y2-1), color, 2)
    cv.putText(output, result['status'], (10,30), cv.FONT_HERSHEY_SIMPLEX, .7, (0,0,255), 2)
    return output
