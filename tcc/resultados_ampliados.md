# Ampliação da comparação A original × B atual

**Registro das avaliações anteriores à reserva 20/180.** A comparação atual está em [367 imagens de desenvolvimento](figuras/a_vs_b_barcelona/index.html): 114 positivas, 73 negativas Kaggle e 180 Barcelona. Foram reservadas 20 Barcelona para próximo treino (80 recortes), ainda não executado. Os resultados abaixo das 200 Barcelona e o ensaio de robustez descrevem os lotes anteriores; seus denominadores não devem ser atribuídos à divisão atual.

Foram mantidos os dois checkpoints e a avaliação de desenvolvimento: 114 imagens positivas com 450 pontos publicados e 73 negativas originais Kaggle revisadas. Nenhuma imagem de treino nem as 105 reservadas para teste final foi adicionada à avaliação. As imagens da comparação principal permanecem as mesmas após a retirada de LABIMED, realizada a pedido do autor depois da inspeção dos resultados; o diagnóstico anterior e os dados dessa fonte foram preservados no arquivo histórico.

## Teste adicional de robustez

Cada um dos 187 originais recebeu as mesmas três transformações: rotação de 90° anti-horária, espelhamento horizontal e multiplicação do brilho por 0,85. Foram processadas 561 versões, além das 187 vistas originais já avaliadas. Pontos e caixas foram transportados para suas posições correspondentes; os rótulos foram herdados. Essas versões não são novos campos independentes, e a independência entre lâminas ou animais não foi demonstrada.

| Condição | Pontos associados A | Pontos associados B | Alarmes A nos 73 negativos | Alarmes B nos 73 negativos |
| --- | ---: | ---: | ---: | ---: |
| Original | 0/450 | 424/450 | 0 | 0 |
| Rotação 90° | 0/450 | 424/450 | 0 | 0 |
| Espelho horizontal | 0/450 | 423/450 | 0 | 1 |
| Brilho × 0,85 | 6/450 | 430/450 | 1 | 0 |

O B conservou a sinalização positiva nas 114 imagens em todas as condições. O A manteve a mesma decisão binária em 63/114 imagens; esse número inclui decisões sempre negativas e não equivale a acerto. Os dois sistemas tiveram decisão estável em 72/73 negativos, com um original sinalizado em alguma condição por cada sistema. Não houve erro de execução.

A associação um a um dos pontos publicados mede cobertura de uma referência parcial. Não comprova precisão geral de detecção; regiões sem ponto correspondente nos positivos permanecem sem referência suficiente para declarar falso positivo. Não somar os pontos repetidos nas versões como observações independentes.

## Negativos originais externos novos

Foram selecionadas antes da inferência 200 imagens PBC/Barcelona, 25 por tipo celular e semente 42, da [fonte original](https://data.mendeley.com/datasets/snkd93bnjr/1), sob CC BY 4.0. Caio confirmou ausência de parasita visível nas 200 imagens. Sua declaração foi registrada com os hashes do inventário e das referências, preservando a referência pendente original. Bytes JPEG e dimensões reais foram preservados; CRC32 dos membros baixados e SHA-256 de cada imagem foram conferidos, sem verificação do hash integral do ZIP.

| Sistema | Imagens com falso alarme | Regiões positivas | Erros |
| --- | ---: | ---: | ---: |
| A original | 3/200 (1,5%) | 3 | 0 |
| B atual | 28/200 (14,0%) | 42 | 0 |

Esse grupo contém células individuais enquadradas, com aquisição humana/CellaVision diferente da base positiva murina. IDs de pacientes/lâminas não estão disponíveis; as imagens não representam 200 pacientes independentes. O resultado deve ser apresentado como avaliação externa de desenvolvimento por fonte, sem inferência clínica ou uma acurácia global misturando aquisições. A revisão visual declarada pelo autor não é laudo clínico.

Os dados mostram maior cobertura positiva do B neste desenvolvimento e maior frequência de falsos alarmes na nova fonte negativa. Isso permite discutir estabilidade e generalização dos sistemas completos, sem atribuir a diferença apenas à arquitetura ou afirmar superioridade universal. Na execução desse diagnóstico, as 200 imagens não tinham entrado no treino. Posteriormente foi preparada a reserva de 20 para próximo treinamento; nenhum ajuste de pesos realizado nesta etapa.

A comparação original reutiliza tempos por imagem da execução anterior. As novas avaliações têm uma execução sequencial por modelo em CPU, duas threads, B em grafo, sem exportação PNG durante medição. Tempos são descritivos, sem benchmark repetido ou aquecimento controlado.

[Todas as figuras e exemplos](figuras/index.html). CSVs e proveniência estão em `experiments/comparison/{a_vs_b,robustez_a_vs_b,barcelona_a_vs_b}/`. O relatório externo apresenta todos os originais com alarme em qualquer sistema e todos os seus 45 recortes positivos, sem marcações.

Na divisão atual, preservando as previsões dos mesmos checkpoints, A sinalizou 3/180 imagens Barcelona e B 24/180; ambos permaneceram em 0/73 nas negativas Kaggle. A mudança de contagem decorre da reserva das 20 imagens, não de melhoria do B. A referência positiva continua com A 0/450 e B 424/450 pontos associados. Resultados por fonte e proveniência em `experiments/comparison/a_vs_b_barcelona/`.
