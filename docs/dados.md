# Dados e fontes atuais

## Base principal autorizada

`C:/Users/PCZAO/Documents/Caio/trypoastigote_images.zip` corresponde ao [Zenodo 5123062](https://zenodo.org/records/5123062): sangue de camundongos com tripomastigotas de *T. cruzi*. SHA-256: `ce6408615b126178fa0ed96068308bee19a5e2a89330268bbb2e1f4ec88fed1b`; MD5 publicado/local: `3434fa22df03956c256f1203b683517e`.

675 JPEGs, 674 legíveis; `train/field0156.jpg` excluído por falha. Divisão preservada: 455 treino, 114 validação, 105 teste reservado. Divisão por imagem não comprova independência entre animais/lâminas. Inventário: `data/protocol/trypomastigote_verified/`; partições: `data/splits/experimento/`.

Referência principal: `data/annotations/experimento_reference_v2.json`; fontes positivas em `data/annotations/public_import/`. Há 450 pontos na validação. Referência parcial: ausência de ponto não significa ausência de parasita. Imagens privadas descartadas não são fontes ativas; `configs/dataset.json` continua restrito ao ZIP público.

## Negativos originais suplementares

[Blood Cell Images / Paul Mooney](https://www.kaggle.com/datasets/paultimothymooney/blood-cells), versão 6: 366 originais e 12.515 imagens previamente aumentadas. Somente originais foram usados. ZIP: `data/external_candidates/kaggle_blood_cells/source_v6.zip`, SHA-256 `38e9d5fc04e4bfb562dd6f170175e5fb12e8460b5a92cf226b0f96549e280d06`. A fonte credita [BCCD](https://github.com/Shenggan/BCCD_Dataset), que declara MIT; preserve atribuição e termos.

Caio declarou ter examinado e aprovado todas as 366 imagens, sem parasita visível. Evidências: `data/annotations/kaggle_originals_20261005/{inventory.csv,reviewed.json,human_approval_all_originals.json}`. Rótulos negativos vêm dessa revisão visual declarada; rótulos de células do fornecedor não comprovam ausência de *T. cruzi*.

Há 365 grupos por similaridade visual, sem independência biológica demonstrada: 293 originais no treino e 73 na validação. Foram acrescentados 1.172 / 292 recortes, até quatro por imagem. A política `configs/negative_source_kaggle_originals.json` exige hashes, origem, rótulo negativo e limite; impede uso no teste final.

## Dados montados

`data/processed/b_real_01/`: 4.301 recortes de treino (3.053 positivos / 1.248 negativos), 1.070 de validação (740 positivos / 330 negativos). Perfil: `configs/model_b_cpu_original_negatives.yaml`. As cópias de entrada em `experiments/runs/b_val_01/` permanecem imutáveis; `relocation.json` no conjunto registra correção de caminhos e conferência dos pixels.

Usado no novo treinamento de 06/10/2026: `data/processed/b_next/`, com 4.381 recortes de treino (3.053 positivos/1.328 negativos) e a mesma validação de 1.070. Foram acrescentados 80 recortes de 20 originais Barcelona (até quatro por imagem). Os 5.371 recortes anteriores continuam nos arquivos originais, referenciados no novo manifesto, sem duplicar pixels. O checkpoint B atual incorpora esse treinamento: 17 épocas, seleção da décima por `val_loss`. O conjunto `b_real_01` é origem dos arquivos compartilhados e registro dos dados do B anterior arquivado.

## LABIMED arquivado

Os 33 campos foram retirados do fluxo ativo a pedido de Caio após inspeção dos resultados. Não entraram no treino atual. Dados, revisões, código específico e resultados anteriores estão em `archive/labimed_historico_20261005.zip`, com hashes conferidos; registro em `archive/labimed_historico_20261005.json`. O diagnóstico anterior encontrou alarmes em A: 20/33 e B: 33/33. A exclusão deve constar no TCC como alteração posterior do escopo, sem apagar essa evidência.

O [artigo de origem](https://journals.plos.org/plosntds/article?id=10.1371/journal.pntd.0012955) descreve aquisição de fotografias microscópicas por smartphone. Não foi demonstrado que os campos usados eram negativos fabricados a partir de positivos. Campo sem parasita visível não estabelece negatividade do doador. A mudança de aquisição é uma hipótese para investigar os alarmes, sem conclusão causal.

## Ampliação da avaliação negativa

A comparação atual contém 73 originais Kaggle de validação e 180 Barcelona destinados à comparação, além de 114 positivas. Os 293 Kaggle já usados no treino e os 20 Barcelona reservados para o próximo treino ficam excluídos. Versões aumentadas podem repetir seus originais e não contam como novos campos. No ZIP, `dataset2-master/.../labels.csv` não fornece vínculo explícito entre cada JPEG aumentado e o original correspondente; nomes de pastas TRAIN/TEST não garantem disjunção da nossa divisão. Auditoria: `data/annotations/kaggle_originals_20261005/augmentation_audit.json`.

Novos originais revisados e sem sobreposição com treino ampliam a evidência. Variações controladas dos 73 originais de validação podem ser usadas somente em relatório adicional de robustez, preservando o grupo do original e a contagem de originais. Não somar essas versões ao denominador principal.

O histórico fica em `archive/`. Não reclassificar desconhecidos como negativos nem abrir o teste para escolher parâmetros.

## Originais PBC/Barcelona — revisão confirmada

Fonte: [Mendeley Data, versão 1](https://data.mendeley.com/datasets/snkd93bnjr/1), DOI `10.17632/snkd93bnjr.1`, autores Andrea Acevedo, Anna Merino, Santiago Alférez, Ángel Molina, Laura Boldú e José Rodellar, licença CC BY 4.0. A fonte descreve imagens originais de células de indivíduos sem infecção, doença hematológica/oncológica ou tratamento farmacológico; não fornece rótulos de ausência de *T. cruzi*.

Baixadas 200 candidatas (25 por tipo, semente 42), antes de qualquer inferência. Bytes JPEG sem transformação; CRC32 do membro ZIP e SHA-256 registrados. A seleção foi baixada por intervalos HTTP; o hash integral do ZIP não foi verificado. Sem duplicatas exatas de bytes/pixels entre candidatas ou contra as 366 originais Kaggle. Isso não comprova independência de pacientes nem exclui toda similaridade visual.

São imagens de células individuais, com dimensões reais preservadas próximas de 360×363. Não tratá-las como campos inteiros equivalentes às imagens positivas. Caio confirmou ausência de parasita visível nas 200; a referência pendente original, `reviewed.json` e a declaração com hashes em `human_approval_all_originals.json` foram preservadas. O diagnóstico anterior das 200 está em `experiments/comparison/barcelona_a_vs_b/`.

Após esse diagnóstico, Caio autorizou separar **20 para treino e 180 para comparação**. A autorização posterior está em `data/protocol/barcelona_split_20261006/authorization.json`; não modifica nem apaga a autorização histórica de uso exclusivo em avaliação. A nova seleção usa apenas tipos celulares/IDs e semente 42, duas ou três por tipo; não escolhe imagens pelos escores ou erros de A/B. `training.csv`, `comparison.csv` e `assignments.csv` identificam todas as imagens e sua finalidade. `configs/negative_source_barcelona_training.json` autoriza somente os 20 IDs no treino. O B foi retreinado com esses 20 originais em 06/10/2026; os 180 restantes integram a nova comparação por fonte em `a_vs_b_barcelona20_20261006`, junto aos 73 Kaggle e 114 positivas. Como as 200 já foram examinadas, as 180 constituem desenvolvimento e não teste final independente. As previsões do B anterior não são usadas como previsões do novo checkpoint.
