# Comandos

Execute na raiz do projeto. A ordem de uso está no [guia](../docs/guia_treinamento.md) e no [roteiro de correção do viés](../docs/roteiro_correcao_vies.md). Os scripts com SHA-256 em `data/protocol/protocolo_congelado.json` não podem ser alterados.

## Teste final e análise

| Finalidade | Comandos |
| --- | --- |
| Abertura única do teste final | `run_final_test.py` |
| Estatística pareada A × B (bootstrap e McNemar) | `paired_analysis.py` |
| Precisão por amostra revisada | `sample_precision_review.py` |
| Revisão cega de A e B na mesma página | `blind_merge_review.py` |
| Figuras do teste final | `generate_final_test_figures.py` |
| Congelamento do protocolo | `freeze_protocol.py` |

## Modelos e comparações

| Finalidade | Comandos |
| --- | --- |
| Inferência individual | `run_model_a.py`, `run_model_b.py` |
| Demonstração do B: painel no navegador e imagem do teste final | `painel_model_b.py`, `demo_model_b.py` |
| Comparação A × B de desenvolvimento | `compare_model_versions.py` |
| Relatório pareado por imagem | `compare_systems.py` |
| Figuras das comparações de desenvolvimento | `generate_tcc_figures.py` |
| Imagens originais e CSVs após inferência | `export_prediction_review.py` |
| A no domínio original | `check_model_a_original_domain.py` |
| Auditoria do A | `audit_model_a.py` |
| Robustez A × B (histórico do B anterior) | `compare_robustness.py` |
| Negativos externos PBC | `compare_external_negatives.py`, `prepare_external_negative_review.py` |

## Treino do B

| Finalidade | Comandos |
| --- | --- |
| Negativos difíceis murinos (só treino) | `mine_hard_negatives.py`, `prepare_hard_negative_dataset.py` |
| Conferir e treinar | `check_training_ready.py`, `start_training.py`, `train_model_b.py` |
| Resumo das sementes | `summarize_seeds.py` |
| Arquivar o B anterior e promover um treino concluído | `promote_model_b.py` |
| Reserva Barcelona 20 treino / 180 comparação | `prepare_barcelona_split.py` |

## Dados e revisão

| Finalidade | Comandos |
| --- | --- |
| Fontes e partições | `prepare_active_dataset.py`, `prepare_data.py`, `prepare_initial_split.py` |
| Anotações publicadas | `import_public_annotations.py` |
| Negativos e revisão | `prepare_original_negatives.py`, `preselect_negatives.py`, `review_annotations.py`, `merge_reviewed_reference.py`, `review_ui.html`, `abrir_revisao.cmd` |
| Transporte para outro PC | `relocate_experiment.py` |
| Notebooks | `notebook_support.py`, `validate_notebooks.py` |

`notebooks/gerar_rois.py` fica junto dos notebooks porque os preparadores o usam.

Retirados na limpeza de 14/10/2026 e guardados em `archive/limpeza_pos_teste_final_20261014.zip`: `compare_classifiers.py` (comparação auxiliar em recortes, fora dos resultados) e `prepare_received.py` (importação de entregas antigas de uma fonte; o transporte atual usa `relocate_experiment.py`). Os scripts de LABIMED e do B anterior estão nos ZIPs anteriores de `archive/`.
