"""Avalia A/B nos originais PBC aprovados destinados à comparação, sem treinar."""
import argparse
from datetime import datetime, timezone
import html
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src import data_protocol as dp
from src.detection_evaluation import load_prediction_run
from src.tcc_reporting import sha, read_json, save_json, write_csv, cohort_metrics, paired_ids
from scripts.compare_model_versions import run_models, MODELS


def prepare(batch,output):
    approval=read_json(batch/'human_approval_all_originals.json')
    if approval['status']!='complete' or approval['images_confirmed']!=200:
        raise ValueError('Exige aprovação humana explícita das 200 originais.')
    for key,name in [('inventory_sha256','inventory.csv'),('reviewed_sha256','reviewed.json'),('source_annotation_sha256','source_annotations.json')]:
        if approval[key]!=sha(batch/name):raise ValueError('Lote/revisão alterado: '+name)
    rows=dp.read_manifest(batch/'inventory.csv');refs=dp.load_annotations(batch/'reviewed.json',rows)
    if len(rows)!=200 or any(r['split']!='development' for r in rows):
        raise ValueError('Somente o lote externo de desenvolvimento.')
    if any(ref['whole_image_label']!=0 or ref['review_status']!='reviewed' or not ref['reference_complete'] for ref in refs.values()):
        raise ValueError('Todo campo exige referência negativa revisada.')
    partition_hashes={};setup=ROOT/'configs/comparison_a_vs_b.json'
    if setup.exists():
        from src.negative_partition import assert_disjoint_training_comparison
        config=read_json(setup)
        for key in ('barcelona_manifest','barcelona_annotations','barcelona_authorization'):
            path=ROOT/config[key]
            if sha(path)!=config[key+'_sha256']:raise ValueError('Reserva Barcelona alterada: '+key)
            partition_hashes[str(path)]=sha(path)
        rows=dp.read_manifest(ROOT/config['barcelona_manifest'])
        refs=dp.load_annotations(ROOT/config['barcelona_annotations'],rows)
        if len(rows)!=180:raise ValueError('Somente as 180 restantes podem entrar na comparação.')
        training=dp.read_manifest(ROOT/config['next_training_manifest'])
        assert_disjoint_training_comparison([r for r in training if r['split']=='train'],rows)
    output.mkdir(parents=True,exist_ok=False)
    rows=[dict(r,cohort='barcelona_negative') for r in rows]
    dp.validate_partitions(rows);dp.write_manifest(rows,output/'images.csv',list(rows[0]))
    save_json(output/'annotations.json',dict(schema_version=1,coordinate_convention='xyxy_half_open',images=list(refs.values())))
    checkpoints={}
    for system,(label,path) in MODELS.items():
        checkpoints[system]=dict(label=label,path=str(path),sha256=sha(path))
        if system=='B':
            meta=read_json(path.parent/'metadata.json')
            if meta['status']!='complete' or meta['synthetic'] is not False or meta['checkpoint_sha256']!=sha(path):
                raise ValueError('B deve ser o checkpoint real já concluído.')
    save_json(output/'protocol.json',dict(created_at=datetime.now(timezone.utc).isoformat(),
        checkpoint=checkpoints,cohorts={'barcelona_negative':len(rows)},partition_source_hashes=partition_hashes,
        source_hashes={f:sha(batch/f) for f in ['inventory.csv','reviewed.json','human_approval_all_originals.json']},
        source='https://data.mendeley.com/datasets/snkd93bnjr/1',
        evaluation='external_development_only',final_test_opened=False,training_changed=False,
        reference='Ausência de parasita visível declarada por Caio; não é laudo de ausência de Chagas.',
        unit='Imagem original de célula individual; não equivale a campo inteiro, paciente ou lâmina independente.',
        timing='Execução única, CPU com duas threads, B compilado, sem PNGs exportados. Não é benchmark repetido.',
        scope='Fonte separada da comparação principal; selecionar antes de inferir, preservar todos os IDs e falhas.'))


