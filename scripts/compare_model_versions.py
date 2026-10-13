"""Executa exclusivamente A original e B atual no mesmo desenvolvimento."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp

MODELS = {
    'A': ('A original', ROOT/'models/model_a/model_trained.keras'),
    'B': ('B atual', ROOT/'experiments/runs/b_atual/best.keras'),
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    primary_path=ROOT/'data/splits/experimento/images.csv'
    combined_path=ROOT/'data/processed/b_real_01/images.csv'
    primary=dp.read_manifest(primary_path)
    combined=dp.read_manifest(combined_path)
    sources={
        'positive_val': [r for r in primary if r['split']=='val'],
        'kaggle_negative_val': [r for r in combined if r['split']=='val' and r['image_id'].startswith('kaggle_original_')],
    }
    if {k:len(v) for k,v in sources.items()} != {'positive_val':114,'kaggle_negative_val':73}:
        raise ValueError('Contagens diferem dos lotes autorizados; revisar o protocolo.')
    comparison_config=ROOT/'configs/comparison_a_vs_b.json'
    barcelona_refs={}; extra_paths=[]; next_training=[]
    if comparison_config.exists():
        from src.negative_partition import assert_disjoint_training_comparison
        setup=read(comparison_config)
        for key in ('barcelona_manifest','barcelona_annotations','barcelona_authorization'):
            path=ROOT/setup[key]
            if sha(path)!=setup[key+'_sha256']:
                raise ValueError('Reserva Barcelona alterada: '+key)
            extra_paths.append(path)
        authorization=read(ROOT/setup['barcelona_authorization'])
        if authorization.get('status')!='complete' or len(authorization.get('training_image_ids',[]))!=20:
            raise ValueError('Reserva de 20 negativos Barcelona ainda não confirmada.')
        sources['barcelona_negative']=dp.read_manifest(ROOT/setup['barcelona_manifest'])
        barcelona_refs=dp.load_annotations(ROOT/setup['barcelona_annotations'],sources['barcelona_negative'])
        if ({k:len(v) for k,v in sources.items()}!=setup['expected_cohorts']
                or {r['image_id'] for r in sources['barcelona_negative']}!=set(authorization['comparison_image_ids'])):
            raise ValueError('Comparação exige exatamente as 180 imagens Barcelona restantes.')
        next_training=dp.read_manifest(ROOT/setup['next_training_manifest'])
        assert_disjoint_training_comparison([r for r in next_training if r['split']=='train'],
                                            [r for rows in sources.values() for r in rows])
        extra_paths += [comparison_config,ROOT/setup['next_training_manifest']]
    batch=ROOT/'data/annotations/kaggle_originals_20261005'
    approval_path=batch/'human_approval_all_originals.json'
    approval=read(approval_path)
    reviewed_path=batch/'reviewed.json'
    if approval['status']!='complete' or approval['reviewed_sha256']!=sha(reviewed_path):
        raise ValueError('A aprovação humana mudou; preservar e conferir o lote.')
    refs=dp.load_annotations(ROOT/'data/annotations/experimento_reference_v2.json',primary)
    reviewed=dp.load_annotations(reviewed_path,dp.read_manifest(batch/'inventory.csv'))
    selected=[]; annotations=[]
    for cohort, rows in sources.items():
        for original in rows:
            if original['split']=='test': raise ValueError('Teste final proibido neste diagnóstico.')
            row=dict(original, source_split=original['split'], split='development', cohort=cohort)
            selected.append(row)
            if cohort=='positive_val':
                entry=deepcopy(refs[row['image_id']])
            elif cohort=='kaggle_negative_val':
                entry=deepcopy(reviewed[row['image_id']])
                if not any(n['bbox']==[0,0,int(row['width']),int(row['height'])] and n['review_status']=='reviewed' for n in entry['negative_regions']):
                    raise ValueError('Imagem sem aprovação do campo inteiro.')
                entry.update(review_status='reviewed', reviewer='Caio', whole_image_label=0,
                             reference_complete=True, review_basis='human_visual_review_reported_by_user',
                             review_usage='development', review_source=str(approval_path))
            else:
                entry=deepcopy(barcelona_refs[row['image_id']])
                if entry['whole_image_label']!=0 or not entry['reference_complete'] or entry['review_status']!='reviewed':
                    raise ValueError('Barcelona exige referência negativa completa.')
            annotations.append(entry)
    reserved={r['image_id'] for r in primary if r['split']=='test'}
    if reserved & {r['image_id'] for r in selected}: raise ValueError('Teste incluído indevidamente.')
    train_external={r['group_id'] for r in combined if r['split']=='train' and r['image_id'].startswith('kaggle_original_')}
    if train_external & {r['group_id'] for r in sources['kaggle_negative_val']}:
        raise ValueError('Grupo visual externo compartilhado com treino.')
    dp.validate_partitions(selected)
    payload={'schema_version':1,'coordinate_convention':'xyxy_half_open','images':annotations}
    dp.validate_annotations(payload,selected)
    fields=list(dict.fromkeys(k for r in selected for k in r))
    dp.write_manifest(selected,output/'images.csv',fields)
    save(output/'annotations.json',payload)
    checkpoints={}
    for key,(label,path) in MODELS.items():
        if key!='A':
            meta=read(path.parent/'metadata.json')
            if meta['status']!='complete' or meta['synthetic'] is not False or meta['checkpoint_sha256']!=sha(path):
                raise ValueError('Treino/checkpoint inválido: '+key)
        checkpoints[key]={'label':label,'path':str(path),'sha256':sha(path)}
    save(output/'protocol.json',dict(created_at=datetime.now(timezone.utc).isoformat(),
        cohorts={k:len(v) for k,v in sources.items()},checkpoint=checkpoints,
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in [primary_path,combined_path,approval_path,reviewed_path]+extra_paths},
        scope='Negativos originais Kaggle da validação e, quando houver reserva 20/180, somente os 180 Barcelona destinados à comparação. Fontes separadas; versões aumentadas do fornecedor excluídas.',
        scope_change='LABIMED retirado a pedido do usuário após inspeção dos resultados. Histórico integral em archive/labimed_historico_20261005.zip. Barcelona: reserva de 20 para próximo treino feita após diagnóstico das 200; 180 na comparação de desenvolvimento. Exclusões não demonstram a causa dos alarmes.',
        evaluation='development_only',test_images_excluded=len(reserved),
        decision_rule='any_argmax_positive_region',threads=2,B_execution='tf_function',
        timing='Uma execução sequencial por modelo; sem exportação PNG, sem aquecimento explícito. Não é benchmark repetido.',
        reference='Pontos positivos parciais; negativos declarados visualmente por Caio. Coortes separadas, sem acurácia global misturando fontes.'))
    if comparison_config.exists():
        b_meta=read(MODELS['B'][1].parent/'metadata.json')
        if b_meta.get('manifests',{}).get('images',{}).get('sha256')==sha(ROOT/setup['next_training_manifest']):
            provenance_path=MODELS['B'][1].parent/'human_review_provenance.json'
            provenance=read(provenance_path)
            if provenance.get('barcelona_training_originals')!=20 or provenance.get('barcelona_training_negative_crops')!=80:
                raise ValueError('Novo B sem prova das 20 imagens negativas e 80 recortes.')
            protocol=read(output/'protocol.json')
            protocol['training_update']=dict(status='complete',barcelona_training_originals=20,
                added_barcelona_negative_crops=80,training_dataset_sha256=b_meta['manifests']['images']['sha256'],
                selected_epoch=b_meta['selected_epoch'],selected_val_loss=b_meta['selected_val_loss'],
                old_checkpoint_archived=True,training_run=str(MODELS['B'][1].parent))
            save(output/'protocol.json',protocol)
    return output


def reuse_completed_runs(output, sources):
    """Combina previsões existentes com igualdade de pixels, referência e configuração."""
    from src.detection_evaluation import load_prediction_run
    rows=dp.read_manifest(output/'images.csv'); expected={r['image_id'] for r in rows}
    if len(expected)!=len(rows): raise ValueError('IDs repetidos no destino.')
    refs=dp.load_annotations(output/'annotations.json',rows)
    protocol=read(output/'protocol.json'); derivation={}; collected={s:{} for s in ('A','B')}
    envelopes={}; artifacts={s:[] for s in ('A','B')}
    identity=('path','sha256','width','height','source','group_id','decoded_sha256')
    for source in sources:
        original_rows=dp.read_manifest(source/'images.csv')
        lookup={r['image_id']:r for r in original_rows}
        if len(lookup)!=len(original_rows): raise ValueError('IDs repetidos na origem.')
        selected=expected & set(lookup)
        original_refs=dp.load_annotations(source/'annotations.json',original_rows)
        for row in rows:
            if row['image_id'] not in selected: continue
            old=lookup[row['image_id']]
            if any(str(row.get(k,''))!=str(old.get(k,'')) for k in identity):
                raise ValueError('Pixels/origem/grupo alterado para reutilização.')
            if row.get('source_split',row['split'])!=old.get('source_split',old['split']):
                raise ValueError('Partição alterada para reutilização.')
            if refs[row['image_id']]!=original_refs[row['image_id']]:
                raise ValueError('Referência alterada para reutilização.')
        for system in ('A','B'):
            path=source/system/'predictions.json'
            entries,origin=load_prediction_run(path,system,'development',sha(source/'images.csv'))
            identifiers=[r['image_id'] for r in entries]
            if len(set(identifiers))!=len(identifiers) or set(identifiers)!=set(lookup):
                raise ValueError('IDs da inferência não correspondem à origem.')
            artifact=origin['artifact']
            if artifact.get('checkpoint_sha256',artifact.get('sha256'))!=protocol['checkpoint'][system]['sha256']:
                raise ValueError('Checkpoint alterado; previsões antigas não podem ser reutilizadas.')
            if system=='B' and artifacts[system] and artifact['config']!=artifacts[system][0]['config']:
                raise ValueError('Configuração B diferente entre execuções.')
            artifacts[system].append(artifact)
            for entry in entries:
                if entry['image_id'] not in selected: continue
                if entry['image_id'] in collected[system]: raise ValueError('ID compartilhado entre execuções de origem.')
                collected[system][entry['image_id']]=entry
            envelopes.setdefault(system,read(path))
            derivation.setdefault(system,[]).append(dict(source=str(source),predictions_sha256=sha(path),
                manifest_sha256=sha(source/'images.csv'),source_count=len(entries),retained_count=len(selected),
                source_artifact=artifact))
    for system in ('A','B'):
        if set(collected[system])!=expected: raise ValueError('Previsões ausentes no lote combinado.')
        payload=deepcopy(envelopes[system])
        payload['images']=[collected[system][r['image_id']] for r in rows]
        payload['manifest_sha256']=sha(output/'images.csv')
        payload['combined_provenance']=dict(sources=derivation[system],
            note='Previsões e tempos por imagem preservados. Nenhuma nova inferência ou treinamento; artefatos das execuções de origem registrados integralmente.')
        payload.pop('subset_provenance',None)
        target=output/system; target.mkdir(exist_ok=False);save(target/'predictions.json',payload)
    protocol['combined_derivation']=derivation
    protocol['timing']='Tempos herdados de duas execuções anteriores, preservados por imagem e fonte. Não houve nova inferência; somas não representam um benchmark do lote combinado.'
    protocol.update(training_started=False,prepared_next_training=True,final_test_opened=False)
    save(output/'protocol.json',protocol)


def reuse_subset(output, source):
    """Deriva um subconjunto sem modificar decisões, caixas ou tempos salvos."""
    from src.detection_evaluation import load_prediction_run
    target_manifest=output/'images.csv'; source_manifest=source/'images.csv'
    rows=dp.read_manifest(target_manifest); source_rows=dp.read_manifest(source_manifest)
    lookup={r['image_id']:r for r in source_rows}
    if len(lookup)!=len(source_rows): raise ValueError('IDs repetidos no manifesto de origem.')
    expected={r['image_id'] for r in rows}
    if len(expected)!=len(rows) or not expected<=set(lookup):
        raise ValueError('Subconjunto contém IDs extras ou repetidos.')
    clean=lambda row:{k:v for k,v in row.items() if v not in ('',None)}
    for row in rows:
        if clean(row)!=clean(lookup[row['image_id']]):
            raise ValueError('Imagem/partição/origem alterada no subconjunto.')
    refs=dp.load_annotations(output/'annotations.json',rows)
    old_refs=dp.load_annotations(source/'annotations.json',source_rows)
    if any(refs[i]!=old_refs[i] for i in expected):
        raise ValueError('Referência alterada no subconjunto.')
    protocol=read(output/'protocol.json'); derivation={}
    for system in ('A','B'):
        old_path=source/system/'predictions.json'
        entries,origin=load_prediction_run(old_path,system,'development',sha(source_manifest))
        ids=[r['image_id'] for r in entries]
        if len(set(ids))!=len(ids) or set(ids)!=set(lookup):
            raise ValueError('IDs da inferência não correspondem à origem.')
        if origin['artifact'].get('checkpoint_sha256',origin['artifact'].get('sha256'))!=protocol['checkpoint'][system]['sha256']:
            raise ValueError('Checkpoint alterado; executar nova inferência.')
        payload=read(old_path)
        provenance=dict(source_predictions_sha256=sha(old_path),source_manifest_sha256=sha(source_manifest),
            historical_archive='archive/labimed_historico_20261005.zip',source_count=len(entries),
            retained_count=len(rows),removed_count=len(entries)-len(rows),
            note='Filtro por IDs do manifesto. Decisões e tempos preservados; nenhuma nova inferência/medição. Artefato conserva a proveniência da execução original.')
        payload['images']=[r for r in entries if r['image_id'] in expected]
        payload['manifest_sha256']=sha(target_manifest)
        payload['subset_provenance']=provenance
        dest=output/system; dest.mkdir(exist_ok=False); save(dest/'predictions.json',payload)
        derivation[system]=provenance
    protocol['subset_derivation']=derivation
    protocol['timing']='Tempos por imagem herdados da execução original de 220 imagens; filtrados, não remedidos. Não é benchmark do novo lote nem execução repetida.'
    save(output/'protocol.json',protocol)


def run_models(output, reuse_a=None):
    for key,(_,checkpoint) in MODELS.items():
        dest=output/key
        if key=='A' and reuse_a is not None:
            import shutil
            from src.detection_evaluation import load_prediction_run
            entries, provenance=load_prediction_run(reuse_a/'predictions.json','A','development',sha(output/'images.csv'))
            if provenance['artifact']['sha256']!=sha(checkpoint) or any(r['status']=='erro' for r in entries):
                raise ValueError('A reutilizado não coincide com o checkpoint ou contém falha.')
            if {r['image_id'] for r in entries}!={r['image_id'] for r in dp.read_manifest(output/'images.csv')}:
                raise ValueError('A reutilizado não contém exatamente os mesmos IDs.')
            shutil.copytree(reuse_a,dest)
            save(output/'reuse_A.json',{'source':str(reuse_a),'predictions_sha256':sha(reuse_a/'predictions.json'),
                'note':'A concluído no mesmo lote, CPU e limite de duas threads; sem nova inferência. Tempos pertencem a essa execução anterior.'})
            print('REUSED A',flush=True)
            continue
        command=[sys.executable,'-u',str(ROOT/'scripts'/('run_model_a.py' if key=='A' else 'run_model_b.py')),
                 '--manifest',str(output/'images.csv'),'--split','development','--output-dir',str(dest)]
        command += (['--model',str(checkpoint),'--threads','2'] if key=='A'
                    else ['--checkpoint',str(checkpoint),'--compiled','--image-mode','none'])
        if (dest/'predictions.json').exists(): raise FileExistsError('Inferência existente: '+str(dest))
        print('START '+key,flush=True)
        environment=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONUNBUFFERED='1')
        with (output/(key+'.stdout.log')).open('w',encoding='utf-8') as stdout, (output/(key+'.stderr.log')).open('w',encoding='utf-8') as stderr:
            result=subprocess.run(command,cwd=ROOT,env=environment,stdout=stdout,stderr=stderr)
        if result.returncode: raise RuntimeError(f'{key} falhou; conferir seus logs (código {result.returncode}).')
        print('DONE '+key,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--summarize-only',action='store_true')
    parser.add_argument('--reuse-a',type=Path,help='Execução A concluída com o mesmo manifesto/checkpoint.')
    parser.add_argument('--reuse-run',type=Path,help='Comparação A/B concluída; deriva o subconjunto atual sem nova inferência.')
    parser.add_argument('--reuse-sources',nargs='+',type=Path,help='Combina execuções concluídas por IDs e referência, sem nova inferência.')
    args=parser.parse_args(); output=args.output_dir.resolve()
    if not args.summarize_only:
        if sum(bool(x) for x in (args.reuse_a,args.reuse_run,args.reuse_sources))>1: parser.error('Escolha somente uma forma de reutilização.')
        prepare(output)
        if args.reuse_sources: reuse_completed_runs(output,[p.resolve() for p in args.reuse_sources])
        elif args.reuse_run: reuse_subset(output,args.reuse_run.resolve())
        else: run_models(output,args.reuse_a)
    from src.tcc_reporting import build_report
    report=build_report(ROOT,output)
    print(json.dumps(report['summary'],ensure_ascii=False),flush=True)


if __name__=='__main__': main()
