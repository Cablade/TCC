# Anotações: revisão e formato

A referência positiva publicada já está importada; sua origem fica em [dados](dados.md#anotacoes-publicas). Este documento reúne a revisão humana e o contrato dos arquivos.

- [Revisão visual](#revisao)
- [Critérios para rotular](#criterios)
- [Formato e validação](#formato)

<a id="revisao"></a>

## Revisão visual

### Pré-seleção disponível para olhar depois

Foi preparado um lote com **20 regiões candidatas**, após triagem visual de 40 propostas em oito imagens reservadas para desenvolvimento. Vinte propostas foram deixadas de fora por borda escura, foco ruim ou ambiguidade. As sugestões restantes estão em sete dessas imagens e **continuam sem rótulo, pendentes de revisão humana**.

Abra a [galeria de pré-seleção](../data/annotations/negative_preselection_v1/index.html) para olhar os recortes. Clique em um recorte para ampliá-lo. Para abrir cada sugestão sobre a imagem original e salvar uma confirmação, use o atalho `scripts\abrir_revisao.cmd` ou execute:

```powershell
.\.venv\Scripts\python.exe scripts/review_annotations.py --batch data/annotations/negative_preselection_v1
```

Abra o endereço local exibido. Clique em **examinar** na candidata, confira a imagem ampliada, informe o revisor e confirme somente depois da avaliação. É possível desenhar outra área. Sugestões ignoradas não entram no treino. A saída humana fica em `data/annotations/negative_preselection_v1/reviewed.json`, separada da fonte; ela cobre apenas as oito imagens deste lote, não substitui automaticamente a referência completa do experimento.

Não abra `scripts/review_ui.html` diretamente pelo Explorer (`file:///`). Essa página usa a API local para carregar as imagens; por isso o navegador precisa estar em `http://127.0.0.1:8765/` com o servidor aberto. O atalho inicia o servidor e mostra esse endereço.

Depois de terminar a revisão, a referência completa foi gerada em `data/annotations/experimento_reference.json` com:

```powershell
.\.venv\Scripts\python.exe scripts/merge_reviewed_reference.py
```

Ela reúne os 674 registros positivos publicados e as 29 regiões negativas revisadas por Caio. O arquivo não transforma as oito imagens em lâminas inteiramente negativas.

`suggestions.json` conserva as candidatas pendentes; `assistant_triage.json` registra as exclusões da triagem. `development_reservation.json` registra IDs, hashes e grupos das oito imagens examinadas. **Essas oito imagens e suas cópias não podem compor um teste final intocado**, mesmo a que ficou sem sugestões. Preserve essa reserva ao definir as partições; a pasta `train` original foi usada apenas para evitar abrir o `test` da fonte, não como prova de independência biológica.

As propostas usam estruturas detectadas e distância mínima de 200 pixels dos pontos positivos conhecidos. Essa distância não comprova ausência de parasitas não anotados. Nenhuma região foi confirmada biologicamente por esta triagem. Para gerar outro lote, use `scripts/preselect_negatives.py --output-dir NOVO_DESTINO`; a seleção automática não inclui a triagem visual feita neste primeiro lote e não sobrescreve saídas existentes.

Esta ferramenta abre as imagens originais no navegador do próprio computador. Você desenha retângulos que examinou e registra seu nome como revisor. Os pontos positivos publicados continuam preservados. Nenhuma região recebe rótulo negativo automaticamente.

### Antes de começar

Reserve as imagens de teste por grupos de origem antes da revisão de desenvolvimento. Uma imagem examinada para escolher negativos de treinamento não deve posteriormente ser apresentada como teste intocado. O inventário fornecido à ferramenta deve conter a coluna `split`; linhas com `test` ficam bloqueadas. Se ainda não houver divisão, a página avisa sobre essa pendência.

O revisor precisa saber reconhecer o parasita e estruturas que podem ser confundidas com ele. Combine esse trabalho com o orientador ou alguém habilitado a revisar as imagens. A ferramenta registra o nome informado; ela não verifica a identidade nem substitui a revisão especializada.

### Abrir no Windows

Na pasta do projeto, com o ambiente Python instalado:

```powershell
.\.venv\Scripts\python.exe scripts\review_annotations.py
```

Abra **http://127.0.0.1:8765/** no navegador. Mantenha o terminal aberto durante a revisão. O servidor aceita conexões somente deste computador.

Os padrões carregam `data/protocol/trypomastigote_verified/eligible_inventory.csv` e `data/annotations/public_import/public_points.json`. A saída é `data/annotations/experimento_reference.json`; o arquivo publicado de entrada permanece intacto.

Para usar o manifesto com as partições já aprovadas:

```powershell
.\.venv\Scripts\python.exe scripts\review_annotations.py `
  --inventory data\splits\experimento\images.csv `
  --annotations data\annotations\public_import\public_points.json `
  --output data\annotations\experimento_reference.json
```

Esse manifesto precisa existir e conter exatamente os IDs presentes na referência. O comando não cria nem aprova a divisão. Se a porta estiver ocupada, acrescente `--port 8766` e abra o endereço mostrado no terminal.

### Revisar e salvar

1. Selecione uma imagem e informe seu nome real.
2. Amplie para examinar os pixels. Vermelho identifica positivos publicados; verde mostra regiões negativas já registradas.
3. Arraste o mouse para desenhar um retângulo. Examine toda a região e suas margens. A ausência de um ponto vermelho não comprova ausência de parasitas.
4. Marque a confirmação somente depois de examinar a área e clique em **Salvar região revisada**.
5. Repita em outras regiões de treino ou validação. Se tiver dúvida, descarte a seleção e deixe a área sem rótulo.

As coordenadas são salvas na resolução original, independentemente da ampliação. Caixas vazias, fora dos limites ou sobrepostas aos positivos conhecidos são rejeitadas. Pontos descrevem uma posição, não toda a extensão do parasita: mantenha distância de qualquer estrutura suspeita.

Uma região negativa pode conter células e artefatos relevantes. Não selecione apenas espaços vazios: o classificador precisa de exemplos de estruturas que podem gerar falsos positivos, desde que revisadas como livres de parasitas visíveis.

### Retomar, corrigir e usar no treinamento

Cada salvamento registra revisor, horário e histórico. A versão anterior da saída fica em um arquivo `.bak`. Para retomar, execute o mesmo comando; as regiões salvas serão carregadas. **Remover** apaga apenas uma região criada nesta ferramenta e mantém o registro da ação. Regiões da referência original permanecem preservadas.

Encerre com `Ctrl+C` no terminal. Seleções não salvas são perdidas. Guarde cópia de segurança da saída e do manifesto usado. Se algum deles mudar durante a revisão, a ferramenta interrompe o salvamento para evitar sobrepor versões. Se o inventário mudar entre sessões, preserve a saída antiga e escolha um novo arquivo de saída; reconciliar versões exige conferir a referência e as partições.

Use o arquivo revisado como argumento de anotações nas etapas do [guia de treinamento](guia_treinamento.md). Somente candidatos inteiramente contidos em uma região negativa revisada recebem rótulo negativo por essa região; áreas desconhecidas continuam sem rótulo.

Salvar regiões **não** altera `reference_complete`, o rótulo da imagem inteira nem o estado de revisão dos positivos. Essa atividade prepara negativos para desenvolvimento; não conclui a referência exaustiva necessária para métricas finais. Uma região sem parasita visível também não comprova que a lâmina ou o paciente sejam negativos para Chagas.

<a id="criterios"></a>

## Critérios para rotular

O modelo B recebe recortes propostos automaticamente. Para treinar, é necessário que esses recortes tenham os dois rótulos: `0` para negativo e `1` para suspeito com referência positiva. Não é necessário que todo recorte negativo venha de um doador negativo.

| O que foi efetivamente revisado | Como registrar | O que permite |
| --- | --- | --- |
| Parasitas em uma imagem, sem assegurar cobertura completa | `positives`, `review_status: reviewed`, revisor real; `reference_complete: false` | Recortes que intersectam positivos revisados podem ensinar a classe positiva |
| Uma área específica sem parasitas | Caixa em `negative_regions`, com estado e revisor próprios | Um recorte inteiramente dentro dessa área e sem interseção positiva pode ensinar a classe negativa |
| Campo inteiro examinado, sem parasitas visíveis | `whole_image_label: 0`, `reference_complete: true`, lista positiva vazia, revisão registrada | Recortes desse campo podem ensinar a classe negativa; o campo pode participar da avaliação por imagem |
| Campo inteiro examinado, com todos os parasitas marcados | `whole_image_label: 1`, `reference_complete: true`, positivos e revisão registrados | Referência para avaliar detecção e decisão no campo |
| Situação incerta ou ainda não examinada | Estado pendente, rótulo `null`, cobertura incompleta | Não vira dado negativo nem referência de teste |

**Um campo sem parasitas visíveis não comprova ausência de Chagas na lâmina inteira, no animal ou no paciente.** Registre separadamente o nível da evidência da fonte. Controles de malária, por exemplo, não demonstram automaticamente teste negativo específico para *T. cruzi*. Consulte [fontes negativas](dados.md#negativos).

Para regiões negativas dentro de uma imagem positiva, examine toda a área marcada e o contexto que será incluído no recorte. O extrator inclui margem: se o recorte ultrapassar a caixa negativa revisada, ele pode permanecer sem rótulo. Isso é esperado; aumente a região somente se a área adicional também tiver sido revisada.

<a id="formato"></a>

## Formato e validação

### Inventário

O inventário é produzido antes de recortes e aumentos:

| Coluna | Significado |
| --- | --- |
| `image_id` | Identificador estável usado em anotações, partições e resultados |
| `path` | Arquivo local ou membro do ZIP, no formato `zip://CAMINHO_ABSOLUTO!membro` |
| `sha256` | Hash do conteúdo do arquivo original |
| `width`, `height` | Dimensões verificadas da imagem original |
| `source` | Origem declarada; desconhecida quando não confirmada |
| `group_id` | Animal/lâmina confiável ou identificador da imagem original |
| `group_level` | Nível efetivamente disponível: animal, lâmina ou imagem |
| `duplicate_of` | ID canônico de conteúdo idêntico; vazio para o exemplar mantido |
| `split` | No manifesto de partições: treino, validação, teste ou desenvolvimento |

Os valores de partição usados pelos scripts são `train`, `val`, `test` e `development`. Um hash de arquivo detecta cópias de bytes idênticos; reencodificações e campos correlacionados exigem revisão adicional. O manifesto de exclusão registra os duplicados sem apagar imagens. Não decidir que dois arquivos são duplicatas apenas por terem o mesmo nome.

### Grupos e reserva

Confirmar animal/lâmina com a equipe; não transformar nomes de pastas em identidades biológicas presumidas. Sem identificadores confiáveis, usar imagem original e declarar que a independência entre lâminas/animais não foi demonstrada. Recortes da mesma imagem herdam seu grupo e partição.

Atribuir partições **antes** de gerar recortes. Persistir semente e escolhas de grupos. Um CSV explícito de atribuições usa:

```csv
group_id,split
grupo_confirmado_001,train
grupo_confirmado_002,val
grupo_confirmado_003,test
```

O exemplo é ilustrativo, não constitui uma partição real aprovada. Primeiro examinar grupos/classes e justificar quantos grupos podem ser reservados. Imagens usadas para inspecionar falhas ou ajustar a localização de B são desenvolvimento. Se não houver dados para teste intocado, registrar a falta; não renomear desenvolvimento como teste.

### Formato de anotação

A referência JSON usa `schema_version: 1` e `coordinate_convention: "xyxy_half_open"`. Todos os valores espaciais se referem aos pixels originais, sem redimensionamento: canto superior esquerdo `(0,0)`, x horizontal e y vertical. Caixas têm extremos direito e inferior exclusivos: `0 <= x1 < x2 <= width` e `0 <= y1 < y2 <= height`. Pontos atendem `0 <= x < width` e `0 <= y < height`.

Exemplo **sintético**, ainda pendente de revisão:

```json
{
  "schema_version": 1,
  "coordinate_convention": "xyxy_half_open",
  "images": [
    {
      "image_id": "exemplo_sintetico",
      "width": 100,
      "height": 80,
      "review_status": "pending",
      "reviewer": null,
      "reference_complete": false,
      "whole_image_label": null,
      "positives": [
        {"annotation_id": "p1", "bbox": [10, 20, 30, 40]},
        {"annotation_id": "p2", "point": [70, 50]}
      ],
      "negative_regions": []
    }
  ]
}
```

Cada objeto positivo contém **ou** `bbox` **ou** `point`, nunca ambos. `review_status` é `pending` ou `reviewed`; uma revisão concluída exige `reviewer` identificado. `reference_complete: true` declara cobertura suficiente de toda a imagem para contabilizar referências não detectadas e falsos positivos. Não marcar automaticamente uma lista vazia como referência completa.

`whole_image_label` é `null` enquanto desconhecido; valores `0` e `1` são rótulos explícitos de ausência/presença no nível da imagem, confirmados por revisão. Detecção exige referência revisada e completa; métricas binárias exigem revisão e rótulo inteiro explícito. Uma anotação parcial não autoriza chamar regiões não anotadas de negativas.

Regiões negativas confirmadas usam:

```json
{
  "annotation_id": "n1",
  "bbox": [40, 0, 60, 20],
  "review_status": "reviewed",
  "reviewer": "identificador_do_revisor"
}
```

Um recorte negativo precisa estar coberto por região negativa confirmada e não pode intersectar qualquer positivo. Para pontos, testar contenção do ponto no recorte; para caixas, testar a área de interseção de toda a caixa do recorte. Distância entre centros é insuficiente. `unknown` não é uma terceira classe experimental nem uma classe negativa: significa candidato sem rótulo utilizável, que deve ser excluído do treino supervisionado.

A revisão deve ser realizada por alguém qualificado da equipe. Previsões do modelo podem ajudar a encontrar candidatos para inspeção, mas não são referência independente e não devem preencher o teste como se fossem marcações humanas.

### Organização dos artefatos

```text
data/
  raw/                 # originais ou referência aos ZIPs preservados
  protocol/            # inventory.csv, exclusões, metadados do inventário
  annotations/         # referência JSON e proveniência/revisão
  splits/              # images.csv e escolhas de grupos/semente
  processed/           # recortes com vínculo ao image_id e partição
```

Não confiar em nomes antigos `raw/train` e `raw/test` para definir o protocolo deste TCC: sua origem deve ser verificada e a atribuição por grupo persistida. Não gerar recortes primeiro para depois dividi-los aleatoriamente.

### Interfaces de preparação

Os comandos seguintes descrevem a interface da implementação desta revisão. Substituir os caminhos de exemplo por caminhos locais reais e conferir `--help`; a execução efetiva deve ser registrada no [checklist](status.md).

```powershell
python scripts/prepare_data.py inventory --input CAMINHO_DO_LOTE --output-dir data/protocol
python scripts/prepare_data.py annotation-template --inventory data/protocol/inventory.csv --output data/annotations/reference.json
python scripts/prepare_data.py split --inventory data/protocol/inventory.csv --assignments grupos.csv --output-dir data/splits --seed 42
python scripts/prepare_data.py validate --splits data/splits/images.csv --annotations data/annotations/reference.json
```

Gerar um template cria campos pendentes, **não anotações confiáveis**. O CSV `grupos.csv` depende da inspeção de grupos e classes. Quando contagens forem usadas no lugar de atribuições explícitas, precisam ser justificadas e persistidas; não há porcentagem padrão adotada pelo protocolo.

### Contrato de predições e comparação

A saída por sistema contém `system: "A"` ou `"B"` e uma lista `images` com `image_id`, `status`, `regions`, `candidates`, `original_decision` e `timings`. Cada região carrega `bbox`, `class_id` e `scores`; propostas ainda não classificadas aparecem em `candidates`. Caixas usam as mesmas coordenadas da referência. Escores não são denominados probabilidades calibradas.

Comparar apenas os mesmos IDs definidos pelo manifesto. Estados de ausência de candidatos e erro também devem aparecer. Associação um a um usa IoU ≥ 0,5 para caixas e ponto contido para referência pontual; limiar e regra são fixados antes do teste. Critérios completos, incluindo referência incompleta, FN por falha de localização e imagem inteira, estão na [metodologia](metodologia.md).

```powershell
python scripts/compare_systems.py --manifest data/splits/images.csv --annotations data/annotations/reference.json --predictions-a experiments/runs/a_test/predictions.json --predictions-b experiments/runs/b_test/predictions.json --output experiments/runs/comparacao.json --split test --iou-threshold 0.5
```

Sem rótulos revisados, o resultado válido é inventário/diagnóstico e verificação sintética da infraestrutura. Não publicar precisão, recall, F1 ou superioridade real com base em rótulos ausentes ou inventados.
