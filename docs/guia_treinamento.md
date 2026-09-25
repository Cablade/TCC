# Guia de treinamento do Modelo B

Atualizado em 25/09/2026. O conjunto inicial já está separado e os recortes foram preparados. O treino real será executado no computador do seu amigo. O perfil fornecido usa **CPU no Windows**; a RX 6600 não acelera esta instalação de TensorFlow/Keras 2.15.

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
