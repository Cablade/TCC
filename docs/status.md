# Estado atual — 06/10/2026

## Reserva 20/180 — preparada, sem treinamento

Caio autorizou reservar 20 dos 200 originais Barcelona para os negativos do próximo treino e acrescentar as 180 restantes à comparação com Kaggle. Seleção com semente 42, duas ou três imagens por tipo celular, sem consultar previsões. Divisão e autorização: `data/protocol/barcelona_split_20261006/`.

- Próximo conjunto: `data/processed/b_next/`, com 4.381 recortes de treino (3.053 positivos/1.328 negativos) e os mesmos 1.070 de validação. Foram acrescentados 80 recortes negativos, até quatro por original; recortes anteriores compartilhados sem copiar pixels.
- O perfil `configs/experiment_b_original_negatives.json` aponta para esse conjunto. Fontes autorizadas por `configs/negative_sources_originals.json`; Barcelona aceita somente os 20 IDs reservados, apenas no treino, com referência negativa revisada e hashes.
- Comparação atual: `experiments/comparison/a_vs_b_barcelona/`, mesmos 367 IDs para A/B: 114 positivas, 73 negativas Kaggle e 180 Barcelona. Nenhuma imagem reservada para treino nem seus grupos/bytes/pixels está na comparação.
- Resultados antes de novo treino: Kaggle 0/73 alarmes em ambos; Barcelona A 3/180 e B 24/180. Previsões anteriores reutilizadas com conferência de referências, conteúdo e checkpoints. Tempos herdados de duas execuções; não representam benchmark novo.
- **Nenhum novo treino foi iniciado**, nenhum peso alterado. `b_real_01` e entradas históricas do B permanecem preservados. As 105 imagens do teste final continuam reservadas; as 180 já examinadas são desenvolvimento.

[Comparação atual e figuras](../tcc/figuras/a_vs_b_barcelona/index.html). O diagnóstico das 200 Barcelona e a robustez sobre os 187 originais anteriores permanecem identificados como histórico; não incluir as 20 de treino em uma avaliação futura.

[Conferir a divisão em imagens](../data/protocol/barcelona_split_20261006/index.html). Validação: 129 testes passaram; 331 links de páginas/imagens/arquivos conferidos, recortes anteriores preservados, modelos com hashes iguais e nenhum `experiments/runs/b_next` criado. Dados e ambiente prontos, sem treino executado. Evidência: `experiments/validation/barcelona_split_20261006/audit.json`.

## Histórico do B atual e das avaliações anteriores

Somente **A original** (`models/model_a/model_trained.keras`) e **B atual** (`experiments/runs/b_val_01/best.keras`) participam da comparação.

O B terminou sem erros: 16 épocas, melhor época 9 por `val_loss` (0,21374), 30,61 minutos de treino em CPU. SHA-256: `24c9507aebfbf87553df5d15320d04e80d721b4c6c0954713ea381b44c908b08`. A acurácia selecionada foi 99,25% **nos recortes de validação**, distinta da avaliação de imagens inteiras.

## Dados usados no treinamento já concluído

- Treino: 4.301 recortes, 3.053 positivos / 1.248 negativos.
- Validação: 1.070 recortes, 740 positivos / 330 negativos.
- Conjunto montado: `data/processed/b_real_01/`.
- Negativos suplementares: 366 originais revisados por Caio, 1.464 recortes, no máximo quatro por imagem. As 12.515 versões previamente aumentadas ficaram fora.
- Cada recorte uma vez por época, sem oversampling/undersampling, com pesos por classe limitados a 4. Rotações e espelhamentos de treino não multiplicam o inventário.
- Teste principal: 105 imagens reservadas.

Os caminhos quebrados pela reorganização local foram corrigidos, preservando pixels, rótulos, grupos e partições. Registro: `data/processed/b_real_01/relocation.json`. As cópias de entrada do treinamento permanecem intactas.

## Comparação anterior de 187 imagens

Lote anterior de 187 imagens: 114 positivas e 73 negativas originais Kaggle da validação. Resultados preservados em `experiments/comparison/a_vs_b/`: A teve 0/450 pontos associados e B 424/450; ambos tiveram zero alarmes em 73 negativas Kaggle. Nenhum erro de execução. [Gráficos históricos](../tcc/figuras/a_vs_b/index.html); o [texto atual](../tcc/resultados_atuais.md) incorpora as 180 Barcelona restantes.

LABIMED foi excluído a pedido de Caio **após inspeção dos resultados**. O diagnóstico anterior (A: 20/33 alarmes; B: 33/33) e seus dados estão preservados em `archive/labimed_historico_20261005.zip`. Os campos não participaram do treino do B. Sua exclusão muda o escopo; não comprova a causa dos alarmes nem melhora os pesos. O artigo descreve fotografias microscópicas, sem comprovação de fabricação artificial dos campos usados.

