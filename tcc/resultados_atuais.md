# Teste final — A (como entregue) × B (proposto)

Teste aberto uma única vez em 14/10/2026, depois do congelamento do protocolo (`data/protocol/protocolo_congelado.json`). 105 imagens murinas de teste do Zenodo 5123062, com 441 pontos publicados, e 253 negativos humanos de outra aquisição (73 Kaggle, 180 Barcelona) como resultado auxiliar. Os mesmos IDs para A e B. Intervalos de 95% por bootstrap pareado de imagens (10.000 réplicas, semente 20261013).

| Desfecho | A | B | B − A |
| --- | ---: | ---: | ---: |
| Cobertura dos pontos publicados | 0,0% [0,0%; 0,0%] | 91,6% [88,9%; 94,2%] | 91,6% [88,9%; 94,2%] |
| Precisão revisada por região | 0,0% (0/23) | 53,3% [44,9%; 62,5%] | — |
| Imagens positivas sinalizadas | 17,1% [10,5%; 24,8%] | 100,0% [100,0%; 100,0%] | 82,9% [75,2%; 89,5%] |
| Negativos sem alarme (auxiliar) | 98,8% [97,2%; 100,0%] | 100,0% [100,0%; 100,0%] | 1,2% [0,0%; 2,8%] |
| Regiões positivas por imagem negativa | 0,012 | 0,000 | −0,012 [−0,028; 0,000] |

Decisão por imagem (McNemar exato, correção de Holm na família positivas/negativas): nas positivas, só B acerta 87 e só A acerta 0 (p Holm = 2,6e-26); nas negativas, 3 × 0 (p = 0,25).

Precisão: o A teve todas as suas 24 regiões revisadas (23 decididas, nenhuma parasita; IC exato de Clopper-Pearson 0% [0; 14,8%]). Do B foi revisada uma amostra aleatória de 200 das 3.028 regiões positivas, em 79 imagens (98 parasitas, 86 não parasitas, 16 incertas); no pior caso, contando as incertas como erro, a precisão é 49,0%. A revisão foi cega quanto ao sistema, ao escore e à existência de ponto publicado. Um segundo avaliador revisou 50 regiões: kappa de Cohen 0,73 em três categorias e 0,90 no binário sem incertas.

Execução: A sem nenhuma região em 87 das 105 imagens; B sem erros, 22.847 candidatos e 3.028 regiões positivas. Tempo de algoritmo em CPU, execução única: 22,2 s para A e 226,2 s para B (medianas de 0,17 s e 1,97 s por imagem). Não é benchmark repetido.

## Como ler

- A referência positiva é parcial. Uma região sem ponto publicado não é automaticamente falso positivo; por isso a precisão vem da revisão humana, e a precisão em torno de 53% indica que o B encontra parasitas não anotados.
- Os negativos são células humanas de outra aquisição. Mostram que o B não dispara fora do domínio murino, mas não substituem negativos do mesmo tipo de imagem dos positivos.
- O A não gera regiões na maioria dos campos murinos. Nas lâminas da FIOCRUZ, ele gera regiões só nas versões pré-processadas, o que sugere falta de transferência para esta aquisição, e não erro de reprodução (sem referência anotada nessas lâminas, não se mede a qualidade dessas regiões).
- Nada aqui é desempenho clínico: as imagens vêm de camundongos, e a divisão por imagem não garante independência entre animais ou lâminas.

## Antes e depois da correção do viés (desenvolvimento)

Nas mesmas 367 imagens de desenvolvimento, o B anterior marcava 12.296 regiões positivas nos 114 campos murinos e alarmava em 3 dos 253 negativos humanos. Com os 517 negativos difíceis murinos no treino, passou a 3.232 regiões e nenhum alarme, mantendo a cobertura (424 e 423 de 450 pontos). O A ficou igual: 27 de 114 positivas sinalizadas, 0 pontos cobertos e 3 alarmes.

Fontes: `experiments/final_test_20261014/stats.md`, `data/annotations/precision_teste_final_20261014/`, `experiments/comparison/a_vs_b_{barcelona20_20261006,hardneg_20261013}/summary.csv`. Figuras: [tcc/figuras/teste_final_20261014](figuras/teste_final_20261014/LEIA-ME.md).
