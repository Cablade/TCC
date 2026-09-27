# Mapa dos comandos

Executar na raiz do projeto. Para o fluxo diário, consultar `docs/guia_treinamento.md`; para decisões científicas, `docs/metodologia.md` e `docs/revisao_geral.md`.

| Finalidade | Arquivos | Situação |
| --- | --- | --- |
| Preparar dados autorizados | `prepare_active_dataset.py`, `prepare_data.py`, `prepare_initial_split.py` | Manter; não sortear outra divisão no transporte. |
| Importar referências | `import_public_annotations.py`, `import_labimed_annotations.py` | Manter; fontes principal e externa separadas. |
| Encontrar/revisar negativos | `fetch_negative_candidates.py`, `preselect_negatives.py`, `review_annotations.py`, `merge_reviewed_reference.py`, `abrir_revisao.cmd`, `review_ui.html` | Manter; não promover ausência de anotação a negativo. |
| Transportar | `prepare_received.py`, `relocate_experiment.py` | Manter; preservam IDs e partições. |
| Treinar | `check_training_ready.py`, `start_training.py`, `train_model_b.py` | Manter; novo treino exige outro nome. |
| Inferir e comparar | `run_model_a.py`, `run_model_b.py`, `compare_systems.py` | Fluxo principal. |
| Diagnosticar classificadores | `compare_classifiers.py` | Auxiliar; recortes comuns não reproduzem os dois sistemas completos. |
| Exportar/figuras | `export_prediction_review.py`, `generate_tcc_figures.py` | Manter; exportar após inferência para não interferir no tempo. |
| Auditar/verificar | `audit_model_a.py`, `audit_experiment.py`, `validate_notebooks.py`, `notebook_support.py` | Manter; suporte dos notebooks não é descartável. |
| Reproduzir escolha geométrica | `tune_region_merging.py` | Histórico útil, não rotina diária. |
| Protótipo de painel | `update_dashboard.py` | Fora do fluxo vigente; caminho de entrada desatualizado e conversão de indisponível em zero. Candidato a arquivamento com `dashboard/`. |

Auditoria sem carregar os modelos:

```powershell
.\.venv\Scripts\python.exe scripts/audit_experiment.py --output experiments/validation/nova_auditoria/audit.json
```

Escolher destino novo. O relatório lista hashes, pareamento, contagens e referências textuais dos scripts. Não trata ausência de referência textual como prova de desuso. Os geradores das galerias recentes citados na conversa não estão nesta cópia; sua ausência é registrada e precisa de recuperação.
