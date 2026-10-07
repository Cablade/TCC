# Comandos em uso

Execute na raiz do projeto. Consulte o [guia atual](../docs/guia_treinamento.md).

| Finalidade | Comandos |
| --- | --- |
| Comparação A original × B atual | `compare_model_versions.py` |
| Robustez adicional A × B | `compare_robustness.py` |
| Negativos externos PBC aprovados | `compare_external_negatives.py` |
| Novos originais PBC para revisão | `prepare_external_negative_review.py` |
| Reserva Barcelona 20 treino / 180 comparação, sem treinar | `prepare_barcelona_split.py` |
| Arquivar B anterior e promover treino concluído | `promote_model_b.py` |
| Inferência individual | `run_model_a.py`, `run_model_b.py` |
| Relatório pareado | `compare_systems.py` |
| Figuras atuais | `generate_tcc_figures.py` |
| Imagens originais e CSVs após inferência | `export_prediction_review.py` |
| Conferir/treinar outra execução | `check_training_ready.py`, `start_training.py`, `train_model_b.py` |
| Fontes e partições | `prepare_active_dataset.py`, `prepare_data.py`, `prepare_initial_split.py` |
| Anotações publicadas | `import_public_annotations.py` |
| Negativos e revisão | `prepare_original_negatives.py`, `preselect_negatives.py`, `review_annotations.py`, `merge_reviewed_reference.py`, `review_ui.html` |
| Transporte | `relocate_experiment.py` |
| Classificadores em recortes (auxiliar) | `compare_classifiers.py` |
| Auditoria do A | `audit_model_a.py` |
| Exploração de notebooks | `notebook_support.py`, `validate_notebooks.py` |

Scripts específicos do B anterior (`audit_experiment.py`, `tune_region_merging.py`, `recover_reviews.py`) estão no ZIP histórico. Não há terceiro modelo na comparação. Comandos ocasionais de revisão, transporte e verificação continuam necessários.

`prepare_received.py` permanece como compatibilidade para entregas antigas de uma fonte e está coberto por teste. Para os dados atuais com dois ZIPs, use `relocate_experiment.py`.

O B atual foi retreinado com `data/processed/b_next/`, que compartilha recortes anteriores e acrescenta 80 negativos de 20 Barcelona. A comparação vigente usa `configs/comparison_a_vs_b.json`: 114 positivas, 73 negativas Kaggle e 180 Barcelona, em `a_vs_b_barcelona20_20261006`. `compare_model_versions.py --reuse-sources` é uma opção histórica para combinar previsões com o mesmo checkpoint; não usar previsões do B arquivado para o B atual. A comparação nova executa os dois modelos novamente. Consulte o guia antes de outra execução.

Os comandos específicos de LABIMED e seus testes estão em `archive/labimed_historico_20261005.zip`, junto aos dados e resultados antigos. O fluxo de comparação atual não usa essa fonte.

Após a limpeza de 06/10/2026, `generate_tcc_figures.py --all` considera somente relatórios disponíveis com os mesmos hashes dos dois checkpoints da comparação atual. Não exige pastas históricas. Os utilitários legados `notebooks/analisar_anotacoes.py` e `visualizar_anotacoes.py` foram arquivados; `gerar_rois.py` permanece porque os preparadores o utilizam.

A apresentação de `generate_tcc_figures.py` usa dois grupos: imagens positivas e negativas. `report.json` conserva `summary` por origem e acrescenta `class_summary`; `summary.csv` resume as duas classes e `per_image.csv` mantém origem e classe. Não há novo treino nem inferência para reorganizar essas figuras.
