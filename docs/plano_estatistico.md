# Plano de análise estatística — comparação dos sistemas A e B

> Versão 1, 13/10/2026. Elaborado em resposta à solicitação do orientador, Prof. Rogério Mandelli, de um plano de análise estatística delimitado. Este documento será congelado, com seu SHA-256 registrado em `data/protocol/protocolo_congelado.json` (`scripts/freeze_protocol.py`), antes da abertura do conjunto de teste de 105 imagens. Alterações posteriores à abertura do teste serão relatadas como desvios do protocolo.

## 1. Pergunta e unidade de análise

A pergunta comparativa é: nas mesmas imagens microscópicas inteiras, como o sistema de referência (A) e o sistema proposto (B) diferem quanto à localização dos parasitas anotados, à proporção de regiões sinalizadas que de fato contêm parasitas e à decisão por imagem?

A **unidade de análise e de reamostragem é a imagem inteira**. A base não identifica animal nem lâmina; por isso, cada imagem original constitui seu próprio grupo, limitação declarada no texto. Regiões, pontos anotados, recortes, aumentos de dados e sementes de treinamento **não** são tratados como observações independentes: múltiplas regiões de uma mesma imagem compartilham preparação, iluminação e aquisição.

Os dois sistemas são avaliados sobre exatamente os mesmos identificadores de imagem. Toda estimativa de diferença preserva esse pareamento.

## 2. Conjuntos de avaliação

| Conjunto | Composição | Papel na análise |
| --- | --- | --- |
| Teste principal | 105 imagens murinas (Zenodo), todas com parasitas e 441 pontos publicados | Resultado principal; aberto uma única vez, após o congelamento |
| Validação | 114 imagens murinas | Seleção do modelo, estimativa de precisão para ajuste do protocolo, variação entre sementes |
| Negativos de outra aquisição | 253 imagens humanas (73 Kaggle, 180 Barcelona), já examinadas | Teste auxiliar de alarmes falsos em outra fonte; não é teste independente |
| LABIMED | 33 imagens de outra aquisição, já examinadas | Resultado descritivo de transferência, mantido no texto |

Como o teste principal contém apenas campos positivos, a especificidade por imagem não pode ser estimada nele. Os alarmes falsos são medidos de duas formas complementares: (i) pela precisão por região nos próprios campos murinos, estimada por revisão de amostra (seção 4.2); e (ii) pela taxa de imagens com alarme nos negativos de outra aquisição, rotulada como resultado auxiliar.

## 3. Referência e regras de correspondência

A referência positiva são os pontos publicados por Morais et al. (2022), que é **parcial**: um parasita sem ponto não está necessariamente ausente. Um ponto é considerado coberto quando está contido em uma região sinalizada como positiva, com associação um a um que maximiza o número de correspondências (`src/detection_evaluation.py`). Uma região não acerta dois parasitas, e duas regiões sobre o mesmo parasita não geram dois acertos.

Por ser parcial, a referência permite estimar a cobertura, mas não a precisão: uma região sem ponto pode conter parasita não anotado. A precisão, portanto, é estimada por revisão humana de amostra aleatória (seção 4.2), nunca pela contagem de regiões sem ponto.

## 4. Desfechos

### 4.1 Desfecho primário de localização: cobertura dos pontos publicados

Cobertura = pontos associados a regiões positivas / total de pontos publicados, somados sobre as imagens do conjunto (razão de somas). Calculada para A e B, com a diferença B − A.

### 4.2 Desfecho primário de alarmes: precisão por região, estimada por amostra revisada

Para cada sistema, sorteia-se uma amostra aleatória simples de até 200 regiões sinalizadas como positivas (semente fixa, `scripts/sample_precision_review.py`). Se o sistema produzir 200 regiões ou menos no conjunto, todas são revisadas. A revisão é **cega**: o revisor vê o recorte e seu contexto, sem o escore do modelo, sem o sistema de origem e sem a indicação de ponto publicado. Cada região recebe uma de três decisões: contém parasita, sem parasita ou incerta.

- Estimativa principal: precisão = contém parasita / (contém parasita + sem parasita).
- Análise de sensibilidade: limites com todas as incertas consideradas erradas (pior caso) e certas (melhor caso).
- A revisão é realizada pelo autor e, sempre que possível, uma subamostra de 50 regiões é revisada de forma independente por um segundo avaliador, com concordância relatada pelo κ de Cohen.

### 4.3 Desfechos secundários

- **Decisão por imagem nas positivas do teste:** proporção de imagens sinalizadas.
- **Alarme por imagem nos negativos de outra aquisição:** proporção de imagens sem nenhuma região positiva e número médio de regiões positivas por imagem negativa.
- **Carga de alarmes:** regiões positivas por imagem nos campos murinos.
- **F1 aproximado:** 2·P·C/(P + C), combinando a precisão estimada (P) e a cobertura (C), apresentado como derivado e com essa ressalva.
- **Custo computacional:** tempo por imagem (mediana e intervalo interquartil), em execução única por sistema, mesma máquina e mesmas threads; descritivo.

