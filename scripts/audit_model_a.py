"""Audita artefato A e equivalência com o código local de referência, sem editar origem."""
import argparse
import importlib.util
import json
from pathlib import Path
import pickle
import sys
import tempfile
import zipfile
import hashlib
import numpy as np
import cv2
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.model_a import normalize_keras_copy,file_sha256,load_original_model,infer_image
from scripts.notebook_support import SyntheticClassifier


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference-dir',required=True,help='Pasta decision/services local conhecida')
    p.add_argument('--output',required=True)
    args=p.parse_args()
    ref=Path(args.reference_dir)
    original=ref/'model_trained.keras'
    model,report=load_original_model(original)
    # O encoder local foi inspecionado por pickletools; o arquivo é artefato da referência.
    with (ref/'label_encoder.dat').open('rb') as f:
        encoder=pickle.load(f)
    if list(encoder.classes_)!=['0','1']:
        raise ValueError('Mapeamento do encoder não corresponde à referência congelada')
    report['label_encoder_sha256']=file_sha256(ref/'label_encoder.dat')
    report['confirmed_classes']=encoder.classes_.tolist()
    with tempfile.TemporaryDirectory(prefix='tcc_audit_') as tmp:
        report['conversion_audit']=normalize_keras_copy(original,Path(tmp)/'normalized.keras')
    # Compara tensores de camadas carregados com valores armazenados, excluindo otimizador.
    import h5py,io
    stored=[]
    with zipfile.ZipFile(original) as z, h5py.File(io.BytesIO(z.read('model.weights.h5')),'r') as f:
        def collect(name,obj):
            if isinstance(obj,h5py.Dataset) and name.replace('\\','/').startswith('layers/'):
                stored.append(hashlib.sha256(np.asarray(obj).tobytes()).hexdigest())
        f.visititems(collect)
    actual=[hashlib.sha256(np.asarray(w).tobytes()).hexdigest() for w in model.weights]
    if sorted(stored)!=sorted(actual):
        raise AssertionError('Valores carregados diferem dos armazenados')
    report['loaded_layer_tensors_verified']=len(actual)
    spec=importlib.util.spec_from_file_location('tcc_reference_a',ref/'decision_predictor.py')
    reference=importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    reference._MODEL_CACHE=SyntheticClassifier(); reference._ENCODER_CACHE=encoder
    cases=[]
    for colored in (False,True):
        hsv=np.full((180,180,3),[0,0,255],np.uint8)
        if colored: hsv[70:95,70:95]=[155,200,100]
        image=cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
        _,encoded=cv2.imencode('.png',image)
        expected=reference.predict_image_has_chagas(encoded.tobytes())
        obtained=infer_image(image,SyntheticClassifier())
        labels={f'componente_{r["component_id"]}':str(r['class_id']) for r in obtained['regions']}
        if labels!=expected: raise AssertionError('Divergência de inferência sintética')
        cases.append({'synthetic':True,'colored':colored,'original_predictions':expected,'status':obtained['status']})
    # O classificador real também recebe um recorte sintético, apenas como verificação de execução.
    report['real_artifact_synthetic_input']=infer_image(image,model,'synthetic_colored_square')
    report['reference_source_sha256']=file_sha256(ref/'decision_predictor.py')
    report['differential_synthetic_cases']=cases
    output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'stored_tensors':report['conversion_audit']['tensor_count'],
                      'loaded_layer_tensors':len(actual),'differential_cases':len(cases)}))


if __name__=='__main__': main()
