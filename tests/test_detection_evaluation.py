from src.detection_evaluation import match_one_to_one,evaluate_system
from src.detection_evaluation import load_prediction_run
import json
import pytest


def test_maximum_one_to_one_matching_and_duplicate_detection():
    refs=[{'point':[2,2]},{'point':[8,8]}]
    match=match_one_to_one([[0,0,10,10],[0,0,4,4]],refs)
    assert len(match['pairs'])==2  # greedy escolheria só um
    match=match_one_to_one([[0,0,4,4],[0,0,4,4]],refs[:1])
    assert len(match['pairs'])==1 and len(match['unmatched_predictions'])==1


def test_missing_regions_and_errors_keep_false_negatives():
    images=[{'image_id':str(i),'width':20,'height':20,'group_id':str(i)} for i in range(3)]
    annotations={str(i):{'review_status':'reviewed','reviewer':'synthetic','reference_complete':True,
                        'whole_image_label':1,'positives':[{'point':[5,5]}]} for i in range(3)}
    predictions=[{'image_id':'0','status':'sem_regioes','regions':[],'candidates':[]},
                 {'image_id':'1','status':'erro','regions':[],'candidates':[]}]
    result=evaluate_system(images,annotations,predictions)
    assert result['detection']['fn']==3 and result['detection']['n_images']==3
    assert result['whole_image']['n_unresolved']==2
    assert result['whole_image']['confusion_matrix']==[[0,0],[1,0]]


def test_unreviewed_data_has_no_supervised_metrics():
    images=[{'image_id':'x','width':10,'height':10}]
    result=evaluate_system(images,{},[])
    assert result['detection']['recall'] is None
    assert result['whole_image']['accuracy'] is None
    assert result['whole_image']['confusion_matrix'] is None
    assert result['status_counts']=={'erro':1}


def test_prediction_provenance_blocks_synthetic_or_wrong_split(tmp_path):
    path=tmp_path/'predictions.json'
    payload={'schema_version':1,'system':'B','split':'test','manifest_sha256':'a'*64,
             'artifact':{'trained_on_synthetic_data':True},'images':[]}
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError): load_prediction_run(path,'B','test','a'*64)
    payload['artifact']['trained_on_synthetic_data']=False
    path.write_text(json.dumps(payload))
    load_prediction_run(path,'B','test','a'*64)
    with pytest.raises(ValueError): load_prediction_run(path,'B','development','a'*64)
    with pytest.raises(ValueError): load_prediction_run(path,'B','test','b'*64)
