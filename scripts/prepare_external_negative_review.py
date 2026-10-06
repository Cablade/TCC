"""Baixa 200 originais PBC/Barcelona para revisão; não cria rótulos negativos."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import io
import json
from pathlib import Path
import random
import struct
import sys
import zipfile
import zlib

import requests
from PIL import Image
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src import data_protocol as dp

SOURCE='https://data.mendeley.com/datasets/snkd93bnjr/1'
DOWNLOAD='https://data.mendeley.com/public-files/datasets/snkd93bnjr/files/2fc38728-2ae7-4a62-a857-032af82334c3/file_downloaded'
SIZE=281366219


def get_range(start,end):
    response=requests.get(DOWNLOAD,headers={'Range':f'bytes={start}-{end}'},timeout=(15,45))
    response.raise_for_status()
    if response.status_code!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{end}/{SIZE}' or len(response.content)!=end-start+1:
        raise ValueError('Fonte mudou ou não respeitou o intervalo solicitado.')
    return response.content


class RemoteReader(io.RawIOBase):
    def __init__(self):self.position=0
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.position
    def seek(self,offset,whence=0):
        self.position=offset if whence==0 else self.position+offset if whence==1 else SIZE+offset
        return self.position
    def read(self,size=-1):
        size=SIZE-self.position if size<0 else min(size,SIZE-self.position)
        if size<=0:return b''
        if size>5_000_000:raise ValueError('Leitura remota excessiva.')
        data=get_range(self.position,self.position+size-1);self.position+=size;return data


def download_entry(info):
    # Um intervalo inclui cabeçalho local e JPEG comprimido; CRC valida o membro.
    end=min(SIZE-1,info.header_offset+30+len(info.filename.encode('utf-8'))+len(info.extra)+info.compress_size+1024)
    chunk=get_range(info.header_offset,end)
    if chunk[:4]!=b'PK\x03\x04':raise ValueError('Cabeçalho ZIP inválido.')
    name_length,extra_length=struct.unpack_from('<HH',chunk,26)
    start=30+name_length+extra_length;compressed=chunk[start:start+info.compress_size]
    raw=zlib.decompress(compressed,-15) if info.compress_type==zipfile.ZIP_DEFLATED else compressed if info.compress_type==zipfile.ZIP_STORED else None
    if raw is None or len(raw)!=info.file_size or zlib.crc32(raw)!=info.CRC:
        raise ValueError('CRC/tamanho do membro ZIP divergente: '+info.filename)
    return info,raw


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'data/annotations/barcelona_originals_review')
    parser.add_argument('--per-class',type=int,default=25)
    parser.add_argument('--resume-incomplete',action='store_true',help='Retoma somente um download sem revisão ou relatório concluído.')
    args=parser.parse_args();output=args.output_dir.resolve()
    if args.per_class<1 or args.per_class>50:parser.error('Use de 1 a 50 imagens por tipo.')
    if output.exists() and (not args.resume_incomplete or (output/'index.html').exists() or (output/'preparation.json').exists()):
        raise FileExistsError('Lote existente; preserve a revisão.')
    with zipfile.ZipFile(RemoteReader()) as remote:
        infos=[i for i in remote.infolist() if i.filename.lower().endswith('.jpg') and not any(p.startswith('.') or p=='__MACOSX' for p in Path(i.filename).parts)]
    classes={}
    for info in infos:classes.setdefault(Path(info.filename).parent.name,[]).append(info)
    print('SOURCE CLASSES',json.dumps({k:len(v) for k,v in classes.items()}),flush=True)
    if len(classes)!=8:raise ValueError('A estrutura da fonte não corresponde aos oito tipos publicados.')
    selected=[];generator=random.Random(42)
    for name,values in sorted(classes.items()):
        values.sort(key=lambda i:i.filename);generator.shuffle(values);selected.extend(values[:args.per_class])
    output.mkdir(parents=True,exist_ok=args.resume_incomplete);images=output/'images';images.mkdir(exist_ok=args.resume_incomplete)
    existing=dp.read_manifest(ROOT/'data/annotations/kaggle_originals_20261005/inventory.csv')
    raw_hashes={r['sha256'] for r in existing};pixel_hashes={r['decoded_sha256'] for r in existing}
    rows=[];rejected=[];cards=[];records=[];seen=set()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for index,(info,raw) in enumerate(pool.map(download_entry,selected),1):
            with Image.open(io.BytesIO(raw)) as image:
                pixels=np.asarray(image.convert('RGB'));width,height=image.size
            digest=hashlib.sha256(raw).hexdigest();decoded=hashlib.sha256(str(pixels.shape).encode()+pixels.tobytes()).hexdigest()
            if digest in raw_hashes or decoded in pixel_hashes or decoded in seen:
                rejected.append(dict(member=info.filename,reason='duplicate_pixels_or_bytes'));continue
            if not (300<=width<=500 and 300<=height<=500):
                raise ValueError('Dimensões inesperadas: '+info.filename)
            seen.add(decoded);image_id='barcelona_original_'+digest[:24];filename=images/(image_id+'.jpg')
            if filename.exists():
                if hashlib.sha256(filename.read_bytes()).hexdigest()!=digest:raise ValueError('Arquivo parcial alterado.')
            else:filename.write_bytes(raw)
            cell_type=Path(info.filename).parent.name
            rows.append(dict(image_id=image_id,path=filename.as_posix(),sha256=digest,width=width,height=height,
                source=SOURCE,group_id=image_id,group_level='imagem_original',split='development',duplicate_of='',
                source_member=info.filename,source_crc32=f'{info.CRC:08x}',decoded_sha256=decoded,cell_type=cell_type,
                original_image_id=image_id,review_status='pending'))
            records.append(dict(image_id=image_id,member=info.filename,byte_range=[info.header_offset,info.header_offset+30+len(info.filename.encode())+len(info.extra)+info.compress_size+1024],sha256=digest,crc32=f'{info.CRC:08x}'))
            cards.append(f'<article data-id="{image_id}"><h3>{index}. {html.escape(cell_type)}</h3><a href="images/{image_id}.jpg" target="_blank"><img loading="lazy" src="images/{image_id}.jpg" width="360" height="363"></a><p>{html.escape(Path(info.filename).name)}</p><select onchange="saveDecision(this)"><option value="pending">Pendente</option><option value="no_visible_parasite">Examinei: sem parasita visível</option><option value="uncertain">Dúvida / excluir</option><option value="visible_parasite">Parasita visível / excluir</option></select></article>')
            if index%25==0:print(f'DOWNLOADED {index}/{len(selected)}',flush=True)
    dp.validate_partitions(rows);dp.write_manifest(rows,output/'inventory.csv',list(rows[0]))
    annotations=dp.annotation_template(rows)
    (output/'source_annotations.json').write_text(json.dumps(annotations,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report=dict(source=SOURCE,doi='10.17632/snkd93bnjr.1',article='https://doi.org/10.1016/j.dib.2020.105474',
        contributors=['Andrea Acevedo','Anna Merino','Santiago Alférez','Ángel Molina','Laura Boldú','José Rodellar'],
        license='CC BY 4.0',source_archive_url=DOWNLOAD,source_archive_bytes=SIZE,
        source_archive_full_hash_verified=False,member_crc32_verified=True,
        sampling=f'{args.per_class} por tipo, semente 42, antes de inferência e independente de decisões dos modelos.',
        source_cell_types={k:len(v) for k,v in classes.items()},downloaded=len(rows),excluded=rejected,members=records,
        observed_dimensions=sorted({(r['width'],r['height']) for r in rows}),
        labels_for_chagas_provided=False,review_required=True,approved_for_comparison=False,trained_on_current_B=False,
        limitation='Originais de células individuais já enquadradas em 360×363, não campos inteiros de lâminas. Fonte humana/CellaVision distinta da base positiva murina; IDs de paciente/lâmina indisponíveis. Relatar fonte separadamente. Sem fabricação por aumento local.',
        duplicate_check='Bytes e pixels contra todos os 366 originais Kaggle e entre candidatos. Não prova independência biológica nem exclui toda similaridade.')
    (output/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    metadata=json.dumps(dict(schema_version=1,source=SOURCE,inventory_sha256=hashlib.sha256((output/'inventory.csv').read_bytes()).hexdigest(),images=[dict(image_id=r['image_id'],source_sha256=r['sha256']) for r in rows]),ensure_ascii=False).replace('<','\\u003c')
    script='''const metadata=METADATA;const key="barcelona_review_"+metadata.inventory_sha256;let decisions=JSON.parse(localStorage.getItem(key)||"{}");document.querySelectorAll('article').forEach(a=>{a.querySelector('select').value=decisions[a.dataset.id]||'pending'});function saveDecision(s){decisions[s.closest('article').dataset.id]=s.value;localStorage.setItem(key,JSON.stringify(decisions));count()}function count(){document.getElementById('count').textContent=Object.values(decisions).filter(v=>v==='no_visible_parasite').length+' aprovadas de '+metadata.images.length}count();function exportReview(){const reviewer=document.getElementById('reviewer').value.trim();if(!reviewer){alert('Informe seu nome real.');return}const payload={...metadata,reviewer,created_at:new Date().toISOString(),review_basis:'human_visual_review',images:metadata.images.map(r=>({...r,decision:decisions[r.image_id]||'pending'}))};const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));a.download='revisao_barcelona_originais.json';a.click();URL.revokeObjectURL(a.href)}'''.replace('METADATA',metadata)
    page='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Novos candidatos negativos — PBC Barcelona</title><style>body{font:16px system-ui;background:#edf2f5;color:#203548;margin:24px}header{position:sticky;top:0;background:white;padding:12px;z-index:1}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(365px,1fr));gap:14px}article{padding:12px;background:white;border-radius:8px}img{max-width:100%;height:auto}select{max-width:100%;padding:10px}p{overflow-wrap:anywhere}</style><header><h1>Novos originais para revisar</h1><p>200 imagens de células individuais: 25 por tipo. Clique para ver os pixels originais. A classe sanguínea e a descrição da fonte não confirmam ausência de T. cruzi; examine cada imagem. Não participaram do treino.</p><label>Revisor: <input id="reviewer" placeholder="Seu nome real"></label> <button onclick="exportReview()">Exportar revisão</button> <span id="count"></span><p>Decisões ficam neste navegador até exportar. Envie o JSON exportado para incorporar apenas as aprovadas na comparação, separadas dos campos Kaggle.</p></header><main class="grid">'+''.join(cards)+'</main><script>'+script+'</script></html>'
    page=page.replace('200 imagens de células individuais: 25 por tipo.',f'{len(rows)} imagens de células individuais: até {args.per_class} por tipo.')
    (output/'index.html').write_text(page,encoding='utf-8')
    print('REVIEW READY '+str(output/'index.html'),flush=True)


if __name__=='__main__':main()