def summarize(output):
    rows=dp.read_manifest(output/'images.csv');refs=dp.load_annotations(output/'annotations.json',rows)
    protocol=read_json(output/'protocol.json');metrics={};details=[];predictions={}
    for system in ('A','B'):
        entries,origin=load_prediction_run(output/system/'predictions.json',system,'development',sha(output/'images.csv'))
        expected=protocol['checkpoint'][system]['sha256']
        if origin['artifact'].get('checkpoint_sha256',origin['artifact'].get('sha256'))!=expected or sha(Path(protocol['checkpoint'][system]['path']))!=expected:
            raise ValueError('Checkpoint divergente.')
        metrics[system],evaluated=cohort_metrics(rows,refs,entries);predictions[system]=entries
        for row in evaluated:
            details.append(dict(image_id=row['image_id'],system=system,status=row['status'],
                candidates=row['n_candidates'],positive_regions=row['n_positive_regions'],
                false_positive_regions=row['false_positive_regions'],algorithm_seconds=row['timings'].get('total_seconds'),error=row.get('error') or ''))
    paired_ids(predictions['A'],predictions['B'],{r['image_id'] for r in rows})
    save_json(output/'report.json',dict(protocol=protocol,summary=metrics,
        input_sha256={f:sha(output/f) for f in ['images.csv','annotations.json','A/predictions.json','B/predictions.json']},
        biological_independence_proven=False))
    write_csv(output/'summary.csv',[dict(system=s,**{k:v for k,v in metrics[s].items() if k!='status_counts'}) for s in ('A','B')])
    write_csv(output/'per_image.csv',details)
    by_type=[]
    for cell_type in sorted({r['cell_type'] for r in rows}):
        batch=[r for r in rows if r['cell_type']==cell_type]
        for system in ('A','B'):
            lookup={r['image_id']:r for r in predictions[system]}
            result,_=cohort_metrics(batch,refs,[lookup[r['image_id']] for r in batch])
            by_type.append(dict(cell_type=cell_type,system=system,n_images=len(batch),
                false_alarm_images=result['false_alarm_images'],positive_regions=result['positive_regions'],errors=result['errors']))
    write_csv(output/'by_cell_type.csv',by_type)
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    out=ROOT/'tcc/figuras'/output.name;out.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,key,title in [(axes[0],'false_alarm_images',f'Imagens com falso alarme (n={len(rows)})'),(axes[1],'false_positive_regions','Regiões positivas nos negativos')]:
        values=[metrics[s][key] for s in ('A','B')];bars=ax.bar(['A original','B atual'],values,color=['#28628e','#c64d50']);ax.bar_label(bars,padding=3)
        ax.set(title=title,ylim=(0,max(values+[1])*1.25));ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    fig.tight_layout()
    for extension in ('png','pdf'):fig.savefig(out/('01_alarmes.'+extension),dpi=180,bbox_inches='tight')
    plt.close(fig)
    import numpy as np
    cell_types=sorted({r['cell_type'] for r in rows});fig,ax=plt.subplots(figsize=(12,4));x=np.arange(len(cell_types))
    for offset,system,color in [(-.18,'A','#28628e'),(.18,'B','#c64d50')]:
        values=[next(r['false_alarm_images'] for r in by_type if r['cell_type']==c and r['system']==system) for c in cell_types]
        bars=ax.bar(x+offset,values,.36,label=system,color=color);ax.bar_label(bars,padding=3)
    labels={'basophil':'Basófilos','eosinophil':'Eosinófilos','erythroblast':'Eritroblastos','ig':'Granulócitos\nimaturos','lymphocyte':'Linfócitos','monocyte':'Monócitos','neutrophil':'Neutrófilos','platelet':'Plaquetas'}
    ax.set(xticks=x,xticklabels=[labels.get(c,c) for c in cell_types],title='Alarmes por tipo celular (denominadores no CSV)',ylabel='Imagens sinalizadas',ylim=(0,30));ax.legend();ax.yaxis.set_major_locator(MaxNLocator(integer=True));fig.tight_layout()
    for extension in ('png','pdf'):fig.savefig(out/('02_tipos_celulares.'+extension),dpi=180,bbox_inches='tight')
    plt.close(fig)
    cards='';cropped=[];assets=out/'recortes';assets.mkdir(exist_ok=True)
    predicted={s:{r['image_id']:r for r in predictions[s]} for s in ('A','B')}
    alarms=sorted({r['image_id'] for r in details if r['positive_regions']>0})
    from PIL import Image
    for identifier in alarms:
        original=next(r for r in rows if r['image_id']==identifier)
        image=Path(original['path']);relative=__import__('os').path.relpath(image,out).replace('\\','/')
        pixels=dp.read_image_rgb(image);models=''
        for system in ('A','B'):
            result=predicted[system][identifier];positive=[(i,r) for i,r in enumerate(result['regions'],1) if r['class_id']==1]
            parts=f'<h4>{system}: {len(positive)} regiões positivas — {result["status"]}</h4>'
            for number,region in positive:
                x1,y1,x2,y2=map(int,region['bbox']);filename=f'recortes/{identifier}_{system}_{number}.png'
                Image.fromarray(pixels[y1:y2,x1:x2]).save(out/filename)
                cropped.append(dict(image_id=identifier,system=system,candidate_id=number,bbox=str(region['bbox']),score_suspect=region['scores'][1],file=filename))
                parts+=f'<figure><img src="{filename}"><figcaption>Caixa {region["bbox"]}; escore {region["scores"][1]:.4f}</figcaption></figure>'
            models+='<section>'+parts+'</section>'
        cards+=f'<article><h3>{html.escape(identifier)}</h3><img src="{relative}"><p>Original revisado como sem parasita visível. {html.escape(original["cell_type"])}</p><div class="models">'+models+'</div></article>'
    if cropped:write_csv(out/'recortes.csv',cropped)
    table=''.join(f'<tr><td>{s}</td><td>{metrics[s]["false_alarm_images"]}/{len(rows)}</td><td>{metrics[s]["positive_regions"]}</td><td>{metrics[s]["errors"]}</td><td>{metrics[s]["algorithm_seconds"]:.2f}</td></tr>' for s in ('A','B'))
    text=f'# A × B — negativos externos PBC/Barcelona\n\n{len(rows)} imagens originais aprovadas por Caio, sem parasita visível. Células individuais enquadradas, fonte humana/CellaVision distinta das positivas murinas. Avaliação de desenvolvimento, sem independência biológica demonstrada; nenhum treinamento nesta execução e teste final reservado.\n\n'
    text+='| Modelo | Imagens com alarme | Regiões positivas | Erros | Tempo (s) |\n| --- | ---: | ---: | ---: | ---: |\n'+''.join(f'| {s} | {metrics[s]["false_alarm_images"]}/{len(rows)} | {metrics[s]["positive_regions"]} | {metrics[s]["errors"]} | {metrics[s]["algorithm_seconds"]:.2f} |\n' for s in ('A','B'))
    text+='\n'+protocol['timing']+'\n\nFonte separada da comparação principal. Os resultados mostram a necessidade de medir alarmes e cobertura positiva conjuntamente; não estabelecem desempenho clínico nem superioridade de arquitetura isolada. A galeria mostra todos os originais com alarme em A ou B e todos os seus recortes positivos, sem marcações.\n'
    (out/'LEIA-ME.md').write_text(text,encoding='utf-8')
    page='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>PBC Barcelona — A × B</title><style>body{font:16px system-ui;margin:24px;color:#203548}img{max-width:100%}td,th{padding:10px;border:1px solid #ccc}table{border-collapse:collapse}.grid{display:flex;flex-wrap:wrap;gap:15px}article{width:370px}p{overflow-wrap:anywhere}</style><h1>200 negativos originais PBC/Barcelona — A × B</h1><p>Ausência de parasita visível declarada por Caio. São imagens de células individuais, não campos inteiros equivalentes à base positiva. Desenvolvimento, sem laudo clínico ou independência biológica comprovada. Fonte separada; nenhum treino ou teste final foi alterado.</p><table><tr><th>Modelo</th><th>Imagens com alarme</th><th>Regiões positivas</th><th>Erros</th><th>Tempo (s)</th></tr>'+table+'</table><p>'+html.escape(protocol['timing'])+'</p><a href="01_alarmes.pdf">PDF</a><br><img src="01_alarmes.png"><h2>Exemplos para conferir</h2><div class="grid">'+cards+'</div></html>'
    page=page.replace('<h2>Exemplos para conferir</h2>','<h2>Por tipo celular</h2><p>Seleção balanceada por tipos, não distribuição populacional ou pacientes independentes.</p><a href="02_tipos_celulares.pdf">PDF</a><br><img src="02_tipos_celulares.png"><h2>Exemplos para conferir</h2>')
    page=page.replace('<h1>200 negativos originais',f'<h1>{len(rows)} negativos originais')
    page=page.replace('<h2>Exemplos para conferir</h2>',f'<h2>Todos os falsos alarmes para conferir</h2><p>{len(alarms)} originais com alarme em A ou B; {len(cropped)} recortes positivos, sem marcações. Lista completa deste lote, ordenada por ID. Escores não são probabilidades calibradas.</p>')
    page=page.replace('</style>','.models{display:flex;flex-wrap:wrap;gap:12px}.models section{width:280px}.models figure{margin:6px 0}article{width:100%;border-top:1px solid #ccc;padding-top:15px}.models img{max-width:224px}</style>')
    setup=ROOT/'configs/comparison_a_vs_b.json'
    if setup.exists() and len(rows)==200:
        active=read_json(setup)['output_dir'].split('/')[-1]
        note='Histórico anterior à reserva 20/180: 20 destas imagens foram destinadas aos negativos do próximo treino. A comparação atual usa somente as 180 restantes e as 73 negativas Kaggle. O B ainda não foi retreinado.'
        page=page.replace('<table>','<p><strong>'+note+'</strong> <a href="../'+active+'/index.html">Abrir comparação atual</a></p><table>',1)
        (out/'LEIA-ME.md').write_text(text+'\n'+note+'\n',encoding='utf-8')
    (out/'index.html').write_text(page,encoding='utf-8');print(text,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch',type=Path,default=ROOT/'data/annotations/barcelona_originals_review')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'experiments/comparison/barcelona_a_vs_b')
    modes=parser.add_mutually_exclusive_group();modes.add_argument('--prepare-only',action='store_true');modes.add_argument('--summarize-only',action='store_true');modes.add_argument('--run-prepared',action='store_true')
    args=parser.parse_args();output=args.output_dir.resolve()
    if not args.summarize_only:
        if not args.run_prepared:prepare(args.batch.resolve(),output)
        else:
            protocol=read_json(output/'protocol.json')
            for name,expected in protocol['source_hashes'].items():
                if sha(args.batch.resolve()/name)!=expected:raise ValueError('Revisão ou lote mudou desde o preparo.')
            for name,expected in protocol.get('partition_source_hashes',{}).items():
                if sha(Path(name))!=expected:raise ValueError('Reserva Barcelona mudou desde o preparo.')
        if args.prepare_only:return
        run_models(output)
    summarize(output)


if __name__=='__main__':main()
