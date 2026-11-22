# Ambiente e transferência

Instalação e transporte dos mesmos dados entre computadores. O passo a passo do experimento está no [guia de treinamento](guia_treinamento.md).

## Correção local do Python — 06/10/2026

O Windows bloqueou `python311.dll` da distribuição anterior sem assinatura (eventos Code Integrity 3033/3077). Foi instalada localmente a distribuição oficial Python Software Foundation 3.11.9 de 64 bits, via pacote NuGet `python/3.11.9`, em `.cache/python/python-3.11.9-official/`. Assinaturas do executável e da DLL conferidas como válidas; origem e hash registrados em `origin.json` nessa pasta. É uma versão anterior dentro da mesma série 3.11, usada para preservar compatibilidade com as dependências existentes.

A `.venv` foi atualizada com `venv --upgrade --without-pip`, preservando os pacotes. O caminho de execução continua `.venv/Scripts/python.exe`; TensorFlow/Keras 2.15, NumPy 1.26.3 e OpenCV 4.9 foram carregados e uma operação TensorFlow executada. Nenhuma política de segurança do Windows foi alterada. Registro e configuração anterior: `data/protocol/retrain_b_barcelona20_20261006/`, arquivado em `archive/limpeza_pos_teste_final_20261014.zip`. A distribuição oficial em `.cache/python` passa a ser necessária; não removê-la como cache descartável.

