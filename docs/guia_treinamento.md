# Guia da rotina atual

Execute na pasta que contém `README.md`, `src` e `scripts`. O ambiente deste PC está instalado; consulte [ambiente](ambiente.md) para outro computador.

## O treino já terminou

Use A em `models/model_a/model_trained.keras` e B em `experiments/runs/b_val_01/best.keras`. O B atual foi treinado com `data/processed/b_real_01/`, preservado. Foi preparado `data/processed/b_next/` com 20 novas negativas Barcelona (80 recortes): **nenhum novo treino foi iniciado**. Preserve histórico, configuração, hashes e entradas na pasta do B.

## Comparar os dois modelos

Escolha uma pasta nova, sem sobrescrever:

```powershell
$pythonTcc = '.\.venv\Scripts\python.exe'
& $pythonTcc scripts/compare_model_versions.py --output-dir experiments/comparison/nova_comparacao
```

O comando avalia os mesmos 367 IDs em A/B: 114 positivas, 73 negativas Kaggle da validação e 180 negativas Barcelona. As 20 reservadas para próximo treino ficam excluídas, por ID, bytes, pixels e grupo. `configs/comparison_a_vs_b.json` registra a reserva e seus hashes. São dados de desenvolvimento já examinados, não teste final independente. Produz relatório, tabelas e figuras por fonte; não abre o teste final. `--reuse-a` só aceita A concluído com os mesmos IDs, manifesto e checkpoint. `--reuse-sources` combina previsões já concluídas somente com conteúdo, referências e configurações coincidentes, preservando decisões e tempos. Foi assim que o lote atual foi montado, sem nova inferência ou treinamento. `--reuse-run` permite derivar um subconjunto compatível.

Regerar somente o relatório de uma comparação concluída:

```powershell
& $pythonTcc scripts/compare_model_versions.py --output-dir experiments/comparison/a_vs_b_barcelona --summarize-only
```

## Se houver outro treino

O perfil `configs/experiment_b_original_negatives.json` já aponta para `data/processed/b_next/`, com 4.381 recortes de treino (3.053 positivos/1.328 negativos) e 1.070 de validação. As duas fontes negativas originais são autorizadas por `configs/negative_sources_originals.json`, com somente as 20 Barcelona aceitas no treino. O próximo nome preparado é `b_next`. Altere se já existir. O usuário pediu somente preparo nesta etapa: não executar treinamento agora.

```powershell
& $pythonTcc scripts/start_training.py --experiment configs/experiment_b_original_negatives.json --check-only
if ($LASTEXITCODE -ne 0) { throw 'Há pendências; não iniciar treino.' }
```

Só execute sem `--check-only` após decidir iniciar outro treino. Limite de 40 épocas, paciência 7, lote 8; todos os recortes uma vez por época, pesos por classe limitados a 4. O checkpoint atual não incorpora os 80 novos recortes. Quando houver substituição do B, executar A/B novamente no lote separado; previsões antigas não são válidas para pesos novos.

## Transportar

Copie código, configurações, modelos, dados e ZIPs originais referenciados nos manifestos. Crie outro ambiente no destino; não copie `.venv`. Ajuste e confira caminhos absolutos com `scripts/relocate_experiment.py --help`. O treinamento guarda cópias históricas imutáveis das entradas.

Acurácia de recortes não é desempenho de imagens inteiras. Consulte [dados](dados.md), [metodologia](metodologia.md) e [estado](status.md).

## Ampliar os negativos

Dos 366 originais Kaggle, 293 participaram do treino e 73 estão na validação. Não acrescentar os 293 à comparação independente. Novos originais exigem conferência de procedência, duplicatas e ausência visual de parasita.

As 12.515 versões aumentadas do fornecedor não trazem mapeamento explícito para seus originais no ZIP; não usar sua partição chamada TEST como prova de separação do nosso treino. Auditoria: `data/annotations/kaggle_originals_20261005/augmentation_audit.json`. Variações que criarmos apenas das 73 imagens de validação podem integrar um teste adicional de robustez, contado por original e relatado separadamente; não equivalem a novos campos ou pacientes.

## Robustez com positivos e negativos

`scripts/compare_robustness.py` usa somente os 114 positivos e 73 negativos originais do lote anterior preservado em `a_vs_b`. Aplica as mesmas três condições a ambas as classes: rotação 90° anti-horária, espelho horizontal e brilho × 0,85. São 561 versões mais 187 originais (748 vistas), com apenas 187 unidades originais e sem independência biológica comprovada. Barcelona não foi acrescentada a esse ensaio já concluído.

A e B continuam congelados. A comparação principal atual está em `a_vs_b_barcelona`; o relatório de robustez anterior fica em `experiments/comparison/robustez_a_vs_b` e `tcc/figuras/robustez_a_vs_b`. Rótulos são herdados, pontos/caixas transformados; nada foi confirmado por uma nova revisão humana. Imagens virtuais evitam multiplicar arquivos de pixels em disco. O comando padrão prepara, executa A/B e gera o relatório; `--prepare-only` só prepara e `--summarize-only` atualiza o relatório concluído.

```powershell
& $pythonTcc scripts/compare_robustness.py
```

Não repetir o comando em uma pasta existente. A tabela apresenta cada condição separadamente e mudanças de decisão em relação ao original; não somar versões como novas lâminas, pacientes ou evidência independente. A referência de pontos permanece parcial. Este teste adicional usa desenvolvimento já examinado, sem modificar treino nem abrir teste final.

## Negativos externos originais novos

Caio confirmou as 200 imagens PBC/Barcelona como sem parasita visível e depois autorizou reservar 20 para os negativos do próximo treino, mantendo 180 na comparação junto ao Kaggle. A reserva reproduzível (semente 42; 2 ou 3 por tipo celular, sem consultar previsões) está em `data/protocol/barcelona_split_20261006/{training.csv,comparison.csv,assignments.csv,authorization.json}`. `prepare_barcelona_split.py` realizou somente preparo, sem treino. As revisões originais e o diagnóstico das 200 em `barcelona_a_vs_b` são históricos preservados. Este lote usa células individuais próximas de 360×363 e não representa campos inteiros equivalentes às positivas.

O comando `scripts/compare_external_negatives.py` prepara, executa os dois modelos e gera figuras/CSVs. Para uma pasta somente preparada, use `--run-prepared`; para atualizar relatórios concluídos, `--summarize-only`. Não iniciar outra inferência simultânea durante medição de tempo. O protocolo exige a aprovação e seus hashes, preserva todos os IDs e distingue erro de negativo correto.

## Atualizar todas as figuras depois das inferências

```powershell
& $pythonTcc scripts/generate_tcc_figures.py --all
```

O comando só gera relatórios/figuras, sem treinar ou executar redes. Atualiza a comparação atual de 367 imagens, a robustez anterior de 187 originais e o diagnóstico histórico das 200 Barcelona. A página de acesso fica em `tcc/figuras/index.html`. Para atualizar uma avaliação específica, informe `--comparison experiments/comparison/robustez_a_vs_b` ou `barcelona_a_vs_b` (padrão atual: `a_vs_b_barcelona`).
