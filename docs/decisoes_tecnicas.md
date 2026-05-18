# Registro de Decisões Técnicas

> **Como usar:** toda vez que tomarmos uma decisão técnica relevante, anote aqui com data, contexto e justificativa. Vai facilitar muito a escrita da metodologia em novembro.

---

## 2026-05-16 — Escolha da arquitetura do Modelo B: EfficientNet-B0

**Contexto:** precisávamos de uma arquitetura moderna comparável à ResNet-50 do Modelo A.

**Decisão:** EfficientNet-B0.

**Justificativa:**
- ~5M parâmetros (vs ~25M da ResNet-50) → menor uso de memória, treino mais rápido em Colab
- Eficiência superior em ImageNet (top-1 accuracy)
- Mesma família de redes convolucionais → comparação direta
- Pré-treinada no ImageNet, disponível nativamente em `keras.applications`

**Alternativas consideradas:**
- ConvNeXt-Tiny: mais moderna, mas curva de aprendizado mais íngreme
- ViT pequeno: requer mais dados para fine-tuning eficaz, arriscado com nosso dataset
- ResNet-50 com técnicas modernas: opção mais segura, mas reduz o diferencial frente ao Modelo A

---

## 2026-05-16 — Manter pipeline OpenCV do Modelo A para Modelo B

**Contexto:** o Modelo A usa segmentação clássica (HSV + morfologia) antes da classificação por CNN. O Modelo B poderia substituir todo o pipeline por uma rede end-to-end (YOLO, U-Net).

**Decisão:** manter o pipeline OpenCV para ambos os modelos.

**Justificativa:**
- Isola a variável sob análise: apenas a etapa de classificação muda
- Comparação metodologicamente mais limpa
- Treinos end-to-end exigem rotulação por bounding box ou máscara, que não temos prontamente
- Reduz escopo do TCC ao viável em 7 meses

**Riscos assumidos:**
- O pipeline OpenCV pode ser um gargalo de performance que ambos os modelos herdam
- Se as ROIs forem ruins, nenhum classificador vai funcionar bem

---

## 2026-05-16 — Dataset: Zenodo 5123062

**Contexto:** não temos acesso ao dataset original da Fuzzylab/FIOCRUZ por questões éticas.

**Decisão:** usar o dataset público "Image dataset from Automatic analysis of Trypanosoma cruzi" (Morais et al., 2021) — DOI 10.5281/zenodo.5123062.

**Justificativa:**
- Licença CC-BY 4.0 (uso livre com atribuição)
- 1,3 GB de imagens, suficiente para treino com augmentation
- Mesmo tipo de preparo (esfregaço fino, Giemsa) que o Modelo A foi treinado
- Provavelmente o dataset original do paper que originou o modelo da Fuzzylab/FIOCRUZ → compatibilidade metodológica

## 2026-05-16 — Achado: divergência treino/inferência no Modelo A

**Contexto:** durante a inspeção inicial do projeto da Fuzzylab/FIOCRUZ, identificamos uma inconsistência entre o pipeline de treino e o pipeline de inferência do Modelo A.

**Evidência:**

O dataset de treino em `classificador/doenca-chagas/dataset/{normal,parasita}/` contém 71 imagens (24 negativas + 47 positivas), todas com as seguintes características (verificado via script `notebooks/investigar_dataset_modelo_a.py`):

- Modo de cor PIL: `L` (grayscale 8-bit, 1 canal)
- Valores únicos: apenas 2 (0 e 255) → máscaras binárias puras
- Tamanhos variados e pequenos: de 24×35 até 120×79 pixels

Já o pipeline de inferência (`fuzzylab_app/decision/services/decision_predictor.py`) recebe ROIs **coloridas (RGB)** extraídas da segmentação por cor HSV do `classification.py`.

O script de treino (`traindeddata.py`) usa `image_dataset_from_directory` com `color_mode` default (`'rgb'`) e `input_shape=(224,224,3)`. Isso faz com que as máscaras 1-canal sejam replicadas em 3 canais idênticos antes de entrar na ResNet-50.

