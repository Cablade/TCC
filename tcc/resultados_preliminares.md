# Resultados preliminares e discussão

Texto de trabalho baseado nas execuções locais auditadas, consolidado em 27/09/2026. Estes resultados descrevem desenvolvimento e validação; não constituem avaliação final independente. As figuras e suas legendas estão em [consolidado_20260927](figuras/consolidado_20260927/index.html). As tabelas por imagem e os hashes dos arquivos utilizados acompanham as figuras.

## Delineamento e amostras

Foram comparados dois sistemas completos de localização e classificação de regiões suspeitas de *Trypanosoma cruzi*. O sistema A foi preservado com seus pesos e procedimentos originais. O sistema B emprega EfficientNet-B0 e uma localização configurável. Como os sistemas diferem em mais de uma etapa, a comparação não permite atribuir isoladamente as diferenças observadas à arquitetura das redes.

A base principal contém 674 imagens utilizáveis de sangue de camundongos, provenientes do depósito Zenodo 5123062. A divisão contém 455 imagens de treino, 114 de validação e 105 reservadas para teste. A divisão foi realizada por imagem original; a correspondência com animais e lâminas individuais permanece desconhecida, limitando afirmações de independência biológica. A geração dos recortes antecede o treinamento e respeita as partições previamente definidas.

O B reduzido utilizou 3.129 recortes de treinamento, dos quais 3.053 positivos e 76 negativos, e 778 recortes de validação, dos quais 740 positivos e 38 negativos. Completou 30 épocas, sendo selecionado o checkpoint da época 23 pela menor perda de validação. O desequilíbrio entre classes exige cautela na leitura da acurácia: a regra trivial que atribui a classe positiva a todos os recortes de validação obteria aproximadamente 95,12% de acerto. Esse valor é uma referência aritmética, não a execução de um terceiro modelo.

## Comparação nas imagens inteiras de validação

Os dois sistemas concluíram as mesmas 114 imagens sem erros registrados. O A produziu 42 candidatos em 27 imagens, todos classificados como suspeitos; nas outras 87 imagens não foram gerados candidatos. O B produziu 25.695 candidatos, dos quais 7.758 receberam classificação positiva, sinalizando as 114 imagens. Esses 25.695 candidatos são o resultado da inferência em campos inteiros, não o número de recortes utilizados no treinamento.

| Medida | A original | B reduzido |
| --- | ---: | ---: |
| Imagens avaliadas | 114 | 114 |
| Imagens sinalizadas | 27 | 114 |
| Imagens sem regiões | 87 | 0 |
| Candidatos | 42 | 25.695 |
| Regiões positivas | 42 | 7.758 |
| Pontos cobertos por propostas | 0/450 | 425/450 |
| Pontos cobertos por regiões positivas | 0/450 | 424/450 |
| Tempo total do algoritmo | 32,37 s | 281,87 s |
| Mediana de tempo por imagem | 0,202 s | 2,341 s |

As correspondências foram recalculadas por associação um a um de cardinalidade máxima, considerando elegível a região que contém o ponto publicado. O B apresentou cobertura de 94,44% dos 450 pontos pelas propostas e de 94,22% pelas regiões classificadas como positivas. As regiões de A não corresponderam a esses pontos. A auditoria anterior reproduziu as 42 regiões de A e suas coordenadas dentro dos arquivos; algumas regiões podem estar sobre a borda escura externa ao campo circular do microscópio, ainda que dentro da imagem retangular.

A referência pontual é parcial. Por isso, as 7.334 regiões positivas de B sem correspondência não podem ser classificadas automaticamente como falsos positivos: podem incluir estruturas confundidas, duplicações ou parasitas não anotados. Também não é adequado interpretar a cobertura dos pontos como sensibilidade geral de detecção. Como todas as imagens desta validação têm referência positiva, a sinalização de 100% dos campos por B não demonstra capacidade de rejeitar campos negativos.

O B consumiu aproximadamente 8,71 vezes o tempo de algoritmo do A nesta execução. As medições excluem a exportação de imagens, mas incluem primeiras chamadas e não formam um benchmark repetido com controle completo de aquecimento e carga. A diferença é apresentada como custo observado dos sistemas completos, sem atribuição exclusiva à rede neural ou extrapolação para outros computadores.

## Diagnóstico externo de alarmes

Foi examinado separadamente um conjunto de 33 campos LABIMED humanos, de oito lâminas associadas a um único caso no manifesto local. O caso possui status positivo; os campos foram utilizados como regiões sem parasita visível, não como controles de pacientes sem Chagas. O A sinalizou 20 dos 33 campos (60,61%), com 140 regiões positivas, enquanto B sinalizou os 33 campos (100%), com 5.277 regiões positivas.

Caio declarou não observar parasitas nesses campos. Na inspeção dos três candidatos de maior escore B por campo, totalizando 99 regiões, relatou apenas células, bordas escuras e sujeira ou artefatos. Após a ausência dos JSONs originais ser identificada, os vínculos dos 99 recortes foram reconstruídos das predições e confirmados pixel a pixel contra as imagens originais. A declaração foi registrada novamente a partir da conversa, com proveniência explícita; isso não equivale à recuperação dos arquivos originais ou a uma nova adjudicação especializada. Não houve classificação individual dos tipos de artefato.

Essa seleção por escores altos evidencia falhas relevantes, mas não é uma amostra aleatória de todas as predições. Portanto, os 99 resultados não estimam a precisão global de B. O domínio humano externo difere da base murina de treinamento, e os campos de um mesmo caso não são amostras biológicas independentes. Os resultados externos permanecem como diagnóstico de desenvolvimento, separados da validação principal.

## Discussão e limites da conclusão

Os resultados mostram uma relação entre maior cobertura dos pontos disponíveis e maior quantidade de regiões sinalizadas e custo de processamento. Na validação principal, B alcançou mais pontos anotados que A; no conjunto externo revisado, B também apresentou maior frequência de alarmes por campo. Esses achados não sustentam uma afirmação de superioridade geral. A maior cobertura pode ser acompanhada de menor capacidade de rejeitar estruturas não parasitárias, questão que demanda referência apropriada e dados adicionais de desenvolvimento.

O estudo permanece centrado na comparação dos sistemas completos. A análise de recortes comuns, embora útil para diagnóstico, é auxiliar e não substitui a comparação ponta a ponta. O histórico de treinamento de A é incompleto, e não foi demonstrada a independência dessa base em relação ao treinamento original de A. A data histórica do sistema também exige documentação antes de se vincular o artefato a 2024.

Antes de uma avaliação final, devem ser definidos com o orientador o alcance da referência, o nível de revisão das anotações e os limites de generalização admitidos. Se os campos externos forem usados para orientar um novo treinamento ou ajuste, não poderão ser apresentados como teste independente da nova versão. O conjunto reservado não foi aberto para criar estas figuras nem utilizado para selecionar novos parâmetros.

## Reprodução

Na raiz do projeto, executar `scripts/generate_tcc_figures.py --complete --output-dir tcc/figuras/nova_edicao` com o Python da `.venv`. A saída deve ser nova. As referências exatas, hashes, contagens e critérios determinísticos de escolha dos exemplos estão em `figuras/consolidado_20260927/summary.json`. Os arquivos de reconstrução da revisão são `review_reconstructed.json` nas galerias externas. Dados e modelos não acompanham automaticamente o Git.
