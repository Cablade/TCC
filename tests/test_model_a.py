import io
import json
import zipfile
from unittest.mock import Mock
import cv2
import h5py
import numpy as np
import pytest
from src.model_a import infer_image, locate_original, normalize_keras_copy, file_sha256, tensor_fingerprints


def synthetic_candidate():
    hsv = np.zeros((180,180,3), dtype=np.uint8)
    hsv[:,:,:] = [0,0,255]
    hsv[70:95,70:95] = [155,200,100]
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def test_no_region_never_calls_classifier():
    model = Mock()
    result = infer_image(np.full((200,200,3),255,np.uint8), model, 'white')
    assert result['status']=='sem_regioes'
    assert result['original_decision']=='sem_suspeita'
    assert result['instrumentation']['hsv_color_pixels']==0
    model.predict.assert_not_called()


def test_positive_negative_and_error_are_distinct():
    image = synthetic_candidate()
    candidates, counts = locate_original(image)
    assert len(candidates)==1
    assert candidates[0]['bbox']==[70,70,95,95]
    positive = Mock(); positive.predict.return_value=np.array([[.1,.9]])
    result = infer_image(image,positive)
    assert result['status']=='predicao_positiva'
    assert result['image_prediction']==1
    negative = Mock(); negative.predict.return_value=np.array([[.9,.1]])
    assert infer_image(image,negative)['status']=='regioes_sem_predicao_positiva'
    failed = Mock(); failed.predict.side_effect=RuntimeError('failure')
    assert infer_image(image,failed)['status']=='erro'
    assert infer_image(None,positive)['status']=='erro'


def test_temporary_conversion_preserves_values_and_original(tmp_path):
    buf = io.BytesIO()
    with h5py.File(buf,'w') as f:
        f.create_dataset('layers\\dense/vars/0', data=np.arange(12,dtype=np.float32).reshape(3,4))
    original = tmp_path/'original.keras'
    with zipfile.ZipFile(original,'w') as z:
        z.writestr('model.weights.h5',buf.getvalue())
        z.writestr('config.json','{}')
        z.writestr('metadata.json','{}')
    digest=file_sha256(original)
    copy=tmp_path/'copy.keras'
    report=normalize_keras_copy(original,copy)
    assert report['all_tensors_preserved'] and report['tensor_count']==1
    assert digest==file_sha256(original)
    with zipfile.ZipFile(copy) as z:
        assert tensor_fingerprints(z.read('model.weights.h5'))==tensor_fingerprints(buf.getvalue())
        with h5py.File(io.BytesIO(z.read('model.weights.h5')),'r') as f:
            assert 'layers/dense/vars/0' in f
    with pytest.raises(ValueError):
        normalize_keras_copy(original,original)