**Implicação:**

A ResNet-50 foi treinada vendo:
- Máscaras binárias preto-e-branco
- Upscale agressivo de ~30×50 px para 224×224 px (pixelização severa)
- Canais R=G=B (sem informação de cor)
- `preprocess_input` calibrado para fotos naturais ImageNet, aplicado em pixels que só valem 0 ou 255

E na inferência recebe:
- ROIs coloridas em escala Giemsa (núcleos roxos/azuis em fundo bege/branco)
- Resolução original maior
- 3 canais com informação de cor real

Isso é uma divergência de distribuição significativa entre treino e inferência.

**Decisão:**

1. Tratar essa divergência como **achado** do TCC, não apenas como bug a contornar. Documentar na metodologia e na discussão.
2. Adotar estrutura de três modelos (A1/A2/B) para isolar contribuições — ver decisão seguinte.
3. Comunicar o achado ao pessoal da Fuzzylab/FIOCRUZ com cuidado, enquadrando como validação do pipeline e não como crítica. Pode haver explicação que não estamos enxergando.

**Riscos assumidos:**

- Se a Fuzzylab/FIOCRUZ apresentar contexto que invalide o achado, ajustamos a metodologia
- A discussão desse achado precisa ser cuidadosa para não soar como crítica gratuita

---

## 2026-05-16 — Estratégia revisada: três modelos comparados (A1/A2/B)

**Contexto:** após identificar a divergência treino/inferência (entrada anterior), a comparação simples "A entregue vs B proposto" se torna confusa, pois B difere de A em múltiplas variáveis simultaneamente (arquitetura, dataset de treino, técnicas modernas, **e** consistência treino/inferência).

**Decisão:** treinar e avaliar três modelos:

| Modelo | Arquitetura | Dataset de treino | Pipeline de classificação | Técnicas modernas | Responde a pergunta |
|---|---|---|---|---|---|
| **A1** | ResNet-50 (entregue) | Original (máscaras binárias) | Como veio | Não | Qual a performance real do sistema atual da Fuzzylab/FIOCRUZ? |
| **A2** | ResNet-50 re-treinada | ROIs RGB do Zenodo | Mesmo código do A1, só muda o input | Não | Quanto do problema se resolve só consertando a divergência treino/inferência? |
| **B** | EfficientNet-B0 | ROIs RGB do Zenodo | Pipeline coerente | Sim (fine-tuning, AdamW, augmentation, label smoothing) | Quanto as técnicas modernas adicionam, controlando pelo dataset e pelo pipeline coerente? |

Todos os três modelos são avaliados no **mesmo conjunto de teste**: ROIs RGB extraídas pelo pipeline OpenCV aplicado ao Zenodo.

**Justificativa:**

- Isolamento de variáveis: cada modelo difere do anterior em **uma única dimensão**, o que permite atribuir ganhos especificamente
- Atende perfeitamente o ponto 4 do feedback do orientador (análise estatística significativa)
- O achado da divergência treino/inferência passa a ter contraprova quantitativa (A1 → A2)
- Cientificamente mais honesto: "B é melhor" pode ser por vários motivos; A1/A2/B permite afirmar **por quê**

**Custo adicional estimado:**

- A2 reusa o código do A1 (só muda a fonte do input), então implementação é rápida
- Adiciona ~1-2 semanas no cronograma de Agosto (mais runs de K-fold)
- Tempo de GPU triplica vs A vs B (de 50h para ~75h total considerando 5 sementes × 5 folds em cada modelo)

**Alternativas consideradas:**

- Comparar só A1 vs B: mais simples, mas a interpretação fica ambígua
- Comparar A2 vs B (descartar A1): perde a contraprova da divergência
- Comparar quatro modelos (incluindo ResNet-50 com técnicas modernas): escopo grande demais para o cronograma

**Próximos passos:**

