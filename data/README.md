# Dados, partições e anotações

> Protocolo A × B, 2026-09-20. Consulte a [metodologia](../docs/metodologia.md). Dados, recortes, pesos e resultados volumosos não são incluídos automaticamente no Git. Preserve os originais.

## Fontes e inventário

A única base local ativa é `trypoastigote_images.zip`, correspondente ao depósito Zenodo 5123062. A auditoria encontrou 675 JPGs únicos, 674 decodificáveis e uma exclusão por integridade. Consulte [base atual](../docs/dataset_atual.md) para checksums, caminhos e reprodução. Todos os ZIPs anteriores foram descartados do experimento. O template atual é `data/annotations/trypomastigote_pending.json`; ele não contém rótulos revisados. As [fontes negativas pesquisadas](../docs/fontes_negativas.md) ainda não foram incorporadas.

Use `data/protocol/trypomastigote_verified/eligible_inventory.csv` como ponto de partida, confirmando grupos antes das partições. Não usar o inventário completo com a imagem inválida como entrada de treino. A ausência de anotações dentro do ZIP não exclui suplementos externos; é necessário inspecionar e reconciliar qualquer anotação importada.

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

## Grupos e reserva

Confirmar animal/lâmina com a equipe; não transformar nomes de pastas em identidades biológicas presumidas. Sem identificadores confiáveis, usar imagem original e declarar que a independência entre lâminas/animais não foi demonstrada. Recortes da mesma imagem herdam seu grupo e partição.

Atribuir partições **antes** de gerar recortes. Persistir semente e escolhas de grupos. Um CSV explícito de atribuições usa:

```csv
group_id,split
grupo_confirmado_001,train
grupo_confirmado_002,val
grupo_confirmado_003,test
```

O exemplo é ilustrativo, não constitui uma partição real aprovada. Primeiro examinar grupos/classes e justificar quantos grupos podem ser reservados. Imagens usadas para inspecionar falhas ou ajustar a localização de B são desenvolvimento. Se não houver dados para teste intocado, registrar a falta; não renomear desenvolvimento como teste.

## Formato de anotação

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

## Organização dos artefatos

```text
data/
  raw/                 # originais ou referência aos ZIPs preservados
  protocol/            # inventory.csv, exclusões, metadados do inventário
  annotations/         # referência JSON e proveniência/revisão
  splits/              # images.csv e escolhas de grupos/semente
  processed/           # recortes com vínculo ao image_id e partição
```

Não confiar em nomes antigos `raw/train` e `raw/test` para definir o protocolo deste TCC: sua origem deve ser verificada e a atribuição por grupo persistida. Não gerar recortes primeiro para depois dividi-los aleatoriamente.

## Interfaces de preparação

Os comandos seguintes descrevem a interface da implementação desta revisão. Substituir os caminhos de exemplo por caminhos locais reais e conferir `--help`; a execução efetiva deve ser registrada no [checklist](../docs/checklist_execucao.md).

```powershell
python scripts/prepare_data.py inventory --input CAMINHO_DO_LOTE --output-dir data/protocol
python scripts/prepare_data.py annotation-template --inventory data/protocol/inventory.csv --output data/annotations/reference.json
python scripts/prepare_data.py split --inventory data/protocol/inventory.csv --assignments grupos.csv --output-dir data/splits --seed 42
python scripts/prepare_data.py validate --splits data/splits/images.csv --annotations data/annotations/reference.json
```

Gerar um template cria campos pendentes, **não anotações confiáveis**. O CSV `grupos.csv` depende da inspeção de grupos e classes. Quando contagens forem usadas no lugar de atribuições explícitas, precisam ser justificadas e persistidas; não há porcentagem padrão adotada pelo protocolo.

## Contrato de predições e comparação

A saída por sistema contém `system: "A"` ou `"B"` e uma lista `images` com `image_id`, `status`, `regions`, `candidates`, `original_decision` e `timings`. Cada região carrega `bbox`, `class_id` e `scores`; propostas ainda não classificadas aparecem em `candidates`. Caixas usam as mesmas coordenadas da referência. Escores não são denominados probabilidades calibradas.

Comparar apenas os mesmos IDs definidos pelo manifesto. Estados de ausência de candidatos e erro também devem aparecer. Associação um a um usa IoU ≥ 0,5 para caixas e ponto contido para referência pontual; limiar e regra são fixados antes do teste. Critérios completos, incluindo referência incompleta, FN por falha de localização e imagem inteira, estão na [metodologia](../docs/metodologia.md).

```powershell
python scripts/compare_systems.py --manifest data/splits/images.csv --annotations data/annotations/reference.json --predictions-a experiments/runs/a_test/predictions.json --predictions-b experiments/runs/b_test/predictions.json --output experiments/runs/comparacao.json --split test --iou-threshold 0.5
```

Sem rótulos revisados, o resultado válido é inventário/diagnóstico e verificação sintética da infraestrutura. Não publicar precisão, recall, F1 ou superioridade real com base em rótulos ausentes ou inventados.
