# Leitura da comparação A × B — 26/09/2026

Diagnóstico das mesmas 114 imagens de validação. Os hashes dos quatro arquivos de entrada do relatório foram reconferidos, e o checkpoint usado pelo B corresponde ao novo modelo ativo (`5ff1aba014490a5ca8fbc6435e764b417e3e6af687a61245ae8d5337a150ed1a`). Ambos terminaram sem erros e sem exportar PNG durante a inferência. O teste reservado não foi usado.

| Medida | A original | B reduzido |
| --- | ---: | ---: |
| Imagens processadas | 114 | 114 |
| Imagens sinalizadas como suspeitas | 27 | 114 |
| Imagens sem candidatos | 87 | 0 |
| Candidatos | 42 | 25.695 |
| Regiões classificadas como suspeitas | 42 | 7.758 |
| Tempo do algoritmo, sem leitura/gravação/carregamento | 32,37 s | 281,87 s |
| Média do algoritmo por imagem | 0,284 s | 2,473 s |
| Tempo com leitura, sem carregamento do modelo | 43,73 s | 292,42 s |
| Pontos publicados associados a propostas, um a um | 0/450 | 425/450 |
| Pontos publicados associados a regiões suspeitas, um a um | 0/450 | 424/450 |

## Interpretação

O B apresenta maior cobertura dos pontos publicados nesta validação: 424 dos 450 pontos (94,22%) correspondem a regiões sinalizadas. As 42 regiões do A não coincidem com esses pontos pela regra atual. Portanto, o fato de A sinalizar 27 campos positivos não significa que tenha localizado corretamente os parasitas anotados. O resultado merece inspeção visual da localização e das coordenadas antes de entrar como conclusão definitiva no TCC.

A cobertura foi calculada adicionalmente com `src.detection_evaluation.match_one_to_one`, usando as coordenadas originais, inclusão do ponto na caixa com extremos direito/inferior exclusivos e associação de cardinalidade máxima. Trata-se de diagnóstico das anotações disponíveis, não de sensibilidade geral ou qualidade de caixas anatômicas. O relatório principal mantém as métricas de detecção como `null`, pois a referência não é exaustiva. Nenhuma região desconhecida foi convertida em negativo.

Das 7.758 regiões suspeitas de B, 424 foram associadas um a um aos pontos e 7.334 ficaram sem associação. Estas últimas podem incluir duplicações, estruturas confundidas e parasitas não anotados; não podemos chamar todas de falsos positivos nem presumir que sejam verdadeiros positivos. No A, as 42 regiões ficaram sem associação. Para medir precisão e alarmes falsos de detecção, falta revisão suficiente da referência.

Todas as 114 imagens têm rótulo inteiro positivo. Assim, os valores de 100% por imagem do B (e precisão de 100% que o relatório calcula para ambos) não demonstram capacidade de rejeitar campos negativos. Um sistema que sempre declare suspeita também obteria 100% de acerto nesse conjunto. A validação já participou da seleção do B; não é um teste independente.

O B foi aproximadamente 8,71 vezes mais lento no tempo do algoritmo nesta execução. Com leitura, a razão foi aproximadamente 6,69. São razões de medidas distintas: não intercambiá-las. Ambos usaram CPU com duas threads intra/inter-op e não salvaram PNGs, mas as execuções ocorreram em momentos distintos, incluem primeiras chamadas e não representam um benchmark repetido com controle completo de carga e aquecimento.

A redução de propostas foi de 140.005 para 25.695 (81,65%), comparada à contagem geométrica da configuração anterior nos mesmos IDs. A rodada completa anterior não terminou; não há medição completa de seu tempo para calcular uma aceleração observada do B antigo para o novo.

## Próximo passo

Inspecionar a ausência de correspondências de A e uma seleção previamente definida de regiões suspeitas de B no desenvolvimento. Completar uma referência independente de avaliação antes de afirmar ganho em detecção. Não escolher amostras apenas por favorecerem um sistema. Preservar o teste reservado e documentar a falta de identificação por animal/lâmina e o histórico incompleto do A.

Entradas: `comparacao_val_reduced_01.json`, `../runs/a_val_02_controlled/predictions.json`, `../runs/b_val_reduced_01/predictions.json` e `../../data/annotations/experimento_reference_v2.json`.
