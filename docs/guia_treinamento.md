# Guia da rotina atual

Execute na pasta que contém `README.md`, `src` e `scripts`. Use `.venv/Scripts/python.exe`; o ambiente local foi corrigido para Python oficial 3.11.9, preservando TensorFlow/Keras 2.15.

## Treino concluído em 06/10/2026

O B foi retreinado com os dados anteriores mais **20 negativas originais Barcelona (80 recortes)**. Foram 17 épocas, melhor época 10 pelo menor `val_loss` (0,21533), cerca de 15,2 minutos em CPU. Limite configurado de 40 épocas, paciência 7, lote 8, pesos por classe; cada recorte uma vez por época, sem oversampling/undersampling.

| Modelo | Caminho atual |
| --- | --- |
| A original, preservado | `models/model_a/model_trained.keras` |
| B retreinado | `experiments/runs/b_val_01/best.keras` |

Dados do B atual: `data/processed/b_next/{images.csv,annotations.json,crops.csv}`. Treino: 4.381 recortes (3.053 positivos/1.328 negativos). Validação: 1.070 (740 positivos/330 negativos). `b_real_01` contém os arquivos dos recortes anteriores compartilhados; não apagar essa pasta. Entradas, revisões, configurações, histórico e metadados do treinamento foram preservados junto ao B.

O B anterior foi arquivado integralmente em `archive/b_anterior_barcelona20_20261006/b_val_01/`, com hashes conferidos. Resultados e figuras desse checkpoint estão identificados como históricos. A comparação usa somente A original e o B atual.

## Comparação após o novo treino

Mesmo lote de **367 imagens** para ambos: 114 positivas, 73 negativas Kaggle da validação e 180 negativas Barcelona. As 20 Barcelona usadas no treino ficam excluídas por ID, bytes, pixels e grupo. A divisão está em `data/protocol/barcelona_split_20261006/`; configuração em `configs/comparison_a_vs_b.json`.

Nova inferência dos dois modelos, sem reutilizar previsões do B anterior. Saída atual: `experiments/comparison/a_vs_b_barcelona20_20261006/`. Essa comparação é de desenvolvimento já examinado; as 105 imagens do teste final continuam reservadas. As fontes são apresentadas separadamente, sem acurácia global misturando células humanas enquadradas e campos murinos positivos.

Para uma nova execução, escolha uma pasta que ainda não exista:

```powershell
$pythonTcc = '.\.venv\Scripts\python.exe'
& $pythonTcc scripts/compare_model_versions.py --output-dir experiments/comparison/nova_comparacao
```

Para atualizar somente tabelas, figuras e a página de acesso, depois das inferências concluídas:

```powershell
& $pythonTcc scripts/generate_tcc_figures.py --all
```

O gerador atualiza relatórios do checkpoint atual; preserva avaliações de checkpoints anteriores como histórico. Página de acesso: `tcc/figuras/index.html`. Não atribuir o diagnóstico antigo das 200 Barcelona ou a robustez antiga ao B retreinado. As variações antigas não foram executadas novamente nesta etapa.

## Antes de qualquer outro treino

O treinamento solicitado já terminou. Não executar novamente apenas para comparar. Se houver outro experimento, escolha nome novo, confira dados e ambiente com `scripts/start_training.py --check-only` e mantenha o teste final reservado. `promote_model_b.py` só arquiva/troca modelos após conferir um treinamento real concluído e seus hashes; nunca substituir um modelo por uma execução parcial.

## Transportar

Copie código, configurações, dois modelos ativos, revisões, fontes e recortes usados. `b_next` referencia recortes em `b_real_01`; as duas pastas são necessárias. Não copie `.venv`: crie um ambiente Python 3.11 de 64 bits no destino, conforme [ambiente](ambiente.md), e confira as dependências fixadas. Manifestos com caminhos absolutos exigem ajuste e revalidação. Cópias históricas de entradas do treinamento não devem ser alteradas.

A acurácia de recortes não é desempenho de imagens inteiras. Consulte [dados](dados.md), [metodologia](metodologia.md) e [estado](status.md).
