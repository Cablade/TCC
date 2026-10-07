# Metodologia — comparação dos sistemas A × B

> Protocolo ativo, iniciado em 2026-09-20. Substitui os desenhos históricos. Este documento define o experimento; a evidência do que foi efetivamente executado deve ficar no checklist e nos relatórios de execução.

Atualização de 06/10/2026: B retreinado com 20 originais Barcelona adicionais e comparado novamente com A original nos mesmos 367 IDs (114 positivas, 73 negativas Kaggle e 180 negativas Barcelona). Apresentação em 114 imagens positivas e 253 negativas, com origens preservadas nos manifestos e tempos medidos nesta execução e nenhuma previsão antiga reutilizada. O [estado atual](status.md) e `experiments/comparison/a_vs_b_barcelona20_20261006/` registram a execução. O lote é desenvolvimento já examinado; as 105 imagens do teste final continuam reservadas. LABIMED foi retirado após inspeção, por solicitação do autor; diagnóstico preservado no arquivo histórico.

## 1. Unidade de comparação

Comparar exatamente dois sistemas completos de localização e classificação de regiões suspeitas de *Trypanosoma cruzi*. O A usa os pesos já treinados e reproduz a inferência original. O B é a proposta, com localização configurável e EfficientNet-B0. Ambos recebem os mesmos IDs de **imagens inteiras** do conjunto reservado. Nenhum retreinamento do A será realizado. As etapas de localização não precisam ser iguais.

O arquivo `.keras` de A não representa sozinho o sistema: segmentação, recortes, ordem dos canais, redimensionamento, pré-processamento e decisão também precisam ser preservados. A proposta B poderá modificar várias etapas; eventual ganho não permite atribuição causal a uma delas. Não são exigidas ablações ou arquiteturas adicionais.

## 2. Origem e rastreabilidade

- TCC inspecionado: commit `e056cd60739d2f4d6f74b329a24beb81b6ae916b`, com alterações locais existentes preservadas antes da revisão.
- Referência indicada pelo pedido: `Cablade/Vision`.
- Referência local encontrada: repositório com remoto `Cablade/VisionCruzi`, commit `59b10244f2ce5cfabff7bece404cb5679668a45d`. A equivalência com a referência indicada precisa ser registrada após confronto; não é presumida.
- Artefato `model_trained.keras` localizado. Desde 22/09/2026, a base positiva selecionada é `trypoastigote_images.zip`, auditada em [base atual](dados.md); os ZIPs anteriores estão excluídos. Sua presença não comprova anotações ou qualidade do modelo.

Cada execução deve registrar commit e modificações locais relevantes, hash SHA-256 do modelo e dos dados, configuração, semente, manifestos, versões, hardware, tempos e caminhos de saída. Dados originais e pesos não devem ser sobrescritos nem incluídos automaticamente no Git.

## 3. Inventário, grupos e partições

O inventário contém identificador estável, caminho, SHA-256, largura, altura, origem, grupo e nível do grupo. Valores desconhecidos são explícitos. Duplicatas por conteúdo ficam no inventário e no manifesto de exclusão; seus originais permanecem intactos. Variantes reencodadas e imagens correlacionadas precisam de inspeção adicional, pois hashes de arquivo não demonstram independência biológica.

Usar identificador de animal, ou de lâmina, quando confirmado; caso contrário, o grupo é a imagem original, com essa limitação declarada. Nomes de diretório não comprovam identidade de animal/lâmina. Não permitir a mesma origem nem duplicatas em partições diferentes.

Separar antes de gerar recortes ou aumentos. Persistir a semente e as atribuições de grupo. Não há porcentagem padrão neste protocolo: primeiro examinar grupos e classes; então registrar uma divisão viável. Dados já usados para diagnóstico ou escolha de parâmetros pertencem ao desenvolvimento. Se não houver grupos suficientes para treino, validação e teste reservado, registrar a impossibilidade e não apresentar o lote de desenvolvimento como teste final.

## 4. Anotações e negativos

