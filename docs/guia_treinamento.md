# Guia vigente de treinamento e comparação

Atualizado em 27/09/2026. O B reduzido já está treinado; não é necessário treinar novamente para gerar figuras. A versão anterior do guia, com o pacote inicial e seus números históricos, está em `archive/documentacao_pre_revisao_20260927.zip`.

## Estado atual

EfficientNet-B0, entrada RGB 224 × 224, lote 8, até 40 épocas, paciência 7 e seleção pela menor `val_loss`. Foram realizadas 30 épocas e selecionada a 23. Configuração: `configs/model_b_cpu_reduced.yaml`. Treino e validação usam 3.129 e 778 recortes, respectivamente. Checkpoint: `experiments/runs/b_real_cpu_01/best.keras`.

O perfil Windows usa CPU. A RX 6600 não acelera a instalação TensorFlow 2.15 deste projeto. Consulte [ambiente](ambiente.md) para instalar Python 3.11 e dependências.

## Comparar os modelos já treinados

Na raiz do projeto, onde ficam `src`, `scripts` e `.venv`, execute apenas se precisar de uma NOVA rodada. Os resultados atuais já estão em `a_val_02_controlled` e `b_val_reduced_01`. Escolha destinos novos; aguarde cada etapa e pare em caso de erro:

```powershell
$pythonTcc = '.\.venv\Scripts\python.exe'
& $pythonTcc scripts/run_model_a.py --manifest data/splits/experimento/images.csv --model models/model_a/model_trained.keras --split val --output-dir experiments/runs/a_val_nova
if ($LASTEXITCODE -ne 0) { throw 'Falha no A.' }
& $pythonTcc scripts/run_model_b.py --manifest data/splits/experimento/images.csv --checkpoint experiments/runs/b_real_cpu_01/best.keras --split val --image-mode none --output-dir experiments/runs/b_val_nova
if ($LASTEXITCODE -ne 0) { throw 'Falha no B.' }
& $pythonTcc scripts/compare_systems.py --manifest data/splits/experimento/images.csv --annotations data/annotations/experimento_reference_v2.json --predictions-a experiments/runs/a_val_nova/predictions.json --predictions-b experiments/runs/b_val_nova/predictions.json --split val --output experiments/results/comparacao_val_nova.json
```

Ambos recebem as mesmas imagens inteiras. Medir tempo sem exportação de PNG; a exportação pode ser feita depois com `scripts/export_prediction_review.py`. `images.csv` resume estados, decisão, candidatos, tempo e erro; `regions.csv` contém as regiões. `sem_regioes` não significa que a rede classificou negativamente.

Para gerar a figura a partir do relatório já existente, sem executar os modelos:

```powershell
& $pythonTcc scripts/generate_tcc_figures.py --output tcc/figuras/nova_exportacao/comparacao
```

As figuras são de validação preliminar. Todas as 114 imagens são positivas; métricas de detecção com referência parcial não permitem concluir superioridade geral. Os campos externos ficam em análise separada. Veja [revisão geral](revisao_geral.md).

## Nova rodada de treinamento, somente com objetivo definido

Preserve o B atual. Copie `configs/experiment_cpu.json` para outro nome, atribua um `run_name` novo e confira `crop_manifest` e `model_config`. A configuração principal aponta para o B reduzido; o nome de execução existente fica bloqueado contra sobrescrita.

```powershell
& $pythonTcc scripts/start_training.py --experiment configs/minha_nova_rodada.json --check-only
if ($LASTEXITCODE -ne 0) { throw 'Há pendências.' }
& $pythonTcc scripts/start_training.py --experiment configs/minha_nova_rodada.json
```

`minha_nova_rodada.json` é um nome de exemplo que deve ser criado antes. Se alterar anotações ou localização, é necessário gerar novos recortes compatíveis, com destino novo, antes do treino. Manter divisão por imagem original e nunca usar teste para ajustar parâmetros. Rejeitar negativos desconhecidos. Aumentos acontecem somente no treino.

Conferir `metadata.json`: `status: complete`, `synthetic: false`, checkpoint e hashes correspondentes. Preserve a pasta inteira da execução, com configuração, manifestos, histórico e `best.keras`. Não há retomada automática de treino interrompido.

## Transporte

Copie código, configurações, anotações, manifestos, recortes reduzidos e ZIP autorizado. Para comparar, leve também as pastas dos dois modelos. Eles não acompanham automaticamente o Git. O pacote antigo de 25/09 não representa por si só a preparação atual.

No destino, crie a `.venv`, instale `requirements.txt` e execute `scripts/prepare_received.py --archive CAMINHO_DO_ZIP` apenas em uma cópia ainda não preparada. Ele usa a configuração principal e conserva IDs e partições. Se já houver `configs/experiment_cpu_local.json`, confira seu conteúdo; não presuma que uma configuração local antiga aponta para os recortes reduzidos. `scripts/relocate_experiment.py` fornece a alternativa de transporte com mapeamentos explícitos.

Os negativos atuais vêm de poucas imagens; a origem por animal/lâmina não é conhecida. Revisão externa usada para orientar ajustes é desenvolvimento. Não misturar esses campos ao teste nem retreinar automaticamente após inspecionar seus erros.