Referências: [distribuições oficiais Python no Windows](https://docs.python.org/3.11/using/windows.html#the-nuget-org-packages), [Python 3.11.9](https://www.python.org/downloads/release/python-3119/), [diagnóstico de bloqueios App Control](https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/operations/appcontrol-debugging-and-troubleshooting).

## Testes

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m pytest -q
```

`pytest.ini` usa `.cache/pytest` como pasta temporária, pois no ambiente de desenvolvimento a pasta padrão do pytest em `AppData\Local\Temp` retornava "Acesso negado". `PYTHONUTF8=1` evita erros de codificação nos textos em português.

- [Windows com RX 6600 e alternativa GPU](#windows)
- [Transferir para outro computador](#transferencia)

<a id="windows"></a>

## Windows com RX 6600 e alternativa GPU

Levantamento de 23/09/2026 para uma máquina Windows 10/11 com GPU AMD RX 6600.

**Conclusão: nessa máquina, a preparação dos dados, a conferência das anotações e o treinamento do Modelo B são feitos pela CPU. A aceleração por GPU exige uma placa NVIDIA compatível em Linux/nuvem; a RX 6600 não é suportada pelo ambiente atual.** O projeto usa TensorFlow/Keras 2.15 e Python 3.11. O Modelo A continua congelado; quem recebe treinamento é o B.

### 1. Por que a RX 6600 não é uma instalação pronta para este projeto?

| Opção | Situação para o TCC |
|---|---|
| Windows + dependências atuais + CPU | Caminho disponível. A velocidade depende do processador, RAM e número de recortes. |
| Windows + RX 6600 + TensorFlow 2.15 | O pacote usado aqui não oferece aceleração CUDA para essa placa. |
| DirectML para TensorFlow | Plugin descontinuado; exige `tensorflow-cpu==2.10` e Python até 3.10. Trocar para ele exige outro ambiente e nova validação do código. |
| RX 6600 + ROCm/WSL/Linux | A RX 6600 não consta nas matrizes oficiais consultadas. Não foi validada neste projeto. |
| Linux/WSL2 + NVIDIA compatível | Alternativa para preservar TensorFlow/Keras 2.15, condicionada à verificação efetiva da GPU. |

O TensorFlow documenta que a última versão com suporte CUDA no Windows nativo foi a 2.10; a rota CUDA nas versões posteriores usa Linux/WSL2 e hardware NVIDIA compatível. Instalar WSL2 por si só não dá CUDA a uma Radeon. [Instalação oficial do TensorFlow](https://www.tensorflow.org/install/pip).

A Microsoft informa a descontinuação do plugin TensorFlow-DirectML e os limites de versões acima. Por isso, instalar esse plugin dentro da `.venv` do TCC não é uma solução compatível com suas dependências. [Documentação oficial DirectML](https://learn.microsoft.com/en-us/windows/ai/directml/gpu-tensorflow-plugin).

A matriz AMD de Windows consultada cobre PyTorch e GPUs selecionadas, sem RX 6600; a matriz unificada também não lista essa placa. A existência de suporte a outras Radeon ou à família profissional W6000 não significa suporte à RX 6600. Este guia não usa modificações comunitárias para simular outra GPU. [Matriz AMD para Windows](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/windows/windows_compatibility.html), [matriz unificada AMD](https://rocm-handbook.amd.com/projects/amd-rocm-programming-guide/en/latest/compatibility/compatibility-matrix.html).

### 2. Preparar outra máquina Windows

O projeto e os dados são copiados conforme o [guia principal](guia_treinamento.md). A pasta `.venv` não deve ser copiada: o ambiente é criado na máquina de destino. Manifestos com caminhos absolutos da máquina de origem precisam ser ajustados e revalidados; copiar somente o código não leva junto o ZIP original, as anotações e os recortes.

Instale Python **3.11 de 64 bits**. A tabela oficial do TensorFlow 2.15 lista Python 3.9–3.11; usar o Python mais novo disponível pode impedir a instalação das versões fixadas. [Versões testadas do TensorFlow](https://www.tensorflow.org/install/source#tested_build_configurations).

Abra PowerShell na pasta que contém `requirements.txt`, `src` e `scripts`. Confira e instale:

```powershell
Get-Location
Test-Path requirements.txt
py -3.11 --version
py -3.11 -m venv .venv
$pythonTcc = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $pythonTcc -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'A instalação não terminou. Corrija o erro antes de continuar.' }
& $pythonTcc -m pip check
```

Se `Test-Path` retornar `False`, entre na pasta interna do projeto. Se `py -3.11` não existir, conclua a instalação do Python antes de continuar. Não é necessário ativar a `.venv` nem mudar a política de execução do PowerShell.

Para consultar as características do computador, sem instalar ferramentas:

```powershell
Get-CimInstance Win32_Processor | Select-Object Name
Get-CimInstance Win32_ComputerSystem | Select-Object @{Name='RAM_GB';Expression={[math]::Round($_.TotalPhysicalMemory / 1GB, 1)}}
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion
```

A RAM do computador é diferente da memória da placa. O perfil CPU começa com lote de 8 recortes para reduzir o uso de memória; isso não garante uma quantidade mínima de RAM nem uma duração específica. Feche outros programas pesados e observe o Gerenciador de Tarefas durante o piloto.

### 3. Conferir o ambiente antes de copiar todos os dados

O projeto já inclui uma configuração para CPU: `configs/experiment_b_original_negatives.json`, com o Modelo B em `configs/model_b_cpu_original_negatives.yaml`.

```powershell
& $pythonTcc scripts/check_training_ready.py --config configs/experiment_b_original_negatives.json --runtime-only --output data/protocol/runtime_cpu.json
if ($LASTEXITCODE -ne 0) { throw 'O ambiente Python ainda precisa ser corrigido.' }
```

O resultado esperado é TensorFlow/Keras 2.15, `ok: true` e, normalmente, `gpus: []`. Nesse caso o caminho é CPU. Uma placa aparecer no Windows não significa que o TensorFlow a reconheça. Como essa conferência verifica somente o ambiente, a linha sobre prontidão dos dados ainda não autoriza o treinamento real.

Faça o teste curto de execução:

```powershell
& $pythonTcc scripts/train_model_b.py --smoke
if ($LASTEXITCODE -ne 0) { throw 'O teste curto falhou. Resolva o erro antes de treinar com os dados reais.' }
```

Esse teste usa imagens artificiais pequenas, não baixa ImageNet e comprova que o programa consegue treinar, salvar e reabrir o modelo. Ele **não mede qualidade nem estima o tempo do treino real**.

### 4. Iniciar o treinamento real pela CPU

Primeiro conclua a revisão, separação dos grupos e extração dos recortes descritas no [guia de treinamento](guia_treinamento.md). O lote CPU altera a quantidade de recortes processados de uma vez; as imagens de entrada continuam com 224 × 224 pixels. As configurações usadas ficam salvas na pasta da execução para registrar essa diferença.

Confira os caminhos, o nome da execução e `require_gpu: false` em `configs/experiment_b_original_negatives.json`. Depois:

```powershell
& $pythonTcc scripts/check_training_ready.py --config configs/experiment_b_original_negatives.json --check-runtime --output data/protocol/readiness_cpu.json
if ($LASTEXITCODE -ne 0) { throw 'Há pendências nos dados ou no ambiente. Leia o relatório antes de continuar.' }
& $pythonTcc scripts/start_training.py --experiment configs/experiment_b_original_negatives.json
```

O lançador repete a conferência antes de iniciar. Havendo rótulos pendentes, recortes incompatíveis, arquivos ausentes ou falta de uma classe no treino/validação, corrija a pendência; não transforme casos desconhecidos em negativos para liberar a execução.

Na primeira execução real pode ocorrer o download dos pesos ImageNet. Mantenha o computador ligado e conectado à energia. Acompanhe as épocas no terminal. O tempo de uma época real já informa melhor a viabilidade da CPU; a parada antecipada pode encerrar antes do limite configurado. Não é possível estimar horas somente sabendo que existe uma RX 6600 na máquina.

Consulte `run_name` e `output_dir` na configuração para localizar a pasta de saída. Guarde a pasta inteira, incluindo `best.keras`, `metadata.json`, `config.json`, `history.json`, `epochs.csv` e cópias dos manifestos. A conclusão correta aparece como `status: complete` e `synthetic: false` em `metadata.json`.

O treino atual seleciona o melhor modelo pela menor `val_loss`. Ele não retoma automaticamente uma execução interrompida. Não reutilize a pasta de uma execução parcial: mantenha-a como registro e escolha outro `run_name` ao reiniciar. Se a CPU for lenta demais, conclua a preparação local e transfira os dados para uma GPU compatível.

### 5. Alternativa para acelerar: GPU NVIDIA em Linux/nuvem

Use um ambiente Linux com **Python 3.11**, driver NVIDIA funcional e GPU compatível com TensorFlow 2.15/CUDA 12.2. A versão testada do TensorFlow 2.15 usa cuDNN 8.9. A primeira verificação deve ser `nvidia-smi`; depois, o teste de GPU do projeto. [Tabela oficial de compatibilidade](https://www.tensorflow.org/install/source#gpu).

No Linux x86-64, use a correção de empacotamento **2.15.0.post1** ao instalar as bibliotecas CUDA: o TensorFlow documentou uma falha nas dependências do extra `and-cuda` em 2.15.0. Isso preserva a linha 2.15, mas é uma variante explicitamente registrada do ambiente Windows. [Correção oficial do TensorFlow](https://blog.tensorflow.org/2023/12/tensorflow-215-update-hot-fix-linux-installation-issue.html).

Após copiar o projeto, abra um terminal Linux na raiz dele. Esses comandos são para esse terminal, não para PowerShell nem para a RX 6600. Execute uma linha por vez e pare em caso de erro:

```bash
nvidia-smi
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install 'tensorflow[and-cuda]==2.15.0.post1'
.venv/bin/python -m pip check
.venv/bin/python scripts/check_training_ready.py --config configs/experiment.json --runtime-only --require-gpu --output data/protocol/runtime_gpu.json
.venv/bin/python scripts/train_model_b.py --smoke
```

O segundo comando de instalação substitui o pacote 2.15.0 pelo hotfix no ambiente Linux; não reinstale `requirements.txt` depois dele, pois isso restauraria a versão anterior. Registre as versões finais com `.venv/bin/python -m pip freeze > environment_linux.txt`. O teste deve mostrar uma GPU e uma operação executada nela, e o smoke deve conseguir salvar e recarregar o modelo. Para o treino, corrija e revalide os caminhos dos dados, mantenha `require_gpu: true` e use:

```bash
.venv/bin/python scripts/check_training_ready.py --config configs/experiment.json --check-runtime --require-gpu
.venv/bin/python scripts/start_training.py --experiment configs/experiment.json
```

Não foi executado um teste nessa máquina remota; esses passos precisam passar nela antes do treino. A ausência de GPU deve bloquear essa rota, para evitar consumir uma sessão paga treinando inadvertidamente pela CPU.

#### Colab e custos

O Colab oferece acesso gratuito a recursos, incluindo GPU, mas disponibilidade, tipo de GPU e duração da sessão variam; planos pagos também têm limites. Os arquivos da máquina temporária podem desaparecer ao encerrar a sessão. Salve resultados fora dela e confira o valor cobrado antes de contratar qualquer plano. [FAQ oficial do Colab](https://research.google.com/colaboratory/faq.html).

Um notebook Colab não fica compatível com o TCC apenas por selecionar GPU: confira sua versão de Python e mantenha o ambiente 3.11/TF 2.15 isolado. O Python padrão do serviço pode ser mais novo. Não instale versões antigas de TensorFlow sobre um ambiente incompatível. Para este projeto, a rota Linux descrita acima é a referência; um Colab sem o ambiente compatível preparado ainda exige essa configuração.

Na CPU local não há cobrança de aluguel de GPU; há consumo de energia e tempo de uso do computador. Na nuvem, o custo depende de duração, tipo de máquina e armazenamento. Não há orçamento estimável antes de conhecer o volume final de recortes e medir uma época real.

### 6. Decisão para começar

1. Prepare e revise os dados no Windows.
2. Faça a conferência do ambiente e o teste curto pela CPU.
3. Quando os dados estiverem aprovados, inicie uma execução real com a configuração CPU.
4. Se a duração ficar impraticável, transfira o mesmo conjunto e as mesmas partições para Linux com GPU NVIDIA validada.

A GPU não resolve falta de anotações ou de negativos confiáveis. O [guia principal](guia_treinamento.md) mostra a preparação, e a [pesquisa de imagens negativas](dados.md#negativos) separa campos sem parasita visível de amostras realmente negativas para Chagas.

<a id="transferencia"></a>

## Transferir para outro computador

Para transportar o conjunto atual, copie as fontes principal e suplementar e confira os caminhos com `scripts/relocate_experiment.py`; o pacote antigo de treino com uma única fonte pertence ao histórico.

O exemplo usa `D:\TCC` como pasta do projeto no destino. Substitua essa pasta se necessário. Faça a [instalação Windows](ambiente.md#windows) no computador de destino; a `.venv` de origem não deve ser copiada.

### O que copiar

Copie o código (`src`, `scripts`, `configs`, `notebooks`, `tests`, `requirements.txt`, documentação) e somente os dados listados abaixo. Não envie a pasta inteira: `.cache`, `.venv`, `.git`, históricos em `archive`, resultados antigos em `experiments` e candidatos externos não são necessários para iniciar B. As pastas abaixo ficam total ou parcialmente fora do Git: baixar apenas o repositório não as transporta.

- `data/protocol/trypomastigote_verified/`, com o inventário elegível;
- `data/annotations/public_import/`, com as marcações positivas e sua origem;
- `data/annotations/experimento_reference_v2.json`, com a revisão preservada;
- `data/splits/experimento/`, com a divisão inicial congelada;
- `data/processed/b_real_01/`, `b_next/` e `b_hardneg/`, com os recortes de treino/validação (o manifesto de `b_hardneg` aponta para as três);
- `data/annotations/negative_preselection_v1/`, com o histórico da revisão e a reserva obrigatória das imagens já examinadas;
- o ZIP original `trypoastigote_images.zip`, por exemplo em `D:\TCC\dados\trypoastigote_images.zip`.

Para a comparação, o Modelo A já está disponível dentro do TCC em `models/model_a/model_trained.keras`, acompanhado de `provenance.json`. A cópia foi conferida byte a byte com o original do ChagasVizion; os pesos permanecem congelados. Ao transportar o experimento A × B, inclua a pasta `models/model_a` e a execução completa do B em `experiments/runs/b_atual` (`b_hardneg_s42`). O pacote inicial de 25/09, destinado apenas ao treinamento do B, não contém esses dois modelos. Arquivos `.keras` não acompanham automaticamente o Git.

### Antes de gerar recortes no PC novo

Os caminhos dentro do inventário ainda apontam para o PC de origem. Na pasta do projeto de destino, rode:

```powershell
$pythonTcc = '.\.venv\Scripts\python.exe'
& $pythonTcc scripts/relocate_experiment.py --images data/protocol/trypomastigote_verified/eligible_inventory.csv --output-dir data/protocol/inventario_neste_pc --map 'C:/Users/PCZAO/Documents/Caio/trypoastigote_images.zip=D:/TCC/dados/trypoastigote_images.zip'
```

O comando valida os bytes de cada imagem pelo SHA-256 e gera `data/protocol/inventario_neste_pc/images.csv`. Ele preserva os IDs, portanto a referência positiva continua associada às mesmas imagens. Esse arquivo é um inventário relocalizado, **não uma nova divisão em treino e teste**.

Para revisar usando esse inventário:

```powershell
& $pythonTcc scripts/review_annotations.py --inventory data/protocol/inventario_neste_pc/images.csv --annotations data/annotations/experimento_reference_v2.json --output data/annotations/revisao_neste_pc.json
```

Se as partições já existirem, use seu `images.csv` no lugar do inventário inicial. Não refaça o inventário por outro caminho apenas para mudar de computador: isso criaria IDs diferentes.

### Quando já houver partições e recortes

```powershell
& $pythonTcc scripts/relocate_experiment.py --images data/splits/experimento/images.csv --crops data/processed/b_real_01/crops.csv --output-dir data/protocol/experimento_neste_pc --map 'C:/Users/PCZAO/Documents/Caio/trypoastigote_images.zip=D:/TCC/dados/trypoastigote_images.zip' --map 'C:/Users/PCZAO/Documents/Caio/TCC/TCC=D:/TCC'
```

Uma saída existente é recusada; para repetir, use outra pasta. A única fonte de pixels permitida é o ZIP público com o SHA-256 configurado. O transporte pode mudar o caminho, mas deve preservar os bytes. Arquivos ausentes ou com conteúdo diferente impedem a conclusão.

Em `configs/experiment_b_original_negatives.json`, ajuste:

```json
"image_manifest": "data/protocol/experimento_neste_pc/images.csv",
"crop_manifest": "data/protocol/experimento_neste_pc/crops.csv"
```

Mantenha o JSON de anotações byte a byte como foi copiado: os recortes registram seu hash. Se as anotações mudarem, gere novos recortes. A configuração do modelo também deve manter a mesma localização usada na extração.

Finalmente:

```powershell
& $pythonTcc scripts/start_training.py --experiment configs/experiment_b_original_negatives.json --check-only
```

Depois da transferência, execute as duas inferências A/B com o mesmo manifesto novo. Não combine predições antigas vinculadas ao hash do manifesto do outro computador.
