# Comparação A original × B atual

Avaliação exploratória de desenvolvimento. Mesmos 367 IDs; fontes separadas e teste reservado. Negativos por revisão visual declarada de Caio; referência positiva parcial.

| Grupo | Modelo | Imagens sinalizadas | Regiões positivas | Tempo (s) | Erros |
| --- | --- | ---: | ---: | ---: | ---: |
| Validação positiva | A original | 27/114 | 42 | 32.65 | 0 |
| Validação positiva | B atual | 114/114 | 9716 | 284.98 | 0 |
| Negativos Kaggle (validação) | A original | 0/73 | 0 | 0.24 | 0 |
| Negativos Kaggle (validação) | B atual | 0/73 | 0 | 12.08 | 0 |
| Negativos Barcelona (comparação) | A original | 3/180 | 3 | 1.01 | 0 |
| Negativos Barcelona (comparação) | B atual | 24/180 | 38 | 12.35 | 0 |

LABIMED retirado a pedido do usuário após inspeção dos resultados. Histórico integral em archive/labimed_historico_20261005.zip. Barcelona: reserva de 20 para próximo treino feita após diagnóstico das 200; 180 na comparação de desenvolvimento. Exclusões não demonstram a causa dos alarmes.

Tempos herdados de duas execuções anteriores, preservados por imagem e fonte. Não houve nova inferência; somas não representam um benchmark do lote combinado.

Reservados 20 originais Barcelona para os negativos do próximo treino; somente os 180 restantes integram esta comparação, junto aos 73 Kaggle. O B mostrado ainda é o checkpoint anterior à reserva: nenhum novo treino foi executado. As 180 imagens já foram examinadas e constituem desenvolvimento, não teste final independente.

Cobertura dos pontos publicados: A 0/450; B 424/450.

Tempo: execução única, CPU, duas threads, B em grafo; inclui primeira imagem e exclui leitura/exportação. Não atribuir ganhos causalmente apenas à arquitetura, não misturar fontes numa acurácia global nem concluir desempenho clínico. Exemplos escolhidos pelas maiores perdas de cobertura (positivos) e maiores alarmes do B (negativos); não são amostra aleatória.
