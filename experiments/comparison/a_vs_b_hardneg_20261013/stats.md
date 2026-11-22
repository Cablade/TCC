# Análise pareada A × B (desenvolvimento)

367 imagens (114 positivas, 253 negativas); bootstrap com 10000 réplicas, semente 20261013.

| Métrica | A | B | B − A (IC 95%) |
| --- | ---: | ---: | ---: |
| Cobertura dos pontos | 0.0% [0.0%; 0.0%] | 94.0% [91.9%; 96.0%] | 94.0% [91.9%; 96.0%] |
| Imagens positivas sinalizadas | 23.7% [15.8%; 31.6%] | 100.0% [100.0%; 100.0%] | 76.3% [68.4%; 84.2%] |
| Imagens negativas sem alarme | 98.8% [97.2%; 100.0%] | 100.0% [100.0%; 100.0%] | 1.2% [0.0%; 2.8%] |
| Regiões positivas por imagem negativa | 0.012 [0.000; 0.028] | 0.000 [0.000; 0.000] | -0.012 [-0.028; 0.000] |

| McNemar (decisão por imagem) | Só A acerta | Só B acerta | p exato | p Holm |
| --- | ---: | ---: | ---: | ---: |
| positivas | 0 | 87 | 1.292e-26 | 2.585e-26 |
| negativas | 0 | 3 | 0.25 | 0.25 |
| todas | 0 | 90 | 1.616e-27 | descritivo |
