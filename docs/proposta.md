# Proposta atual do TCC — sistemas A × B

> Proposta vigente. O protocolo detalhado está na [metodologia](metodologia.md).

## Tema e problema

Desde 22/09/2026, a base positiva escolhida é `trypoastigote_images.zip`, de imagens de sangue de camundongos disponibilizadas no Zenodo. A [auditoria da base](dados.md#base) e a [pesquisa de controles negativos](dados.md#negativos) delimitam os dados disponíveis. As bases privadas anteriores estão fora do estudo. Negativos originais Kaggle e Barcelona revisados foram incorporados como fontes suplementares, documentadas em [dados](dados.md); resultados de fontes excluídas permanecem somente no histórico.

Comparar dois sistemas computacionais de localização e classificação de regiões suspeitas de *Trypanosoma cruzi* em imagens microscópicas de esfregaço sanguíneo. A avaliação deve considerar tanto a localização dos candidatos quanto a classificação da imagem, pois um parasita que não gera recorte nunca chega ao classificador.

O sistema de referência do Vision/FuzzyLab/FIOCRUZ utiliza um classificador ResNet-50 entregue como artefato treinado. A proposta do TCC utiliza EfficientNet-B0 e pode alterar a etapa de localização. A pergunta é: **como o sistema de referência, desenvolvido anteriormente, e o sistema proposto se comportam, em detecção e custo computacional, sobre o mesmo conjunto de imagens inteiras com referência confiável?**

## Objetivo geral

Implementar um protocolo reproduzível e comparar o sistema A, preservado como referência, com o sistema B proposto pelo TCC, medindo o resultado gerado e classificação de regiões suspeitas nas mesmas imagens microscópicas inteiras.

O enfoque confirmado em 26/09/2026 é a evolução de um sistema anterior para uma nova proposta: A permanece original, sem retreinamento. A data de 2024 associada ao sistema A só é vinculada ao artefato mediante documentação que a comprove. Não se presume que A tenha sido o melhor sistema disponível naquele ano. A magnitude de eventual melhoria será expressa por métricas específicas e custo computacional, com seus limites, sem antecipar a vitória de B ou atribuir todo o efeito à arquitetura.

## Objetivos específicos

1. Inventariar os dados, controlar duplicatas e documentar aquisição, grupos e disponibilidade de anotações.
2. Separar as origens entre treino, validação e teste antes da geração de recortes, evitando vazamento dentro dos identificadores disponíveis.
3. Reproduzir o fluxo original do A sem retreinar ou modificar seus parâmetros para favorecer resultados, registrando versões, pesos e decisão original.
4. Implementar uma localização configurável para B e alinhar seus candidatos de treino aos de inferência, com EfficientNet-B0 e pré-processamento compatível.
5. Comparar cobertura de localização, precisão, recall, F1, falsos positivos por imagem e custo. Calcular métricas por imagem somente com referência confiável nesse nível.
6. Discutir limitações, falhas e condições em que cada sistema é aplicável, sem atribuir a uma técnica isolada os efeitos de mudanças simultâneas.

## Desenho experimental

| Aspecto | Modelo A — referência | Modelo B — proposta |
| --- | --- | --- |
| Treinamento | Pesos entregues, fixos; nenhum retreinamento | Treino com dados disponíveis, rotulados e separados |
| Localização | Fluxo e parâmetros originais do Vision | Fluxo configurável definido no desenvolvimento |
| Classificador | ResNet-50, sujeito à inspeção do artefato | EfficientNet-B0, já presente no código-base |
| Entrada principal | Imagem microscópica inteira | A mesma imagem microscópica inteira |
| Saída | Presença ou ausência de parasito, decisão segundo a regra original, número de candidatos, número de regiões classificadas, tempo de execução (s) e erros | Regiões, escores, classes e decisão segundo a regra do modelo |

Há exatamente duas abordagens. Repetições do B com sementes distintas não constituem novos modelos. Não há obrigação de ablações, detector complexo, número fixo de folds ou número pré-fixado de treinos.

O compartilhamento da localização não é obrigatório. O bloqueio da segmentação do A em um lote foi relatado anteriormente e precisa ser reproduzido com rastreabilidade. Eventual ausência de regiões integra o resultado do sistema, sem ser descrita como classificação negativa da rede.

## Hipóteses verificáveis

- A localização proposta para B pode aumentar a cobertura dos parasitas anotados no conjunto reservado.
- O sistema B pode alterar recall, precisão, falsos positivos por imagem e F1 em relação ao A; o sentido e a magnitude dependem do experimento.
- As mudanças podem afetar o custo de inferência e a relação entre cobertura e falsos positivos.

Essas hipóteses não antecipam superioridade ou significância estatística. Critérios e limiares serão definidos antes da avaliação final, conforme a [metodologia](metodologia.md) e o [plano estatístico](plano_estatistico.md): bootstrap pareado por imagem para cobertura e precisão e McNemar para a decisão por imagem.

## Dados, análise e limitações

Os inventários e as partições estão registrados em [dados](dados.md). A identidade do animal ou lâmina deve ser confirmada; nomes de pastas não bastam para inferi-la. Não se fixa proporção de divisão sem conhecer grupos e classes. O conjunto usado para ajustar B é desenvolvimento, não teste final intocado.

Anotações devem ter coordenadas compatíveis com a imagem original, cobertura declarada e revisão qualificada. Previsões automáticas podem auxiliar inspeção, mas não substituem referência independente. Sem rótulos confiáveis, o escopo executável é infraestrutura, diagnóstico e verificações sintéticas, sem conclusões de qualidade real.

O histórico de treinamento do A é incompleto; não se afirma igualdade do tamanho de treinamento nem independência de um teste possivelmente visto durante seu treino. Poucos grupos, diferenças de aquisição/resolução e anotações incompletas limitam a generalização. Métricas auxiliares de recortes não substituem a avaliação ponta a ponta. As decisões estatísticas devem respeitar as unidades independentes; recortes correlacionados e sementes não aumentam o número de lâminas avaliadas.

## Entregas

Protocolo central, inventário e manifestos, notebooks numerados, execução instrumentada do A, infraestrutura e verificação curta do B, comparação funcional e relatório de resultados e limitações. Treino real e comparação de desenvolvimento já concluídos; a avaliação final depende do congelamento do protocolo e da referência do conjunto reservado. O [estado atual](status.md) registra treino, comparação concluída e pendências do teste final.
