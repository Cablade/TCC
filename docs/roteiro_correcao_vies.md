# Roteiro — correção do viés de origem antes do teste final

> **Concluído em 14/10/2026.** Todos os passos foram executados; o estado e os resultados estão em [status.md](status.md). Mantido como registro dos comandos usados.

> 13/10/2026. Responde à revisão de 13/10/2026: o B atual separa a origem das imagens (camundongo × humano), não a presença de parasita. A ordem abaixo é obrigatória; o teste de 105 imagens só é aberto no passo 9.

Execute na raiz do TCC, com o mesmo Python do guia:

```powershell
$py = '.\.venv\Scripts\python.exe'
```

## 0. Renomear a pasta do B em uso (uma vez)

A pasta `b_val_01` passa a se chamar `b_atual`, nome do lugar fixo do B em uso; o treino contido nela continua identificado por `metadata.json` → `run_name` (`b_next`).

```powershell
Rename-Item experiments\runs\b_val_01 b_atual
```

## 1. Minerar candidatos a negativos difíceis (só treino, só camundongo)

```powershell
& $py scripts/mine_hard_negatives.py `
    --image-manifest data/processed/b_next/images.csv `
    --annotations data/processed/b_next/annotations.json `
    --checkpoint experiments/runs/b_atual/best.keras `
    --output-dir data/annotations/hard_negatives_20261013
```

Roda o B nas 455 imagens murinas de treino (CPU, alguns minutos), guarda as regiões sinalizadas sem ponto publicado e sorteia até 2 por imagem, no máximo 600. A seleção é uniforme, não pelos maiores escores, para não encher a fila de parasitas não anotados. Nenhuma imagem de validação ou de teste é lida.

## 2. Revisar as regiões (decisão humana)

Abra `data/annotations/hard_negatives_20261013/revisao.html` no navegador. Para cada região: **1** sem parasita, **2** contém parasita, **3** incerto. Só "sem parasita" entra no treino. O progresso fica salvo no navegador; ao terminar, clique em "Exportar decisões" e salve `decisions.json` na mesma pasta da fila.

## 3. Montar o novo conjunto de treino

```powershell
& $py scripts/prepare_hard_negative_dataset.py `
    --queue data/annotations/hard_negatives_20261013/queue.json `
    --decisions data/annotations/hard_negatives_20261013/decisions.json `
    --destination data/processed/b_hardneg
```

Acrescenta os negativos confirmados à referência (como `negative_regions` revisadas), gera os recortes com a mesma localização e confere pixels, rótulos e partições. A validação não muda. `assembly.json` informa a nova proporção de negativos murinos × humanos e lista as regiões marcadas como "contém parasita".

## 4. Treinar o B com as cinco sementes

```powershell
foreach ($s in 42, 123, 456, 789, 1024) {
  & $py scripts/train_model_b.py --run-name "b_hardneg_s$s" --seed $s `
      --image-manifest data/processed/b_hardneg/images.csv `
      --crop-manifest data/processed/b_hardneg/crops.csv `
      --annotations data/processed/b_hardneg/annotations.json `
      --supplementary-policy configs/negative_sources_originals.json
}
& $py scripts/summarize_seeds.py experiments/runs/b_hardneg_s42 experiments/runs/b_hardneg_s123 `
    experiments/runs/b_hardneg_s456 experiments/runs/b_hardneg_s789 experiments/runs/b_hardneg_s1024
```

Cerca de 15 minutos por semente em CPU. A semente 42 é o modelo principal declarado no [plano estatístico](plano_estatistico.md); as outras medem estabilidade.

## 5. Promover a semente 42 e repetir a comparação de desenvolvimento

```powershell
& $py scripts/promote_model_b.py --candidate experiments/runs/b_hardneg_s42 `
    --archive archive/b_vies_origem_20261013
& $py scripts/compare_model_versions.py --output-dir experiments/comparison/a_vs_b_hardneg_20261013
& $py scripts/paired_analysis.py `
    --per-image experiments/comparison/a_vs_b_hardneg_20261013/per_image.csv `
    --output experiments/comparison/a_vs_b_hardneg_20261013/stats.json
```

Depois da promoção, a semente 42 fica em `experiments/runs/b_atual` (com `run_name` `b_hardneg_s42`) e o B com viés vai para o arquivo. Compare com a execução de 06/10/2026: regiões positivas por campo murino, cobertura dos 450 pontos e alarmes em Kaggle/Barcelona.

## 6. Estimar a precisão na validação (revisão cega de 200 regiões)

```powershell
& $py scripts/sample_precision_review.py sample `
    --regions experiments/comparison/a_vs_b_hardneg_20261013/B/regions.csv `
    --image-manifest experiments/comparison/a_vs_b_hardneg_20261013/images.csv `
    --output-dir data/annotations/precision_B_val_20261013 --n 200
```

Revise em `revisao.html`, exporte `decisions.json` e calcule:

```powershell
& $py scripts/sample_precision_review.py estimate `
    --queue data/annotations/precision_B_val_20261013/queue.json `
    --decisions data/annotations/precision_B_val_20261013/decisions.json
```

Se a precisão continuar muito baixa, a decisão de repetir os passos 1–5 com o novo B (segunda rodada de mineração, ainda só no treino) é tomada aqui, antes do congelamento.

## 7. Verificar o A no domínio original

```powershell
& $py scripts/check_model_a_original_domain.py `
    --images C:\caminho\para\VisionCruzi\imagens_de_exemplo `
    --zenodo-manifest experiments/comparison/a_vs_b_hardneg_20261013/images.csv --zenodo-limit 10 `
    --output-dir experiments/validation/model_a_original_domain_20261013
```

Esperado: o A gera e classifica regiões nas imagens do VisionCruzi. Na comparação de 06/10, os campos murinos tinham mediana de 36,5 componentes de núcleo antes do filtro de área (450–1100 px) e só 27 de 114 imagens ficaram com algum candidato; `summary.json` compara a área desses componentes nos dois domínios.

## 8. Congelar o protocolo

```powershell
& $py scripts/freeze_protocol.py --checkpoint-b experiments/runs/b_atual/best.keras `
    --precision-validation data/annotations/precision_B_val_20261013/precision.json `
    --model-a-check experiments/validation/model_a_original_domain_20261013/summary.json `
    --seeds experiments/runs/b_hardneg_s123 experiments/runs/b_hardneg_s456 `
            experiments/runs/b_hardneg_s789 experiments/runs/b_hardneg_s1024 `
    --extra data/processed/b_hardneg/images.csv data/processed/b_hardneg/annotations.json `
    --confirm "congelar"
```

Faça um commit logo depois do congelamento.

## 9. Abrir o teste de 105 imagens (uma única vez)

Executar A e B com `--split test`, gerar `per_image.csv`, sortear a amostra de precisão do teste (`sample_precision_review.py sample --final-test`), revisar às cegas e rodar `paired_analysis.py --evaluation-set teste_final`. Nenhuma escolha de modelo, limiar ou localização é feita depois de ver o teste.
