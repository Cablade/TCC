# Metodologia — comparação dos sistemas A × B

> Protocolo ativo, iniciado em 2026-09-20. Substitui os desenhos históricos. Este documento define o experimento; a evidência do que foi efetivamente executado deve ficar no checklist e nos relatórios de execução.

## 1. Unidade de comparação

Comparar exatamente dois sistemas completos de localização e classificação de regiões suspeitas de *Trypanosoma cruzi*. O A usa os pesos já treinados e reproduz a inferência original. O B é a proposta, com localização configurável e EfficientNet-B0. Ambos recebem os mesmos IDs de **imagens inteiras** do conjunto reservado. Nenhum retreinamento do A será realizado. As etapas de localização não precisam ser iguais.

O arquivo `.keras` de A não representa sozinho o sistema: segmentação, recortes, ordem dos canais, redimensionamento, pré-processamento e decisão também precisam ser preservados. A proposta B poderá modificar várias etapas; eventual ganho não permite atribuição causal a uma delas. Não são exigidas ablações ou arquiteturas adicionais.

## 2. Origem e rastreabilidade

- TCC inspecionado: commit `e056cd60739d2f4d6f74b329a24beb81b6ae916b`, com alterações locais existentes preservadas antes da revisão.
- Referência indicada pelo pedido: `Cablade/Vision`.
- Referência local encontrada: repositório com remoto `Cablade/VisionCruzi`, commit `59b10244f2ce5cfabff7bece404cb5679668a45d`. A equivalência com a referência indicada precisa ser registrada após confronto; não é presumida.
- Artefato `model_trained.keras` localizado. Desde 22/09/2026, a única base local selecionada é `trypoastigote_images.zip`, auditada em [base atual](dados.md#base); os ZIPs anteriores estão excluídos. Sua presença não comprova anotações ou qualidade do modelo.

Cada execução deve registrar commit e modificações locais relevantes, hash SHA-256 do modelo e dos dados, configuração, semente, manifestos, versões, hardware, tempos e caminhos de saída. Dados originais e pesos não devem ser sobrescritos nem incluídos automaticamente no Git.

## 3. Inventário, grupos e partições

O inventário contém identificador estável, caminho, SHA-256, largura, altura, origem, grupo e nível do grupo. Valores desconhecidos são explícitos. Duplicatas por conteúdo ficam no inventário e no manifesto de exclusão; seus originais permanecem intactos. Variantes reencodadas e imagens correlacionadas precisam de inspeção adicional, pois hashes de arquivo não demonstram independência biológica.

Usar identificador de animal, ou de lâmina, quando confirmado; caso contrário, o grupo é a imagem original, com essa limitação declarada. Nomes de diretório não comprovam identidade de animal/lâmina. Não permitir a mesma origem nem duplicatas em partições diferentes.

Separar antes de gerar recortes ou aumentos. Persistir a semente e as atribuições de grupo. Não há porcentagem padrão neste protocolo: primeiro examinar grupos e classes; então registrar uma divisão viável. Dados já usados para diagnóstico ou escolha de parâmetros pertencem ao desenvolvimento. Se não houver grupos suficientes para treino, validação e teste reservado, registrar a impossibilidade e não apresentar o lote de desenvolvimento como teste final.

## 4. Anotações e negativos

As [fontes candidatas de negativos](dados.md#negativos) devem ser avaliadas quanto a espécie, preparação, equipamento e nível do rótulo. Campo ou recorte sem parasita não equivale a lâmina/animal negativo. Não confundir a origem do conjunto com a classe; evitar positivos exclusivamente de uma fonte e negativos de outra. A base atual é de camundongos e não sustenta, por si, conclusões clínicas sobre humanos.

O formato de referência está em [data/README.md](anotacoes.md#formato). Coordenadas usam a imagem original: origem no canto superior esquerdo, x para a direita, y para baixo. Caixas `[x1,y1,x2,y2]` têm extremos direito/inferior exclusivos; pontos são `[x,y]`. Imagens e marcações devem declarar revisão e responsável. A ausência de marcação ou de arquivo de anotação nunca significa negativo.

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

A implementação inicial usa black-hat na luminância, Otsu com contraste mínimo, componentes conexos e recorte contextual com bordas limitadas à imagem. Trata-se de um protótipo anterior à troca da base. Os valores de `configs/model_b.yaml` são provisórios e precisam ser examinados no desenvolvimento da base atual, sem transferir conclusões da base descartada. A caixa avaliada é o recorte contextual; `proposal_bbox` registra o componente bruto. Interseção com positivo revisado rotula o crop para classificação; a métrica de detecção ainda exige IoU/ponto e associação um a um.

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
