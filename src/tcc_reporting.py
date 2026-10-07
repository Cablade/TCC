"""Relatório da comparação A original × B atual, sem executar modelos."""
import csv
import hashlib
import html
import json
from pathlib import Path
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from .detection_evaluation import load_prediction_run, match_one_to_one, evaluate_system
from .data_protocol import read_manifest, load_annotations, read_image_rgb
COLORS=['#28628e','#c64d50']
NAMES=['A original','B atual']


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_json(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save_json(path,value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def write_csv(path,rows):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
def paired_ids(a,b,expected):
    for rows in (a,b):
        ids=[r['image_id'] for r in rows]
        if len(ids)!=len(set(ids)) or set(ids)!=set(expected): raise ValueError('IDs ausentes, extras ou repetidos.')
    return sorted(expected)
def coverage_rows(predictions,annotations):
    result=[]
    for system,items in predictions.items():
        for image_id,item in sorted(items.items()):
            refs=annotations[image_id]['positives']; valid=item.get('status')!='erro'
            boxes=[r['bbox'] for r in item['regions'] if r['class_id']==1] if valid else []
            proposals=item['candidates'] if valid else []
            result.append(dict(system=system,image_id=image_id,reference_points=len(refs),matched_proposals=len(match_one_to_one(proposals,refs)['pairs']),matched_positive_regions=len(match_one_to_one(boxes,refs)['pairs'])))
    return result


def cohort_metrics(rows,annotations,predictions):
    evaluated=evaluate_system(rows,annotations,predictions)
    details=evaluated['per_image']; by_id={r['image_id']:r for r in predictions}
    for row in details:
        ref=annotations[row['image_id']]; item=by_id[row['image_id']]; valid=row['status']!='erro'
        boxes=[r['bbox'] for r in item['regions'] if r['class_id']==1] if valid else []
        refs=ref.get('positives',[])
        row.update(reference_points=len(refs),matched_proposals=len(match_one_to_one(item['candidates'] if valid else [],refs)['pairs']),matched_positive_regions=len(match_one_to_one(boxes,refs)['pairs']))
        row['false_positive_regions']=(len(boxes) if valid else None) if ref.get('whole_image_label')==0 else None
    times=[r['timings']['total_seconds'] for r in details if isinstance(r['timings'].get('total_seconds'),(int,float))]
    negative=all(annotations[r['image_id']].get('whole_image_label')==0 for r in rows)
    metrics=dict(n_images=len(rows),status_counts=evaluated['status_counts'],signaled_images=sum(r['status']=='predicao_positiva' for r in details),errors=sum(r['status']=='erro' for r in details),candidates=sum(r['n_candidates'] for r in details),positive_regions=sum(r['n_positive_regions'] for r in details),false_alarm_images=sum(r['status']=='predicao_positiva' for r in details) if negative else None,rejected_negative_images=sum(r['status'] in {'sem_regioes','regioes_sem_predicao_positiva'} for r in details) if negative else None,false_positive_regions=sum(r['false_positive_regions'] or 0 for r in details) if negative else None,reference_points=sum(r['reference_points'] for r in details),matched_proposals=sum(r['matched_proposals'] for r in details),matched_positive_regions=sum(r['matched_positive_regions'] for r in details),algorithm_seconds=sum(times),median_seconds=float(np.median(times)) if times else None,timing_count=len(times))
    return metrics,details


def class_groups(rows, annotations):
    """Agrupa pelas referências; a origem continua no manifesto de cada imagem."""
    groups = {'positive': [], 'negative': []}
    for row in rows:
        label = annotations[row['image_id']].get('whole_image_label')
        if label not in (0, 1):
            raise ValueError('Agrupamento por classe exige rótulo de imagem explícito.')
        groups['positive' if label == 1 else 'negative'].append(row)
    if not all(groups.values()):
        raise ValueError('A comparação exige imagens positivas e negativas.')
    return groups


def build_report(root,comparison):
    manifest=comparison/'images.csv'; reference=comparison/'annotations.json'
    images=read_manifest(manifest); annotations=load_annotations(reference,images); protocol=read_json(comparison/'protocol.json')
    if set(protocol['checkpoint'])!={'A','B'}: raise ValueError('Somente A e B atual são permitidos.')
    predictions={}; provenance={}; inputs=[manifest,reference,comparison/'protocol.json']
    for system in ('A','B'):
        path=comparison/system/'predictions.json'; entries,origin=load_prediction_run(path,system,'development',sha(manifest))
        expected=protocol['checkpoint'][system]['sha256']
        if origin['artifact'].get('checkpoint_sha256',origin['artifact'].get('sha256'))!=expected or sha(Path(protocol['checkpoint'][system]['path']))!=expected: raise ValueError('Checkpoint divergente.')
        predictions[system]={r['image_id']:r for r in entries}
        if len(entries)!=len(predictions[system]): raise ValueError('IDs repetidos.')
        provenance[system]=origin; inputs.append(path)
    paired_ids(list(predictions['A'].values()),list(predictions['B'].values()),{r['image_id'] for r in images})
    cohorts=list(protocol['cohorts']); labels={'positive_val':'Validação positiva','kaggle_negative_val':'Negativos Kaggle (validação)','barcelona_negative':'Negativos Barcelona (comparação)'}
    if not {'positive_val','kaggle_negative_val'}<=set(cohorts) or set(cohorts)-set(labels):
        raise ValueError('A comparação exige positivas, originais Kaggle e somente fontes adicionais autorizadas.')
    negative_cohorts=[c for c in cohorts if c!='positive_val']
    summary={}; per_image=[]
    for cohort in cohorts:
        rows=[r for r in images if r['cohort']==cohort]
        if len(rows)!=protocol['cohorts'][cohort]: raise ValueError('Denominador do grupo divergente.')
        summary[cohort]={}
        for system in ('A','B'):
            metrics,details=cohort_metrics(rows,annotations,[predictions[system][r['image_id']] for r in rows]); summary[cohort][system]=metrics
            for r in details:
                per_image.append(dict(image_id=r['image_id'],cohort=cohort,system=system,status=r['status'],original_decision=r['original_decision'],candidates=r['n_candidates'],classified_regions=r['n_regions'],positive_regions=r['n_positive_regions'],false_positive_regions=r['false_positive_regions'],reference_points=r['reference_points'],matched_proposals=r['matched_proposals'],matched_positive_regions=r['matched_positive_regions'],algorithm_seconds=r['timings'].get('total_seconds'),error=r.get('error') or ''))
    groups=class_groups(images,annotations)
    class_summary={}; class_table=[]
    for group,rows in groups.items():
        class_summary[group]={}
        for system in ('A','B'):
            metrics,_=cohort_metrics(rows,annotations,[predictions[system][r['image_id']] for r in rows])
            class_summary[group][system]=metrics
            class_table.append(dict(image_class=group,system=system,**{k:v for k,v in metrics.items() if k!='status_counts'}))
    for row in per_image:
        row['image_class']='positive' if annotations[row['image_id']]['whole_image_label']==1 else 'negative'
    report=dict(summary=summary,class_summary=class_summary,presentation_grouping='whole_image_label',protocol=protocol,provenance=provenance,input_sha256={str(p.relative_to(root)):sha(p) for p in inputs},paired_images=len(images),final_test_opened=False)
    save_json(comparison/'report.json',report); write_csv(comparison/'summary.csv',class_table); write_csv(comparison/'per_image.csv',per_image)
    from .prediction_exports import write_review_csvs
    for system in ('A','B'): write_review_csvs(list(predictions[system].values()),comparison/system)
    summary=class_summary
    cohorts=list(groups)
    negative_cohorts=['negative']
    labels={'positive':'Imagens positivas','negative':'Imagens negativas'}
    out=root/'tcc/figuras'/comparison.name; out.mkdir(parents=True,exist_ok=True); figures=[]
    def save(fig,name,caption):
        for ax in fig.axes:
            if ax.axison: ax.spines[['top','right']].set_visible(False)
        fig.tight_layout(); fig.savefig(out/(name+'.png'),dpi=200,bbox_inches='tight'); fig.savefig(out/(name+'.pdf'),bbox_inches='tight'); plt.close(fig); figures.append(dict(name=name,caption=caption))
    def bars(ax,values,title,ylabel):
        b=ax.bar(NAMES,values,color=COLORS); ax.bar_label(b,fmt='%g',padding=3); ax.set(title=title,ylabel=ylabel,ylim=(0,max(values+[1])*1.25))
    fig,axes=plt.subplots(1,len(cohorts),figsize=(5*len(cohorts),4)); axes=np.atleast_1d(axes)
    for ax,c in zip(axes,cohorts): bars(ax,[summary[c][s]['signaled_images'] for s in ('A','B')],labels[c]+f" (n={len(groups[c])})",'Imagens sinalizadas')
    save(fig,'01_sinalizacoes','Mesmos IDs por grupo. Sinalização não comprova localização correta; nos negativos revisados, é falso alarme de desenvolvimento.')
    fig,ax=plt.subplots(figsize=(8,4)); x=np.arange(2); width=.35
    for offset,key,label,color in [(-width/2,'matched_proposals','Propostas','#91adc3'),(width/2,'matched_positive_regions','Regiões positivas','#c64d50')]:
        b=ax.bar(x+offset,[summary['positive'][s][key] for s in ('A','B')],width,label=label,color=color); ax.bar_label(b,padding=3)
    total=summary['positive']['A']['reference_points']; ax.axhline(total,color='#555',linestyle='--',label=f'{total} pontos publicados'); ax.set(xticks=x,xticklabels=NAMES,ylabel='Pontos associados uma única vez',ylim=(0,total*1.2),title='Cobertura da referência positiva parcial'); ax.legend(fontsize=8,loc='upper left')
    save(fig,'02_cobertura','Associação de cardinalidade máxima um a um: ponto dentro da caixa semiaberta. Referência parcial; não é sensibilidade geral nem precisão de detecção.')
    fig,axes=plt.subplots(1,len(negative_cohorts),figsize=(5*len(negative_cohorts),4)); axes=np.atleast_1d(axes)
    for ax,c in zip(axes,negative_cohorts): bars(ax,[summary[c][s]['false_positive_regions'] for s in ('A','B')],labels[c],'Regiões positivas em imagens negativas')
    save(fig,'03_falsas_regioes','Regiões positivas nas imagens negativas confirmadas visualmente por Caio. Regiões não são pacientes independentes; referência positiva parcial não permite contar falsos positivos nas imagens positivas.')
    fig,axes=plt.subplots(1,len(cohorts),figsize=(5*len(cohorts),4)); axes=np.atleast_1d(axes)
    for ax,c in zip(axes,cohorts): bars(ax,[round(summary[c][s]['algorithm_seconds'],2) for s in ('A','B')],labels[c],'Tempo do algoritmo (s)')
    save(fig,'04_tempo','Tempo exclui leitura/exportação e inclui primeira imagem. Execução única em CPU, duas threads, B compilado; Tempos herdados da execução original quando houver derivação de subconjunto; consulte o protocolo. Não é benchmark repetido com aquecimento controlado.')
    fig,axes=plt.subplots(1,len(cohorts),figsize=(5*len(cohorts),4)); axes=np.atleast_1d(axes)
    for ax,c in zip(axes,cohorts):
        series=[[r['algorithm_seconds'] for r in per_image if r['image_class']==c and r['system']==s and r['algorithm_seconds'] is not None] for s in ('A','B')]; ax.boxplot(series,labels=NAMES); ax.set(title=labels[c],ylabel='Segundos por imagem')
    save(fig,'05_distribuicao_tempo','Dispersão por imagem; caixas não são intervalos de confiança e imagens não são unidades biológicas independentes.')
    b_run=Path(protocol['checkpoint']['B']['path']).parent
    history=read_json(b_run/'history.json'); meta=read_json(b_run/'metadata.json'); fig,axes=plt.subplots(1,2,figsize=(10,4)); epochs=np.arange(1,len(history['loss'])+1)
    for ax,key,title in [(axes[0],'loss','Perda'),(axes[1],'accuracy','Acurácia dos recortes')]:
        ax.plot(epochs,history[key],label='Treino'); ax.plot(epochs,history['val_'+key],label='Validação'); ax.axvline(meta['selected_epoch'],linestyle='--',color='#555',label='Época selecionada'); ax.set(title=title,xlabel='Época'); ax.legend(fontsize=8)
    save(fig,'06_treinamento_B','B atual: época escolhida por menor val_loss; validação com 1.070 recortes. Sem histórico comparável do A.')
    # Exemplos com critério explícito, sem alterar pixels dos recortes.
    selected=[]
    for c in cohorts:
        rows=[r for r in per_image if r['system']=='B' and r['image_class']==c]
        key=(lambda r:(r['matched_positive_regions']-r['reference_points'],r['image_id'])) if c=='positive' else (lambda r:(-r['positive_regions'],r['image_id']))
        selected.extend((r['image_id'],labels[c]) for r in sorted(rows,key=key)[:3])
    assets=out/'exemplos'; assets.mkdir(exist_ok=True); cards=[]; examples=[]; lookup={r['image_id']:r for r in images}
    for i,(image_id,category) in enumerate(selected,1):
        pixels=read_image_rgb(lookup[image_id]['path']); preview=Image.fromarray(pixels); preview.thumbnail((1200,1200)); filename=f'exemplos/{i:02d}_campo.png'; preview.save(out/filename); details=[]
        refs=annotations[image_id]['positives']
        if refs:
            px,py=map(int,refs[0]['point']); bbox=[max(0,px-112),max(0,py-112),min(pixels.shape[1],px+112),min(pixels.shape[0],py+112)]; x1,y1,x2,y2=bbox; fn=f'exemplos/{i:02d}_referencia.png'; Image.fromarray(pixels[y1:y2,x1:x2]).save(out/fn); details.append(f'<figure><img src="{fn}"><figcaption>Contexto do ponto publicado {refs[0]["point"]}; não é proposta.</figcaption></figure>')
        for s in ('A','B'):
            item=predictions[s][image_id]; regions=sorted((r for r in item['regions'] if r['class_id']==1),key=lambda r:-r['scores'][1])[:3]; details.append(f'<p>{s}: {item["status"]}; {sum(r["class_id"]==1 for r in item["regions"])} regiões positivas.</p>')
            for j,r in enumerate(regions,1):
                bbox=list(map(int,r['bbox'])); x1,y1,x2,y2=bbox; fn=f'exemplos/{i:02d}_{s}_{j}.png'; Image.fromarray(pixels[y1:y2,x1:x2]).save(out/fn); details.append(f'<figure><img src="{fn}"><figcaption>{s}, caixa {bbox}, escore {r["scores"][1]:.4f}</figcaption></figure>'); examples.append(dict(image_id=image_id,category=category,system=s,bbox=json.dumps(bbox),score_suspect=r['scores'][1],file=fn))
        cards.append(f'<article><h3>{category}</h3><p>{html.escape(image_id)}</p><img class="campo" src="{filename}"><div class="recortes">'+''.join(details)+'</div></article>')
    if examples: write_csv(out/'exemplos.csv',examples)
    rows_html=''; text=f'# Comparação A original × B atual\n\nAvaliação exploratória de desenvolvimento. Mesmos {len(images)} IDs, agrupados em imagens positivas e negativas; teste reservado. Negativos por revisão visual declarada de Caio; referência positiva parcial.\n\n| Grupo | Modelo | Imagens sinalizadas | Regiões positivas | Tempo (s) | Erros |\n| --- | --- | ---: | ---: | ---: | ---: |\n'
    for c in cohorts:
        for i,s in enumerate(('A','B')):
            m=summary[c][s]; rows_html+=f'<tr><td>{labels[c]}</td><td>{NAMES[i]}</td><td>{m["signaled_images"]}/{m["n_images"]}</td><td>{m["positive_regions"]}</td><td>{m["algorithm_seconds"]:.2f}</td><td>{m["errors"]}</td></tr>'; text+=f'| {labels[c]} | {NAMES[i]} | {m["signaled_images"]}/{m["n_images"]} | {m["positive_regions"]} | {m["algorithm_seconds"]:.2f} | {m["errors"]} |\n'
    text+='\n'+protocol['timing']+'\n'
    text+=f"\nComparação: {len(groups['positive'])} imagens positivas e {len(groups['negative'])} imagens negativas. As origens continuam registradas nos manifestos e em `report.json`, sem divisão por fonte nos gráficos. Agrupamento descritivo por classe; não demonstra desempenho clínico nem remove diferenças de aquisição.\n"
    if protocol.get('training_update',{}).get('status')=='complete':
        text+='\nB retreinado e A original preservado. Nova inferência dos dois sistemas nas mesmas imagens, após o treino. Imagens usadas no treino permanecem excluídas da comparação. Este lote já foi examinado e constitui desenvolvimento, não teste final independente.\n'
    text+=f'\nCobertura dos pontos publicados: A {summary["positive"]["A"]["matched_positive_regions"]}/{total}; B {summary["positive"]["B"]["matched_positive_regions"]}/{total}.\n\nTempo: execução única, CPU, duas threads, B em grafo; inclui primeira imagem e exclui leitura/exportação. Não atribuir ganhos causalmente apenas à arquitetura, não misturar fontes numa acurácia global nem concluir desempenho clínico. Exemplos escolhidos pelas maiores perdas de cobertura (positivos) e maiores alarmes do B (negativos); não são amostra aleatória.\n'
    (root/'tcc/resultados_atuais.md').write_text(text,encoding='utf-8'); (out/'LEIA-ME.md').write_text(text+'\n'+''.join(f'\n- {f["name"]}: {f["caption"]}' for f in figures),encoding='utf-8'); save_json(out/'summary.json',dict(input_sha256=report['input_sha256'],class_summary=class_summary,summary=report['summary'],figures=figures))
    charts=''.join(f'<section><h2>{f["name"]}</h2><a href="{f["name"]}.pdf">PDF</a><img class="grafico" src="{f["name"]}.png"><p>{html.escape(f["caption"])}</p></section>' for f in figures)
    page='<html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>A original × B atual</title><style>body{font:16px system-ui;background:#edf2f5;color:#203548;margin:24px;line-height:1.5}section,article{background:white;padding:18px;margin:18px 0;border-radius:8px}table{border-collapse:collapse;background:white}td,th{padding:10px;border:1px solid #cdd7df}.grafico{display:block;max-width:100%;width:1100px}.campo{max-width:100%;max-height:500px}.recortes{display:flex;flex-wrap:wrap;gap:10px}.recortes figure{width:220px;margin:4px}.recortes img{width:100%}p{overflow-wrap:anywhere}</style><h1>A original × B atual</h1><p>'+str(len(images))+' imagens de desenvolvimento; teste reservado. Agrupamento em imagens positivas e negativas. Referência positiva parcial e negativos revisados visualmente por Caio.</p><table><tr><th>Grupo</th><th>Modelo</th><th>Sinalizadas</th><th>Regiões positivas</th><th>Tempo (s)</th><th>Erros</th></tr>'+rows_html+'</table><p>'+'As origens permanecem registradas nos arquivos de dados. O agrupamento por classe é descritivo e não demonstra desempenho clínico.'+'</p><p>'+html.escape(protocol['timing'])+'</p>'+charts+'<h2>Exemplos para conferência</h2><p>Campo sem marcações em prévia reduzida; recortes dos pixels originais. Seleção determinística pelas maiores perdas de cobertura e maiores alarmes do B. Escore não é probabilidade calibrada.</p>'+''.join(cards)+'</html>'
    division=f"<p><strong>Comparação: {len(groups['positive'])} imagens positivas e {len(groups['negative'])} imagens negativas.</strong></p>"
    page=page.replace('<table>',division+'<table>',1)
    (out/'index.html').write_text('<!doctype html>'+page,encoding='utf-8')
    return report
