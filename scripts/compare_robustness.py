"""Teste adicional A/B em três variações dos mesmos originais de validação."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp
from src.robustness_dataset import TRANSFORMS, DESCRIPTIONS, transform_annotation, variant_bytes
from src.tcc_reporting import sha, read_json, save_json, write_csv, cohort_metrics, paired_ids
from src.detection_evaluation import load_prediction_run
from scripts.compare_model_versions import run_models, MODELS


def prepare(base, output):
    if output.exists(): raise FileExistsError('Use uma pasta nova para preservar o experimento.')
    rows=dp.read_manifest(base/'images.csv'); refs=dp.load_annotations(base/'annotations.json',rows)
    protocol=read_json(base/'protocol.json')
    if Counter(r['cohort'] for r in rows)!=Counter(positive_val=114,kaggle_negative_val=73):
        raise ValueError('Base diferente do lote revisado de 187 imagens.')
    if any(r['split']!='development' or r['source_split']!='val' for r in rows):
        raise ValueError('Somente originais de validação; treino e teste são proibidos.')
    for system, (_, checkpoint) in MODELS.items():
        if sha(checkpoint)!=protocol['checkpoint'][system]['sha256']:
            raise ValueError('Checkpoint mudou desde a comparação original.')
        entries,_=load_prediction_run(base/system/'predictions.json',system,'development',sha(base/'images.csv'))
        paired_ids(entries,entries,{r['image_id'] for r in rows})
    variants=[]; annotations=[]
    for index,row in enumerate(rows,1):
        raw=dp.read_image_bytes(row['path'])
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('Original alterado: '+row['image_id'])
        for transform in TRANSFORMS:
            image_id=row['image_id']+'__'+transform
            reference=transform_annotation(refs[row['image_id']],image_id,transform)
            pixels=variant_bytes(raw,transform)
            variants.append(dict(row,image_id=image_id,original_image_id=row['image_id'],
                original_sha256=row['sha256'],transform=transform,
                path='variant://'+transform+'!'+row['path'],
                sha256=hashlib.sha256(pixels).hexdigest(),
                width=reference['width'],height=reference['height']))
            annotations.append(reference)
        if index%25==0: print(f'PREPARED {index}/{len(rows)} originais',flush=True)
    dp.validate_partitions(variants)
    payload=dict(schema_version=1,coordinate_convention='xyxy_half_open',images=annotations)
    dp.validate_annotations(payload,variants)
    output.mkdir(parents=True)
    dp.write_manifest(variants,output/'images.csv',list(variants[0]))
    save_json(output/'annotations.json',payload)
    save_json(output/'protocol.json',dict(created_at=datetime.now(timezone.utc).isoformat(),
        evaluation='development_robustness_only',base_comparison=str(base),
        base_sha256={f:sha(base/f) for f in ['images.csv','annotations.json','protocol.json','A/predictions.json','B/predictions.json']},
        checkpoint=protocol['checkpoint'],original_images=len(rows),derived_images=len(variants),
        views_including_original=len(rows)+len(variants),transforms=list(TRANSFORMS),
        group_rule='Todas as versões conservam group_id e original_image_id; não são campos ou pacientes independentes.',
        reference_rule='Coordenadas transformadas deterministicamente; rótulos herdados dos originais, sem nova revisão humana.',
        pixel_rule='PNG RGB virtual, sem nova compressão JPEG, sem recorte; geometria exata e brilho multiplicado por 0,85.',
        final_test_opened=False,training_changed=False,threads=2,
        timing='Execução única, B compilado, sem exportação PNG; tempos originais herdados do lote anterior. Não é benchmark controlado.',
        interpretation='Não combinar versões com o denominador da comparação principal; relatar cada condição sobre 187 originais e comparar decisões por original.'))
    print(f'READY: {len(rows)} originais, {len(variants)} versões, sem PNGs duplicados em disco.',flush=True)


def summarize(output):
    protocol=read_json(output/'protocol.json'); base=Path(protocol['base_comparison'])
    for name,expected in protocol['base_sha256'].items():
        if sha(base/name)!=expected: raise ValueError('Comparação original mudou: '+name)
    base_rows=dp.read_manifest(base/'images.csv'); rows=dp.read_manifest(output/'images.csv')
    references={'original':dp.load_annotations(base/'annotations.json',base_rows)}
    variant_refs=dp.load_annotations(output/'annotations.json',rows)
    systems={}; baseline={}; origins={}
    for system in ('A','B'):
        baseline[system],_=load_prediction_run(base/system/'predictions.json',system,'development',sha(base/'images.csv'))
        systems[system],origins[system]=load_prediction_run(output/system/'predictions.json',system,'development',sha(output/'images.csv'))
        if origins[system]['artifact'].get('checkpoint_sha256',origins[system]['artifact'].get('sha256'))!=protocol['checkpoint'][system]['sha256']:
            raise ValueError('Checkpoint divergente.')
        if sha(Path(protocol['checkpoint'][system]['path']))!=protocol['checkpoint'][system]['sha256']:
            raise ValueError('Checkpoint local alterado.')
    paired_ids(systems['A'],systems['B'],{r['image_id'] for r in rows})
    table=[]; per_image=[]
    for transform in ('original',)+TRANSFORMS:
        selected=base_rows if transform=='original' else [r for r in rows if r['transform']==transform]
        annotations=references['original'] if transform=='original' else variant_refs
        if len(selected)!=protocol['original_images'] or len({r.get('original_image_id',r['image_id']) for r in selected})!=protocol['original_images']:
            raise ValueError('Condição não contém exatamente uma versão por original.')
        for system in ('A','B'):
            predictions=baseline[system] if transform=='original' else systems[system]
            lookup={p['image_id']:p for p in predictions}; old={p['image_id']:p for p in baseline[system]}
            for cohort in ('positive_val','kaggle_negative_val'):
                batch=[r for r in selected if r['cohort']==cohort]
                metrics,details=cohort_metrics(batch,annotations,[lookup[r['image_id']] for r in batch])
                details_by_id={r['image_id']:r for r in details}
                changes=0; failed_pairs=0
                for row in batch:
                    detail=details_by_id[row['image_id']]
                    original_id=row.get('original_image_id',row['image_id']); prediction=lookup[row['image_id']]; original=old[original_id]
                    valid=prediction['status']!='erro' and original['status']!='erro'
                    changed=(prediction['status']=='predicao_positiva')!=(original['status']=='predicao_positiva') if valid else None
                    changes+=bool(changed); failed_pairs+=not valid
                    per_image.append(dict(condition=transform,cohort=cohort,system=system,
                        original_image_id=original_id,image_id=row['image_id'],status=prediction['status'],
                        original_status=original['status'],decision_changed=changed,
                        matched_points=detail['matched_positive_regions'],reference_points=detail['reference_points'],
                        positive_regions=detail['n_positive_regions'],error=prediction.get('error','')))
                table.append(dict(condition=transform,cohort=cohort,system=system,
                    **{k:v for k,v in metrics.items() if k!='status_counts'},
                    decisions_changed_from_original=changes,invalid_pairs=failed_pairs))
    write_csv(output/'summary.csv',table); write_csv(output/'per_image.csv',per_image)
    by_original=[];stability=[]
    for system in ('A','B'):
        for original in base_rows:
            cases=[r for r in per_image if r['system']==system and r['original_image_id']==original['image_id']]
            if len(cases)!=4:raise ValueError('Cada original exige as quatro condições.')
            valid=all(r['status']!='erro' for r in cases)
            signals=[r['status']=='predicao_positiva' for r in cases]
            by_original.append(dict(original_image_id=original['image_id'],cohort=original['cohort'],system=system,
                conditions=4,errors=sum(r['status']=='erro' for r in cases),
                stable_decision=len(set(signals))==1 if valid else None,
                signaled_all_conditions=all(signals) if valid else None,
                signaled_any_condition=any(signals),
                reference_points=cases[0]['reference_points'],
                minimum_matched_points=min(r['matched_points'] for r in cases),
                maximum_matched_points=max(r['matched_points'] for r in cases)))
        for cohort in ('positive_val','kaggle_negative_val'):
            cases=[r for r in by_original if r['system']==system and r['cohort']==cohort]
            stability.append(dict(system=system,cohort=cohort,n_originals=len(cases),
                stable_decision_originals=sum(r['stable_decision'] is True for r in cases),
                originals_with_error=sum(r['errors']>0 for r in cases),
                signaled_all_conditions=sum(r['signaled_all_conditions'] is True for r in cases),
                signaled_any_condition=sum(r['signaled_any_condition'] for r in cases)))
    write_csv(output/'by_original.csv',by_original);write_csv(output/'stability.csv',stability)
    import PIL
    import numpy as np
    save_json(output/'report.json',dict(protocol=protocol,summary=table,provenance=origins,
        input_sha256={f:sha(output/f) for f in ['images.csv','annotations.json','A/predictions.json','B/predictions.json']},
        unique_originals=187,biological_independence_proven=False,stability_by_original=stability,
        report_implementation_sha256=sha(Path(__file__)),
        transform_implementation_sha256=sha(ROOT/'src/robustness_dataset.py'),
        image_runtime_versions={'numpy':np.__version__,'Pillow':PIL.__version__}))
    import matplotlib.pyplot as plt
    import numpy as np
    out=ROOT/'tcc/figuras'/output.name;out.mkdir(parents=True,exist_ok=True)
    figures=[];conditions=('original',)+TRANSFORMS
    for name,cohort,key,title,ylabel in [
        ('01_cobertura','positive_val','matched_positive_regions','Cobertura dos 450 pontos por condição','Pontos associados'),
        ('02_alarmes','kaggle_negative_val','false_alarm_images','Falsos alarmes em 73 originais negativos por condição','Imagens sinalizadas'),
        ('03_estabilidade','positive_val','decisions_changed_from_original','Mudanças de decisão em 114 originais positivos','Decisões diferentes do original')]:
        fig,ax=plt.subplots(figsize=(10,4)); x=np.arange(len(conditions))
        for offset,system,color in [(-.18,'A','#28628e'),(.18,'B','#c64d50')]:
            values=[next(r[key] for r in table if r['system']==system and r['cohort']==cohort and r['condition']==c) for c in conditions]
            bars=ax.bar(x+offset,values,.36,label=system,color=color);ax.bar_label(bars,padding=3)
        if key=='matched_positive_regions':ax.axhline(450,color='#777',linestyle='--',label='450 pontos parciais')
        ax.set(xticks=x,xticklabels=[DESCRIPTIONS[c] for c in conditions],title=title,ylabel=ylabel)
        ax.set_ylim(0,max(1,ax.get_ylim()[1])*1.15);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.16),ncol=3,frameon=False);fig.tight_layout()
        for extension in ('png','pdf'):fig.savefig(out/(name+'.'+extension),dpi=180,bbox_inches='tight')
        plt.close(fig);figures.append(name)
    header='<tr><th>Condição</th><th>Grupo</th><th>Modelo</th><th>Originais</th><th>Sinalizadas</th><th>Pontos associados</th><th>Mudanças de decisão</th><th>Erros</th></tr>'
    body=''.join('<tr>'+''.join(f'<td>{html.escape(str(v))}</td>' for v in [DESCRIPTIONS[r['condition']],r['cohort'],r['system'],r['n_images'],r['signaled_images'],r['matched_positive_regions'],r['decisions_changed_from_original'],r['errors']])+'</tr>' for r in table)
    # Exemplos negativos: mostrar pixels sem marcações dos maiores alarmes,
    # com caixas/escores no texto, mantendo a seleção explícita.
    from PIL import Image
    assets=out/'exemplos';assets.mkdir(exist_ok=True)
    lookup={r['image_id']:r for r in rows};base_lookup={r['image_id']:r for r in base_rows}
    prediction_lookup={s:{r['image_id']:r for r in systems[s]} for s in ('A','B')}
    alarms=sorted((r for r in per_image if r['cohort']=='kaggle_negative_val' and r['condition']!='original' and r['positive_regions']>0),key=lambda r:(-r['positive_regions'],r['system'],r['condition'],r['image_id']))[:12]
    cards=[]
    for index,case in enumerate(alarms,1):
        original=dp.read_image_rgb(base_lookup[case['original_image_id']]['path'])
        variant=dp.read_image_rgb(lookup[case['image_id']]['path'])
        original_file=f'exemplos/{index:02d}_original.png';variant_file=f'exemplos/{index:02d}_variacao.png'
        Image.fromarray(original).save(out/original_file);Image.fromarray(variant).save(out/variant_file)
        crops=[]
        regions=sorted((r for r in prediction_lookup[case['system']][case['image_id']]['regions'] if r['class_id']==1),key=lambda r:-r['scores'][1])[:2]
        for number,region in enumerate(regions,1):
            x1,y1,x2,y2=map(int,region['bbox']);filename=f'exemplos/{index:02d}_recorte_{number}.png'
            Image.fromarray(variant[y1:y2,x1:x2]).save(out/filename)
            crops.append(f'<figure><img src="{filename}"><figcaption>Caixa {region["bbox"]}; escore {region["scores"][1]:.4f}</figcaption></figure>')
        cards.append(f'<article><h3>{case["system"]} — {DESCRIPTIONS[case["condition"]]}</h3><p>{case["original_image_id"]}; {case["positive_regions"]} regiões positivas.</p><div class="examples"><figure><img src="{original_file}"><figcaption>Original</figcaption></figure><figure><img src="{variant_file}"><figcaption>Variação</figcaption></figure>'+''.join(crops)+'</div></article>')
    page='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Robustez A × B</title><style>body{font:16px system-ui;margin:30px;color:#203548}td,th{padding:8px;border:1px solid #ccc}table{border-collapse:collapse}img{max-width:100%}</style><h1>Teste adicional de robustez A × B</h1><p>187 imagens originais (114 positivas e 73 negativas), 561 versões e 748 vistas contando os originais. As versões não são novos campos independentes. Treino e teste final não foram alterados.</p><p>Mesmas transformações para os dois modelos e as duas classes. Referência positiva parcial; rótulos herdados e pontos transformados. Desenvolvimento, sem conclusão clínica.</p><table>'+header+body+'</table>'+''.join(f'<h2>{name}</h2><a href="{name}.pdf">PDF</a><br><img src="{name}.png">' for name in figures)+'</html>'
    page=page.replace('</html>','<h2>Falsos alarmes das variações para conferir</h2><p>Até 12 casos com mais regiões positivas nos negativos já revisados, sem seleção aleatória. Pixels sem marcações; escore não calibrado. Referência herdada do original.</p>'+''.join(cards)+'</html>')
    stability_rows=''.join('<tr>'+''.join(f'<td>{v}</td>' for v in [r['system'],r['cohort'],r['n_originals'],r['stable_decision_originals'],r['signaled_all_conditions'],r['signaled_any_condition'],r['originals_with_error']])+'</tr>' for r in stability)
    stability_table='<h2>Estabilidade por original</h2><p>Uma unidade por imagem original. Decisão estável exige ausência de erro e a mesma sinalização nas quatro condições. Nos negativos, qualquer condição sinalizada identifica um falso alarme naquele original. Erros não são negativos corretos.</p><table><tr><th>Modelo</th><th>Grupo</th><th>Originais</th><th>Decisão estável</th><th>Sinalizados em todas</th><th>Sinalizados em alguma</th><th>Com erro</th></tr>'+stability_rows+'</table>'
    page=page.replace('<h2>Falsos alarmes das variações para conferir</h2>',stability_table+'<h2>Falsos alarmes das variações para conferir</h2>')
    page=page.replace('</style>','.examples{display:flex;flex-wrap:wrap;gap:10px}.examples figure{width:280px;margin:5px}.examples img{width:100%}article{border-top:1px solid #ccc;margin-top:20px}p{overflow-wrap:anywhere}</style>')
    (out/'index.html').write_text(page,encoding='utf-8')
    print('REPORT '+str(out/'index.html'),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=ROOT/'experiments/comparison/a_vs_b')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'experiments/comparison/robustez_a_vs_b')
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--prepare-only',action='store_true')
    modes.add_argument('--summarize-only',action='store_true')
    args=parser.parse_args();output=args.output_dir.resolve()
    if not args.summarize_only:
        prepare(args.base.resolve(),output)
        if args.prepare_only:return
        run_models(output)
    summarize(output)


if __name__=='__main__':main()
