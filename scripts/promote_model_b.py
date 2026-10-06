"""Arquiva B anterior e promove uma execução concluída; preserva históricos e hashes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def read(path):return json.loads(Path(path).read_text('utf-8-sig'))
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def validate_run(path):
    metadata=read(path/'metadata.json')
    if metadata.get('status')!='complete' or metadata.get('synthetic') is not False:
        raise ValueError('Execução incompleta/sintética não pode ser promovida ou substituir o B.')
    if sha(path/'best.keras')!=metadata['checkpoint_sha256']:
        raise ValueError('Checkpoint divergente do treinamento concluído.')
    for entry in metadata.get('manifests',{}).values():
        if sha(path/entry['copy'])!=entry['sha256']:
            raise ValueError('Entrada histórica de treino alterada.')
    return metadata


def promote(root,candidate,current,archive):
    root=Path(root).resolve();candidate=Path(candidate).resolve();current=Path(current).resolve();archive=Path(archive).resolve()
    if (not candidate.is_relative_to(root/'experiments/runs') or not current.is_relative_to(root/'experiments/runs')
            or not archive.is_relative_to(root/'archive') or archive==root/'archive'
            or candidate==current or archive.exists()):
        raise ValueError('Destinos precisam ficar nas pastas de execuções/arquivo do projeto, sem sobreposição.')
    new=validate_run(candidate);old=validate_run(current)
    if new['checkpoint_sha256']==old['checkpoint_sha256']:
        raise ValueError('Candidato tem o mesmo checkpoint do B anterior.')
    files={p.relative_to(current).as_posix():sha(p) for p in current.rglob('*') if p.is_file()}
    archive.mkdir(parents=True,exist_ok=False)
    destination=archive/current.name
    record=dict(created_at=datetime.now(timezone.utc).isoformat(),status='prepared',old_run=str(current),
        archived_run=str(destination),candidate_run=str(candidate),current_run=str(current),
        old_checkpoint_sha256=old['checkpoint_sha256'],new_checkpoint_sha256=new['checkpoint_sha256'],
        old_files_sha256=files)
    save(archive/'promotion.json',record)
    # Renomes na mesma área de trabalho: nenhum arquivo é apagado ou sobrescrito.
    current.rename(destination)
    try:
        candidate.rename(current)
    except Exception:
        destination.rename(current)
        raise
    if any(sha(destination/p)!=digest for p,digest in files.items()):
        raise RuntimeError('Conferência do arquivo histórico falhou.')
    if validate_run(current)['checkpoint_sha256']!=new['checkpoint_sha256']:
        raise RuntimeError('Conferência do B promovido falhou.')
    saved_protocols=archive/'previous_protocols';saved_protocols.mkdir()
    historical=[]
    comparisons=root/'experiments/comparison'
    for folder in comparisons.iterdir() if comparisons.exists() else []:
        path=folder/'protocol.json'
        if not path.is_file():continue
        protocol=read(path)
        if protocol.get('checkpoint',{}).get('B',{}).get('sha256')!=old['checkpoint_sha256']:continue
        before=path.read_bytes();(saved_protocols/(folder.name+'.json')).write_bytes(before)
        protocol['checkpoint']['B']['path']=str(destination/'best.keras')
        protocol['historical_model']=dict(status='archived',promotion_record=str(archive/'promotion.json'),
            original_protocol_sha256=hashlib.sha256(before).hexdigest(),
            note='Resultados do B anterior preservados; somente caminho de acesso ao modelo atualizado.')
        save(path,protocol);historical.append(folder.name)
        page=root/'tcc/figuras'/folder.name/'index.html'
        if page.is_file():
            text=page.read_text('utf-8')
            banner='<p style="padding:16px;background:#fff0ce;border:1px solid #c58b22"><strong>HISTÓRICO — resultados do modelo B anterior, agora arquivado.</strong> Esta página não apresenta o B retreinado com as 20 Barcelona.</p>'
            index=text.find('<h1>')
            if index>=0:page.write_text(text[:index]+banner+text[index:],encoding='utf-8')
    for name in historical:
        path=comparisons/name/'protocol.json';protocol=read(path)
        if 'base_comparison' in protocol:
            base=Path(protocol['base_comparison'])
            protocol['base_sha256']={key:sha(base/key) for key in protocol['base_sha256']}
            save(path,protocol)
    record.update(status='complete',historical_comparisons=historical,archive_verified=True)
    save(archive/'promotion.json',record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--current',type=Path,default=ROOT/'experiments/runs/b_val_01')
    parser.add_argument('--archive',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(promote(ROOT,args.candidate,args.current,args.archive),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
