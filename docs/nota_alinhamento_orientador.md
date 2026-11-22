# Nota de alinhamento da proposta — para o Prof. Rogério Mandelli

> Rascunho de 13/10/2026, para envio pelo Victor junto com o [plano estatístico](plano_estatistico.md). Revisar antes de enviar.

Prezado Prof. Rogério,

Encaminhamos a atualização do desenho experimental do TCC, para que a proposta registrada corresponda ao que foi efetivamente implementado e ao que será avaliado. As mudanças em relação à versão enviada anteriormente são as seguintes.

| Aspecto | Proposta anterior | Desenho atual | Motivo |
| --- | --- | --- | --- |
| Sistemas comparados | Três modelos (A1, A2 e B) | Dois sistemas completos: A original, preservado, e B proposto | O A2 (retreino do A) foi retirado do escopo em 26/09/2026; a pergunta passou a ser a comparação entre o sistema existente e a proposta |
| Região de interesse | Recorte fixo de 100 × 100 px | Localização por black-hat e limiar de Otsu, com recorte contextual (mínimo de 100 px, até 224 px após agrupamento), redimensionado para 224 × 224 | A avaliação passou a ser feita na imagem inteira, e a mesma localização gera os recortes de treino e de inferência |
| Aumento de dados | Albumentations | Somente rotações de 90° e espelhamentos | Transformações que preservam morfologia e cor da aquisição; implementação própria em NumPy |
| Negativos de treino | Regiões aleatórias distantes dos positivos | Regiões revisadas manualmente, incluindo negativos difíceis da mesma aquisição dos positivos | Regiões não anotadas não são necessariamente negativas; a revisão de 13/10/2026 mostrou que negativos de outra fonte levavam o modelo a reconhecer a origem da imagem |
| Análise estatística | Não detalhada | Bootstrap pareado por imagem para cobertura e precisão; McNemar exato para a decisão por imagem, com correção de Holm | Atende ao pedido de plano de análise estatística |

Também informamos que, na análise dos resultados de desenvolvimento, identificamos que o classificador do sistema B estava separando as imagens pela origem (camundongo × humano), e não pela presença do parasita. Antes da abertura do conjunto de teste, o modelo será retreinado com negativos da mesma aquisição, revisados manualmente, e sua precisão será estimada por revisão de amostra. O conjunto de teste de 105 imagens permanece fechado até o congelamento do protocolo.

Ficamos à disposição para discutir o plano.

Atenciosamente,
Caio Nascimento e Victor Jacques
