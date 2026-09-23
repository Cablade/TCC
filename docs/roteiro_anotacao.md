# Preparar a referência para o treinamento

O objetivo desta etapa é ligar cada imagem utilizável a marcações confiáveis de parasitas e de regiões sem parasitas. A importação de anotações públicas pode reduzir bastante o trabalho. Ela não deve converter ausência de marcação em negativo nem transformar previsões de um modelo em revisão humana.

## 1. Aproveitar as anotações disponíveis

Consulte a [base atual](dataset_atual.md) para os suplementos e arquivos públicos identificados. Preserve uma cópia da anotação original e registre fonte, versão, licença, hash do arquivo e transformação aplicada. Um arquivo importado deve manter os identificadores da origem além do `image_id` usado no projeto, em um registro de correspondências.

Antes de aceitar a conversão, confira:

1. **Imagem certa:** o nome corresponde a uma única imagem? Quando a fonte repete nomes em pastas diferentes, preserve a pasta. Use conteúdo e dimensões para confirmar a correspondência; o nome sozinho pode ser insuficiente.
2. **Pixels certos:** as coordenadas pertencem à imagem original ou a uma versão reduzida? Registre a escala em x e y e confira sobreposições sobre os pixels originais. Uma troca de largura/altura ou de x/y pode produzir arquivos válidos com marcações no lugar errado.
3. **Significado certo:** a fonte fornece caixas, pontos, máscaras ou recortes? Um ponto não delimita o tamanho do parasita; não invente uma caixa como se fosse anotação original.
4. **Cobertura conhecida:** o artigo afirma que todos os parasitas foram marcados? A lista pode ser parcial. Imagem sem linha na tabela não é automaticamente imagem negativa.
5. **Revisão documentada:** registre quem produziu a referência pública e o que a equipe conferiu localmente. Uma atribuição de revisor deve ser real e rastreável; não preencher um nome genérico para fazer o programa aceitar o arquivo.

Uma revisão de alguns exemplos ajuda a detectar erros da conversão, mas não confirma que todas as imagens sem marcações sejam negativas. Inconsistências e casos incertos ficam pendentes ou excluídos, com motivo registrado.

## 2. Revisar positivos e negativos

O modelo B recebe recortes propostos automaticamente. Para treinar, é necessário que esses recortes tenham os dois rótulos: `0` para negativo e `1` para suspeito com referência positiva. Não é necessário que todo recorte negativo venha de um doador negativo.

| O que foi efetivamente revisado | Como registrar | O que permite |
| --- | --- | --- |
| Parasitas em uma imagem, sem assegurar cobertura completa | `positives`, `review_status: reviewed`, revisor real; `reference_complete: false` | Recortes que intersectam positivos revisados podem ensinar a classe positiva |
| Uma área específica sem parasitas | Caixa em `negative_regions`, com estado e revisor próprios | Um recorte inteiramente dentro dessa área e sem interseção positiva pode ensinar a classe negativa |
| Campo inteiro examinado, sem parasitas visíveis | `whole_image_label: 0`, `reference_complete: true`, lista positiva vazia, revisão registrada | Recortes desse campo podem ensinar a classe negativa; o campo pode participar da avaliação por imagem |
| Campo inteiro examinado, com todos os parasitas marcados | `whole_image_label: 1`, `reference_complete: true`, positivos e revisão registrados | Referência para avaliar detecção e decisão no campo |
| Situação incerta ou ainda não examinada | Estado pendente, rótulo `null`, cobertura incompleta | Não vira dado negativo nem referência de teste |

**Um campo sem parasitas visíveis não comprova ausência de Chagas na lâmina inteira, no animal ou no paciente.** Registre separadamente o nível da evidência da fonte. Controles de malária, por exemplo, não demonstram automaticamente teste negativo específico para *T. cruzi*. Consulte [fontes negativas](fontes_negativas.md).

Para regiões negativas dentro de uma imagem positiva, examine toda a área marcada e o contexto que será incluído no recorte. O extrator inclui margem: se o recorte ultrapassar a caixa negativa revisada, ele pode permanecer sem rótulo. Isso é esperado; aumente a região somente se a área adicional também tiver sido revisada.

## 3. Usar as coordenadas e campos corretos

O formato completo está em [Dados e anotações](../data/README.md). Os pontos e caixas usam os pixels originais da imagem:

- `point: [x, y]`: x cresce para a direita e y para baixo.
- `bbox: [x1, y1, x2, y2]`: canto superior esquerdo seguido pelo inferior direito; x2 e y2 são extremos exclusivos.
- As dimensões de cada anotação devem coincidir com `width` e `height` no inventário.
- Cada positivo contém ponto **ou** caixa. Cada região negativa contém caixa e sua revisão.

Não redimensione ou regrave os originais para ajustar uma marcação. Corrija a transformação de coordenadas, documente-a e preserve os hashes das imagens. Não substitua o JSON revisado por um novo template vazio ao atualizar o inventário.

## 4. Separar as imagens antes de ajustar o sistema

Preencha os grupos de animal/lâmina quando a fonte os fornecer. Mantenha todos os campos do mesmo grupo na mesma partição. Se só a imagem original puder ser identificada, registre essa limitação; uma identificação não documentada de animal não melhora a separação.

Reserve os grupos de teste antes de ajustar o localizador ou escolher as configurações do classificador. A revisão biológica do teste deve ser independente das previsões que serão avaliadas. Anotações de desenvolvimento podem ser usadas para calibrar o sistema, mas essas imagens não voltam a ser teste intocado.

Quando houver imagens provenientes de outro estudo, evite uma divisão em que todos os positivos sejam de uma origem e todos os negativos de outra. O classificador pode aprender coloração, câmera ou preparação. Registre a origem por imagem e planeje a análise por fonte.

## 5. Conferir antes de entregar ao treino

O conjunto de trabalho usa os nomes definidos no [guia de treinamento](guia_treinamento.md): inventário, `grupos.csv`, manifesto de partições e `experimento_reference.json`. A conferência deve responder:

- Os IDs e dimensões batem com as imagens legíveis, sem reintroduzir o JPEG excluído?
- A origem das marcações e o responsável pela revisão estão registrados?
- Existem positivos e negativos confiáveis nos grupos de treino e validação?
- As regiões negativas não intersectam os positivos e cobrem os recortes que serão usados?
- Os grupos não aparecem em partições diferentes?
- O teste contém referência apropriada para as métricas que serão apresentadas?

Execute a validação e o verificador descritos no guia. Eles detectam problemas estruturais e requisitos ausentes; não inspecionam os pixels como um especialista. Guarde o relatório e a referência utilizada com cada execução. Uma revisão posterior exige novos recortes, porque o treino confere o hash da anotação que os gerou.