- Atualizar `configs/` para incluir `model_a2.yaml`
- Adicionar `src/model_a2.py` (reusa `model_a.py`, recebe ROIs RGB)
- Atualizar `docs/proposta_v2.md` → `proposta_v3.md` refletindo a estratégia A1/A2/B
- Avisar o orientador da mudança com a justificativa

---

## 2026-05-16 — Comunicação com Fuzzylab adiada por restrição de tempo

**Contexto:** consideramos consultar a Fuzzylab/FIOCRUZ sobre o achado da divergência treino/inferência antes de fixar a estratégia.

**Decisão:** seguir com a estratégia A1/A2/B sem aguardar resposta da Fuzzylab.

**Justificativa:**

- Cronograma até Dezembro é apertado; aguardar resposta institucional pode atrasar semanas
- A divergência foi verificada por script reprodutível (`investigar_dataset_modelo_a.py`), não é especulação
- Em qualquer cenário que a Fuzzylab eventualmente responda, os dados de A1/A2/B continuam válidos:
  - Se confirmarem o achado: reforça nossa análise
  - Se trouxerem contexto que invalide: ajustamos a discussão, mas mantemos os experimentos
- O TCC mencionará que apresentamos o achado e não obtivemos esclarecimento dentro do prazo do trabalho

**Riscos assumidos:**

- A Fuzzylab pode responder próximo ao prazo final com informação relevante que demande revisão
  → mitigação: discussão do TCC será estruturada para acomodar atualizações marginais
- Pode haver desconforto institucional se eles só souberem do achado pelo TCC pronto
  → mitigação: enviar uma comunicação curta e informativa em algum momento, sem cobrar resposta

**Sobre autorização formal de uso do modelo:** segue como item pendente em paralelo, independente desta decisão.

---

## 2026-05-16 — Premissa de trabalho: ausência de resposta da Fuzzylab/FIOCRUZ

**Contexto:** após o achado da divergência treino/inferência, foi acordado que tentaríamos consultar a equipe da Fuzzylab/FIOCRUZ para esclarecer se o dataset analisado representa o estado real do projeto ou se há contexto que invalide a observação. Também solicitaríamos a autorização formal de uso do modelo no TCC.

**Decisão:** assumir como premissa de trabalho que **a Fuzzylab/FIOCRUZ não responderá a tempo hábil** para influenciar a estratégia experimental.

**Justificativa:**

- O cronograma de entrega (Dezembro/2026) não permite ficar bloqueado aguardando retorno
- Caio é colaborador da Fuzzylab/FIOCRUZ e tem acesso técnico legítimo aos artefatos do projeto
- O uso é interno-acadêmico, sobre trabalho do qual o Caio já participa
- A estratégia A1/A2/B é robusta independentemente de confirmação externa: A1 é a âncora factual do que está entregue, A2 e B são construções do TCC

**Implicações:**

1. **Autorização formal:** sem documento escrito da Fuzzylab a tempo. Mitigação: o Caio está listado como colaborador do projeto Fuzzylab, e o próprio acesso ao código e modelo treinado em sua máquina demonstra autorização de fato. O TCC documentará essa relação de colaboração de forma clara na metodologia. Se autorização escrita vier eventualmente, será anexada como evidência complementar.

2. **Achado da divergência:** sem contraprova da Fuzzylab, o achado deve ser documentado em tom científico neutro, não como crítica. Exemplo de fraseado a usar:
   > *"A inspeção do dataset de treino disponível revelou características (máscaras binárias 1-canal de baixa resolução) distintas das ROIs RGB recebidas pelo pipeline de inferência. Este trabalho não obteve esclarecimento adicional da equipe responsável sobre se o material analisado representa o estado de produção do sistema. Os experimentos seguintes investigam o impacto dessa característica sobre a performance, tratando-a como variável experimental."*

3. **Comunicar ao orientador:** a mudança de estratégia (A1/A2/B) e a premissa de ausência de resposta da Fuzzylab devem ser comunicadas ao Prof. Mandelli na próxima atualização da proposta (v3).

