"""Comparação pareada A × B em imagens inteiras, sem descartar falhas."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.data_protocol import read_manifest,load_annotations
from src.detection_evaluation import compare_systems,load_prediction_run


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','annotations','predictions-a','predictions-b','output'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--split',default='test')
    p.add_argument('--iou-threshold',type=float,default=.5)
    p.add_argument('--synthetic-fixture',action='store_true',help='Somente dados/anotações/previsões explicitamente sintéticos; não é experimento final')
    p.add_argument('--image-decision-field',choices=['any_positive_region','image_decision','original_decision'],default='any_positive_region')
    args=p.parse_args()
    rows=read_manifest(args.manifest)
    if args.synthetic_fixture:
        reference_payload=json.loads(Path(args.annotations).read_text(encoding='utf-8-sig'))
        if reference_payload.get('synthetic') is not True or not all(str(row.get('source','')).startswith(('sintetica','synthetic')) for row in rows):
            raise ValueError('Modo fixture proibido para dados ou anotações de origem real/desconhecida')
    manifest_hash=hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest()
    predictions_a, provenance_a=load_prediction_run(args.predictions_a,'A',args.split,manifest_hash,synthetic_fixture=args.synthetic_fixture)
    predictions_b, provenance_b=load_prediction_run(args.predictions_b,'B',args.split,manifest_hash,synthetic_fixture=args.synthetic_fixture)
    report=compare_systems(rows,load_annotations(args.annotations,rows),
        predictions_a,predictions_b,
        split=args.split,iou_threshold=args.iou_threshold,image_decision_rule=args.image_decision_field)
    report['provenance']={'A':provenance_a,'B':provenance_b}
    report['synthetic']=args.synthetic_fixture or provenance_a['synthetic'] or provenance_b['synthetic']
    report['input_sha256']={name:hashlib.sha256(Path(getattr(args,name)).read_bytes()).hexdigest()
                           for name in ('manifest','annotations','predictions_a','predictions_b')}
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(f'Comparação de {len(report["image_ids"])} imagens em {output}')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
