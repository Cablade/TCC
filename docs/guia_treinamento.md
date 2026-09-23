# Guia prático: treinar o B e comparar com o A

Este é o roteiro para sair do ZIP e chegar ao primeiro treinamento real. Os comandos PowerShell abaixo preparam o projeto nesta máquina Windows; o treinamento será feito no computador com GPU escolhido por você, depois de conferir o ambiente e transportar os caminhos dos dados. **Somente B será treinado; A usa os pesos originais fixos.** O código pronto e o teste artificial não substituem imagens rotuladas: a liberação do treino depende dos arquivos conferidos pelo verificador da seção 5.

| Etapa | Resultado que permite avançar |
| --- | --- |
| Conferir a instalação | Teste rápido salva e reabre o modelo |
| Preparar a referência | Anotações públicas reconciliadas com as imagens e revisão registrada |
| Separar as imagens | Treino, validação e teste sem compartilhar grupos |
| Preparar os recortes | Positivos e negativos revisados em treino e validação |
| Conferir o treino | Verificador mostra quais requisitos passaram e quais faltam |
| Treinar B | `best.keras` e execução concluída em `metadata.json` |
| Comparar com A | Ambos executados nas mesmas imagens de teste reservadas |

Não é preciso criar marcações do zero se houver anotações públicas compatíveis. O [roteiro de anotação](roteiro_anotacao.md) explica como aproveitá-las e o que precisa ser conferido. As [fontes negativas](fontes_negativas.md) distinguem campos sem parasitas de lâminas ou doadores negativos.

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

A única base ativa é `trypoastigote_images.zip`. A auditoria leu os pixels de 675 JPGs únicos: **674 aprovados e um excluído por erro**. O inventário elegível está em `data/protocol/trypomastigote_verified/eligible_inventory.csv`; o template `data/annotations/trypomastigote_pending.json` contém 674 registros **sem marcações confiáveis**. Partições finais ainda não foram criadas. Consulte [base atual](dataset_atual.md). Os ZIPs e manifestos anteriores estão fora do experimento.

Antes de seguir, é preciso reconciliar as marcações disponíveis e registrar a revisão por alguém qualificado. O projeto define o formato JSON; o [roteiro de anotação](roteiro_anotacao.md) detalha a revisão, incluindo a identificação dos grupos de lâmina/animal quando disponível. Alterar apenas `pending` para `reviewed` não substitui essa revisão. Se a fonte não permitir identificar o animal ou a lâmina, registre o nível `imagem_original` e declare a limitação de independência.

Imagens usadas para ajustar o sistema não podem virar teste final. A auditoria de integridade não realizou inferência nem ajuste de parâmetros. As pastas originais `train/test` do ZIP não demonstram independência entre animais/lâminas. Para obter negativos, consulte [fontes e critérios de uso](fontes_negativas.md); não é obrigatório que cada recorte negativo venha de uma lâmina negativa, mas ele precisa ser revisado e não conter parasitas.

## 4. Preparar os arquivos do experimento real

**As seções 4 a 8 dependem dos dados revisados. Os nomes abaixo são os arquivos de trabalho a preparar, não arquivos já completos.**

Parta de `data/protocol/trypomastigote_verified/eligible_inventory.csv` e prepare uma cópia em `data/protocol/experimento/inventory.csv`, preenchendo os grupos confirmados e preservando `image_id`, caminho e SHA-256. Prepare também um CSV `data/protocol/experimento/grupos.csv` com as colunas `group_id,split`. Use os IDs reais desse inventário e as partições `train`, `val`, `test` ou `development`. Não defina percentuais antes de verificar grupos e classes. Não reintroduza a imagem com falha de integridade.

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

Esse comando não sobrescreve arquivo existente. Se a revisão já tiver sido feita no template da base ativa, copie a referência revisada para o nome do experimento e confira a correspondência dos IDs, sem criar outro template vazio. Depois da revisão:

```powershell
& $pythonTcc scripts/prepare_data.py validate --splits data/splits/experimento/images.csv --annotations data/annotations/experimento_reference.json
```

A validação confere estrutura e separação; ela não certifica a correção biológica das marcações.

**O papel de cada conjunto:** `train` ensina os pesos; `val` escolhe a melhor época e orienta decisões do B; `development` permite inspecionar exemplos e calibrar a localização; `test` fica reservado para a comparação final. Os recortes e aumentos de uma imagem sempre permanecem na partição da imagem original.

