"""Fixtures geométricas exclusivamente sintéticas para executar os notebooks."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from src import data_protocol as dp


class SyntheticClassifier:
    """Dublê determinístico: verifica fluxo, não representa pesos A ou B."""
    def predict(self, batch, **kwargs):
        return np.tile([0.2,0.8], (len(batch),1))

    def __call__(self, batch, **kwargs):
        return self.predict(batch)


def prepare_synthetic(root):
    root=Path(root)
    output=root/'experiments'/'validation'/'notebooks_synthetic'
    raw=output/'raw'
    raw.mkdir(parents=True,exist_ok=True)
    for index in range(4):
        image=np.full((180,180,3),255-index,np.uint8)
        if index % 2:
            image[70:95,70:95]=[100,22,87]
        Image.fromarray(image).save(raw/f'image_{index}.png')
    inventory=dp.build_inventory([raw])
    for row in inventory['images']:
        row['source']='sintetica_geometrica_sem_material_biologico'
    dp.write_manifest(inventory['images'],output/'inventory.csv')
    rows=dp.assign_splits(inventory['images'],counts={'train':1,'val':1,'test':2},seed=42)
    dp.write_manifest(rows,output/'images.csv')
    template=dp.annotation_template(rows)
    (output/'pending.json').write_text(json.dumps(template,indent=2),encoding='utf-8')
    for item in template['images']:
        row=next(row for row in rows if row['image_id']==item['image_id'])
        positive=int(Path(row['path']).stem.rsplit('_',1)[1])%2
        item.update(review_status='reviewed',reviewer='fixture_sintetica_gerada_por_codigo',
                    reference_complete=True,whole_image_label=positive)
        item['positives']=[{'annotation_id':'synthetic_square','bbox':[70,70,95,95]}] if positive else []
    template['synthetic']=True
    (output/'synthetic_annotations.json').write_text(json.dumps(template,indent=2),encoding='utf-8')
    return output,rows


def synthetic_comparison(output, rows):
    """Previsões artificiais, independentes das redes, para testar métricas."""
    from src.detection_evaluation import compare_systems
    annotations=dp.load_annotations(output/'synthetic_annotations.json',rows)
    predictions=[]
    for row in rows:
        if row['split']!='test':
            continue
        positive=bool(annotations[row['image_id']]['positives'])
        regions=[{'bbox':[70,70,95,95],'class_id':1,'scores':[.2,.8]}] if positive else []
        predictions.append({'image_id':row['image_id'],'status':'predicao_positiva' if positive else 'sem_regioes',
                            'regions':regions,'candidates':[{'bbox':[70,70,95,95]}] if positive else [],
                            'original_decision':int(positive),'timings':{}})
    for system in ('A','B'):
        from src.model_a import file_sha256
        (output/f'fixture_{system}.json').write_text(json.dumps({'schema_version':1,'system':system,'synthetic':True,
            'split':'test','manifest_sha256':file_sha256(output/'images.csv'),'images':predictions},indent=2),encoding='utf-8')
    report=compare_systems(rows,annotations,predictions,predictions)
    report['synthetic']=True
    report['warning']='Previsões artificiais de teste do avaliador; não são desempenho dos modelos.'
    (output/'comparison_synthetic.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
