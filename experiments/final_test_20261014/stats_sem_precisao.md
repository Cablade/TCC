# Análise pareada A × B (teste_final)

358 imagens (105 positivas, 253 negativas); bootstrap com 10000 réplicas, semente 20261013.

| Métrica | A | B | B − A (IC 95%) |
| --- | ---: | ---: | ---: |
| Cobertura dos pontos | 0.0% [0.0%; 0.0%] | 91.6% [88.9%; 94.2%] | 91.6% [88.9%; 94.2%] |
| Imagens positivas sinalizadas | 17.1% [10.5%; 24.8%] | 100.0% [100.0%; 100.0%] | 82.9% [75.2%; 89.5%] |
| Imagens negativas sem alarme | 98.8% [97.2%; 100.0%] | 100.0% [100.0%; 100.0%] | 1.2% [0.0%; 2.8%] |
| Regiões positivas por imagem negativa | 0.012 [0.000; 0.028] | 0.000 [0.000; 0.000] | -0.012 [-0.028; 0.000] |

| McNemar (decisão por imagem) | Só A acerta | Só B acerta | p exato | p Holm |
| --- | ---: | ---: | ---: | ---: |
| positivas | 0 | 87 | 1.292e-26 | 2.585e-26 |
| negativas | 0 | 3 | 0.25 | 0.25 |
| todas | 0 | 90 | 1.616e-27 | descritivo |

Registro intermediário de 14/10/2026, mantido como gerado. Intervalos de largura nula: ver a nota de correção em `stats.md`.