## 5. Procedimentos estatísticos

### 5.1 Intervalos de confiança por bootstrap pareado

- Bootstrap não paramétrico com 10.000 réplicas, intervalo percentil de 95% e semente 20261013.
- Em cada réplica, sorteiam-se imagens com reposição **dentro de cada classe** (positivas e negativas), preservando o tamanho de cada grupo; o mesmo vetor de imagens alimenta A e B, o que mantém o pareamento.
- Para a precisão, a reamostragem é feita sobre as imagens das regiões revisadas (bootstrap por conglomerado), pois regiões de uma mesma imagem são correlacionadas.
- Réplicas em que uma estatística fica indefinida (denominador nulo) são contadas e relatadas.

### 5.2 Teste de McNemar para a decisão por imagem

Para cada imagem, define-se se a decisão de cada sistema está correta (sinalizar nas positivas; não sinalizar nas negativas). O teste de McNemar exato bilateral (binomial com p = 0,5 nos pares discordantes) compara A e B. A família de testes é pré-declarada com dois testes: positivas do teste principal e negativos de outra aquisição. A correção de Holm é aplicada a essa família, com α = 0,05. O McNemar sobre todas as imagens é apenas descritivo.

Imagens em que algum sistema falhou na execução saem do teste e são relatadas separadamente, sem receber classe inventada.

### 5.3 Interpretação

- Diferenças são apresentadas em valores absolutos, com denominadores e intervalo de confiança. Razões do tipo "X vezes melhor" só são usadas quando a métrica e o denominador estiverem explícitos.
- Um intervalo de confiança para B − A que exclui zero é interpretado como evidência de diferença nas condições avaliadas, não como superioridade universal da arquitetura.
- Ganho de cobertura acompanhado de queda de precisão é relatado como compromisso, não como melhoria.
- Não há inferência clínica: a base é murina e não contém lâminas negativas da mesma aquisição.

## 6. Variação entre sementes

O B é treinado com as cinco sementes declaradas na configuração (42, 123, 456, 789 e 1024). A semente 42 é declarada como modelo principal antes do treino e é a única avaliada no teste. As outras quatro medem a estabilidade do treinamento: são relatados média, desvio padrão, mínimo e máximo de `val_loss`, acurácia de validação, cobertura e regiões positivas por imagem na validação (`scripts/summarize_seeds.py`). Sementes não são novas amostras e não entram nos intervalos de confiança.

## 7. Regra de decisão e limiar

A regra de decisão do B é a presença de ao menos uma região com classe prevista positiva (argmax dos escores, equivalente ao limiar de 0,5). O limiar só pode ser alterado com base na validação e antes do congelamento. O A mantém sua regra original.

## 8. Ordem de execução

1. Correção do viés de origem: negativos difíceis murinos, revisados manualmente, apenas das imagens de treino; retreino do B com as cinco sementes.
2. Estimativa de precisão na validação com amostra revisada de 200 regiões.
3. Verificação do A no domínio original (imagens de exemplo do VisionCruzi).
4. Congelamento: registro dos hashes deste plano, dos scripts de análise, do checkpoint principal, da configuração e dos manifestos.
5. Abertura única do teste de 105 imagens; execução de A e B; revisão cega da amostra de regiões; análise conforme este plano.

## 9. Ferramentas

- `src/paired_stats.py`: bootstrap pareado estratificado, McNemar exato, correção de Holm e precisão por amostra revisada (testes em `tests/test_paired_stats.py`).
- `scripts/paired_analysis.py`: lê `per_image.csv` de uma execução e gera `stats.json` e `stats.md`.
- `scripts/sample_precision_review.py`: sorteio da amostra, página de revisão cega e estimativa da precisão.

## 10. Ilustração com o lote de desenvolvimento (não é resultado final)

Aplicado à comparação de desenvolvimento de 06/10/2026 (114 positivas e 253 negativas, 2.000 réplicas), o procedimento produz:

| Métrica | A | B | B − A (IC 95%) |
| --- | ---: | ---: | ---: |
| Cobertura dos pontos | 0,0% | 94,2% | +94,2 p.p. [92,0; 96,2] |
| Imagens positivas sinalizadas | 23,7% | 100,0% | +76,3 p.p. [68,4; 83,4] |
| Imagens negativas sem alarme | 98,8% | 98,8% | 0,0 p.p. [−1,6; 1,6] |

McNemar nas positivas: 87 pares em que só B acerta e 0 em que só A acerta (p < 0,001). Esses números ilustram o procedimento, mas **não** sustentam conclusão: o B atual sinaliza 48% das regiões dos campos murinos, e a sinalização de 100% das imagens positivas é consistente com o reconhecimento da origem da imagem, e não do parasita. Por isso a precisão revisada (seção 4.2) é desfecho primário, e o teste só será aberto após a correção do viés de origem.
