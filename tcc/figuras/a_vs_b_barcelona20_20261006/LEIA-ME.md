# Comparação A original × B atual

Avaliação exploratória de desenvolvimento. Mesmos 367 IDs, agrupados em imagens positivas e negativas; teste reservado. Negativos por revisão visual declarada de Caio; referência positiva parcial.

| Grupo | Modelo | Imagens sinalizadas | Regiões positivas | Tempo (s) | Erros |
| --- | --- | ---: | ---: | ---: | ---: |
| Imagens positivas | A original | 27/114 | 42 | 27.62 | 0 |
| Imagens positivas | B atual | 114/114 | 12296 | 273.51 | 0 |
| Imagens negativas | A original | 3/253 | 3 | 0.73 | 0 |
| Imagens negativas | B atual | 3/253 | 5 | 22.79 | 0 |

Uma execução sequencial por modelo; sem exportação PNG, sem aquecimento explícito. Não é benchmark repetido.

Comparação: 114 imagens positivas e 253 imagens negativas. As origens continuam registradas nos manifestos e em `report.json`, sem divisão por fonte nos gráficos. Agrupamento descritivo por classe; não demonstra desempenho clínico nem remove diferenças de aquisição.

B retreinado e A original preservado. Nova inferência dos dois sistemas nas mesmas imagens, após o treino. Imagens usadas no treino permanecem excluídas da comparação. Este lote já foi examinado e constitui desenvolvimento, não teste final independente.

Cobertura dos pontos publicados: A 0/450; B 424/450.

Tempo: execução única, CPU, duas threads, B em grafo; inclui primeira imagem e exclui leitura/exportação. Não atribuir ganhos causalmente apenas à arquitetura, não misturar fontes numa acurácia global nem concluir desempenho clínico. Exemplos escolhidos pelas maiores perdas de cobertura (positivos) e maiores alarmes do B (negativos); não são amostra aleatória.


- 01_sinalizacoes: Mesmos IDs por grupo. Sinalização não comprova localização correta; nos negativos revisados, é falso alarme de desenvolvimento.
- 02_cobertura: Associação de cardinalidade máxima um a um: ponto dentro da caixa semiaberta. Referência parcial; não é sensibilidade geral nem precisão de detecção.
- 03_falsas_regioes: Regiões positivas nas imagens negativas confirmadas visualmente por Caio. Regiões não são pacientes independentes; referência positiva parcial não permite contar falsos positivos nas imagens positivas.
- 04_tempo: Tempo exclui leitura/exportação e inclui primeira imagem. Execução única em CPU, duas threads, B compilado; Tempos herdados da execução original quando houver derivação de subconjunto; consulte o protocolo. Não é benchmark repetido com aquecimento controlado.
- 05_distribuicao_tempo: Dispersão por imagem; caixas não são intervalos de confiança e imagens não são unidades biológicas independentes.
- 06_treinamento_B: B atual: época escolhida por menor val_loss; validação com 1.070 recortes. Sem histórico comparável do A.