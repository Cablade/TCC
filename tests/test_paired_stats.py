import numpy as np
import pytest

from src.paired_stats import (decision_value, holm_adjust, image_decision_tests, mcnemar_exact,
                              paired_table, point_metrics, reviewed_precision, stratified_bootstrap)


def rows():
    out = []
    for i in range(6):
        cls = "positive" if i < 3 else "negative"
        out.append(dict(image_id=f"i{i}", system="A", image_class=cls, reference_points=2 if i < 3 else 0,
                        matched_positive_regions=0, positive_regions=0, original_decision="sem_suspeita"))
        out.append(dict(image_id=f"i{i}", system="B", image_class=cls, reference_points=2 if i < 3 else 0,
                        matched_positive_regions=1 if i < 3 else 0, positive_regions=1 if i == 3 else 0,
                        original_decision="1" if i <= 3 else "0"))
    return out


def test_decision_values_keep_errors_unknown():
    assert decision_value("suspeita") == 1 and decision_value(0) == 0 and decision_value("") is None


def test_paired_table_requires_same_ids():
    bad = rows()[:-1]
    with pytest.raises(ValueError):
        paired_table(bad)


def test_point_metrics_and_bootstrap_preserve_strata():
    table = paired_table(rows())
    m = point_metrics(table, np.arange(6))
    assert m["coverage_B"] == 0.5 and m["coverage_A"] == 0.0
    assert m["sensitivity_B"] == 1.0 and m["specificity_B"] == pytest.approx(2 / 3)
    boot = stratified_bootstrap(table, point_metrics, n_resamples=200, seed=1)
    assert boot["n_positive"] == 3 and boot["n_negative"] == 3
    assert boot["metrics"]["coverage_B"]["ci_low"] == boot["metrics"]["coverage_B"]["ci_high"] == 0.5


def test_mcnemar_counts_discordant_pairs_and_excludes_errors():
    result = mcnemar_exact([True, False, False, None], [True, True, True, True])
    assert result["only_B_correct"] == 2 and result["excluded_pairs_with_error"] == 1
    assert result["p_value"] == pytest.approx(0.5)
    tests = image_decision_tests(paired_table(rows()))
    assert tests["positivas"]["only_B_correct"] == 3 and tests["negativas"]["only_A_correct"] == 1


def test_holm_is_monotone():
    adj = holm_adjust({"x": 0.01, "y": 0.04})
    assert adj == {"x": 0.02, "y": 0.04}


def test_reviewed_precision_bounds():
    sample = [{"image_id": "a", "decision": "parasita"}, {"image_id": "a", "decision": "nao_parasita"},
              {"image_id": "b", "decision": "incerto"}, {"image_id": "b", "decision": "parasita"}]
    r = reviewed_precision(sample, n_resamples=100)
    assert r["metrics"]["precision"]["estimate"] == pytest.approx(2 / 3)
    assert r["metrics"]["precision_worst_case"]["estimate"] == 0.5
    assert r["metrics"]["precision_best_case"]["estimate"] == 0.75
    with pytest.raises(ValueError):
        reviewed_precision([{"image_id": "a", "decision": "talvez"}])
