import io
from copy import deepcopy

import numpy as np
from PIL import Image
import pytest

from src.data_protocol import read_image_bytes, validate_annotations, point_in_box
from src.robustness_dataset import (TRANSFORMS, transform_pixels,
    transform_point, transform_bbox, transform_annotation)


@pytest.mark.parametrize('transform', TRANSFORMS)
def test_reference_points_follow_the_actual_pixels_and_boxes(transform):
    pixels=np.zeros((3,5,3),dtype=np.uint8)
    for point in ([0,0],[4,0],[0,2],[4,2],[2,1]):
        pixels[:]=0;x,y=point;pixels[y,x]=[100,20,40]
        moved=transform_point(point,5,3,transform)
        result=transform_pixels(pixels,transform)
        expected=[85,17,34] if transform=='brightness85' else [100,20,40]
        assert result[moved[1],moved[0]].tolist()==expected
        box=transform_bbox([x,y,x+1,y+1],5,3,transform)
        assert point_in_box(moved,box)
        assert box[2]-box[0]==box[3]-box[1]==1


def test_derived_reference_preserves_label_and_original_without_new_review():
    source=dict(image_id='original',width=5,height=3,review_status='reviewed',reviewer='Caio',
        whole_image_label=0,reference_complete=True,positives=[],
        negative_regions=[dict(annotation_id='negative',bbox=[0,0,5,3],review_status='reviewed',reviewer='Caio')])
    snapshot=deepcopy(source)
    derived=transform_annotation(source,'rotated','rotation90')
    assert source==snapshot
    assert derived['negative_regions'][0]['bbox']==[0,0,3,5]
    assert derived['whole_image_label']==0
    assert derived['derived_reference']['new_human_review'] is False
    validate_annotations(dict(schema_version=1,coordinate_convention='xyxy_half_open',images=[derived]))


def test_virtual_image_is_deterministic_and_matches_geometric_pixels(tmp_path):
    pixels=np.arange(45,dtype=np.uint8).reshape(3,5,3)
    path=tmp_path/'source.png';Image.fromarray(pixels).save(path)
    locator='variant://rotation90!'+str(path)
    first=read_image_bytes(locator)
    assert first==read_image_bytes(locator)
    with Image.open(io.BytesIO(first)) as image:
        assert np.array_equal(np.asarray(image),np.rot90(pixels))
    assert len(list(tmp_path.iterdir()))==1


def test_fractional_point_and_chained_variant_are_rejected():
    with pytest.raises(ValueError,match='inteiros'):
        transform_point([.25,1],5,3,'rotation90')
    with pytest.raises(ValueError,match='encadeamento'):
        read_image_bytes('variant://rotation90!variant://flip_horizontal!source.png')