**Riscos assumidos:**

- Se a Fuzzylab responder depois com contexto que invalide o achado, o TCC pode precisar de revisão pontual da discussão (não da metodologia, que permanece válida em qualquer cenário)
- Se a Fuzzylab questionar o uso, há protocolo a seguir via orientador e coordenação

---

## 2026-05-16 — Descoberta do paper original e implicações

**Contexto:** ao explorar o dataset Zenodo baixado, percebemos que não havia arquivo de anotações. Pesquisando o paper que originou o dataset, descobrimos várias diferenças importantes entre o trabalho original e a implementação da Fuzzylab/FIOCRUZ que estamos chamando de "Modelo A".

**Paper original identificado:**

Morais et al. (2022). *Automatic detection of the parasite Trypanosoma cruzi in blood smears using a machine learning approach applied to mobile phone images*. PeerJ 10:e13470. DOI: 10.7717/peerj.13470. PMC: PMC9150695.

**Diferenças descobertas:**

| Aspecto | Paper original (Morais et al.) | Modelo A (Fuzzylab/FIOCRUZ) |
|---|---|---|
| Classificador | Random Forest, SVM, KNN com ensemble | ResNet-50 (transfer learning) |
| Features | Morfométricas, cor, textura, momentos de Hu (manuais) + PCA | Features aprendidas pela CNN |
| Segmentação | Algoritmo baseado em grafos (Felzenszwalb-Huttenlocher) | HSV + morfologia matemática |
| Tamanho ROI | 100×100 pixels | 224×224 pixels (com upscale) |
| Dados de treino | ROIs coloridas RGB | Máscaras binárias 1-canal |
| Imagens | 674 imagens de celular Moto G4, 3456×4608 px | Mesmo dataset Zenodo |
| Rotulação | Point-and-click manual por especialistas; 1.314 parasitas + 1.314 "unknown" | Treino em máscaras pré-segmentadas |

**Implicações:**

1. O "Modelo A" é uma **reimplementação/derivação** do paper, não o modelo original. Isso não invalida o TCC, mas precisa ser deixado explícito na metodologia: estamos comparando contra a versão entregue pela Fuzzylab/FIOCRUZ, não contra o paper.

2. As **anotações manuais** (coordenadas X, Y de cada parasita) estão no **material suplementar do paper PeerJ, não no Zenodo**. Arquivo "Data S1". Baixar manualmente de https://peerj.com/articles/13470/.

3. Ter o Data S1 **destrava completamente o cronograma** — elimina o maior risco identificado (rotulação manual de centenas de ROIs).

4. Podemos agora reproduzir **com fidelidade** o pipeline do paper, além de avaliar o Modelo A da Fuzzylab/FIOCRUZ. Opção nova de discussão no TCC: posicionar o Modelo A como derivação e comparar com o original.

**Decisão:**

- Baixar Data S1 do PeerJ e armazenar em `data/raw/annotations/`
- Manter a estratégia A1/A2/B, mas com nuances revisadas na próxima entrada do log
- Não re-implementar o pipeline Felzenszwalb-Huttenlocher: continuar com a segmentação HSV do Modelo A para não expandir escopo. O paper segmenta com Felzenszwalb, a Fuzzylab/FIOCRUZ usa HSV — essa escolha de pipeline da Fuzzylab/FIOCRUZ é parte do "Modelo A" como entidade experimental.

**Riscos atualizados:**

- O Data S1 pode estar em formato pouco amigável (PDF, Excel mal estruturado) — verificar após download
- As coordenadas estão relativas às imagens originais 3456×4608, não ao que o pipeline OpenCV da Fuzzylab/FIOCRUZ pode esperar — ajustes podem ser necessários

---

<!--
## YYYY-MM-DD — Título curto da decisão

**Contexto:**

**Decisão:**

**Justificativa:**

**Alternativas consideradas:**

**Riscos assumidos:**
-->
