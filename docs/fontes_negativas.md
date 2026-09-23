# Fontes candidatas para imagens negativas

Pesquisa em 22/09/2026. Foram consultadas fontes públicas; nenhuma imagem externa foi baixada ou incorporada ao experimento. A base ativa contém sangue de camundongos, conforme o [depósito original](https://zenodo.org/records/5123062). Não encontrei nesta pesquisa uma base já validada como controle negativo de *T. cruzi* com aquisição equivalente ao ZIP atual.

## Opções encontradas

| Fonte e acesso | O que a fonte oferece | Adequação ao TCC |
| --- | --- | --- |
| **NIH/NLM — esfregaços finos**, [página oficial e downloads](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html) | 193 participantes: 148 infectados por *P. falciparum* e **45 não infectados** no estudo de malária; imagens de campo, além de um conjunto separado de recortes celulares. | Candidata a controles, condicionada à identificação dos participantes não infectados. São amostras humanas, com aquisição diferente da base de camundongos; a descrição não comprova teste negativo específico para *T. cruzi*. |
| **LABIMED/SpotLab — T. cruzi**, [artigo](https://journals.plos.org/plosntds/article?id=10.1371/journal.pntd.0012955) e [depósito indicado](https://zenodo.org/records/15007339) | O artigo descreve 726 imagens, incluindo campos positivos e negativos, de 36 preparações de nove participantes positivos; mistura esfregaços finos, espessos e líquor. Também reutiliza as 675 imagens da base atual. | Pode ajudar com **campos sem parasitas**, mas não oferece evidência de doadores negativos nessa coleção. Conferir metadados, selecionar o tipo de amostra pertinente e reconciliar imagens reutilizadas. O depósito não pôde ser inspecionado nesta consulta; conteúdo e licença permanecem pendentes. |
| **Tryp**, [depósito Figshare](https://figshare.com/articles/dataset/Tryp_a_dataset_of_microscopy_images_of_unstained_thick_blood_smears_for_trypanosome_detection/22825787) e [artigo](https://www.nature.com/articles/s41597-023-02608-y) | Conjunto de tripanossomos com imagens negativas; usa *T. brucei brucei* e esfregaços espessos sem coloração. | Diferenças de espécie, preparação e aparência tornam esta opção pouco adequada para a comparação principal com a base atual. Não incorporar automaticamente. |

Para NIH/NLM, selecionar **NLM-Falciparum&Uninfected-Thin-193Patients** na página de downloads. O [README oficial](https://data.lhncbc.nlm.nih.gov/public/Malaria/NIH-NLM-ThinBloodSmearsPf/ReadMe.pdf) descreve imagens inteiras de 5312 × 2988, cinco por participante, e organização por `Patient ID`. O rótulo `Uninfected` dentro de uma anotação identifica uma **hemácia**: não comprova que o participante nem a imagem inteira sejam negativos. A identificação dos controles precisa vir de metadados adequados.

O conjunto popular **cell_images**, de 27.558 imagens, contém recortes de células. Não substitui campos microscópicos para a avaliação principal A × B; inclui células normais de participantes infectados. [Descrição oficial do NIH/NLM](https://lhncbc.nlm.nih.gov/LHC-downloads/mobile-app.html).

## Como usar isso no planejamento

Esta é uma recomendação metodológica para o TCC, condicionada à revisão da equipe:

1. Para treinar o classificador de **recortes**, revisar regiões sem parasitas nas próprias imagens da base ativa. Uma lâmina positiva pode fornecer recortes negativos, mas a região deve ser examinada e não conter positivos. Não transformar automaticamente o fundo não anotado em negativo.
2. Para avaliar **campos inteiros**, obter campos integralmente revisados, positivos e negativos. Um campo negativo numa lâmina positiva permite estudar falsos alarmes por campo; não autoriza concluir que a pessoa ou o animal é negativo.
3. Para avaliar **lâminas/doadores negativos**, priorizar controles confirmados, fotografados com preparação, coloração e equipamento comparáveis, idealmente pela mesma fonte. A busca pública acima fornece candidatas, não controles equivalentes já aprovados.
4. Se forem usados dados externos, registrar fonte, licença, espécie, preparação, equipamento, grupo e nível do rótulo. Evitar que todos os positivos venham de uma fonte e todos os negativos de outra: o modelo pode aprender a diferença entre as fontes. Manter grupos separados e relatar resultados por origem.

O próximo trabalho com a equipe é verificar as anotações disponíveis da base ativa e a possibilidade de obter controles compatíveis. O [guia de treinamento](guia_treinamento.md) mostra as etapas seguintes; o treino real continua condicionado à referência revisada e à divisão por grupos.
