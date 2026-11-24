# Análise pareada A × B (teste_final)

358 imagens (105 positivas, 253 negativas); bootstrap com 10000 réplicas, semente 20261013.

| Métrica | A | B | B − A (IC 95%) |
| --- | ---: | ---: | ---: |
| Cobertura dos pontos | 0.0% [0.0%; 3.5%]¹ | 91.6% [88.9%; 94.2%] | 91.6% [88.9%; 94.2%] |
| Imagens positivas sinalizadas | 17.1% [10.5%; 24.8%] | 100.0% [96.5%; 100.0%]¹ | 82.9% [75.2%; 89.5%] |
| Imagens negativas sem alarme | 98.8% [97.2%; 100.0%] | 100.0% [98.6%; 100.0%]¹ | 1.2% [0.0%; 2.8%] |
| Regiões positivas por imagem negativa | 0.012 [0.000; 0.028] | 0.000² | -0.012 [-0.028; 0.000] |

| McNemar (decisão por imagem) | Só A acerta | Só B acerta | p exato | p Holm |
| --- | ---: | ---: | ---: | ---: |
| positivas | 0 | 87 | 1.292e-26 | 2.585e-26 |
| negativas | 0 | 3 | 0.25 | 0.25 |
| todas | 0 | 90 | 1.616e-27 | descritivo |

Precisão revisada de A: 0.0% [0.0%; 14.8%]¹, 24 regiões em 18 imagens (1 incertas).

Precisão revisada de B: 53.3% [44.9%; 62.5%], 200 regiões em 79 imagens (16 incertas).

## Nota de correção dos intervalos (24/11/2026)

Com proporção observada de 0% ou 100%, o bootstrap percentil tem largura nula e não representa a incerteza. Esses intervalos (¹) foram substituídos pelo intervalo exato de Clopper-Pearson de 95%, com n = 105 imagens positivas, 253 negativas ou 23 regiões decididas (precisão de A), como na Tabela 4 da monografia. Estimativas pontuais, diferenças B − A e testes de McNemar não mudaram.

| Medida | Antes (bootstrap) | Depois (exato) |
| --- | ---: | ---: |
| Cobertura, A | [0.0%; 0.0%] | [0.0%; 3.5%] |
| Positivas sinalizadas, B | [100.0%; 100.0%] | [96.5%; 100.0%] |
| Negativas sem alarme, B | [100.0%; 100.0%] | [98.6%; 100.0%] |
| Precisão revisada, A (0/23) | [0.0%; 0.0%] | [0.0%; 14.8%] |

² É uma média de contagens, não uma proporção: o Clopper-Pearson não se aplica e o intervalo nulo do bootstrap foi retirado. `stats.json` conserva a saída original do `paired_analysis.py` (congelado), inclusive os intervalos degenerados.