As [fontes candidatas de negativos](dados.md#negativos-originais-suplementares) devem ser avaliadas quanto a espécie, preparação, equipamento e nível do rótulo. Campo ou recorte sem parasita não equivale a lâmina/animal negativo. Não confundir a origem do conjunto com a classe; evitar positivos exclusivamente de uma fonte e negativos de outra. A base atual é de camundongos e não sustenta, por si, conclusões clínicas sobre humanos.

O formato de referência está em [documento de anotações](anotacoes.md#formato). Coordenadas usam a imagem original: origem no canto superior esquerdo, x para a direita, y para baixo. Caixas `[x1,y1,x2,y2]` têm extremos direito/inferior exclusivos; pontos são `[x,y]`. Imagens e marcações devem declarar revisão e responsável. A ausência de marcação ou de arquivo de anotação nunca significa negativo.

A referência exige revisão de alguém qualificado da equipe. Não gerar referência de avaliação a partir das próprias previsões. Regiões negativas devem ser explicitamente confirmadas; verificar a interseção de **todo o recorte** com positivos, inclusive bordas. Distância entre centros não basta. Regiões não anotadas continuam desconhecidas, salvo cobertura completa e negativa confirmada.

## 5. Execução do A

Preservar o fluxo original de referência e registrar sua origem. Nesta execução, `label_encoder.dat` confirmou classes `['0','1']`, e a API do VisionCruzi confirmou `1 = suspeita` e `0 = negativa`. O hash auditado está congelado em `configs/model_a.yaml` e no carregador; outro artefato exige nova verificação de origem/mapeamento. Se a compatibilidade do arquivo exigir correção de caminhos internos, trabalhar em cópia temporária e verificar preservação exata dos tensores. Não substituir o original.

Instrumentar pixels selecionados por etapa, candidatos, regiões classificadas, coordenadas, escores e duração, sem mudar decisões. Escores não são chamados de probabilidades calibradas. Registrar decisão original e um dos estados:

| Estado | Significado |
| --- | --- |
| `sem_regioes` | A localização não gerou recortes; o classificador não foi chamado. |
| `regioes_sem_predicao_positiva` | Houve classificação, sem região positiva conforme regra original. |
| `predicao_positiva` | Ao menos uma região recebeu decisão positiva. |
| `erro` | O sistema não concluiu a inferência; registrar causa. |

Se o fluxo original retorna sem suspeita quando não localiza candidatos, preservar a decisão, mas não afirmar que a rede classificou recortes negativos. Produzir tabela por imagem e sobreposição nas coordenadas originais. A execução sintética é uma verificação técnica, não resultado real de qualidade.

## 6. Preparação e treinamento do B

A localização deve ser executável, configurável e separada dos parâmetros congelados do A. Uma primeira solução deve ser examinada nas imagens de desenvolvimento; mudar limites HSV não é presumido suficiente. Os candidatos de treino seguem a mesma geometria, contexto e tratamento de bordas da inferência. Documentar como recebem rótulos; candidatos desconhecidos não viram negativos. Positivos não localizados permanecem na referência e contam na avaliação ponta a ponta.

Para a EfficientNet do Keras com reescala interna, a entrada RGB mantém tipo e faixa compatíveis, sem segunda divisão por 255. Registrar a versão efetiva. Aumentos são aplicados apenas no treino; transformações devem respeitar a morfologia e aquisição. Registrar camadas congeladas, Batch Normalization, otimizador, taxa de aprendizado, regularização e semente. A configuração final deve refletir o código executado, não uma lista de técnicas prometidas.

A implementação inicial usa black-hat na luminância, Otsu com contraste mínimo, componentes conexos e recorte contextual com bordas limitadas à imagem. O perfil atual está em `configs/model_b_cpu_original_negatives.yaml`, com localização preservada no treino e na inferência. As escolhas foram feitas no desenvolvimento, sem transferir conclusões de fontes descartadas. A caixa avaliada é o recorte contextual; `proposal_bbox` registra o componente bruto. Interseção com positivo revisado rotula o crop para classificação; a métrica de detecção ainda exige IoU/ponto e associação um a um.

Configuração efetiva: RGB float32 [0,255], resize bilinear TensorFlow comum ao treino e inferência, aumento apenas com rotações de 90 graus e espelhamentos. EfficientNet-B0, últimas 30 camadas elegíveis descongeladas (inclui camadas sem pesos na contagem), Batch Normalization congelada e base chamada com `training=False`, AdamW, LR inicial 1e-4, weight decay 1e-4, scheduler cosseno, dropout 0,3 e label smoothing 0,1. O smoke usa entrada 32 × 32, pesos aleatórios e base toda congelada, explicitamente para verificar execução.

Checkpoint e early stopping usam `val_loss`, modo mínimo; a inferência recebe `best.keras` reaberto. Não há restauração diferente em memória. Avaliar o artefato selecionado pela validação, nunca escolher pelo teste. Salvar configuração, partição, versões, histórico e checkpoint. Sem anotações confiáveis, executar apenas infraestrutura/verificações sintéticas e deixar treino real pendente. A comparação verifica sistema, partição e hash do manifesto, e bloqueia checkpoint sintético no teste final. O modo explícito `--synthetic-fixture` exige dados, anotações e previsões marcados como artificiais.

## 7. Regras de avaliação previamente definidas

### Localização e detecção

- Caixas: correspondência elegível por IoU ≥ 0,5, com limiar persistido antes do teste.
- Pontos: correspondência elegível quando o ponto anotado está contido na caixa prevista, respeitando extremos exclusivos. Essa avaliação mede cobertura do ponto, não a qualidade de uma caixa anatômica ausente.
- Associação **um a um**, maximizando o número de correspondências elegíveis. Desempates determinísticos devem ser documentados na implementação. Uma previsão não acerta dois parasitas; duas previsões do mesmo parasita não geram dois acertos.
- Cobertura da localização: parasitas associados a propostas / total de parasitas anotados, antes da classificação.
- Detecção final: TP são associações válidas de regiões positivas; FP são regiões positivas sem associação; FN são referências sem associação, **inclusive quando não houve recorte**. Precisão = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN), FP/imagem = FP/número de imagens avaliáveis. Denominadores nulos devem ser explícitos e tratados consistentemente.
- Detecção supervisionada exige referência revisada e cobertura completa. Referência parcial permite diagnóstico limitado, não estimativa válida de precisão/FP no restante desconhecido.

### Imagem inteira e recortes

Métricas binárias e matriz de confusão por imagem exigem rótulo inteiro explícito e revisado. A usa sua decisão original; para B, a regra inicial é presença de ao menos uma região classificada como positiva, com limiar definido na validação e congelado antes do teste. Não inferir rótulo inteiro negativo de uma lista vazia de marcações sem revisão. Métricas de recortes, quando disponíveis, são auxiliares e não substituem detecção.

### Erros, pareamento e custo

Comparar A e B sobre os mesmos IDs de teste. Incluir imagens sem candidatos e falhas. Uma falha com referência completa não pode apagar seus parasitas do denominador de detecção; registrar FN e taxa de falhas separadamente. Na avaliação binária, erro não recebe classe inventada: informar cobertura de execução e denominar claramente o subconjunto com decisões disponíveis.

Registrar tempo total e por etapa, hardware, aquecimento e condições de medição, tamanho dos artefatos e tempo de treino do B. Tempo de treino do A desconhecido fica indisponível. Ajustes de parâmetros e limiares usam somente desenvolvimento/validação. Resultados no teste não orientam nova seleção do mesmo experimento.

Intervalos de confiança, quando viáveis, devem reamostrar grupos independentes e preservar o pareamento A × B. Recortes correlacionados e sementes não são novas amostras independentes. Poucos grupos podem impedir inferência estatística confiável; não há obrigação de Wilcoxon, folds ou significância.

## 8. Limitações a manter no texto final

Histórico de treinamento do A incompleto, possível sobreposição com seu treino, poucos grupos independentes, aquisição/resolução heterogêneas, possível diferença de domínio e ausência ou incompletude de anotações. A igualdade dos IDs de avaliação **não implica igualdade da quantidade de imagens de treinamento**. O experimento compara sistemas completos; não identifica isoladamente a causa de uma diferença.

## 9. Evidências e execução

O [status atual](status.md) separa implementação, verificações técnicas e pendências do experimento. Diagnósticos de bases descartadas não são resultados da base atual. Registros anteriores foram preservados no [arquivo histórico](../archive/README.md).

## 10. Revisão da paridade experimental — 26/09/2026

Esta revisão explicita o alcance das conclusões; não autoriza retreinar ou substituir o A original. A superioridade do B é uma hipótese a testar, não uma premissa do trabalho. Uma comparação válida pode encontrar vantagem do A, do B ou um compromisso entre erros e custo de execução.

### Duas perguntas diferentes

| Pergunta | Desenho necessário | Conclusão possível |
| --- | --- | --- |
| Qual sistema pronto funciona melhor nesta base? | A original e B proposto recebem as mesmas imagens inteiras, referência, regras de pontuação e condições de execução. Cada um conserva seu processamento próprio. | Comparação dos sistemas como implementados, sujeita à história de treino e diferença de domínio. Não isola o efeito da arquitetura. |
| Qual arquitetura aprende melhor sob condições semelhantes? | Treinar uma nova versão da arquitetura de A e B com os mesmos exemplos rotulados, partições e regras de seleção; orçamento de ajuste comparável e inicialização/pretreino documentados. Recortes devem ser definidos por regra comum independente das previsões de ambos. | Comparação controlada de aprendizagem, ainda sujeita à independência dos dados e aos fatores que não puderem ser igualados. |

**Decisão de escopo confirmada por Caio em 26/09/2026:** adotar o primeiro desenho, preservando A original como referência histórica e avaliando a evolução representada pelo sistema B. Não retreinar A. O segundo desenho foi discutido como alternativa e não será adotado neste escopo. O diagnóstico com recortes comuns permanece auxiliar, não substitui a comparação dos sistemas completos.

O ano de 2024 foi informado por Caio como contexto do A; sua associação ao artefato/versão deve ser confirmada por documentação do trabalho original. Não descrever A como "a melhor tecnologia de 2024" ou representante de todo o estado da arte sem revisão bibliográfica que sustente essa afirmação. A formulação é "sistema de referência desenvolvido anteriormente" e, após comprovação da data, "sistema desenvolvido em 2024". A diferença entre A e B reflete o conjunto das mudanças de dados, treinamento, localização e classificação, não uma medida isolada do avanço tecnológico entre anos.

### Como expressar a evolução

Apresentar valores absolutos de cada sistema, denominadores e diferença em uma métrica definida. "X vezes melhor" sem identificar a métrica não é uma conclusão válida. Exemplos exclusivamente ilustrativos: recall de 40% para 80% corresponde a +40 pontos percentuais e razão 2 entre recalls; falsos positivos de 10 para 5 por imagem correspondem a redução de 50%; tempo de 2 para 6 segundos por imagem representa duração 3 vezes maior. Razões exigem denominador não nulo e estimativas válidas. Um ganho em detecção pode acompanhar maior custo ou mais alarmes falsos; apresentar ambos.

Esse desenho pode sustentar melhoria do sistema proposto sobre a referência histórica nas condições avaliadas. Não demonstra superioridade universal da EfficientNet-B0 sobre outra arquitetura nem garante generalização clínica. Diferenças de treino e possível sobreposição de dados do A devem continuar explícitas.

### O que a execução atual permite

A validação usa as mesmas 114 imagens inteiras. A gerou 42 candidatos; a configuração inicial de B gera 140.005. São regiões propostas dentro das imagens, não 140.005 imagens independentes ou novas amostras de avaliação. A diferença de candidatos é uma propriedade dos localizadores e explica parte do custo. Não descartar arbitrariamente propostas de B nem avaliar somente imagens em que A encontrou candidatos para aproximar os resultados.

A regra de presença de qualquer região positiva favorece decisões positivas quando há muitas propostas. Como os campos atuais têm referência positiva, marcar quase tudo como suspeito pode aparentar bom resultado por imagem mesmo com muitos alarmes indevidos. É necessário medir falsos positivos em referência suficiente para esse fim; o conjunto atual não permite estimar especificidade em lâminas negativas. Mais candidatos, mais decisões positivas e maior tempo não demonstram maior qualidade.

O diagnóstico suplementar de classificadores nos mesmos recortes de validação é apenas exploratório: os recortes foram selecionados pelo localizador B e seus pixels brutos diferem das regiões mascaradas usadas pelo A original. Dar os mesmos recortes a redes prontas não corrige históricos de treino diferentes nem torna esse diagnóstico uma comparação neutra de arquiteturas. Não o usar como resultado principal de superioridade.

### Condições para a comparação principal

- Fixar pergunta, conjunto de avaliação, regras de correspondência e métricas antes do teste. A validação pode orientar ajustes; o teste reservado não pode orientar a escolha do modelo. Essa separação segue as [recomendações de prevenção de vazamento do scikit-learn](https://scikit-learn.org/1.8/common_pitfalls.html#data-leakage).
- Manter todas as imagens elegíveis e contabilizar casos sem regiões e falhas. Quantificar cobertura de localização separadamente dos erros de classificação.
- Comparar tempo e qualidade conjuntamente. Registrar mesma máquina, recursos de CPU/GPU, modo de execução e aquecimento. Separar carregamento, leitura/gravação e algoritmo; a medição atual é exploratória e inclui primeiras chamadas.
- Para detecção, revisar a referência necessária para identificar falsos positivos; não transformar regiões não anotadas em negativas. Para diagnóstico por lâmina, obter lâminas negativas e rótulos compatíveis antes de afirmar especificidade.
- Esclarecer possível sobreposição do treino de A com a base e a identidade animal/lâmina. O uso de IDs iguais na avaliação não resolve essas pendências.

Não alterar dados, limites ou métricas para garantir a vitória de B ou aproximar artificialmente os resultados. As interrupções e preparações anteriores estão documentadas no arquivo histórico.

## Protocolo adicional de robustez (ensaio anterior arquivado)

Aplicar a cada uma das 187 imagens de desenvolvimento (114 positivas/73 negativas) as mesmas três transformações predefinidas, sem escolher intensidade pelo resultado: rotação 90° anti-horária, espelho horizontal e brilho multiplicado por 0,85. Os modelos, dados de treino, limiares e localização permanecem congelados. Aumentar ambos os grupos evita assimetria de condições, mas não elimina confusão entre fontes, espécies e aquisição.

As 561 versões herdam a referência do original; transformações geométricas transportam pontos e caixas para os pixels correspondentes. Comparar decisões e cobertura por original/condição; não computar 748 vistas como 748 unidades independentes nem atribuir intervalos de confiança independentes a versões do mesmo original. Imagens de treino e as 105 de teste não entram. Resultados são exploratórios e adicionais à comparação principal, sem seleção de melhores versões.

## Reserva Barcelona e separação de origens

Após o diagnóstico das 200 imagens, Caio autorizou reservar 20 para treino e 180 para comparação. Semente 42, duas ou três imagens por tipo celular, sem consultar previsões. A autorização e os manifestos imutáveis estão em `data/protocol/barcelona_split_20261006/`. A disjunção é conferida por IDs, grupos, hashes de bytes e pixels; recortes e variantes das 20 imagens de treino ficam excluídos da avaliação. Como o lote já foi examinado, as 180 restantes são desenvolvimento, não teste final independente.

O ensaio anterior de robustez e o diagnóstico das 200 pertencem ao B arquivado; resultados, figuras e a documentação anterior estão em `archive/limpeza_pos_retreino_20261006.zip`. O novo B exige nova inferência; não reutilizar previsões de outro checkpoint.

## Treinamento concluído com os 20 originais Barcelona — 06/10/2026

Após nova autorização de Caio, o B foi treinado novamente com as mesmas regras de arquitetura, localização, aumento e seleção, acrescentando os 80 recortes negativos dos 20 originais reservados. Todos os 4.381 recortes de treino foram consumidos uma vez por época, com pesos por classe calculados das novas contagens, sem oversampling/undersampling. A validação permanece com 1.070 recortes. Foram concluídas 17 épocas; o checkpoint da décima foi selecionado por menor `val_loss` (0,21533), salvo e reaberto. A acurácia correspondente de 99,25% refere-se somente aos recortes de validação.

O B anterior foi arquivado integralmente e conferido por hashes. O A original permanece inalterado. A comparação pós-treino executa os dois modelos novamente nos mesmos 367 IDs (114 positivas, 73 negativas Kaggle e 180 negativas Barcelona); não reutiliza previsões do B anterior. O lote, rótulos, pontos e critérios de correspondência foram mantidos. Não usar os 20 originais de treino nem suas versões na avaliação.

A distribuição anterior de Python 3.11.15 foi bloqueada pela política de assinatura do Windows; a execução usou Python oficial 3.11.9, preservando TensorFlow/Keras 2.15 e as demais dependências. Ambiente e reparo estão registrados junto à execução. A medição atual é uma execução sequencial por sistema em CPU, duas threads, sem exportação de imagens durante a inferência; não é benchmark repetido com aquecimento controlado. Os resultados antigos de robustez e das 200 Barcelona continuam históricos do checkpoint arquivado. O teste final de 105 imagens não foi aberto.

## Apresentação por classe — 06/10/2026

A pedido do autor, gráficos e tabelas visuais usam somente imagens positivas (114) e negativas (253). O agrupamento não altera partições, referências, modelos ou previsões. Medianas e distribuições de tempo dos negativos são recalculadas a partir de todas as imagens, sem fazer média das medianas das fontes. `class_summary` descreve os grupos visuais; `summary`, `cohort` e `source` conservam a procedência nos arquivos técnicos. Não interpretar o agrupamento como demonstração de generalização clínica ou equivalência entre aquisições.
