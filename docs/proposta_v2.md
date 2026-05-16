# Proposta de TCC — Versão 2

> **Status:** enviada ao Prof. Rogério Mandelli em maio/2026, em resposta ao retorno com solicitação de refinamento.

## Tema

Análise comparativa entre modelos de Inteligência Artificial aplicados à classificação de núcleos de *Trypanosoma cruzi* em imagens de esfregaço sanguíneo:

- **Modelo A (referência):** ResNet-50 com base congelada, utilizado pela equipe Fuzzylab/FIOCRUZ.
- **Modelo B (proposto):** EfficientNet-B0 com fine-tuning, data augmentation, AdamW + cosine annealing, label smoothing e regularização ajustada.

Ambos compartilham o mesmo pipeline de pré-processamento (segmentação por cor via OpenCV), isolando a etapa de classificação como variável sob análise.

## Hipótese central

A combinação de uma arquitetura convolucional moderna (EfficientNet-B0) com fine-tuning, data augmentation, AdamW com scheduler cosseno e regularização adequada produz ganho estatisticamente significativo em F1-score na tarefa de classificação binária de núcleos celulares em esfregaços sanguíneos de *T. cruzi*, em comparação ao Modelo A avaliado em suas condições originais.

## Base de dados

Dataset público "Image dataset from Automatic analysis of Trypanosoma cruzi" (Morais et al., 2021), DOI: 10.5281/zenodo.5123062, licença CC-BY 4.0.

- Imagens de esfregaço fino de sangue de camundongo corado com Giemsa
- ~1,3 GB de imagens em baixa resolução
- Divisão: 70% treino / 15% validação / 15% teste, com Stratified 5-Fold sobre treino+validação

## Análise estatística

- 5 execuções independentes com sementes diferentes
- Stratified 5-Fold cross-validation
- Métricas: acurácia, precisão, recall, F1-score, matriz de confusão (média ± desvio-padrão)
- Teste de Wilcoxon pareado sobre F1-score por fold, α = 0,05
- Curva ROC e AUC complementares

## Próximos passos imediatos

- [ ] Formalização da autorização Fuzzylab/FIOCRUZ
- [ ] Investigação da divergência treino-em-máscara/inferência-em-RGB no Modelo A entregue
- [ ] Download e exploração do dataset Zenodo
- [ ] Calibração do pipeline de segmentação para o Zenodo

## Cronograma alvo

| Período | Atividade |
|---|---|
| Mai/Jun 2026 | Autorização + Exploração de dados + Setup |
| Jul/Ago 2026 | Replicação Modelo A + Pipeline OpenCV |
| Set/Out 2026 | Implementação e treino do Modelo B |
| Nov 2026 | Análise estatística + Escrita |
| Dez 2026 | Revisão final + Apresentação |
