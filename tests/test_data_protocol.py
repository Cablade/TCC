from copy import deepcopy
import numpy as np
from PIL import Image
import pytest
from src import data_protocol as dp


def test_inventory_hash_duplicates_and_group_splits(tmp_path):
    for i in range(4):
        Image.fromarray(np.full((20,30,3),i*40,np.uint8)).save(tmp_path/f'{i}.png')
    (tmp_path/'copy.png').write_bytes((tmp_path/'0.png').read_bytes())
    inv=dp.build_inventory([tmp_path])
    assert inv['summary']['files']==5 and inv['summary']['unique_images']==4
    assert len(inv['exclusions'])==1 and inv['images'][0]['source']=='desconhecida'
    rows=dp.assign_splits(inv['images'],counts={'train':2,'val':1,'test':1},seed=42)
    assert rows==dp.assign_splits(inv['images'],counts={'train':2,'val':1,'test':1},seed=42)
    dp.validate_partitions(rows)
    corrupt=deepcopy(rows); corrupt[0]['sha256']=corrupt[1]['sha256']
    with pytest.raises(ValueError): dp.validate_partitions(corrupt)
    corrupt=deepcopy(rows); corrupt[0]['sha256']=corrupt[1]['sha256'].upper()
    with pytest.raises(ValueError): dp.validate_partitions(corrupt)
    train=next(row for row in rows if row['split']=='train')
    val=next(row for row in rows if row['split']=='val')
    val['group_id']=train['group_id']
    with pytest.raises(ValueError): dp.validate_partitions(rows)


def test_unknown_is_not_negative_and_intersection_checks_entire_box():
    ann={'width':100,'height':100,'review_status':'reviewed','reviewer':'fixture sintética',
         'reference_complete':False,'whole_image_label':None,
         'positives':[{'annotation_id':'p','bbox':[40,40,50,50]}],
         'negative_regions':[{'annotation_id':'n','bbox':[0,0,30,30],'review_status':'reviewed','reviewer':'fixture sintética'}]}
    assert not dp.validate_negative_box([0,0,41,41],ann['positives'])
    assert dp.candidate_label([0,0,41,41],ann)==1
    assert dp.candidate_label([0,0,20,20],ann)==0
    assert dp.candidate_label([60,60,90,90],ann) is None
    ann['review_status']='pending'
    assert dp.candidate_label([40,40,50,50],ann) is None


def test_coordinates_and_contradictory_annotations():
    assert dp.point_in_box([0,0],[0,0,10,10])
    assert not dp.point_in_box([10,5],[0,0,10,10])
    for box in ([0,0,0,1],[-1,0,3,3],[0,0,11,10],[0,0,float('nan'),5]):
        with pytest.raises(ValueError): dp.validate_bbox(box,10,10)
    item={'image_id':'x','width':100,'height':100,'review_status':'reviewed','reviewer':'synthetic',
          'reference_complete':True,'whole_image_label':0,'positives':[{'annotation_id':'p','point':[1,1]}], 'negative_regions':[]}
    with pytest.raises(ValueError):
        dp.validate_annotations({'schema_version':1,'coordinate_convention':'xyxy_half_open','images':[item]})
