import numpy as np
import pytest
from src.evaluate import compute_metrics
from src.stats import wilcoxon_paired, confidence_interval_mean


def test_single_class_crop_auc_unavailable():
    result=compute_metrics(np.array([0,0]),np.array([0,1]),np.array([.2,.8]))
    assert result['auc'] is None and result['roc'] is None
    assert result['confusion_matrix']==[[1,1],[0,0]]


def test_statistics_require_explicit_independent_units():
    with pytest.raises(ValueError): wilcoxon_paired([.1,.2],[.2,.3])
    with pytest.raises(ValueError): confidence_interval_mean([.1,.2])
    result=wilcoxon_paired([.1,.2],[.1,.2],independent_group_ids=['a','b'])
    assert result['p_value']==1 and not result['significant']
