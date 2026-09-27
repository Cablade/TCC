# Guia de treinamento do Modelo B

Atualizado em 26/09/2026. A primeira execução real foi recebida e conferida; o modelo está em `experiments/runs/b_real_cpu_01`. Este guia permanece como roteiro de instalação e treinamento. Para uma nova rodada, escolha outro `run_name` antes de começar, conforme a seção 6, e preserve o modelo recebido. O perfil fornecido usa **CPU no Windows**; a RX 6600 não acelera esta instalação de TensorFlow/Keras 2.15.

## 1. Receber os arquivos

Envie o pacote `entrega_modelo_b_20260925.zip` e o ZIP original `trypoastigote_images.zip`. Extraia o pacote numa pasta, por exemplo `D:\TCC`. A raiz correta contém este README, `requirements.txt`, `src`, `scripts` e `configs`. Coloque o ZIP de imagens em `D:\TCC\dados\trypoastigote_images.zip`; ele pode permanecer compactado.

O pacote contém código, anotações, divisão e recortes da fonte pública autorizada. O ambiente Python será instalado no destino. O Modelo A será necessário somente na etapa posterior de comparação.

## 2. Instalar o ambiente

Instale Python **3.11 de 64 bits**. Abra PowerShell na pasta do projeto. Execute os blocos na ordem e pare se houver erro:

```powershell
Set-Location 'D:\TCC'
py -3.11 -m venv .venv
$pythonTcc = '.\.venv\Scripts\python.exe'
& $pythonTcc -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha na instalação.' }
& $pythonTcc -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependências incompatíveis.' }
```

Substitua `D:\TCC` pela pasta escolhida. Não é necessário ativar a `.venv`. Em outro terminal, entre novamente na raiz e defina `$pythonTcc`. Detalhes de hardware e alternativa NVIDIA estão em [ambiente](ambiente.md).

## 3. Ajustar os caminhos automaticamente

```powershell
& $pythonTcc scripts/prepare_received.py --archive 'D:\TCC\dados\trypoastigote_images.zip'
if ($LASTEXITCODE -ne 0) { throw 'Falha ao conferir os arquivos recebidos.' }
```

Esse comando confere os bytes do ZIP, das imagens e dos recortes, conserva os IDs e as partições e cria `configs/experiment_cpu_local.json`. Execute-o uma vez. Se a preparação já tiver terminado, prossiga com essa configuração. Não refaça o inventário nem sorteie outra divisão no destino.

## 4. Testar o programa e conferir os dados

```powershell
& $pythonTcc scripts/train_model_b.py --smoke
if ($LASTEXITCODE -ne 0) { throw 'O teste curto falhou.' }
& $pythonTcc scripts/start_training.py --experiment configs/experiment_cpu_local.json --check-only
if ($LASTEXITCODE -ne 0) { throw 'Há pendências nos dados ou no ambiente.' }
```

O teste curto usa imagens artificiais e não baixa pesos. Ele deve treinar, salvar e reabrir um modelo; o arquivo `smoke.json` registra `reload_equal: true`. A conferência seguinte deve mostrar os requisitos de treino aprovados. As observações sobre poucos negativos, grupos por imagem e referência incompleta de teste são limitações científicas reais e continuam no relatório.

## 5. Começar o treinamento real

```powershell
& $pythonTcc scripts/start_training.py --experiment configs/experiment_cpu_local.json
```

O perfil usa EfficientNet-B0 com pesos ImageNet, entrada RGB de 224 × 224, lote 8, limite de 40 épocas e parada após 7 épocas sem melhora de `val_loss`. Os pesos ImageNet podem ser baixados na primeira execução; mantenha acesso à internet. O melhor modelo é escolhido pela menor `val_loss`. Os aumentos de imagem acontecem somente no treino.

Deixe o terminal aberto e o computador ligado. A duração depende do processador e da RAM, ainda não informados; a presença da RX 6600 não permite estimar o tempo. O treino lê recortes por lote. Se houver falta de memória, reduza `training.batch_size` em `configs/model_b_cpu.yaml`, escolha outro `run_name` no JSON local e inicie uma nova execução.

## 6. Conferir e devolver o resultado

Ao finalizar:

```powershell
Get-Content experiments/runs/b_real_cpu_01/metadata.json -Raw | ConvertFrom-Json | Select-Object status, synthetic, selected_epoch, selected_val_loss, training_seconds
Test-Path experiments/runs/b_real_cpu_01/best.keras
```