## 5. Gerar os recortes do B

Primeiro, fixe os parâmetros de localização usando desenvolvimento/validação. A configuração fica em [configs/model_b.yaml](../configs/model_b.yaml); os valores atuais são provisórios e ainda não foram avaliados no novo ZIP.

Para calibrar a localização sem acessar o teste, use o arquivo `development.csv` gerado na divisão. Crie uma referência que contenha apenas esses IDs, preservando os rótulos já revisados:

```powershell
$idsDesenvolvimento = @(Import-Csv data/splits/experimento/development.csv | ForEach-Object { $_.image_id })
$referenciaDesenvolvimento = Get-Content data/annotations/experimento_reference.json -Raw | ConvertFrom-Json
$referenciaDesenvolvimento.images = @($referenciaDesenvolvimento.images | Where-Object { $_.image_id -in $idsDesenvolvimento })
$destinoReferencia = 'data/annotations/experimento_development.json'
if (Test-Path $destinoReferencia) { throw 'A referência de desenvolvimento já existe; confira a versão antes de gerar outra.' }
$referenciaDesenvolvimento | ConvertTo-Json -Depth 20 | Set-Content $destinoReferencia -Encoding UTF8
```

Este comando processa somente o desenvolvimento:

```powershell
& $pythonTcc notebooks/gerar_rois.py --image-manifest data/splits/experimento/development.csv --annotations data/annotations/experimento_development.json --config configs/model_b.yaml --output-dir data/processed/b_desenvolvimento_01
```

Examine os recortes e `extraction_report.json` com a referência. O campo `missed_positive_ids` ajuda a encontrar parasitas que a localização não alcançou; ele não é a métrica final de detecção. Se alterar os parâmetros, use outro destino, como `b_desenvolvimento_02`. Caso não exista grupo de desenvolvimento reservado, planeje a calibração somente na validação e documente esse uso; não use o teste para suprir essa falta.

Depois de fixar os parâmetros, confira a extração final sem gravar recortes:

```powershell
& $pythonTcc notebooks/gerar_rois.py --image-manifest data/splits/experimento/images.csv --annotations data/annotations/experimento_reference.json --config configs/model_b.yaml --output-dir data/processed/b_real_01 --dry-run
```

Quando os dados e parâmetros estiverem preparados, retire `--dry-run`:

```powershell
& $pythonTcc notebooks/gerar_rois.py --image-manifest data/splits/experimento/images.csv --annotations data/annotations/experimento_reference.json --config configs/model_b.yaml --output-dir data/processed/b_real_01
```

A saída contém os recortes, `crops.csv` e `extraction_report.json`. Candidatos sem rótulo confiável não viram negativos. O classificador exige recortes das duas classes em **treino e validação**. Se `labeled_crops` for zero, ainda não há dados utilizáveis para o treino.

O extrator percorre as partições presentes no manifesto; os recortes de teste nunca entram no `fit`. Não use o conteúdo ou os resultados de teste para ajustar a localização. Planeje e congele as escolhas usando apenas desenvolvimento/validação antes de executar a extração final.

Agora execute a conferência que antecede o treinamento:

```powershell
& $pythonTcc scripts/check_training_ready.py
```

Os caminhos dessa conferência ficam em `configs/experiment.json` e correspondem aos nomes deste guia. Se você escolher nomes diferentes, atualize essa configuração. O relatório indica arquivos ausentes, revisão pendente, separação dos grupos e disponibilidade dos recortes. **Uma validação de estrutura bem-sucedida na seção 4 não significa que já há dados suficientes para treinar.** Resolva os bloqueios relacionados ao treino antes da seção 6; requisitos de avaliação também precisam ser atendidos antes da comparação final.

Para conferir também o TensorFlow e o hardware visível neste ambiente:

```powershell
& $pythonTcc scripts/check_training_ready.py --check-runtime
```

Esse comando não treina o modelo. A ausência de GPU visível pode significar treinamento pela CPU; não conclua que há aceleração só porque o computador possui placa de vídeo. O tempo depende do hardware efetivamente reconhecido e da quantidade de recortes.

## 6. Treinar com os recortes reais

Depois das etapas anteriores:

