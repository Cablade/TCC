# Proposta atual do TCC — sistemas A × B

> Revisão de 2026-09-20. O nome deste arquivo foi mantido para preservar referências existentes. O desenho anterior foi substituído; sua cópia, incluindo alterações locais, está em [histórico](historico/proposta_anterior.md).

## Tema e problema

Desde 22/09/2026, a base local escolhida é exclusivamente `trypoastigote_images.zip`, de imagens de sangue de camundongos disponibilizadas no Zenodo. A [auditoria da base](dataset_atual.md) e a [pesquisa de controles negativos](fontes_negativas.md) delimitam os dados disponíveis. As bases locais anteriores estão fora do estudo; resultados nelas não são resultados do novo experimento.

Comparar dois sistemas computacionais de localização e classificação de regiões suspeitas de *Trypanosoma cruzi* em imagens microscópicas de esfregaço sanguíneo. A avaliação deve considerar tanto a localização dos candidatos quanto a classificação, pois um parasita que não gera recorte nunca chega ao classificador.

O sistema de referência do Vision/FuzzyLab/FIOCRUZ utiliza um classificador ResNet-50 entregue como artefato treinado. A proposta do TCC utiliza EfficientNet-B0 e pode alterar a etapa de localização. A pergunta é: **como os dois sistemas se comportam, em detecção e custo computacional, sobre o mesmo conjunto de imagens inteiras com referência confiável?**

## Objetivo geral

Implementar um protocolo reproduzível e comparar o sistema A, preservado como referência, com o sistema B proposto pelo TCC, medindo a localização e classificação de regiões suspeitas nas mesmas imagens microscópicas inteiras.

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
| Saída | Regiões, escores, classes e decisão original | Regiões, escores, classes e decisão definida na validação |

Há exatamente duas abordagens. Repetições do B com sementes distintas não constituem novos modelos. Não há obrigação de ablações, detector complexo, número fixo de folds ou número pré-fixado de treinos.

O compartilhamento da localização não é obrigatório. O bloqueio da segmentação do A em um lote foi relatado anteriormente e precisa ser reproduzido com rastreabilidade. Eventual ausência de regiões integra o resultado do sistema, sem ser descrita como classificação negativa da rede.

## Hipóteses verificáveis

- A localização proposta para B pode aumentar a cobertura dos parasitas anotados no conjunto reservado.
- O sistema B pode alterar recall, precisão, falsos positivos por imagem e F1 em relação ao A; o sentido e a magnitude dependem do experimento.
- As mudanças podem afetar o custo de inferência e a relação entre cobertura e falsos positivos.

Essas hipóteses não antecipam superioridade ou significância estatística. Critérios e limiares serão definidos antes da avaliação final, conforme a [metodologia](metodologia.md).

## Dados, análise e limitações

O lote de lâminas disponível e a fonte Zenodo mencionada no projeto devem ser inventariados antes de escolher partições. A identidade do animal ou lâmina deve ser confirmada; nomes de pastas não bastam para inferi-la. Não se fixa proporção de divisão sem conhecer grupos e classes. O conjunto usado para ajustar B é desenvolvimento, não teste final intocado.

Anotações devem ter coordenadas compatíveis com a imagem original, cobertura declarada e revisão qualificada. Previsões automáticas podem auxiliar inspeção, mas não substituem referência independente. Sem rótulos confiáveis, o escopo executável é infraestrutura, diagnóstico e verificações sintéticas, sem conclusões de qualidade real.

O histórico de treinamento do A é incompleto; não se afirma igualdade do tamanho de treinamento nem independência de um teste possivelmente visto durante seu treino. Poucos grupos, diferenças de aquisição/resolução e anotações incompletas limitam a generalização. Métricas auxiliares de recortes não substituem a avaliação ponta a ponta. As decisões estatísticas devem respeitar as unidades independentes; recortes correlacionados e sementes não aumentam o número de lâminas avaliadas.

## Entregas

Protocolo central, inventário e manifestos, notebooks numerados, execução instrumentada do A, infraestrutura e verificação curta do B, comparação funcional e relatório de resultados e limitações. Treino supervisionado real e comparação final dependem dos dados revisados e do conjunto reservado. O [cronograma](cronograma.md) e o [checklist](checklist_execucao.md) detalham essa sequência.
