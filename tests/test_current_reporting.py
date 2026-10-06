from src.tcc_reporting import cohort_metrics


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
