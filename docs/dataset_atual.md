# Base ativa do TCC

Atualização: 22/09/2026. A única base local selecionada é `C:\Users\PCZAO\Documents\Caio\trypoastigote_images.zip`. Os ZIPs anteriores e seus manifestos estão excluídos do experimento. Nenhuma pessoa ou instituição é atribuída a partir de um nome de arquivo.

## Origem verificada

O nome, tamanho e MD5 do ZIP local correspondem ao depósito [Zenodo 5123062](https://zenodo.org/records/5123062), que descreve imagens de esfregaço de sangue de **camundongos** contendo tripomastigotas de *T. cruzi*. A origem deve ser citada pelo depósito e pelos autores da publicação, sem atribuição baseada no nome de uma pasta. Os termos de licença/reutilização ainda devem ser registrados antes de redistribuir as imagens.

| Verificação local | Resultado |
| --- | --- |
| Tamanho do ZIP | 1.302.179.075 bytes |
| MD5 publicado e local | `3434fa22df03956c256f1203b683517e` |
| SHA-256 local | `ce6408615b126178fa0ed96068308bee19a5e2a89330268bbb2e1f4ec88fed1b` |
| Imagens JPG | 675 |
| Conteúdos distintos por SHA-256 | 675; nenhuma duplicata por bytes |
| Decodificação completa | 674 aprovadas; uma falha |
| Organização original | 570 arquivos em `train`, 105 em `test` |
| Anotações dentro do ZIP | Nenhum arquivo; somente imagens |

As pastas originais são registradas como organização da fonte. Elas **não comprovam independência por animal/lâmina** e não foram adotadas automaticamente como partições finais do TCC.

## Integridade e arquivos preparados

A auditoria fez leitura completa dos pixels, sem habilitar recuperação de JPEG truncado. Arquivos com falha ficam no inventário e no manifesto de exclusão, sem apagar ou modificar o ZIP. O relatório local `data/protocol/trypomastigote_verified/audit.json` registra a verificação individual das 675 imagens.

- Inventário completo: `data/protocol/trypomastigote_verified/inventory.csv`.
- 674 imagens únicas com leitura aprovada: `data/protocol/trypomastigote_verified/eligible_inventory.csv`.
- Exclusões de integridade: `data/protocol/trypomastigote_verified/integrity_exclusions.csv`.
- Template de revisão: `data/annotations/trypomastigote_pending.json`.
- Configuração da única fonte ativa: [configs/dataset.json](../configs/dataset.json).

O arquivo `train/field0156.jpg` apresentou `Truncated File Read`. Não será usado sem obter uma cópia válida e registrar uma nova auditoria. Elegibilidade técnica não confirma foco, qualidade biológica ou presença/ausência de parasitas.

O template conserva rótulos nulos e revisão pendente. Não foi criado `data/splits/trypomastigote/images.csv`: a divisão depende dos grupos e das classes revisadas. Ainda não houve treino supervisionado nem comparação A × B nesta base. Os parâmetros atuais de localização do B são um protótipo e precisam ser examinados no desenvolvimento desta base.

## Como reproduzir a preparação

No terminal da pasta `C:\Users\PCZAO\Documents\Caio\TCC\TCC`:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_active_dataset.py
```

As saídas já foram preparadas nesta máquina. Para repetir sem sobrescrever anotações ou manifestos, escolha novos destinos:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_active_dataset.py --output-dir data/protocol/trypomastigote_reaudit --annotations data/annotations/trypomastigote_reaudit_pending.json
```

Se apenas o ZIP mudar de local, forneça `--archive 'CAMINHO_DO_MESMO_ZIP'`. Os checksums continuam obrigatórios. Os IDs dependem do caminho e do conteúdo; reconciliar pelo SHA-256 ao transferir anotações entre inventários feitos em locais diferentes. O script não escolhe automaticamente pastas externas nem combina bases anteriores.

## Próximos passos para treinar

1. Conferir as possíveis anotações públicas e sua correspondência com os pixels originais; completar a revisão qualificada.
2. Identificar animais/lâminas ou declarar a limitação quando só houver imagem original.
3. Revisar positivos e regiões/campos negativos. Consultar [fontes negativas](fontes_negativas.md); nenhum conjunto externo já foi incorporado.
4. Definir partições por grupo antes de inspecionar resultados ou ajustar a localização.
5. Seguir a seção 4 do [guia de treinamento](guia_treinamento.md), usando como ponto de partida o inventário elegível acima.

O [artigo original (PeerJ/PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9150695/) lista o [suplemento 1, com posições dos parasitas](https://doi.org/10.7717/peerj.13470/supp-1), e o [suplemento 2, com atributos e presença/ausência em regiões](https://doi.org/10.7717/peerj.13470/supp-2). Sua existência não significa que já estejam importados ou validados no formato do TCC; conferir escala e coordenadas antes da conversão. O [estudo posterior em PLOS](https://journals.plos.org/plosntds/article?id=10.1371/journal.pntd.0012955) também reutiliza essas imagens; consultar as limitações e a possível sobreposição em [fontes negativas](fontes_negativas.md).

## Verificações desta atualização

Em 22/09/2026, passaram 25 testes automatizados e os cinco notebooks executaram em modo sintético. A preparação foi executada no ZIP real; a proteção contra sobrescrita, exclusão de arquivo corrompido/duplicado e recusa de checksum incorreto também foram verificadas com arquivos artificiais. Isso valida a preparação técnica, sem medir a qualidade do detector em imagens reais.
