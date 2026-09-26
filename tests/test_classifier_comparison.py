import numpy as np
from scripts.compare_classifiers import summarize


def test_common_crop_metrics_use_same_denominator_and_handle_missing_prediction_class():
    result=summarize(np.array([0,0,1,1,1]),np.array([0,1,0,1,1]))
    assert result['confusion_matrix_rows_true_columns_predicted']==[[1,1],[1,2]]
    assert result['accuracy']==0.6
    assert result['negative_recall']==0.5
    assert result['positive_recall']==2/3
    assert summarize(np.array([0,1]),np.array([0,0]))['positive_precision'] is None
