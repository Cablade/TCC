import hashlib
import json
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from scripts.prepare_original_negatives import original_members, similarity_groups
from src.class_balance import resolve_class_weights
from src import data_protocol as dp
from src.dataset_policy import supplementary_inventory, validate_active_images, validate_supplementary_crops


def test_augmented_and_traversal_members_are_not_originals():
    original="dataset-master/dataset-master/JPEGImages/BloodImage_00000.jpg"
    augmented="dataset2-master/dataset2-master/TRAIN/NEUTROPHIL/a.jpg"
    assert original_members([augmented, original, original.replace('BloodImage_', '../BloodImage_'),
                             original.replace('BloodImage_', 'example_')]) == [original]


def test_similarity_grouping_is_transitive_for_split_reservation():
    # Mesmo grupo para a cadeia de imagens próximas, mesmo quando extremos diferem.
    groups=similarity_groups([0b0000,0b0011,0b1111,0b1111111100000000],distance=2)
    assert groups[0]==groups[1]==groups[2]
    assert groups[3]!=groups[0]


def test_class_weights_are_capped_without_changing_input_counts():
    labels=[0]*2+[1]*98
    before=list(labels)
    assert resolve_class_weights(labels,maximum=4)=={0:4,1:100/196}
    assert labels==before
    assert resolve_class_weights([0,1,0,1],maximum=4)=={0:1,1:1}


@pytest.mark.parametrize("labels,maximum", [([1,1],4),([0,1],0),([0,1],float('nan')),([0,2],4),([False,1],4)])
def test_invalid_balancing_is_blocked(labels,maximum):
    with pytest.raises(ValueError): resolve_class_weights(labels,maximum=maximum)


def policy_fixture(tmp_path):
    archive=tmp_path/'source.zip'
    member='dataset-master/dataset-master/JPEGImages/BloodImage_00000.jpg'
    with zipfile.ZipFile(archive,'w') as z: z.writestr(member,b'synthetic bytes, no biological image')
    row=dict(image_id='external',path=f'zip://{archive.as_posix()}!{member}',sha256='a'*64,
             width=100,height=100,source='https://www.kaggle.com/datasets/paultimothymooney/blood-cells',
             group_id='group',group_level='imagem_original',split='development',duplicate_of='',original_member=member)
    inventory=tmp_path/'external.csv'; dp.write_manifest([row],inventory,list(row))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    policy=dict(source=row['source'],archive=str(archive),expected_archive_sha256=digest(archive),
                inventory=str(inventory),inventory_sha256=digest(inventory),
                allowed_member_prefix='dataset-master/dataset-master/JPEGImages/',negative_only=True,max_crops_per_image=4)
    path=tmp_path/'policy.json'; path.write_text(json.dumps(policy),encoding='utf-8')
    (tmp_path/'configs').mkdir()
    (tmp_path/'configs/dataset.json').write_text(json.dumps({'output_dir':'primary','source':'synthetic','expected_sha256':'x'}))
    (tmp_path/'primary').mkdir(); dp.write_manifest([],tmp_path/'primary/eligible_inventory.csv')
    (tmp_path/'data/annotations/negative_preselection_v1').mkdir(parents=True)
    (tmp_path/'data/annotations/negative_preselection_v1/development_reservation.json').write_text('{"images":[]}')
    return row,path,inventory


def test_external_source_requires_explicit_policy_and_cannot_enter_test(tmp_path):
    row,policy,_=policy_fixture(tmp_path)
    with pytest.raises(ValueError): validate_active_images([row],root=tmp_path)
    validate_active_images([row],root=tmp_path,supplementary_policy=policy)
    with pytest.raises(ValueError): validate_active_images([{**row,'split':'test'}],root=tmp_path,supplementary_policy=policy)
    with pytest.raises(ValueError): validate_active_images([{**row,'group_id':'changed'}],root=tmp_path,supplementary_policy=policy)


def test_supplementary_inventory_tampering_and_positive_label_blocked(tmp_path):
    _,policy,inventory=policy_fixture(tmp_path)
    with pytest.raises(ValueError):
        validate_supplementary_crops(pd.DataFrame([{'image_id':'external','label':1}]),policy,tmp_path)
    with pytest.raises(ValueError):
        validate_supplementary_crops(pd.DataFrame([{'image_id':'external','label':0}]*5),policy,tmp_path)
    inventory.write_text('tampered',encoding='utf-8')
    with pytest.raises(ValueError): supplementary_inventory(policy,tmp_path)


def test_training_dataset_consumes_every_crop_once_without_resampling(tmp_path):
    import numpy as np
    from PIL import Image
    from src.data_pipeline import make_dataset
    rows=[]
    for i in range(9):
        path=tmp_path/f'{i}.png'; Image.new('RGB',(8,8),(i,0,0)).save(path)
        rows.append({'path':str(path),'label':int(i>1)})
    dataset=make_dataset(pd.DataFrame(rows),image_size=(8,8),batch_size=4,shuffle=True,partition='train')
    seen=[]; labels=[]
    for pixels, truth in dataset.as_numpy_iterator():
        seen.extend(pixels[:,0,0,0].astype(int).tolist()); labels.extend(truth.tolist())
    assert sorted(seen)==list(range(9))
    assert len(labels)==9 and labels.count(0)==2 and labels.count(1)==7