O esperado é `status: complete`, `synthetic: false` e `True` para o arquivo. Devolva **a pasta inteira `experiments/runs/b_real_cpu_01`**, contendo o modelo, configuração, histórico e cópias dos manifestos. Acurácia dos recortes e conclusão do treino não demonstram qualidade de detecção no teste.

`Ctrl+C` no terminal do treino interrompe a execução e registra `interrupted`; encerrar à força pode deixar `running`. A existência de `best.keras` sozinha não comprova conclusão. Não existe retomada automática: preserve a execução parcial, resolva o problema e altere `run_name`, por exemplo para `b_real_cpu_02`. O programa recusa sobrescrever uma execução.

## Dados e limitações desta rodada

- Única fonte de pixels: ZIP do [Zenodo 5123062](https://zenodo.org/records/5123062), com sangue de camundongos. São 674 imagens legíveis; uma imagem corrompida foi excluída.
- Referência: 2.715 pontos positivos publicados e 29 áreas negativas revisadas por Caio, preservadas com histórico em `data/annotations/experimento_reference_v2.json`.
- Divisão: 455 imagens de treino, 114 de validação e 105 reservadas para teste. A pasta `test` original foi preservada; as 569 imagens restantes foram separadas com semente 42, garantindo negativos revisados em treino e validação.
- As oito imagens já examinadas ficaram em treino (6) e validação (2). Os recortes não foram divididos independentemente das imagens de origem. O extrator de treinamento não abre imagens de teste.
- Saber que são camundongos não identifica qual animal ou lâmina originou cada imagem. A divisão atual é por `imagem_original`; a independência entre animais não está demonstrada. Se essa correspondência for obtida, prepare uma nova versão do experimento por grupos biológicos antes de interpretar resultados como generalização entre animais.
- Os negativos são regiões sem parasita visível dentro de campos positivos. Poucas imagens originam todos os recortes negativos. Esta rodada permite **treinamento real inicial**, mas exige ampliar a revisão para uma avaliação robusta.
- O teste contém campos positivos e referência não exaustiva. Ainda não permite concluir especificidade em lâminas negativas nem fechar a comparação científica A × B.

## Reproduzir ou revisar a preparação

A divisão congelada está em `data/splits/experimento/images.csv` e seu protocolo em `split_report.json`. `scripts/prepare_initial_split.py` reproduz a separação a partir do inventário original e da referência v2; exige um destino novo para preservar a divisão existente. Não o execute novamente apenas para transportar o projeto.

Os recortes estão em `data/processed/b_real_01`. Para uma nova versão, depois de uma mudança documentada nas anotações ou na localização, use a referência completa e um destino novo:

```powershell
& $pythonTcc notebooks/gerar_rois.py --image-manifest data/protocol/experimento_neste_pc/images.csv --annotations data/annotations/experimento_reference_v2.json --config configs/model_b_cpu.yaml --output-dir data/processed/b_real_02 --splits train val
```

Altere `crop_manifest` e `run_name` na configuração da nova execução. Preserve as versões anteriores. O programa verifica hashes de anotações, localização e pixels; trocar só os nomes não atualiza os recortes. Para revisar novos negativos, siga [anotações](anotacoes.md) e use apenas treino/validação.

## Comparação A × B posterior

Não execute o teste reservado para escolher parâmetros. Antes da comparação final, defina com o orientador a cobertura da referência, as limitações de independência e o histórico de treino do A. A referência atual não libera uma avaliação completa.

Quando esses requisitos estiverem resolvidos, use o mesmo manifesto transportado e as mesmas imagens para `scripts/run_model_a.py`, `scripts/run_model_b.py` e `scripts/compare_systems.py`. Consulte `--help` e a [metodologia](metodologia.md). O Modelo A mantém os pesos originais; somente B recebe treinamento.

### Comparação preliminar na validação — computador do Caio

Com os dois modelos já disponíveis, execute os blocos abaixo, um por vez, esperando cada comando terminar. Eles aplicam A e B às mesmas **114 imagens inteiras de validação**. As 105 imagens de teste permanecem reservadas. Se um comando falhar, pare e examine o erro antes de continuar.

```powershell
Set-Location 'C:\Users\PCZAO\Documents\Caio\TCC\TCC'
$pythonTcc = '.\.venv\Scripts\python.exe'
```

Execute o A:

```powershell
& $pythonTcc scripts/run_model_a.py --manifest data/splits/experimento/images.csv --model models/model_a/model_trained.keras --split val --output-dir experiments/runs/a_val_01 --overlays
```

Execute o B:

```powershell
& $pythonTcc scripts/run_model_b.py --manifest data/splits/experimento/images.csv --checkpoint experiments/runs/b_real_cpu_01/best.keras --split val --output-dir experiments/runs/b_val_01
```

Gere o relatório pareado:

```powershell
& $pythonTcc scripts/compare_systems.py --manifest data/splits/experimento/images.csv --annotations data/annotations/experimento_reference_v2.json --predictions-a experiments/runs/a_val_01/predictions.json --predictions-b experiments/runs/b_val_01/predictions.json --split val --output experiments/results/comparacao_val_01.json
```

As pastas `a_val_01` e `b_val_01` contêm predições por imagem. O A desenha caixas e status quando recebe `--overlays`; as imagens ficam em `a_val_01/overlays`. O B agora salva, por padrão, PNGs inteiros **sem marcações**, em `b_val_01/images`, e os CSVs descritos abaixo. Execuções antigas do B podem conter arquivos `_overlay.png`; eles são preservados. O relatório combinado fica em `experiments/results/comparacao_val_01.json`. Ele informa decisões por imagem, regiões propostas, falhas e tempos. As métricas de detecção que exigem referência exaustiva ficam indisponíveis (`null`) com as anotações atuais; isso não significa desempenho zero. Como todas as imagens têm referência positiva, o relatório não permite estimar especificidade em lâminas negativas nem concluir superioridade geral de um sistema.

A validação já participou da seleção do B; essa execução é um diagnóstico preliminar. Para repetir, escolha destinos novos e atualize os caminhos dos dois arquivos de predições no último comando. Ao transportar para outro computador, use nos três comandos o mesmo manifesto de imagens ajustado para esse computador.

### Consultar os resultados sem marcações nas imagens

Nas novas execuções do B, `--image-mode original` é o padrão. Ele salva um PNG RGB por imagem inteira, com os mesmos pixels decodificados, sem caixas, textos, redimensionamento ou arquivos de recortes individuais. Os nomes são identificadores seguros; a coluna `image_file` liga cada PNG ao seu `image_id`.

- `images.csv`: uma linha por imagem. As primeiras colunas seguem o A: `image_id`, `status`, `original_decision`, `candidates`, `classified`, `seconds`, `error`. Depois aparecem as contagens de regiões positivas/negativas, o caminho do PNG e o tempo/erro de exportação.
- `regions.csv`: uma linha por candidato, começando por `image_id` e `candidate_id`. Inclui classificação (`suspeita` ou `sem_suspeita`), classe 1/0, coordenadas e escores das duas classes. Um candidato não classificado por falha fica explícito e não vira negativo. Coordenadas começam em zero; `x2` e `y2` são limites exclusivos.
- `predictions.json`: resultado completo usado na comparação automática. `per_image.csv` continua disponível no formato anterior do B para compatibilidade.

`seconds` mede o algoritmo, sem leitura nem gravação de imagens, como no CSV do A. `image_seconds` em cada região repete o tempo da imagem inteira; não é o tempo individual daquela região e não deve ser somado. O B processa regiões em lotes e não mede tempos individuais. `export_seconds` fica separado, e `export_error` não altera a decisão do modelo. Os escores não são probabilidades calibradas. `sem_regioes` significa que o localizador não encontrou candidatos; não comprova ausência do parasita.

Para medir desempenho dos dois sistemas, execute A sem `--overlays` e B com `--image-mode none` (ou o equivalente antigo `--no-overlays`). Para solicitar caixas no B explicitamente, use `--image-mode overlay`.

É possível produzir os PNGs e os dois CSVs **depois da comparação**, sem executar a rede novamente. O comando abaixo aceita resultados tanto do A quanto do B e exige uma pasta nova:

```powershell
& $pythonTcc scripts/export_prediction_review.py --manifest data/splits/experimento/images.csv --predictions experiments/runs/b_val_01_compiled/predictions.json --output-dir experiments/runs/b_val_01_compiled/review
```

Use esse comando somente quando `predictions.json` estiver concluído. Não há necessidade de treinar novamente para mudar a apresentação dos resultados.
