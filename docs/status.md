# Estado do experimento e próximos passos

Atualizado em 25/09/2026. **O conjunto inicial está tecnicamente pronto para treinar B pela CPU.** O treino real completo e a avaliação final ainda não foram executados. No computador do amigo, a instalação e a conferência precisam passar novamente.

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

São 7.019 recortes. O manifesto está em `data/splits/experimento/images.csv`, os recortes em `data/processed/b_real_01` e a referência em `data/annotations/experimento_reference_v2.json`. O relatório do lançador registra `ready_to_train: true` no ambiente CPU local e `evaluation_reference_ready: false`.

A divisão preserva o teste original do ZIP; as demais imagens foram separadas em treino/validação com semente 42, estratificando a disponibilidade de negativos revisados. As oito imagens já examinadas não entram no teste.

## Verificação técnica

Passaram 77 testes automatizados e os cinco notebooks executaram em modo sintético. O relatório da suíte está em `experiments/validation/review_20260925_tests.xml`. O treino sintético completo salvou e reabriu o checkpoint, com `reload_equal: true`, em `experiments/runs/b_smoke_review_20260925`. Isso demonstra execução do programa, sem medir desempenho real. O treino completo com pesos ImageNet ainda será executado no destino; o primeiro uso pode exigir download.

## Próximo passo

A transferência foi simulada em outra pasta: ajuste automático de caminhos e conferência do conjunto real passaram. Registro local: `experiments/validation/transfer_readiness_20260925.json`. O ambiente Python utilizado nessa simulação foi o desta máquina; o computador do amigo ainda precisa ser validado.

Envie `entrega_modelo_b_20260925.zip` e o ZIP original `trypoastigote_images.zip`. Seu amigo deve seguir o [guia de treinamento](guia_treinamento.md): instalar Python/dependências, ajustar os caminhos, executar o teste curto, conferir os dados e iniciar o treino. Ao terminar, devolve a pasta inteira `experiments/runs/b_real_cpu_01`.

## Limitações para o TCC

- A fonte descreve sangue de camundongos, mas não temos o vínculo de cada imagem com animal/lâmina individual. `imagem_original` não comprova independência biológica; a divisão poderá precisar de nova versão se esses IDs forem obtidos.
- Os negativos são áreas revisadas de campos positivos, provenientes de apenas oito imagens. Centenas de recortes não equivalem a centenas de amostras independentes. Ampliar a revisão é importante para uma avaliação robusta.
- A localização inicial intersectou 26 de 28 pontos conhecidos nas oito imagens de desenvolvimento. Houve duas falhas; esse diagnóstico não é sensibilidade de detecção. Nenhum parâmetro foi escolhido com base no teste.
- O teste atual contém somente campos positivos, com referência não exaustiva. Não permite concluir especificidade em lâminas negativas nem completar todas as métricas A × B.
- O histórico de treinamento do A e possível sobreposição com esta base ainda precisam ser esclarecidos antes da comparação final. Consulte a [metodologia](metodologia.md).
