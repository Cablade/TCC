# Teste final — Modelo A (entregue) × Modelo B (proposto)

105 imagens murinas de teste (441 pontos publicados), abertas uma única vez após o congelamento do protocolo; 253 negativos humanos de outra aquisição como resultado auxiliar. IC 95% por bootstrap pareado de imagens (10.000 réplicas, semente 20261013).

| Desfecho | A | B | B − A |
| --- | ---: | ---: | ---: |
| Cobertura dos pontos publicados | 0.0% [0.0%; 0.0%] | 91.6% [88.9%; 94.2%] | 91.6% [88.9%; 94.2%] |
| Precisão revisada por região | 0.0% [0.0%; 0.0%] | 53.3% [44.9%; 62.5%] | — |
| Imagens positivas sinalizadas | 17.1% [10.5%; 24.8%] | 100.0% [100.0%; 100.0%] | 82.9% [75.2%; 89.5%] |
| Negativos sem alarme (auxiliar) | 98.8% [97.2%; 100.0%] | 100.0% [100.0%; 100.0%] | 1.2% [0.0%; 2.8%] |
| F1 aproximado (derivado) | 0.00 | 0.67 | — |

Precisão do A: 0 de 23 regiões decididas; IC exato (Clopper-Pearson) 0% [0; 14,8%].
Concordância entre avaliadores (50 regiões): ver data/annotations/precision_teste_final_20261014/kappa_segundo_avaliador/kappa.json.

- **01_desfechos_primarios**: Teste final: 105 imagens murinas, 441 pontos publicados. Cobertura: pontos associados um a um a regiões positivas; IC 95% por bootstrap pareado de imagens (10.000 réplicas). Precisão: amostra revisada às cegas (A: todas as 24 regiões; B: 200 de 3028), IC por bootstrap de imagens.
- **02_decisao_por_imagem**: McNemar exato nas positivas: só A acerta 0, só B acerta 87 (p Holm = 2.6e-26). Negativos de outra aquisição (73 Kaggle, 180 Barcelona) avaliados com os mesmos checkpoints; resultado auxiliar.
- **03_regioes_por_imagem**: Distribuição por imagem. A referência publicada é parcial: com precisão revisada de cerca de 53%, o B sinaliza mais parasitas do que os pontos publicados.
- **04_avanco_treinamento_B**: Desenvolvimento (114 campos murinos de validação e 253 negativos humanos), mesmas imagens nas duas execuções. A mineração e revisão de 517 negativos difíceis murinos (só treino) reduziu as regiões por campo sem perder cobertura e zerou os alarmes em negativos humanos.
- **05_estabilidade_sementes**: Cinco treinos do B com sementes declaradas antes do treino; a semente 42 (destacada) é o modelo avaliado no teste. Validação de 1.070 recortes.
- **06_treinamento_B**: B avaliado (b_hardneg_s42): EfficientNet-B0, AdamW, cosseno, época escolhida por menor val_loss (época 9). Sem histórico de treino comparável do A.
- **07_tempo**: Execução única em CPU, duas threads, B em grafo TensorFlow; inclui a primeira imagem e exclui leitura e exportação. Descritivo, não é benchmark repetido.
- **08_overlay_1**: img_9eb2de4f0e28f94cdaff90b5 (Zenodo, CC BY 4.0). A e B sobre a mesma imagem. Seleção determinística: positivas do teste = a com mais pontos entre as que o A sinalizou, a de carga mediana do B e a com mais pontos; negativas = a primeira de cada fonte por identificador. Ilustrativo, não é amostra representativa.
- **08_overlay_2**: img_0fa0fd46387df17132f14eae (Zenodo, CC BY 4.0). A e B sobre a mesma imagem. Seleção determinística: positivas do teste = a com mais pontos entre as que o A sinalizou, a de carga mediana do B e a com mais pontos; negativas = a primeira de cada fonte por identificador. Ilustrativo, não é amostra representativa.
- **08_overlay_3**: kaggle_original_052188b20794b44c19c78c7b (https://www.kaggle.com/datasets/paultimothymooney/blood-cells). A e B sobre a mesma imagem. Seleção determinística: positivas do teste = a com mais pontos entre as que o A sinalizou, a de carga mediana do B e a com mais pontos; negativas = a primeira de cada fonte por identificador. Ilustrativo, não é amostra representativa.
- **08_overlay_4**: barcelona_original_01b7c6cd88c031177b694cb0 (https://data.mendeley.com/datasets/snkd93bnjr/1). A e B sobre a mesma imagem. Seleção determinística: positivas do teste = a com mais pontos entre as que o A sinalizou, a de carga mediana do B e a com mais pontos; negativas = a primeira de cada fonte por identificador. Ilustrativo, não é amostra representativa.
- **09_recortes_revisados**: Recortes da revisão cega do teste, os primeiros de cada categoria em ordem de identificador (seleção determinística, não escolhida a dedo). O A não teve nenhuma região revisada como parasita.
