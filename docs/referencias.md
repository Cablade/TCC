# Referências Bibliográficas

> Lista bibliográfica herdada do projeto, com atualização da fonte de dados em 22/09/2026. As demais referências ainda exigem conferência de metadados, conteúdo e pertinência antes do texto final. Nenhum método estatístico é obrigatório apenas por constar nesta lista.

## Dataset e modelo de referência

- Morais, M. C. C., Silva, D. M. da, Oliveira, M. T., Lana, M. de, & Nakaya, H. I. (2021). *Image dataset from Automatic analysis of Trypanosoma cruzi: A machine learning approach for the detection of blood trypomastigotes in low resolution images*. Zenodo. https://doi.org/10.5281/zenodo.5123062

  Fonte da base local ativa, confirmada pelo MD5 publicado em 22/09/2026. Inventário e exclusões em [base atual](dados.md#base). Licença de reutilização, anotações e grupos devem ser registrados antes do experimento supervisionado.

- Morais et al. (2022). *Automatic detection of the parasite Trypanosoma cruzi in blood smears using a machine learning approach applied to mobile phone images*. PeerJ, 10:e13470. [Artigo e suplementos](https://pmc.ncbi.nlm.nih.gov/articles/PMC9150695/).

  O suplemento 1 descreve posições de parasitas e o suplemento 2, atributos e presença/ausência em regiões. Ainda não foram importados nem reconciliados com as coordenadas do TCC.

Fontes candidatas de controles e suas limitações estão em [fontes negativas](dados.md#negativos); sua citação não significa que foram incorporadas.

## Doença de Chagas

- TODO: incluir diretrizes da OMS sobre diagnóstico de Chagas
- TODO: incluir trabalhos brasileiros relevantes (Ministério da Saúde, FIOCRUZ)

## Arquiteturas

- He, K., Zhang, X., Ren, S., & Sun, J. (2016). *Deep Residual Learning for Image Recognition*. CVPR. (ResNet-50)
- Tan, M., & Le, Q. V. (2019). *EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks*. ICML.

## Técnicas de treinamento

- Loshchilov, I., & Hutter, F. (2019). *Decoupled Weight Decay Regularization*. ICLR. (AdamW)
- Loshchilov, I., & Hutter, F. (2017). *SGDR: Stochastic Gradient Descent with Warm Restarts*. ICLR. (Cosine Annealing)
- Szegedy, C. et al. (2016). *Rethinking the Inception Architecture for Computer Vision*. CVPR. (Label Smoothing)
- Buslaev, A. et al. (2020). *Albumentations: Fast and Flexible Image Augmentations*. Information.

## Avaliação estatística

- Demšar, J. (2006). *Statistical Comparisons of Classifiers over Multiple Data Sets*. Journal of Machine Learning Research.
- Wilcoxon, F. (1945). *Individual Comparisons by Ranking Methods*. Biometrics Bulletin.
