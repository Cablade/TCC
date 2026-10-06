from copy import deepcopy

import pytest

from src import data_protocol as dp
from scripts.compare_model_versions import read, save, sha, reuse_subset, reuse_completed_runs


def fixture(tmp_path):
    source=tmp_path/'source';target=tmp_path/'target';source.mkdir();target.mkdir()
    rows=[dict(image_id=str(i),path=f'image_{i}.png',sha256=str(i)*64,
        width=10,height=10,split='development',source_split='val',cohort='kaggle_negative_val') for i in range(2)]
    references=[dict(image_id=str(i),width=10,height=10,review_status='reviewed',reviewer='Caio',
        reference_complete=True,whole_image_label=0,positives=[],negative_regions=[]) for i in range(2)]
    dp.write_manifest(rows,source/'images.csv',list(rows[0]))
    dp.write_manifest(rows[:1],target/'images.csv',list(rows[0]))
    envelope=lambda images:dict(schema_version=1,coordinate_convention='xyxy_half_open',images=images)
    save(source/'annotations.json',envelope(references));save(target/'annotations.json',envelope(references[:1]))
    save(target/'protocol.json',dict(checkpoint={s:dict(sha256='checkpoint_'+s) for s in ('A','B')}))
    for s in ('A','B'):
        (source/s).mkdir()
        save(source/s/'predictions.json',dict(schema_version=1,system=s,split='development',
            manifest_sha256=sha(source/'images.csv'),artifact=dict(sha256='checkpoint_'+s),
            images=[dict(image_id=str(i),status='sem_regioes',regions=[],candidates=[],timings=dict(total_seconds=i+.1)) for i in range(2)]))
    return source,target


def test_subset_preserves_decisions_and_times_and_declares_derivation(tmp_path):
    source,target=fixture(tmp_path)
    original=read(source/'A/predictions.json')
    reuse_subset(target,source)
    derived=read(target/'A/predictions.json')
    assert derived['images']==original['images'][:1]
    assert derived['artifact']==original['artifact']
    assert derived['manifest_sha256']==sha(target/'images.csv')
    assert derived['subset_provenance']['source_predictions_sha256']==sha(source/'A/predictions.json')
    assert derived['subset_provenance']['removed_count']==1


def test_same_ids_with_different_image_or_split_cannot_reuse_predictions(tmp_path):
    source,target=fixture(tmp_path)
    rows=dp.read_manifest(target/'images.csv');rows[0]['source_split']='train'
    dp.write_manifest(rows,target/'images.csv',list(rows[0]))
    with pytest.raises(ValueError,match='partição'):
        reuse_subset(target,source)


def test_changed_reference_is_not_an_unchanged_subset(tmp_path):
    source,target=fixture(tmp_path)
    refs=read(target/'annotations.json');refs['images'][0]['reviewer']='Outro revisor'
    save(target/'annotations.json',refs)
    with pytest.raises(ValueError,match='Referência alterada'):
        reuse_subset(target,source)


def test_duplicate_prediction_ids_are_not_silently_deduplicated(tmp_path):
    source,target=fixture(tmp_path)
    payload=read(source/'A/predictions.json');payload['images'].append(deepcopy(payload['images'][0]))
    save(source/'A/predictions.json',payload)
    with pytest.raises(ValueError,match='IDs da inferência'):
        reuse_subset(target,source)


def test_combined_predictions_preserve_decisions_times_and_source_provenance(tmp_path):
    source,target=fixture(tmp_path)
    original=read(source/'A/predictions.json')
    reuse_completed_runs(target,[source])
    combined=read(target/'A/predictions.json')
    assert combined['images']==original['images'][:1]
    assert combined['combined_provenance']['sources'][0]['predictions_sha256']==sha(source/'A/predictions.json')
    assert read(target/'protocol.json')['training_started'] is False


def test_combined_predictions_reject_reference_changes(tmp_path):
    source,target=fixture(tmp_path)
    reference=read(target/'annotations.json');reference['images'][0]['reviewer']='Outro revisor'
    save(target/'annotations.json',reference)
    with pytest.raises(ValueError,match='Referência alterada'):
        reuse_completed_runs(target,[source])


def test_combined_predictions_reject_overlapping_source_ids(tmp_path):
    source,target=fixture(tmp_path)
    with pytest.raises(ValueError,match='compartilhado'):
        reuse_completed_runs(target,[source,source])


def test_combined_predictions_require_all_target_ids(tmp_path):
    _,target=fixture(tmp_path)
    with pytest.raises(ValueError,match='ausentes'):
        reuse_completed_runs(target,[])
