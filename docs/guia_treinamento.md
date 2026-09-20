# Guia prático: treinar o B e comparar com o A

Comece pelo teste rápido da seção 2. Ele já funciona nesta máquina. O treinamento com imagens reais vem depois de revisar as anotações e definir as partições. **Somente B será treinado; A usa os pesos originais fixos.**

## 1. Abrir o projeto no PowerShell

Abra o PowerShell ou o terminal do editor e cole:

```powershell
Set-Location 'C:\Users\PCZAO\Documents\Caio\TCC\TCC'
$pythonTcc = '.\.venv\Scripts\python.exe'
& $pythonTcc --version
```

O resultado esperado neste ambiente é Python 3.11.15. A pasta correta tem `src`, `scripts`, `configs` e `notebooks`. Existem duas pastas TCC no caminho. Não é necessário ativar o ambiente: os comandos chamam diretamente o Python da `.venv`.

O ambiente já está preparado nesta máquina. Se abrir outro terminal, repita o bloco acima para definir o diretório e `$pythonTcc`. Para outra máquina, use Python 3.10/3.11 e as dependências do [README](../README.md).

## 2. Fazer um treino de teste agora

```powershell
& $pythonTcc scripts/train_model_b.py --smoke
```

Esse comando gera dados artificiais, constrói o B sem baixar pesos, treina uma etapa, salva o modelo, reabre o arquivo e faz inferência. Não usa as lâminas reais e não mede a qualidade do TCC.

Ao terminar, o terminal mostra `run_dir`, `checkpoint` e `synthetic: true`. A saída fica em uma pasta nova com data/hora, como `experiments/runs/b_smoke_YYYYMMDD_HHMMSS/`.

| Arquivo gerado | Para que serve |
| --- | --- |
| `best.keras` | Modelo salvo e selecionado pela validação |
| `config.json` | Configuração realmente utilizada |
| `history.json` e `epochs.csv` | Histórico de perda e acurácia durante o treino |
| `metadata.json` | Semente, versões, tempo, hardware, hashes e época escolhida |
| `smoke.json` | Confirmação da recarga e inferência sintética |

O teste terminou corretamente quando o comando retorna ao terminal sem erro e `smoke.json` registra `reload_equal: true`. Esse checkpoint é apenas técnico; o fluxo bloqueia seu uso como modelo treinado para o teste final.

Opcionalmente, execute a suíte de verificações:

```powershell
& $pythonTcc -m pytest -q
```

## 3. Entender o que falta para treinar de verdade

O treino real precisa destes arquivos, que têm funções diferentes:

| Entrada | Conteúdo |
| --- | --- |
| Inventário | Quais imagens existem, seus caminhos, hashes, dimensões e grupos |
| Manifesto de partições (`images.csv`) | Quais imagens/grupos pertencem a treino, validação, teste ou desenvolvimento |
| Anotações (`reference.json`) | Positivos/negativos revisados, coordenadas, cobertura e responsável |
| Manifesto de recortes (`crops.csv`) | Recortes gerados pelo localizador B, seus rótulos e imagens de origem |

Hoje existe o inventário de 106 JPGs únicos em `data/protocol/all_available_jpg/inventory.csv`. O lote 1 tem seu manifesto separado em `data/splits/lote_1/images.csv`, com 58 imagens somente em `development`. O arquivo `data/annotations/lote_1_pending.json` é um template **sem marcações confiáveis**. Usá-lo agora na extração produz candidatos sem rótulo, não um conjunto pronto para treinar.

Antes de seguir, alguém qualificado precisa revisar as marcações e confirmar os grupos de lâmina/animal. O projeto define o formato JSON, mas ainda não oferece uma interface gráfica de anotação. O formato e as coordenadas estão em [Dados e anotações](../data/README.md). Alterar apenas `pending` para `reviewed` não substitui essa revisão.

