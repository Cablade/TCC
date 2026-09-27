"""Estuda união de propostas só em treino/validação, com política registrada antes da seleção."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp
from src.data_pipeline import file_sha256
from src.segmentation import propose_regions, merge_overlapping_regions, localization_hash
from src.detection_evaluation import match_one_to_one


def measurements(candidates, annotation):
    points = annotation['positives']
    hit = {p['annotation_id'] for p in points if any(dp.annotation_intersects_box(p,c['bbox']) for c in candidates)}
    labels = Counter(dp.candidate_label(c['bbox'], annotation) for c in candidates)
    return {'candidates':len(candidates), 'known_positives':len(points), 'covered_points':len(hit),
            'covered_ids':sorted(hit), 'one_to_one_matches':len(match_one_to_one(candidates, points)['pairs']),
            'positive_crops':labels[1], 'negative_crops':labels[0], 'unknown_crops':labels[None]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'experiments/validation/region_merging_20260926')
    args=parser.parse_args()
    out=args.output_dir
    out.mkdir(parents=True,exist_ok=True)
    manifest=ROOT/'data/splits/experimento/images.csv'
    ann_path=ROOT/'data/annotations/experimento_reference_v2.json'
    base_path=ROOT/'experiments/runs/b_real_cpu_01/config.json'
    base=json.loads(base_path.read_text(encoding='utf-8'))
    images=dp.read_manifest(manifest)
    dp.validate_partitions(images)
    from src.dataset_policy import validate_active_images
    validate_active_images(images)
    annotations=dp.load_annotations(ann_path,images)
    selected=[row for row in images if row['split'] in ('train','val')]
    policy={'caps':[128,160,192,224], 'splits':['train','val'], 'test_pixels_read':False,
            'selection':'Maior redução de candidatos entre alternativas elegíveis; nenhum desempenho de rede usado.',
            'requirements':{'additional_uncovered_points':0,'maximum_one_to_one_losses_fraction':0.01,
                            'preserve_all_negative_source_images':True,'both_classes_train_and_val':True},
            'comparison_note':'Cobertura de positivos conhecidos é diagnóstico, não sensibilidade final.',
            'image_manifest_sha256':file_sha256(manifest),'annotation_sha256':file_sha256(ann_path),
            'baseline_config_sha256':file_sha256(base_path),'baseline_localization_sha256':localization_hash(base['localization'])}
    policy_path=out/'selection_policy.json'
    if policy_path.exists():
        assert json.loads(policy_path.read_text(encoding='utf-8'))==policy,'Política/entradas mudaram; use outro destino.'
    else:
        policy_path.write_text(json.dumps(policy,ensure_ascii=False,indent=2),encoding='utf-8')
    import cv2
    cv2.setNumThreads(1)
    cache=out/'cache'
    cache.mkdir(exist_ok=True)
    summaries={str(cap):{split:Counter() for split in ('train','val')} for cap in [0]+policy['caps']}
    negative_sources={str(cap):{split:set() for split in ('train','val')} for cap in [0]+policy['caps']}
    per_image=[]
    started=time.perf_counter()
    for index,row in enumerate(selected,1):
        file=cache/(row['image_id']+'.json.gz')
        if file.exists():
            with gzip.open(file,'rt',encoding='utf-8') as stream: saved=json.load(stream)
            assert saved['sha256']==row['sha256'] and saved['localization_sha256']==policy['baseline_localization_sha256']
            candidates=saved['candidates']
        else:
            import hashlib
            assert hashlib.sha256(dp.read_image_bytes(row['path'])).hexdigest()==row['sha256']
            candidates,diag=propose_regions(dp.read_image_rgb(row['path']),base['localization'])
            with gzip.open(file,'wt',encoding='utf-8') as stream:
                json.dump({'sha256':row['sha256'],'localization_sha256':policy['baseline_localization_sha256'],
                           'candidates':candidates},stream)
        result={'image_id':row['image_id'],'split':row['split'],'profiles':{}}
        baseline=measurements(candidates,annotations[row['image_id']])
        for cap in [0]+policy['caps']:
            metrics=baseline if not cap else measurements(merge_overlapping_regions(candidates,cap),annotations[row['image_id']])
            metrics['additional_uncovered_points']=len(set(baseline['covered_ids'])-set(metrics['covered_ids']))
            metrics['one_to_one_losses']=max(0,baseline['one_to_one_matches']-metrics['one_to_one_matches'])
            result['profiles'][str(cap)]=metrics
            summaries[str(cap)][row['split']].update({k:v for k,v in metrics.items() if isinstance(v,int)})
            if metrics['negative_crops']:
                negative_sources[str(cap)][row['split']].add(row['image_id'])
        per_image.append(result)
        if index % 20 == 0 or index==len(selected):
            print(f'Geometria: {index}/{len(selected)} imagens; {time.perf_counter()-started:.0f}s.',flush=True)
    eligible=[]
    for cap in policy['caps']:
        passed=all(summaries[str(cap)][split]['additional_uncovered_points']==0
                   and summaries[str(cap)][split]['one_to_one_losses'] <= 0.01*summaries['0'][split]['one_to_one_matches']
                   and summaries[str(cap)][split]['positive_crops']>0
                   and summaries[str(cap)][split]['negative_crops']>0
                   and negative_sources[str(cap)][split]==negative_sources['0'][split]
                   for split in ('train','val'))
        if passed: eligible.append(cap)
    winner=min(eligible,key=lambda cap:sum(summaries[str(cap)][s]['candidates'] for s in ('train','val'))) if eligible else None
    report={'policy':policy,'profiles':summaries,'negative_source_counts':{c:{s:len(ids) for s,ids in splits.items()} for c,splits in negative_sources.items()},
            'eligible_caps':eligible,'selected_merge_max_size':winner,'images':per_image,'seconds':time.perf_counter()-started}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='images'},ensure_ascii=False,indent=2),flush=True)
    return 0 if winner is not None else 2


if __name__=='__main__':
    raise SystemExit(main())
