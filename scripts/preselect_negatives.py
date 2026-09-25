"""Sugere regiões para revisão humana; nunca cria rótulos negativos de treino."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp
from src.segmentation import propose_regions


def select_images(rows, count, seed):
    # Sem partição final: somente a pasta train da fonte; test/val existentes são intocados.
    eligible = [r for r in rows if not r.get('duplicate_of') and
                (r.get('split') == 'development' or
                 (not r.get('split') and '!train/' in r['path'].replace('\\', '/')))]
    eligible.sort(key=lambda r: r['image_id'])
    random.Random(seed).shuffle(eligible)
    if len(eligible) < count:
        raise ValueError('Não há imagens elegíveis suficientes fora das reservas de avaliação.')
    return [{**r, 'split': 'development'} for r in eligible[:count]]


def safe_distance(box, positives, width, height, margin=200):
    expanded = [max(0, box[0]-margin), max(0, box[1]-margin),
                min(width, box[2]+margin), min(height, box[3]+margin)]
    return dp.validate_negative_box(expanded, positives)


def proposals(pixels, positives, limit, seed):
    import numpy as np
    height, width = pixels.shape[:2]
    candidates, _ = propose_regions(pixels)
    random.Random(seed).shuffle(candidates)
    selected = []
    side = 384
    for candidate in candidates:
        x1,y1,x2,y2 = candidate['bbox']
        cx,cy=(x1+x2)//2,(y1+y2)//2
        left,top=max(0,min(width-side,cx-side//2)),max(0,min(height-side,cy-side//2))
        box=[left,top,left+side,top+side]
        if width < side or height < side or not safe_distance(box, positives, width, height):
            continue
        if any(max(box[0], b[0]) < min(box[2], b[2]) and
               max(box[1], b[1]) < min(box[3], b[3]) for b in selected):
            continue
        gray=pixels[top:top+side,left:left+side].mean(axis=2)
        # Apenas qualidade/diversidade de candidatos: isto NÃO decide ausência de parasita.
        if float(np.std(gray)) < 8 or float((gray > 245).mean()) > .9 or float((gray < 30).mean()) > .2:
            continue
        selected.append(box)
        if len(selected) == limit:
            break
    return selected


def save_json(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    from PIL import Image, ImageDraw
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,default=ROOT/'data/protocol/trypomastigote_verified/eligible_inventory.csv')
    parser.add_argument('--annotations',type=Path,default=ROOT/'data/annotations/public_import/public_points.json')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'data/annotations/negative_preselection_v1')
    parser.add_argument('--images',type=int,default=8)
    parser.add_argument('--per-image',type=int,default=5)
    parser.add_argument('--seed',type=int,default=42)
    args=parser.parse_args()
    if args.images < 1 or args.per_image < 1:
        parser.error('Quantidades devem ser positivas.')
    if args.output_dir.exists():
        raise FileExistsError('Lote já existe; use um novo destino para preservar a revisão.')
    rows=select_images(dp.read_manifest(args.inventory),args.images,args.seed)
    payload=json.loads(args.annotations.read_text(encoding='utf-8-sig'))
    source=dp.validate_annotations(payload)
    subset=deepcopy(payload)
    subset['images']=[source[row['image_id']] for row in rows]
    dp.validate_annotations(subset,rows)
    args.output_dir.mkdir(parents=True)
    # Persistir a exposição ao desenvolvimento ANTES de abrir os pixels.
    dp.write_manifest(rows,args.output_dir/'inventory.csv')
    save_json(args.output_dir/'source_annotations.json',subset)
    save_json(args.output_dir/'development_reservation.json',{
        'created_at':datetime.now(timezone.utc).isoformat(), 'seed':args.seed,
        'purpose':'negative_candidate_preselection', 'excluded_from_future_test':True,
        'images':[{'image_id':r['image_id'],'sha256':r['sha256'],'group_id':r['group_id']} for r in rows],
        'limitation':'Grupos por imagem; não comprovam independência de animais/lâminas.'})
    (args.output_dir/'previews').mkdir()
    queue=[]; sections=[]
    for index,row in enumerate(rows):
        raw=dp.read_image_bytes(row['path'])
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:
            raise ValueError('Conteúdo da imagem mudou.')
        pixels=dp.read_image_rgb(row['path'])
        boxes=proposals(pixels,source[row['image_id']]['positives'],args.per_image,args.seed+index)
        cards=[]
        sheet=Image.new('RGB',(384*max(1,len(boxes)),420),'white')
        draw=ImageDraw.Draw(sheet)
        for number,box in enumerate(boxes,1):
            identifier=f'candidate_{index+1:02d}_{number:02d}'
            preview=f'previews/{identifier}.png'
            crop=Image.fromarray(pixels[box[1]:box[3],box[0]:box[2]])
            crop.save(args.output_dir/preview)
            sheet.paste(crop,((number-1)*384,36)); draw.text(((number-1)*384+8,8),identifier,fill='black')
            queue.append({'candidate_id':identifier,'image_id':row['image_id'],'source_sha256':row['sha256'],
                'bbox':box,'review_status':'pending','reviewer':None,'label':None,
                'selection_method':'blackhat_proposal_with_context_and_distance_filter',
                'known_positive_margin_pixels':200,'preview':preview})
            cards.append(f'<article><h3>{identifier}</h3><a href="{preview}"><img src="{preview}" width="384" height="384"></a><p>Coordenadas: {box}</p><p class="pending">Candidata — revisão pendente</p></article>')
        sheet.save(args.output_dir/f'previews/overview_{index+1:02d}.jpg')
        sections.append(f'<section><h2>{html.escape(Path(row["path"]).name)} — desenvolvimento</h2><div class="grid">'+''.join(cards)+'</div></section>')
        print(f'{index+1}/{len(rows)}: {len(boxes)} sugestões',flush=True)
    suggestions={'schema_version':1,'purpose':'unreviewed_negative_candidates',
        'source_annotation_sha256':hashlib.sha256((args.output_dir/'source_annotations.json').read_bytes()).hexdigest(),
        'candidates':queue}
    save_json(args.output_dir/'suggestions.json',suggestions)
    page='''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Pré-seleção para revisão</title>
<style>body{font:16px system-ui;margin:32px;background:#f4f6f8;color:#172535}.grid{display:flex;flex-wrap:wrap;gap:18px}article{background:white;padding:14px;border-radius:10px}img{max-width:100%;height:auto}.pending{color:#985000;font-weight:600}code{overflow-wrap:anywhere}section{margin-top:30px}</style>
<h1>Regiões candidatas para você examinar</h1><p>As sugestões foram escolhidas por estruturas e distância dos pontos conhecidos. <strong>Não confirmam ausência de parasitas e não possuem rótulo de treino.</strong> Clique num recorte para ampliar.</p>
<p>As imagens deste lote foram reservadas para desenvolvimento. Não reutilizar no teste final. Examine toda a região e o contexto na imagem original antes de confirmar.</p>'''
    command=f'.\\.venv\\Scripts\\python.exe scripts/review_annotations.py --batch {args.output_dir.relative_to(ROOT).as_posix() if args.output_dir.is_relative_to(ROOT) else str(args.output_dir)}'
    page+=f'<p>Para confirmar ou desenhar outra região, abra a revisão interativa no terminal do projeto:</p><pre><code>{html.escape(command)}</code></pre>'
    page+=''.join(sections)+'</html>'
    (args.output_dir/'index.html').write_text(page,encoding='utf-8')
    save_json(args.output_dir/'report.json',{'images':len(rows),'suggestions':len(queue),'confirmed_negatives':0,
        'status':'pending_human_review','seed':args.seed,'source_inventory':str(args.inventory),
        'source_annotations':str(args.annotations),'review_command':command})
    print(f'{len(queue)} candidatas pendentes. Galeria: {args.output_dir / "index.html"}')


if __name__=='__main__':
    main()