Imagens já usadas para desenvolvimento não podem virar teste final. No inventário conjunto, as cópias podem ter outro ID canônico: preserve o vínculo pelo SHA-256. A independência dos 48 JPGs adicionais ainda precisa ser confirmada.

## 4. Preparar os arquivos do experimento real

**As seções 4 a 8 dependem dos dados revisados. Os nomes abaixo são os arquivos de trabalho a preparar, não arquivos já completos.**

Prepare um inventário em `data/protocol/experimento/inventory.csv`, com os grupos confirmados, e um CSV `data/protocol/experimento/grupos.csv` com as colunas `group_id,split`. Use os IDs reais desse inventário e as partições `train`, `val`, `test` ou `development`. Não defina percentuais antes de verificar grupos e classes.

Para gerar o inventário com grupos reproduzíveis, `scripts/prepare_data.py inventory` aceita `--metadata`: um CSV com `path,source,group_id,group_level`. O `path` deve corresponder exatamente ao caminho local/ZIP inventariado; `group_level` aceita `animal`, `lamina` ou `imagem_original`. Registre a origem das identificações. Consulte `--help` e mantenha esse CSV junto dos registros do experimento.

Com o inventário e as atribuições prontos:

```powershell
& $pythonTcc scripts/prepare_data.py split --inventory data/protocol/experimento/inventory.csv --assignments data/protocol/experimento/grupos.csv --output-dir data/splits/experimento --seed 42
```

O comando cria `data/splits/experimento/images.csv` e o registro da divisão. Grupos não atribuídos ficam em `development`; eles não serão automaticamente usados para treinar.

Se ainda não houver anotações para **esses mesmos IDs**, crie um template novo e providencie sua revisão:

```powershell
& $pythonTcc scripts/prepare_data.py annotation-template --inventory data/splits/experimento/images.csv --output data/annotations/experimento_reference.json
```

Esse comando não sobrescreve arquivo existente. Não misture anotações do manifesto isolado do Lote 1 com IDs do inventário conjunto sem reconciliá-los. Depois da revisão:

```powershell
& $pythonTcc scripts/prepare_data.py validate --splits data/splits/experimento/images.csv --annotations data/annotations/experimento_reference.json
```

A validação confere estrutura e separação; ela não certifica a correção biológica das marcações.

## 5. Gerar os recortes do B

Primeiro, fixe os parâmetros de localização usando desenvolvimento/validação. A configuração fica em [configs/model_b.yaml](../configs/model_b.yaml); os valores atuais de localização são provisórios.

Para conferir a extração sem gravar recortes:

```powershell
& $pythonTcc notebooks/gerar_rois.py --image-manifest data/splits/experimento/images.csv --annotations data/annotations/experimento_reference.json --config configs/model_b.yaml --output-dir data/processed/b_real_01 --dry-run
```

Quando os dados e parâmetros estiverem preparados, retire `--dry-run`:

```powershell
& $pythonTcc notebooks/gerar_rois.py --image-manifest data/splits/experimento/images.csv --annotations data/annotations/experimento_reference.json --config configs/model_b.yaml --output-dir data/processed/b_real_01
```

A saída contém os recortes, `crops.csv` e `extraction_report.json`. Candidatos sem rótulo confiável não viram negativos. O classificador exige recortes das duas classes em **treino e validação**. Se `labeled_crops` for zero, ainda não há dados utilizáveis para o treino.

O extrator percorre as partições presentes no manifesto; os recortes de teste nunca entram no `fit`. Não use o conteúdo ou os resultados de teste para ajustar a localização. Planeje e congele as escolhas usando apenas desenvolvimento/validação antes de executar a extração final.

## 6. Treinar com os recortes reais

Depois das etapas anteriores:

```powershell
& $pythonTcc scripts/train_model_b.py --image-manifest data/splits/experimento/images.csv --crop-manifest data/processed/b_real_01/crops.csv --annotations data/annotations/experimento_reference.json --config configs/model_b.yaml --run-name b_real_01
```

