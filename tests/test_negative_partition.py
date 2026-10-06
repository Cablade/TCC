from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from src import data_protocol as dp
from src.negative_partition import split_barcelona, assert_disjoint_training_comparison
from src.dataset_policy import validate_active_images
from tests.test_original_negatives import policy_fixture


def originals():
    return [dict(image_id=str(i), sha256=f'{i:064x}', decoded_sha256=f'{i+200:064x}',
                 group_id=str(i), cell_type=f'type_{i//25}', split='development',
                 path=f'image_{i}.jpg') for i in range(200)]


def test_split_is_reproducible_stratified_and_disjoint_even_if_input_order_changes():
    rows=originals(); before=deepcopy(rows)
    result=split_barcelona(rows)
    training=[r for r in result if r['split']=='train']
    comparison=[r for r in result if r['split']=='development']
    assert len(training)==20 and len(comparison)==180
    assert Counter(Counter(r['cell_type'] for r in training).values())=={2:4,3:4}
    assert {r['image_id'] for r in split_barcelona(list(reversed(rows))) if r['split']=='train'}=={r['image_id'] for r in training}
    assert rows==before
    assert_disjoint_training_comparison(training,comparison)


@pytest.mark.parametrize('key',['image_id','sha256','decoded_sha256','group_id'])
def test_duplicate_or_related_images_cannot_be_partitioned_as_independent(key):
    rows=originals(); rows[1][key]=rows[0][key]
    with pytest.raises(ValueError,match='repetidos'): split_barcelona(rows)


@pytest.mark.parametrize('key',['image_id','sha256','decoded_sha256','group_id','path'])
def test_training_overlap_is_blocked_for_comparison(key):
    training=originals()[:1]; comparison=originals()[1:2]
    comparison[0][key]=training[0][key]
    with pytest.raises(ValueError,match='compartilham'): assert_disjoint_training_comparison(training,comparison)


def test_augmented_descendant_of_training_image_cannot_enter_comparison():
    rows=originals()
    rows[1]['original_image_id']=rows[0]['image_id']
    with pytest.raises(ValueError,match='Versão'): assert_disjoint_training_comparison(rows[:1],rows[1:2])


def barcelona_policy(tmp_path):
    _,kaggle,_=policy_fixture(tmp_path)
    rows=[]; image_root=tmp_path/'images'; image_root.mkdir()
    for i in range(200):
        path=image_root/f'{i}.jpg'; path.write_bytes(f'synthetic fixture {i}'.encode())
        rows.append(dict(image_id=f'b{i}',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            path=str(path),width=100,height=100,source='https://data.mendeley.com/datasets/snkd93bnjr/1',
            group_id=f'b{i}',group_level='imagem_original',split='train' if i<20 else 'development',duplicate_of=''))
    paths={key:tmp_path/f'{key}.json' for key in ('approval','reviewed')}
    paths['partition_manifest']=tmp_path/'partition.csv'; paths['inventory']=tmp_path/'train.csv'
    dp.write_manifest(rows,paths['partition_manifest'],list(rows[0]))
    dp.write_manifest(rows[:20],paths['inventory'],list(rows[0]))
    paths['approval'].write_text(json.dumps(dict(status='complete',training_allowed=True,training_image_ids=[r['image_id'] for r in rows[:20]])))
    paths['reviewed'].write_text(json.dumps(dict(schema_version=1,coordinate_convention='xyxy_half_open',images=[dict(
        image_id=r['image_id'],width=100,height=100,review_status='reviewed',reviewer='Caio',
        whole_image_label=0,reference_complete=True,positives=[],negative_regions=[]) for r in rows[:20]])))
    policy=dict(source=rows[0]['source'],negative_only=True,allowed_splits=['train'],max_crops_per_image=4,image_root='images')
    for key,path in paths.items():
        policy[key]=str(path); policy[key+'_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    path=tmp_path/'barcelona_policy.json'; path.write_text(json.dumps(policy))
    bundle=tmp_path/'bundle.json'; bundle.write_text(json.dumps({'policies':[str(kaggle),str(path)]}))
    return rows,bundle


def test_only_authorized_twenty_barcelona_can_train_and_not_validate_or_test(tmp_path):
    rows,bundle=barcelona_policy(tmp_path)
    validate_active_images(rows[:20],root=tmp_path,supplementary_policy=bundle)
    with pytest.raises(ValueError,match='fora do inventário'):
        validate_active_images(rows[20:21],root=tmp_path,supplementary_policy=bundle)
    for split in ('val','test','development'):
        with pytest.raises(ValueError,match='não podem integrar'):
            validate_active_images([{**rows[0],'split':split}],root=tmp_path,supplementary_policy=bundle)
    Path(rows[0]['path']).write_bytes(b'tampered')
    with pytest.raises(ValueError,match='pixels alterados'):
        validate_active_images(rows[:1],root=tmp_path,supplementary_policy=bundle)
