"""Diagnóstico suplementar de A/B nos MESMOS recortes revisados de validação.

Não substitui comparação em imagens inteiras. Os recortes foram propostos pelo
B original, e o domínio bruto desses recortes difere das regiões mascaradas do A.
"""
from pathlib import Path
import argparse
from collections import Counter
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def summarize(truth, predicted):
    import numpy as np
    matrix=np.zeros((2,2),dtype=int)
    np.add.at(matrix,(truth,predicted),1)
    tn,fp,fn,tp=matrix.ravel().tolist()
    ratio=lambda a,b:a/b if b else None
    return {'n':len(truth),'accuracy':float(np.mean(truth==predicted)),
            'confusion_matrix_rows_true_columns_predicted':matrix.tolist(),
            'negative_recall':ratio(tn,tn+fp),'positive_recall':ratio(tp,tp+fn),
            'positive_precision':ratio(tp,tp+fp),'positive_f1':ratio(2*tp,2*tp+fp+fn)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment',type=Path,default=ROOT/'configs/experiment_cpu.json',
                        help='Define o conjunto comum de recortes; apenas val é avaliado.')
    parser.add_argument('--model-a',type=Path,default=ROOT/'models/model_a/model_trained.keras')
    parser.add_argument('--checkpoint-b',type=Path,default=ROOT/'experiments/runs/b_real_cpu_01/best.keras')
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--batch-size',type=int,default=8)
    parser.add_argument('--compiled',action='store_true',help='Executa ambas as redes em grafo TensorFlow.')
    args=parser.parse_args()
    if args.output_dir.exists(): raise FileExistsError('Use um destino novo para preservar o diagnóstico.')
    if args.batch_size<1: raise ValueError('Lote deve ser positivo.')
    import numpy as np
    import tensorflow as tf
    from PIL import Image
    from scripts.check_training_ready import resolve_paths
    from src import data_protocol as dp
    from src.data_pipeline import file_sha256,load_split,validate_crop_manifest,resize_rgb_for_model
    from src.dataset_policy import validate_active_images
    from src.segmentation import localization_hash
    from src.train import load_config
    from src.model_a import load_original_model,preprocess_original
    tf.config.threading.set_inter_op_parallelism_threads(2)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    experiment=json.loads(args.experiment.read_text(encoding='utf-8-sig'))
    paths=resolve_paths(experiment)
    images=dp.read_manifest(paths['image_manifest'])
    validate_active_images(images)
    annotations=dp.load_annotations(paths['annotations'],images)
    cfg=load_config(paths['model_config'])
    crops=load_split(paths['crop_manifest'])
    validate_crop_manifest(crops,images,annotations,localization_hash(cfg['localization']),file_sha256(paths['annotations']))
    val=crops.loc[crops['split']=='val'].copy()
    if set(val['label'].astype(int))!={0,1}: raise ValueError('Validação comum deve ter as duas classes.')
    meta=json.loads((args.checkpoint_b.parent/'metadata.json').read_text(encoding='utf-8-sig'))
    if meta.get('synthetic') is not False or meta.get('status')!='complete' or meta.get('checkpoint_sha256')!=file_sha256(args.checkpoint_b):
        raise ValueError('B exige checkpoint real concluído e hash correto.')
    saved=json.loads((args.checkpoint_b.parent/'config.json').read_text(encoding='utf-8-sig'))
    model_a,artifact_a=load_original_model(args.model_a)
    model_b=tf.keras.models.load_model(args.checkpoint_b,safe_mode=True)
    call_a,call_b=model_a,model_b
    if args.compiled:
        from src.model_b import compiled_inference
        call_a=compiled_inference(model_a,tuple(model_a.input_shape[1:]))
        call_b=compiled_inference(model_b,tuple(model_b.input_shape[1:]))
    args.output_dir.mkdir(parents=True)
    outputs={key:[] for key in ('A','B')}
    timings=Counter()
    rows=val.to_dict('records')
    # Alterna a ordem por lote para reduzir o efeito da ordem de execução.
    for start in range(0,len(rows),args.batch_size):
        batch_rows=rows[start:start+args.batch_size]
        rgb=[]
        for row in batch_rows:
            path=Path(row['path'])
            with Image.open(path if path.is_absolute() else ROOT/path) as image:
                rgb.append(np.array(image.convert('RGB')))
        for system in (('A','B') if (start//args.batch_size)%2==0 else ('B','A')):
            begin=time.perf_counter()
            if system=='A':
                x=np.concatenate([preprocess_original(image[:,:,::-1].copy()) for image in rgb])
                model=call_a
            else:
                x=np.stack([resize_rgb_for_model(image,saved['model']['input_shape'][:2]) for image in rgb])
                model=call_b
            timings[system+'_preprocessing_seconds']+=time.perf_counter()-begin
            begin=time.perf_counter()
            scores=np.asarray(model(x,training=False))
            timings[system+'_classification_seconds']+=time.perf_counter()-begin
            if scores.shape!=(len(rgb),2) or not np.isfinite(scores).all(): raise ValueError('Escores inválidos.')
            outputs[system].extend(scores.tolist())
        if start%256==0: print(f'Recortes comuns: {min(start+args.batch_size,len(rows))}/{len(rows)}',flush=True)
    truth=val['label'].astype(int).to_numpy()
    report={'purpose':'diagnostico_suplementar_mesmos_recortes','split':'val','heldout_test_evaluated':False,
            'crop_manifest_sha256':file_sha256(paths['crop_manifest']), 'annotation_sha256':file_sha256(paths['annotations']),
            'model_a_sha256':artifact_a['sha256'],'model_b_sha256':file_sha256(args.checkpoint_b),
            'images':int(val['image_id'].nunique()),'negative_source_images':int(val.loc[val['label']==0,'image_id'].nunique()),
            'batch_size_both_models':args.batch_size,'hardware':[d.name for d in tf.config.list_physical_devices()],
            'execution_mode_both_models':'tf_function' if args.compiled else 'eager',
            'systems':{k:summarize(truth,np.asarray(v).argmax(axis=1)) for k,v in outputs.items()},
            'timings':dict(timings),
            'limitations':['Validação participou da seleção do B; não é teste independente.',
                'Recortes selecionados pelo localizador B original; não representam distribuição neutra de propostas.',
                'A recebeu mesmos pixels brutos que B; a segmentação de fundo do sistema A foi excluída deste diagnóstico.',
                'Mantidos pré-processamentos próprios: A usa resize OpenCV/ResNet50; B resize TensorFlow/RGB [0,255].',
                'Histórico de treinamento e possível sobreposição da base com A continuam desconhecidos.',
                'Tempos incluem primeira chamada e não constituem benchmark controlado.']}
    (args.output_dir/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    records=val[['crop_id','image_id','label']].copy()
    for key,scores in outputs.items():
        values=np.asarray(scores)
        records[key+'_predicted']=values.argmax(axis=1)
        records[key+'_positive_score']=values[:,1]
    records.to_csv(args.output_dir/'predictions.csv',index=False)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