Os arquivos ficam em `experiments/runs/b_real_01/`. Na configuração atual, o limite é 40 épocas, lote de 32 recortes e parada antecipada após 7 épocas sem melhora de `val_loss`. A duração real depende dos dados e hardware; o tempo do smoke não permite estimá-la. O treino padrão usa pesos ImageNet e pode precisar baixá-los na primeira execução.

Durante o treino, `loss` mede o erro no treino e `val_loss` o erro na validação. O checkpoint escolhido é o de menor `val_loss`, que pode não ser o da última época. Acurácia de recortes não equivale à detecção de parasitas na imagem inteira.

Para repetir, use outro nome, por exemplo `b_real_02`. Não reutilize um diretório existente. Se mudar localização ou anotações, gere novos recortes antes de treinar: os hashes são conferidos. O comando não oferece retomada automática de treino interrompido; `best.keras` e o histórico parcial, quando existentes, ficam disponíveis para inspeção.

## 7. Executar A e B nas mesmas imagens de teste

Somente depois de definir o teste independente e fixar as escolhas do B:

```powershell
$modeloOriginalA = 'C:\Users\PCZAO\Documents\Caio\ChagasVizion\Backend\fuzzylab_app\decision\services\model_trained.keras'
& $pythonTcc scripts/run_model_a.py --manifest data/splits/experimento/images.csv --model $modeloOriginalA --split test --output-dir experiments/runs/a_test_01 --overlays
& $pythonTcc scripts/run_model_b.py --manifest data/splits/experimento/images.csv --checkpoint experiments/runs/b_real_01/best.keras --split test --output-dir experiments/runs/b_test_01
```

O A não treina. O B utiliza a configuração salva junto do checkpoint. Cada execução gera `predictions.json`, tabela por imagem e sobreposições. A ausência de regiões permanece registrada, assim como eventuais falhas.

## 8. Gerar a comparação

```powershell
& $pythonTcc scripts/compare_systems.py --manifest data/splits/experimento/images.csv --annotations data/annotations/experimento_reference.json --predictions-a experiments/runs/a_test_01/predictions.json --predictions-b experiments/runs/b_test_01/predictions.json --split test --iou-threshold 0.5 --output experiments/runs/comparacao_real_01.json
```

O relatório separa cobertura da localização, detecção final, decisão por imagem e tempos. Métricas supervisionadas exigem referência revisada; campos indisponíveis não significam resultado zero. Não ajuste o B depois de olhar o teste e reapresente o mesmo conjunto como intocado.

## 9. Se preferir usar os notebooks

```powershell
& $pythonTcc -m jupyter lab notebooks
```

Abra os notebooks 01 a 05 nessa ordem. Eles começam em modo sintético e explicam entradas e saídas. O notebook 04 não dispara treino completo automaticamente; seu treino curto é opcional. Para o treino real, o comando da seção 6 é o caminho mais direto.

## Problemas comuns

| Mensagem ou situação | Como resolver |
| --- | --- |
| Python ou caminho não encontrado | Repetir a seção 1 e conferir se está na pasta TCC interna |
| Diretório de execução já existe | Usar novo `--run-name` ou `--output-dir` |
| Treino/validação sem recortes ou sem as duas classes | Conferir grupos, anotações revisadas e `extraction_report.json`; não inventar negativos |
| Localização/anotações diferentes dos hashes | Gerar novos recortes com os arquivos atuais |
| Falha ao baixar ImageNet | Verificar a conexão; o smoke continua disponível sem download |
| Memória insuficiente no treino real | Reduzir `training.batch_size` na configuração, registrar a mudança e iniciar outra execução |
| Comparação rejeita partição/hash | Usar exatamente o mesmo manifesto das inferências; mudanças exigem novas execuções |
| Checkpoint sintético rejeitado no teste | Usar o `best.keras` do treino real, não o smoke |

O [relatório de execução](execucao_2026-09-20.md) mostra o que já foi testado. O [checklist](checklist_execucao.md) registra as pendências para o experimento real.
