import pytest
from scripts.generate_tcc_figures import status_counts


def test_negative_decision_and_error_are_not_no_regions():
    counts = status_counts({"n_images": 10, "status_counts": {
        "predicao_positiva": 2, "sem_regioes": 3,
        "regioes_sem_predicao_positiva": 4, "erro": 1}})
    assert counts["sem_regioes"] == 3
    assert counts["erro"] == 1
    assert counts["regioes_sem_predicao_positiva"] == 4


@pytest.mark.parametrize("counts", [{"erro": 2}, {"unknown": 1}])
def test_inconsistent_statuses_do_not_generate_figure(counts):
    with pytest.raises(ValueError):
        status_counts({"n_images": 1, "status_counts": counts})
