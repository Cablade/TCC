# Estado do experimento e próximos passos

Atualizado em 26/09/2026. **O primeiro treinamento real do B foi concluído e recebido.** O modelo foi reaberto nesta máquina e reproduziu 98,70% de acerto nos recortes de validação. A avaliação final permanece pendente; as 105 imagens de teste não foram avaliadas. Consulte o [relatório da execução](../experiments/validation/b_real_cpu_01_received_20260926/relatorio.md).

## Revisão e correções

- Removidos resultados antigos que ainda continham 58 imagens privadas de sobreposição, além dos registros associados. O pacote de envio inclui apenas recortes do ZIP público autorizado.
- A referência v2 conserva os 2.715 pontos publicados, as 29 áreas negativas revisadas e o histórico da revisão humana. A incorporação da revisão agora confere inventário, origem, dimensões e positivos, preservando negativos já existentes.
- A preparação e o treino real verificam o SHA-256 do ZIP autorizado e a reserva das imagens examinadas para desenvolvimento. Recortes idênticos não podem atravessar partições; rótulos fracionários ou incompatíveis são rejeitados.
- A extração de treinamento exclui o teste. Checkpoints sintéticos, incompletos ou alterados são bloqueados para o teste real. Interrupções passam a registrar `interrupted`.
- O limite de dois núcleos fica restrito ao teste curto; o treino real permite que o TensorFlow gerencie o paralelismo da CPU.
- O transporte ganhou um comando que preserva IDs, rótulos e divisão e confere os arquivos no novo caminho.

## Dados preparados

| Conjunto | Imagens | Recortes positivos | Recortes negativos | Imagens com negativos revisados |
| --- | ---: | ---: | ---: | ---: |
| Treino | 455 | 5.012 | 625 | 6 |
| Validação | 114 | 1.196 | 186 | 2 |
| Teste reservado | 105 | Não extraídos | Não extraídos | 0 |

São 7.019 recortes. O manifesto está em `data/splits/experimento/images.csv`, os recortes em `data/processed/b_real_01` e a referência em `data/annotations/experimento_reference_v2.json`. O relatório de prontidão de 25/09 aprovou os dados e o ambiente; após receber a execução, o mesmo nome de pasta fica bloqueado para evitar sobrescrita. A referência de avaliação final continua incompleta.

A divisão preserva o teste original do ZIP; as demais imagens foram separadas em treino/validação com semente 42, estratificando a disponibilidade de negativos revisados. As oito imagens já examinadas não entram no teste.

## Verificação técnica

Na revisão de 25/09, passaram 77 testes automatizados e os cinco notebooks executaram em modo sintético. O relatório da suíte está em `experiments/validation/review_20260925_tests.xml`. Em 26/09, foram conferidos o ZIP recebido, os hashes do checkpoint e dos manifestos, as anotações, a configuração, as partições e o histórico. O checkpoint real foi reaberto e a validação reproduzida: 1.364/1.382 acertos, com cinco falsos positivos e treze falsos negativos em recortes. Auditoria: `experiments/validation/b_real_cpu_01_received_20260926/audit.json`.

## Próximo passo

O modelo real está em `experiments/runs/b_real_cpu_01/best.keras`, junto de todo o histórico recebido. Foram concluídas 26 épocas na CPU em aproximadamente 52 minutos; a melhor foi a época 19, seguida por sete épocas sem melhora. Não é necessário refazer esse treino. Preserve a execução; qualquer rodada futura deve usar outro nome.

Examine os erros e o comportamento em imagens inteiras de desenvolvimento/validação. Prepare a referência necessária para a comparação A × B e esclareça a independência das amostras e o histórico do A antes de avaliar o teste reservado. A acurácia de recortes de validação não substitui essa etapa.

## Limitações para o TCC

- A fonte descreve sangue de camundongos, mas não temos o vínculo de cada imagem com animal/lâmina individual. `imagem_original` não comprova independência biológica; a divisão poderá precisar de nova versão se esses IDs forem obtidos.
- Os negativos são áreas revisadas de campos positivos, provenientes de apenas oito imagens. Centenas de recortes não equivalem a centenas de amostras independentes. Ampliar a revisão é importante para uma avaliação robusta.
- A localização inicial intersectou 26 de 28 pontos conhecidos nas oito imagens de desenvolvimento. Houve duas falhas; esse diagnóstico não é sensibilidade de detecção. Nenhum parâmetro foi escolhido com base no teste.
- O teste atual contém somente campos positivos, com referência não exaustiva. Não permite concluir especificidade em lâminas negativas nem completar todas as métricas A × B.
- O histórico de treinamento do A e possível sobreposição com esta base ainda precisam ser esclarecidos antes da comparação final. Consulte a [metodologia](metodologia.md).
