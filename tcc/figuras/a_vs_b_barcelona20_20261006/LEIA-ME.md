# Comparação A original × B atual

Avaliação exploratória de desenvolvimento. Mesmos 367 IDs; fontes separadas e teste reservado. Negativos por revisão visual declarada de Caio; referência positiva parcial.

| Grupo | Modelo | Imagens sinalizadas | Regiões positivas | Tempo (s) | Erros |
| --- | --- | ---: | ---: | ---: | ---: |
| Validação positiva | A original | 27/114 | 42 | 27.62 | 0 |
| Validação positiva | B atual | 114/114 | 12296 | 273.51 | 0 |
| Negativos Kaggle (validação) | A original | 0/73 | 0 | 0.19 | 0 |
| Negativos Kaggle (validação) | B atual | 0/73 | 0 | 11.58 | 0 |
| Negativos Barcelona (comparação) | A original | 3/180 | 3 | 0.54 | 0 |
| Negativos Barcelona (comparação) | B atual | 3/180 | 5 | 11.21 | 0 |

LABIMED retirado a pedido do usuário após inspeção dos resultados. Histórico integral em archive/labimed_historico_20261005.zip. Barcelona: reserva de 20 para próximo treino feita após diagnóstico das 200; 180 na comparação de desenvolvimento. Exclusões não demonstram a causa dos alarmes.

Uma execução sequencial por modelo; sem exportação PNG, sem aquecimento explícito. Não é benchmark repetido.

Separados 20 originais Barcelona para treino; somente os 180 restantes integram esta comparação, junto aos 73 Kaggle. O B foi retreinado com os 20 originais Barcelona (80 recortes negativos), além dos dados anteriores. As previsões desta comparação foram executadas após o novo treino. As 180 imagens já foram examinadas e constituem desenvolvimento, não teste final independente.

Cobertura dos pontos publicados: A 0/450; B 424/450.

Tempo: execução única, CPU, duas threads, B em grafo; inclui primeira imagem e exclui leitura/exportação. Não atribuir ganhos causalmente apenas à arquitetura, não misturar fontes numa acurácia global nem concluir desempenho clínico. Exemplos escolhidos pelas maiores perdas de cobertura (positivos) e maiores alarmes do B (negativos); não são amostra aleatória.


- 01_sinalizacoes: Mesmos IDs por grupo. Sinalização não comprova localização correta; nos negativos revisados, é falso alarme de desenvolvimento.
- 02_cobertura: Associação de cardinalidade máxima um a um: ponto dentro da caixa semiaberta. Referência parcial; não é sensibilidade geral nem precisão de detecção.
- 03_falsas_regioes: Regiões positivas nos negativos confirmados visualmente por Caio. Fontes separadas; regiões não são pacientes independentes.
- 04_tempo: Tempo exclui leitura/exportação e inclui primeira imagem. Execução única em CPU, duas threads, B compilado; Tempos herdados da execução original quando houver derivação de subconjunto; consulte o protocolo. Não é benchmark repetido com aquecimento controlado.
- 05_distribuicao_tempo: Dispersão por imagem; caixas não são intervalos de confiança e imagens não são unidades biológicas independentes.
- 06_treinamento_B: B atual: época escolhida por menor val_loss; validação com 1.070 recortes. Sem histórico comparável do A.