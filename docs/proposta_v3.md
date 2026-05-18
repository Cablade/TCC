# Proposta de TCC — Versão 3

> **Status:** preparada em 2026-05-16, a ser enviada ao Prof. Rogério Mandelli como atualização à v2.
> **Motivo da atualização:** identificação de inconsistência metodológica no pipeline do Modelo A durante a inspeção inicial, levando à mudança da estratégia experimental para comparação de três modelos (A1/A2/B).

## Tema

Análise comparativa entre modelos de Inteligência Artificial aplicados à classificação de núcleos de *Trypanosoma cruzi* em imagens de esfregaço sanguíneo, com foco em isolar contribuições de pipeline coerente e de técnicas modernas de treinamento.

## Mudança em relação à v2

Durante a inspeção do projeto da Fuzzylab/FIOCRUZ, identificamos que o dataset usado para treinar o Modelo A consiste em **máscaras binárias 1-canal de baixa resolução** (24 a 120 pixels, valores apenas 0 e 255), enquanto o pipeline de inferência recebe **ROIs RGB coloridas** geradas pela segmentação por cor HSV em OpenCV. Há, portanto, divergência significativa de distribuição entre treino e inferência.

Esse achado tornou a comparação simples "A vs B" ambígua: o Modelo B difere do A em múltiplas dimensões simultaneamente (arquitetura, dataset, técnicas, **e** consistência treino/inferência), o que impediria atribuir ganhos a causas específicas.

A v3 propõe comparar **três modelos** ao invés de dois, isolando uma variável por vez.

## Estratégia experimental: três modelos

| Modelo | Arquitetura | Dataset de treino | Técnicas modernas | Pergunta científica |
|---|---|---|---|---|
| **A1** | ResNet-50 (entregue) | Máscaras binárias originais | Não | Qual a performance do sistema atual da Fuzzylab/FIOCRUZ no conjunto de teste padronizado? |
| **A2** | ResNet-50 re-treinada | ROIs RGB do Zenodo | Não | Quanto se ganha apenas corrigindo a divergência treino/inferência? |
| **B** | EfficientNet-B0 | ROIs RGB do Zenodo | Sim | Quanto as técnicas modernas adicionam, controlando pelo pipeline coerente? |

Todos os três modelos são avaliados no **mesmo conjunto de teste**: ROIs RGB extraídas pelo pipeline OpenCV (mesmo do Modelo A) aplicado ao dataset Zenodo. A etapa de segmentação é mantida idêntica para os três, isolando a classificação como variável sob análise.

## Hipóteses

- **H1:** A2 supera A1 com diferença estatisticamente significativa em F1-score (corrigir a divergência traz ganho mensurável)
- **H2:** B supera A2 com diferença estatisticamente significativa em F1-score (as técnicas modernas trazem ganho adicional, controlando pelo pipeline coerente)
- **H3:** O ganho total (A1 → B) decompõe-se em parcela atribuível à correção da divergência (A1 → A2) e parcela atribuível às técnicas modernas (A2 → B)

## Base de dados

Dataset público "Image dataset from Automatic analysis of Trypanosoma cruzi" (Morais et al., 2021), DOI 10.5281/zenodo.5123062, licença CC-BY 4.0.

- Imagens de esfregaço fino de sangue de camundongo corado com Giemsa
- ~1,3 GB de imagens em baixa resolução
- Divisão: 70% treino / 15% validação / 15% teste, com Stratified 5-Fold sobre treino+validação

A rotulagem das ROIs será detalhada conforme exploração inicial revelar a disponibilidade no dataset Zenodo. Caso não haja rotulagem pronta, será adotada estratégia híbrida (rotulação de subset + auto-rotulação assistida por modelo + revisão).

## Modelo B: delimitação detalhada

- **Arquitetura:** EfficientNet-B0 (escolhida por eficiência computacional e modernidade)
- **Transfer learning:** pesos pré-treinados em ImageNet, com fine-tuning das últimas 30 camadas convolucionais
- **Data augmentation:** Albumentations com rotação, flip horizontal/vertical, color jitter leve, CoarseDropout
- **Otimizador:** AdamW com weight decay = 1e-4
- **Scheduler:** Cosine Annealing
- **Regularização:** Label smoothing (0,1) + Dropout (0,3)
- **Balanceamento:** class_weight inverso à frequência

## Análise estatística

- 5 execuções independentes com sementes diferentes, para cada um dos 3 modelos
- Stratified 5-Fold cross-validation
- Total: **75 runs** (5 sementes × 5 folds × 3 modelos)
- Métricas: acurácia, precisão, recall, F1-score, matriz de confusão (média ± desvio-padrão)
- Teste de Wilcoxon pareado sobre F1-score por fold, α = 0,05, aplicado a duas comparações:
  - A1 vs A2 (testa H1)
  - A2 vs B (testa H2)
- Curva ROC e AUC complementares

## Sobre o acesso ao Modelo A (ponto 1 do feedback v1)

- Acesso técnico completo: código de treino (`traindeddata.py`), pipeline de segmentação (`classification.py`), modelo treinado (`model_trained.keras`), pipeline de inferência (`decision_predictor.py`)
- Caio é colaborador ativo do projeto Fuzzylab/FIOCRUZ, com acesso legítimo aos artefatos
- Tentativa de obter autorização formal escrita está em curso; não há resposta a tempo hábil até o momento. O TCC será conduzido sob a relação de colaboração de fato já existente, documentada na metodologia. Autorização escrita, se vier, será anexada como evidência complementar.

## Sobre o achado da divergência

O achado será apresentado em tom científico neutro como **resultado parcial da inspeção inicial**, não como crítica ao trabalho original. A metodologia A1/A2/B foi desenhada precisamente para tratar essa observação como variável experimental investigável, e não como bug a contornar silenciosamente. Os resultados quantitativos da comparação A1 → A2 fornecerão a melhor evidência sobre o impacto real da divergência.

## Cronograma alvo (ver `cronograma.md` para detalhes)

| Período | Atividade |
|---|---|
| Mai 2026 | Setup, exploração de dados, proposta v3 |
| Jun 2026 | Pipeline OpenCV, rotulagem de ROIs |
| Jul-Ago 2026 | Implementação A1, A2 e B |
| Set-Out 2026 | K-fold completo (75 runs) + análise estatística |
| Nov 2026 | Escrita do TCC |
| Dez 2026 | Revisão final + apresentação |
