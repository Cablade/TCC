import pytest
from src.tcc_reporting import cohort_metrics, class_groups


def fixture(labels):
    rows=[]; refs={}
    for index,label in enumerate(labels):
        identifier=str(index)
        rows.append(dict(image_id=identifier,width=100,height=100,group_id=identifier))
        refs[identifier]=dict(image_id=identifier,review_status='reviewed',reviewer='Caio',
            reference_complete=label==0,whole_image_label=label,
            positives=[] if label==0 else [{'point':[90,90]}])
    return rows,refs


def result(identifier,status,class_id=None):
    box={'bbox':[0,0,10,10]}
    regions=[] if class_id is None else [dict(box,class_id=class_id,scores=[.1,.9])]
    return dict(image_id=identifier,status=status,candidates=[box] if regions else [],
        regions=regions,original_decision=None if status=='erro' else int(class_id==1),
        timings={'total_seconds':1.0})


def test_failure_is_not_a_correct_negative_or_an_alarm():
    rows,refs=fixture([0,0])
    metrics,details=cohort_metrics(rows,refs,[result('0','predicao_positiva',1),result('1','erro')])
    assert metrics['n_images']==2
    assert metrics['false_alarm_images']==1
    assert metrics['errors']==1
    assert metrics['rejected_negative_images']==0
    assert details[1]['false_positive_regions'] is None


def test_unmatched_region_is_not_a_false_positive_on_partial_positive_reference():
    rows,refs=fixture([1])
    metrics,details=cohort_metrics(rows,refs,[result('0','predicao_positiva',1)])
    assert metrics['reference_points']==1
    assert metrics['matched_positive_regions']==0
    assert metrics['false_alarm_images'] is None
    assert metrics['false_positive_regions'] is None
    assert details[0]['false_positive_regions'] is None


def test_no_regions_and_classified_negatives_remain_different_states():
    rows,refs=fixture([0,0])
    metrics,_=cohort_metrics(rows,refs,[result('0','sem_regioes'),result('1','regioes_sem_predicao_positiva',0)])
    assert metrics['rejected_negative_images']==2
    assert metrics['status_counts']=={'sem_regioes':1,'regioes_sem_predicao_positiva':1}
    assert metrics['false_positive_regions']==0


def test_negative_sources_are_pooled_with_all_images_and_original_times():
    rows, refs = fixture([1, 0, 0, 0])
    for row, cohort in zip(rows, ['positive_val', 'kaggle_negative_val', 'kaggle_negative_val', 'barcelona_negative']):
        row['cohort'] = cohort
    groups = class_groups(rows, refs)
    assert len(groups['positive']) == 1
    assert [r['image_id'] for r in groups['negative']] == ['1', '2', '3']
    predictions = [result('1', 'sem_regioes'), result('2', 'predicao_positiva', 1), result('3', 'erro')]
    for pred, seconds in zip(predictions, [1, 3, 100]):
        pred['timings']['total_seconds'] = seconds
    metrics, _ = cohort_metrics(groups['negative'], refs, predictions)
    assert metrics['n_images'] == 3
    assert metrics['false_alarm_images'] == 1
    assert metrics['rejected_negative_images'] == 1
    assert metrics['errors'] == 1
    assert metrics['algorithm_seconds'] == 104
    assert metrics['median_seconds'] == 3
    assert [r['cohort'] for r in groups['negative']] == ['kaggle_negative_val', 'kaggle_negative_val', 'barcelona_negative']


def test_class_grouping_does_not_turn_unknown_reference_into_negative():
    rows, refs = fixture([1, 0])
    refs['1']['whole_image_label'] = None
    with pytest.raises(ValueError, match='rótulo'):
        class_groups(rows, refs)
