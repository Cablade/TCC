# Guia da rotina atual

Execute na pasta que contém `README.md`, `src` e `scripts`, com `.venv/Scripts/python.exe` (Python oficial 3.11.9, TensorFlow/Keras 2.15; ver [ambiente](ambiente.md)).

```powershell
$py = '.\.venv\Scripts\python.exe'
$env:PYTHONUTF8 = '1'
```

## Situação

O protocolo está congelado (`data/protocol/protocolo_congelado.json`) e o teste final já foi aberto (`data/protocol/teste_aberto.json`). `run_final_test.py` recusa uma segunda abertura. Não treine de novo, não troque o B em `experiments/runs/b_atual/` e não altere nenhum dos 21 arquivos com hash registrado: qualquer mudança neles é desvio de protocolo e precisa ser declarada no texto.

| Modelo | Caminho |
| --- | --- |
| A, como entregue | `models/model_a/model_trained.keras` |
| B avaliado (`b_hardneg_s42`) | `experiments/runs/b_atual/best.keras` |
| Sementes 123, 456, 789, 1024 | `experiments/runs/b_hardneg_s*/` |

B: EfficientNet-B0, AdamW com cosseno, seleção da época de menor `val_loss` (época 9 na semente 42). Dados em `data/processed/b_hardneg/`: 4.898 recortes de treino (3.053 positivos/1.845 negativos, incluindo 517 negativos difíceis murinos) e 1.070 de validação. Cada recorte uma vez por época, pesos por classe, sem oversampling.

## Conferir o protocolo

Para conferir que nada congelado mudou, compare os SHA-256 de `protocolo_congelado.json` com os arquivos (é o primeiro passo de `run_final_test.py`). Faça isso antes de qualquer commit que mexa em `src/`, `scripts/`, `docs/metodologia.md` ou `docs/plano_estatistico.md`.

## Etapas e saídas

O passo a passo com os comandos usados está no [roteiro de correção do viés](roteiro_correcao_vies.md).

| Etapa | Script | Saída |
| --- | --- | --- |
| Negativos difíceis (só treino) | `mine_hard_negatives.py`, `prepare_hard_negative_dataset.py` | `data/annotations/hard_negatives_20261013/`, `data/processed/b_hardneg/` |
| Treino com cinco sementes | `train_model_b.py`, `summarize_seeds.py` | `experiments/runs/b_hardneg_s*` |
| Promoção da semente 42 | `promote_model_b.py` | `experiments/runs/b_atual/` (anterior em `archive/b_vies_origem_20261013/`) |
| Comparação de desenvolvimento | `compare_model_versions.py` | `experiments/comparison/a_vs_b_hardneg_20261013/` |
| Precisão por amostra cega | `sample_precision_review.py`, `blind_merge_review.py` | `data/annotations/precision_B_val_20261013/` |
| A no domínio original | `check_model_a_original_domain.py --no-overlays` | `experiments/validation/model_a_original_domain_20261013/` |
| Congelamento | `freeze_protocol.py` | `data/protocol/protocolo_congelado.json` |
| Teste final | `run_final_test.py`, `paired_analysis.py` | `experiments/final_test_20261014/` |
| Precisão e kappa no teste | `sample_precision_review.py`, `blind_merge_review.py` | `data/annotations/precision_teste_final_20261014/` |
| Figuras do teste final | `generate_final_test_figures.py` | `tcc/figuras/teste_final_20261014/` |

As figuras só leem resultados já gravados; para refazê-las:

```powershell
& $py scripts/generate_final_test_figures.py
```

`generate_tcc_figures.py --all` continua gerando as páginas das comparações de desenvolvimento.

## Comparações de desenvolvimento

`a_vs_b_barcelona20_20261006` (B antes da correção) e `a_vs_b_hardneg_20261013` (B corrigido) usam as mesmas 367 imagens: 114 campos murinos de validação, 73 Kaggle e 180 Barcelona. Ficam no projeto porque mostram o viés de origem e a correção, e a figura 04 do teste final usa as duas. São desenvolvimento já examinado, não teste.

## Transportar

Copie código, configurações, os dois modelos, revisões, fontes e as três pastas de recortes (`b_real_01`, `b_next`, `b_hardneg`): o manifesto do B aponta para recortes das três. Não copie `.venv`; crie o ambiente no destino conforme [ambiente](ambiente.md). Manifestos com caminhos absolutos exigem `relocate_experiment.py` e nova conferência dos hashes.

A acurácia em recortes não é desempenho em imagens inteiras. Consulte [dados](dados.md), [metodologia](metodologia.md) e [estado](status.md).
