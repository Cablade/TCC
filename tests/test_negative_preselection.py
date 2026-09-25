"""Sugestões permanecem desconhecidas até a confirmação humana explícita."""
import hashlib
import json

import pytest

from scripts.preselect_negatives import select_images, safe_distance
from scripts.review_annotations import ReviewStore
from src import data_protocol as dp


def test_selection_is_reproducible_and_excludes_evaluation():
    rows=[{'image_id':str(i),'path':f'zip://source.zip!{folder}/x{i}.jpg','split':split}
          for i,(folder,split) in enumerate([('train',''),('train',''),('test',''),
                                             ('train','test'),('train','val')])]
    result=select_images(rows,2,42)
    assert result==select_images(rows,2,42)
    assert {r['image_id'] for r in result}=={'0','1'}
    assert all(r['split']=='development' for r in result)
    with pytest.raises(ValueError): select_images(rows,3,42)


def test_margin_excludes_nearby_positive_even_outside_crop():
    assert not safe_distance([100,100,200,200],[{'point':[250,150]}],800,800)
    assert safe_distance([100,100,200,200],[{'point':[700,700]}],800,800)


def batch(tmp_path):
    rows=[{'image_id':'one','path':'unused.png','sha256':'a'*64,'width':100,'height':100,
           'source':'synthetic','group_id':'one','group_level':'imagem_original','split':'development'}]
    inventory=tmp_path/'inventory.csv'; dp.write_manifest(rows,inventory)
    payload=dp.annotation_template(rows)
    payload['images'][0].update(review_status='reviewed',reviewer='Synthetic source',
                               whole_image_label=1,positives=[{'annotation_id':'p','point':[90,90]}])
    reference=tmp_path/'reference.json'; reference.write_text(json.dumps(payload),encoding='utf-8')
    queue={'source_annotation_sha256':hashlib.sha256(reference.read_bytes()).hexdigest(),
           'candidates':[{'candidate_id':'s1','image_id':'one','source_sha256':'a'*64,
                          'bbox':[0,0,20,20],'review_status':'pending','label':None}]}
    suggestions=tmp_path/'suggestions.json'; suggestions.write_text(json.dumps(queue),encoding='utf-8')
    return inventory,reference,tmp_path/'reviewed.json',suggestions


def test_suggestion_never_becomes_a_label_just_by_opening(tmp_path):
    paths=batch(tmp_path)
    store=ReviewStore(*paths)
    assert len(store.suggestions)==1
    assert dp.candidate_label([0,0,20,20],store.annotation('one')) is None
    assert not paths[2].exists()
    with pytest.raises(ValueError):
        store.change({'image_id':'one','bbox':[0,0,20,20],'reviewer':'test','confirmed':False})
    store.change({'image_id':'one','bbox':[0,0,20,20],'reviewer':'Synthetic tester','confirmed':True})
    assert dp.candidate_label([0,0,20,20],store.annotation('one'))==0
    assert store.annotation('one')['reference_complete'] is False
    assert json.loads(paths[3].read_text())['candidates'][0]['label'] is None


@pytest.mark.parametrize('key,value',[('label',0),('review_status','reviewed'),
                                     ('source_sha256','b'*64),('bbox',[80,80,100,100])])
def test_rejects_wrong_labels_hashes_and_positive_overlap(tmp_path,key,value):
    paths=batch(tmp_path)
    queue=json.loads(paths[3].read_text()); queue['candidates'][0][key]=value
    paths[3].write_text(json.dumps(queue),encoding='utf-8')
    with pytest.raises(ValueError): ReviewStore(*paths)