```powershell
& $pythonTcc scripts/train_model_b.py --image-manifest data/splits/experimento/images.csv --crop-manifest data/processed/b_real_01/crops.csv --annotations data/annotations/experimento_reference.json --config configs/model_b.yaml --run-name b_real_01
```

Os arquivos ficam em `experiments/runs/b_real_01/`. Na configuração atual, o limite é 40 épocas, lote de 32 recortes e parada antecipada após 7 épocas sem melhora de `val_loss`. A duração real depende dos dados e hardware; o tempo do smoke não permite estimá-la. O treino padrão usa pesos ImageNet e pode precisar baixá-los na primeira execução.

Durante o treino, `loss` mede o erro no treino e `val_loss` o erro na validação. O checkpoint escolhido é o de menor `val_loss`, que pode não ser o da última época. Acurácia de recortes não equivale à detecção de parasitas na imagem inteira.

Deixe o terminal aberto até o fim. Para acompanhar as épocas em outro PowerShell, sem abrir outro treinamento:

```powershell
Set-Location 'C:\Users\PCZAO\Documents\Caio\TCC\TCC'
Get-Content experiments/runs/b_real_01/epochs.csv -Tail 10 -Wait
```

Esse acompanhamento funciona depois de `epochs.csv` ser criado. `Ctrl+C` **nesse segundo terminal** encerra apenas a leitura; no terminal do treino, interrompe o treinamento.

Ao terminar, confira:

```powershell
Get-Content experiments/runs/b_real_01/metadata.json -Raw | ConvertFrom-Json | Select-Object status, synthetic, selected_epoch, selected_val_loss, training_seconds
Test-Path experiments/runs/b_real_01/best.keras
```

O resultado esperado é `status = complete`, `synthetic = False` e o arquivo presente (`True`). Isso confirma uma execução real concluída, ainda sem demonstrar qualidade no teste. `history.json` guarda todas as épocas concluídas; `metadata.json` informa qual foi selecionada. Preserve a pasta inteira da execução, incluindo configuração e cópias dos manifestos, ao guardar ou transferir o modelo.

Para repetir, use outro nome, por exemplo `b_real_02`. Não reutilize um diretório existente. Se mudar localização ou anotações, gere novos recortes antes de treinar: os hashes são conferidos. O comando não oferece retomada automática de treino interrompido; `best.keras` e o histórico parcial, quando existentes, ficam disponíveis para inspeção.

Se houver interrupção antes de completar uma época, pode não existir checkpoint. Após interrupção manual ou fechamento do processo, o registro pode ainda mostrar `running`; a existência de `best.keras` sozinha não confirma conclusão. Corrija o problema e inicie uma nova execução com outro nome. A lista `runs.seeds` da configuração não dispara cinco treinamentos automaticamente: o comando usa apenas `data.seed` em cada execução.

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

O notebook 01 também pode consultar o inventário elegível já auditado em modo real. Os notebooks 02 a 05 precisam do manifesto de partições; enquanto ele não existir, mostram uma orientação para completar a preparação. Para usar os arquivos das seções anteriores, abra o Jupyter com estas variáveis **somente depois de prepará-los**:

```powershell
$env:TCC_RUN_MODE = 'real'
$env:TCC_MANIFEST = 'C:\Users\PCZAO\Documents\Caio\TCC\TCC\data\splits\experimento\images.csv'
$env:TCC_ANNOTATIONS = 'C:\Users\PCZAO\Documents\Caio\TCC\TCC\data\annotations\experimento_reference.json'
& $pythonTcc -m jupyter lab notebooks
```

Para voltar ao teste artificial, use `$env:TCC_RUN_MODE = 'synthetic'` e reinicie o kernel. Definir caminhos não substitui a revisão das anotações.

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
| `validate` passou, mas o verificador bloqueou | A estrutura está correta, mas faltam requisitos de treino, como revisão ou duas classes nos recortes |
| `epochs.csv` ainda não existe | Aguardar o início da primeira época; confira no terminal principal se está baixando pesos ou carregando dados |
| `status` ficou `running` depois de fechar o treino | Tratar como execução interrompida; não declarar conclusão apenas porque existe um checkpoint |

A [auditoria da base atual](dataset_atual.md) registra a preparação do novo ZIP. O [checklist](checklist_execucao.md) registra as pendências para o experimento real. Verificações técnicas anteriores permanecem no [histórico](historico/execucao_2026-09-20.md), cujos dados foram descartados.