As previsões atuais são um subconjunto conferido da execução anterior: mesmos pixels, IDs, referências, decisões e checkpoints. Os tempos por imagem foram herdados, não remedidos; não tratar a soma como novo benchmark. Protocolo e hashes registram a derivação.

Medir cobertura dos 450 pontos, sinalizações, falsos alarmes nos negativos, regiões, erros e tempo. Referência positiva parcial não permite chamar toda região sem associação de falso positivo. Negativos são revisão visual declarada por Caio, não laudo clínico. Desenvolvimento/validação não é teste final independente.

## Limpeza

Histórico e arquivos obsoletos foram compactados e conferidos em `archive/limpeza_fluxo_atual_20261005.zip`; registro em `archive/limpeza_fluxo_atual_20261005.json`. Galeria duplicada, caches e temporários foram retirados. Python e ambiente preservados.

Próximo: conferir exemplos e erros, atualizar texto/figuras, fechar limitações com o orientador e congelar o protocolo antes do teste final.

A prévia dos 1.464 negativos compartilha os PNGs do conjunto montado, eliminando cópias duplicadas sem mudar pixels ou revisão. Registro: `archive/recortes_compartilhados_20261005.json`.

Conferência final: 106 testes passaram, os dois checkpoints preservam seus hashes, os 5.371 recortes estão válidos e todas as imagens das prévias possuem arquivos existentes. Evidência: `experiments/validation/cleanup_current_20261005/audit.json`.

## Ampliação da avaliação

Teste adicional concluído sem erros: as mesmas três variações para positivos e negativos — rotação 90°, espelho horizontal e brilho × 0,85. 187 originais/561 versões; relato separado em `robustez_a_vs_b`, sem retreinar modelos ou abrir teste final. Não confundir vistas repetidas com novos campos.

Novos candidatos baixados: 200 originais PBC/Barcelona, 25 por tipo celular, da fonte [Mendeley](https://data.mendeley.com/datasets/snkd93bnjr/1), CC BY 4.0. São células individuais próximas de 360×363, com dimensões reais preservadas (360×360, 360×363 e 366×369 neste lote), não campos inteiros, e Caio confirmou nesta conversa ausência de parasita visível nas 200 imagens. Lote em `data/annotations/barcelona_originals_review/`; procedência e CRC por membro no relatório de preparo. Sua avaliação foi separada por fonte; os rótulos de tipos celulares não são rótulos de Chagas.

Verificação após a mudança de escopo: 109 testes passaram; os 187 IDs estão pareados entre A e B, 30 arquivos da prévia existem e LABIMED permanece somente no histórico. Evidência: `experiments/validation/kaggle_scope_20261005/audit.json`.

Caio aprovou as 200 novas originais na conversa iniciada em 05/10/2026. Declaração e hashes registrados em `data/annotations/barcelona_originals_review/human_approval_all_originals.json`; fonte pendente original preservada e referência revisada separada. Avaliação externa A/B concluída em `experiments/comparison/barcelona_a_vs_b/`, sem alterar os 187 originais do teste adicional de robustez.

## Resultados da ampliação

- Robustez: 187 originais, 561 versões (rotação 90°, espelho horizontal e brilho × 0,85), A/B sem erros. B associou 424, 424, 423 e 430 dos 450 pontos nos originais e nas três condições. A associou 0, 0, 0 e 6. Nos 73 negativos Kaggle, A sinalizou um caso no brilho reduzido e B um no espelhamento. As duas ocorrências pertencem ao desenvolvimento, com referência herdada dos originais.
- Decisão binária positiva estável nas quatro condições: B 114/114; A 63/114. Estabilidade do A inclui imagens que ficaram sempre sem sinalização; não é medida de acerto.
- Novos negativos PBC/Barcelona, 200 originais revisados: A sinalizou 3/200 (3 regiões), B 28/200 (42 regiões), sem erros. Fonte humana/CellaVision e células enquadradas; não misturar com os campos positivos para uma acurácia global.

B apresentou maior cobertura positiva, mas mais falsos alarmes na nova fonte; a comparação não sustenta superioridade universal. Modelos e treino permanecem os mesmos. Página de acesso: [todas as figuras](../tcc/figuras/index.html). A galeria externa inclui todos os originais com alarme em A ou B e todos os seus 45 recortes positivos, sem marcações.

Verificação da ampliação: 113 testes passaram, três avaliações pareadas sem erros, apenas dois checkpoints com hashes preservados e todos os links de imagens/PDFs das páginas existem. Auditoria: `experiments/validation/expanded_comparison_20261006/audit.json`.
