# Registro de decisões técnicas — A × B

> Decisões ativas de 2026-09-20. As entradas anteriores, inclusive alegações não reconfirmadas, foram preservadas no [histórico](historico/decisoes_tecnicas_2026-05.md). A [metodologia](metodologia.md) é a referência central.

## Dois sistemas completos

**Decisão:** comparar A original, com pesos fixos, e B proposto. A entrada principal é a mesma imagem inteira. Não retreinar o A nem exigir uma abordagem adicional.

**Motivo:** a localização condiciona quais objetos chegam ao classificador. Compartilhar obrigatoriamente a segmentação impediria avaliar uma proposta que também atua nessa etapa. Eventual diferença de desempenho será atribuída ao sistema completo, sem decomposição causal por técnica.

## Reprodução e instrumentação do A

**Decisão:** preservar segmentação, canais, recortes, pré-processamento e decisão da referência. Correções de compatibilidade do arquivo usam cópia temporária e prova de preservação dos tensores. Registrar versão do repositório e hash do modelo.

**Motivo:** ajustar o A para melhorar resultados produziria uma referência diferente da entregue. Instrumentar contagens e tempos permite distinguir falha de localização, classificação negativa e erro de execução.

**Pendência:** confrontar o remoto local `Cablade/VisionCruzi` com `Cablade/Vision`, indicado no pedido, e registrar qual implementação sustenta os experimentos.

## Dados antes dos recortes

**Decisão:** inventário por imagem com hash e grupo; exclusão de duplicatas via manifesto, preservando arquivos; partições antes da geração de recortes e aumentos. Preferir animal/lâmina confirmados. Na ausência deles, agrupar por imagem original e declarar a limitação.

**Motivo:** recortes da mesma origem compartilham características e não podem aparecer em treino e teste. Pastas e nomes de arquivo não demonstram independência dos grupos. Não escolher porcentagens/folds sem contar os grupos e classes.

## Referência independente

**Decisão:** documentar cobertura, estado de revisão e responsável por cada imagem; aceitar negativos apenas quando confirmados. Interseção do recorte inteiro com positivos impede rotulá-lo como negativo.

**Motivo:** ausência de marcação pode significar região não examinada. Previsões do próprio modelo não são referência para avaliar sua qualidade. Treino real e métricas finais dependem de revisão qualificada.

## EfficientNet-B0 e localização do B

**Decisão:** manter EfficientNet-B0 como proposta atual, já implementada no código-base, e tornar sua localização configurável. Pré-processamento deve respeitar RGB, dtype e faixa esperada pela versão real do Keras, evitando dupla normalização. A geometria de recortes de treino e inferência deve coincidir.

**Motivo:** manter escopo viável e corrigir riscos identificados antes do experimento. O uso da arquitetura não comprova desempenho superior. A primeira localização deve ser verificada no desenvolvimento, sem presumir que ajuste HSV basta nem impor detector complexo.

**Treino:** registrar fine-tuning, congelamento e Batch Normalization, otimizador, taxa e aumentos. Checkpoint e restauração compartilham critério de validação. Configuração efetiva e resultados executados prevalecem sobre técnicas apenas previstas em documentos antigos.

## Avaliação pareada e inferência estatística

**Decisão:** definir critérios de correspondência e limiares antes do teste; associação um a um; medir cobertura de localização, detecção final, decisão por imagem quando houver referência e custo. Manter falhas e imagens sem regiões no relatório.

**Motivo:** um parasita sem recorte é um falso negativo na detecção final. Recortes e sementes não são novas lâminas independentes. O mesmo conjunto de avaliação não implica o mesmo histórico ou tamanho de treinamento.

## Separação entre implementação e resultado

**Decisão:** modo curto sintético comprova execução, salvamento e recarga, sem ser apresentado como qualidade real. Registrar diagnósticos em imagens reais sem rótulo como diagnósticos, sem inventar métricas. Relatos de sessões anteriores permanecem identificados até serem reproduzidos.

**Motivo:** código presente, teste sintético, inferência real e avaliação supervisionada respondem a perguntas diferentes. O checklist e o relatório devem distinguir essas evidências.
