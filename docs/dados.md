# Dados e fontes do experimento

Origem, integridade e evidências públicas. Para executar o treino, siga o [guia](guia_treinamento.md); para registrar negativos, consulte [anotações](anotacoes.md).

- [Base principal](#base)
- [Anotações positivas públicas](#anotacoes-publicas)
- [Fontes de negativos](#negativos)

<a id="base"></a>

## Base principal

Atualização: 24/09/2026. A base principal é `C:\Users\PCZAO\Documents\Caio\trypoastigote_images.zip`. Os ZIPs anteriormente descartados continuam excluídos do experimento. A coleção LABIMED foi preparada separadamente para examinar negativos, sem substituir a base principal. Nenhuma pessoa ou instituição é atribuída a partir de um nome de arquivo.

### Origem verificada

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

As pastas originais **não comprovam independência por animal/lâmina**. Na rodada inicial de 25/09/2026, as 105 imagens de `test` foram mantidas reservadas e as 569 imagens legíveis de `train` foram separadas em 455 para treino e 114 para validação. A divisão é por imagem original, com semente 42 e negativos revisados em ambos os conjuntos. O protocolo está em `data/splits/experimento/split_report.json`; não é uma divisão comprovadamente independente por animal.

### Integridade e arquivos preparados

A auditoria fez leitura completa dos pixels, sem habilitar recuperação de JPEG truncado. Arquivos com falha ficam no inventário e no manifesto de exclusão, sem apagar ou modificar o ZIP. O relatório local `data/protocol/trypomastigote_verified/audit.json` registra a verificação individual das 675 imagens.

- Inventário completo: `data/protocol/trypomastigote_verified/inventory.csv`.
- 674 imagens únicas com leitura aprovada: `data/protocol/trypomastigote_verified/eligible_inventory.csv`.
- Exclusões de integridade: `data/protocol/trypomastigote_verified/integrity_exclusions.csv`.
- Referência positiva importada: `data/annotations/public_import/public_points.json`.
- Template vazio original, preservado: `data/annotations/trypomastigote_pending.json`.
- Configuração da única fonte ativa: [configs/dataset.json](../configs/dataset.json).

O arquivo `train/field0156.jpg` apresentou `Truncated File Read`. Não será usado sem obter uma cópia válida e registrar uma nova auditoria. Elegibilidade técnica não confirma foco, qualidade biológica ou presença/ausência de parasitas.

O template antigo conserva rótulos nulos e revisão pendente. A referência ativa é `data/annotations/experimento_reference_v2.json` e a divisão está em `data/splits/experimento/images.csv`. Foram preparados 7.019 recortes de treino/validação. O primeiro treino real foi concluído e recebido em 26/09/2026; a comparação A × B permanece pendente. Consulte o relatório em `experiments/validation/b_real_cpu_01_received_20260926/relatorio.md`. Os parâmetros de localização foram mantidos nesta rodada inicial; o diagnóstico nas oito imagens de desenvolvimento encontrou interseção para 26 de 28 pontos conhecidos, com duas falhas. Isso não constitui sensibilidade de detecção nem otimização validada.

### Como reproduzir a preparação

No terminal da pasta `C:\Users\PCZAO\Documents\Caio\TCC\TCC`:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_active_dataset.py
```

As saídas já foram preparadas nesta máquina. Para repetir sem sobrescrever anotações ou manifestos, escolha novos destinos:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_active_dataset.py --output-dir data/protocol/trypomastigote_reaudit --annotations data/annotations/trypomastigote_reaudit_pending.json
```

Se apenas o ZIP mudar de local, forneça `--archive 'CAMINHO_DO_MESMO_ZIP'`. Os checksums continuam obrigatórios. Os IDs dependem do caminho e do conteúdo; reconciliar pelo SHA-256 ao transferir anotações entre inventários feitos em locais diferentes. O script não escolhe automaticamente pastas externas nem combina bases anteriores.

### Próximos passos para treinar

1. Aproveitar os pontos públicos já importados e completar a referência com negativos revisados usando a [ferramenta visual](anotacoes.md#revisao).
2. Identificar animais/lâminas ou declarar a limitação quando só houver imagem original.
3. Revisar positivos e regiões/campos negativos. Consultar [fontes negativas](dados.md#negativos); nenhum conjunto externo já foi incorporado.
4. Definir partições por grupo antes de inspecionar resultados ou ajustar a localização.
5. Seguir a seção 4 do [guia de treinamento](guia_treinamento.md), usando como ponto de partida o inventário elegível acima.

Em 23/09/2026, os suplementos do [artigo original (PeerJ/PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9150695/) foram obtidos e comparados aos CSVs usados pelo importador: são idênticos byte a byte. A referência positiva contém **2.715 pontos em 674 imagens**, com escala, nomes e dimensões conferidos. Consulte [anotações públicas](dados.md#anotacoes-publicas). Isso não comprova cobertura completa nem fornece recortes RGB negativos: os `False` do suplemento 2 rotulam segmentos em áreas centradas em parasitas. As fontes externas e seus limites estão em [preparação de negativos](dados.md#negativos).

### Verificações desta atualização

Em 22/09/2026, passaram 25 testes automatizados e os cinco notebooks executaram em modo sintético. A preparação foi executada no ZIP real; a proteção contra sobrescrita, exclusão de arquivo corrompido/duplicado e recusa de checksum incorreto também foram verificadas com arquivos artificiais. Isso valida a preparação técnica, sem medir a qualidade do detector em imagens reais.

<a id="anotacoes-publicas"></a>

## Anotações positivas públicas

Verificação de 23/09/2026. As **674 imagens legíveis da base ativa já têm 2.715 pontos positivos importados**. Não é necessário começar marcando esses positivos do zero. A referência é a anotação publicada pelos autores; não representa uma nova revisão biológica feita pela equipe do TCC.

### Arquivos disponíveis

| Arquivo | Conteúdo |
| --- | --- |
| `data/annotations/public_import/public_points.json` | Referência positiva no formato aceito pelo projeto |
| `data/annotations/public_import/source_mapping.csv` | Ligação entre imagem original, ID do projeto, pasta original e número de pontos |
| `data/annotations/public_import/import_report.json` | Contagens, origem, hashes e inconsistências da fonte |
| `data/annotations/public_import/raw/` | CSVs e documentação da versão pública utilizada |
| `data/annotations/public_source/peerj-10-13470-s001.csv` | Suplemento 1 obtido diretamente do acervo do artigo |
| `data/annotations/public_source/peerj-10-13470-s002.csv` | Suplemento 2 obtido diretamente do acervo do artigo |
| `data/annotations/public_source/supplements_provenance.json` | Endereço de obtenção e hashes dos suplementos |
| `data/annotations/public_source/readiness_audit.json` | Auditoria local de reprodução da importação |

Esses dados locais ficam fora do Git. Inclua as pastas de dados no pacote transferido para o outro computador. O template `trypomastigote_pending.json` permanece preservado; ele não foi sobrescrito por esta referência.

### O que foi confirmado

O [repositório dos autores](https://github.com/csbl-br/chagas_detection) associa seus CSVs ao [conjunto de imagens do Zenodo](https://zenodo.org/records/5123062). Os [suplementos do artigo](https://pmc.ncbi.nlm.nih.gov/articles/PMC9150695/#supplemental-information) também foram obtidos pelo [serviço Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9150695/supplementaryFiles). Os dois CSVs são idênticos, byte a byte, às cópias utilizadas na importação:

| Arquivo | SHA-256 |
| --- | --- |
| Posições / suplemento 1 | `e53861f400e84bde199fb941ff1a8e8784ab49f5a5a03837ce37dfa73e070064` |
| Atributos / suplemento 2 | `88f183b566616b06194dd94bb86702a1b48714a8dafd7463a17c88092d4f6c06` |

A associação é inequívoca para as 674 imagens elegíveis: nomes únicos, dimensões originais, pasta original e escala conferem. `x, y` são as coordenadas nos pixels originais. `new_x, new_y` servem apenas para conferir a transformação para altura 1.024; não substituem as coordenadas originais.

O filtro `NUCLEUS`, `NUCLEUS_CELL_BODY` e `T_CRUZI` acompanha a seleção feita no [código publicado](https://github.com/csbl-br/chagas_detection/blob/b0b8f4d74dc679756bca4c5569c3f8abbe0d10d5/main/my_tools.py). Cinetoplastos não são contados como um segundo parasita. Das 5.250 linhas de estruturas, 2.717 passam nesse filtro; dois pontos exatamente repetidos foram unidos, conservando as linhas de origem, resultando em **2.715 pontos**.

O JSON final foi regenerado em memória e comparado integralmente à cópia existente: resultado idêntico. Os dez testes do importador passaram, incluindo escala, limites, associação incorreta, duplicatas e preservação de cobertura desconhecida. Esta auditoria examinou metadados e coordenadas, sem abrir visualmente imagens ou previsões do futuro teste.

### Por que o suplemento 2 não resolve sozinho os negativos

O CSV de atributos contém 1.314 linhas `True` e 1.314 `False`. Esses rótulos pertencem a **segmentos**, não a imagens completas. O código de extração trabalha numa área de 100 × 100 pixels em torno de um ponto de parasita; um segmento vizinho pode receber `False` enquanto o recorte RGB inclui o parasita central. A [descrição dos atributos](https://github.com/csbl-br/chagas_detection#functionality) distingue a posição local e o rótulo do segmento.

Consequentemente, esses 1.314 segmentos não foram convertidos em lâminas negativas nem em caixas RGB negativas. O modelo B atual precisa de recortes RGB com rótulo defensável. É possível completar a classe negativa com campos públicos cuja anotação sustente ausência de parasitas visíveis, ou com regiões negativas efetivamente revisadas. Consulte [fontes negativas](dados.md#negativos) e o [roteiro de anotação](anotacoes.md#criterios).

### O que esses pontos permitem

- Usar como positivos os recortes que contêm pontos publicados, preservando a origem da anotação.
- Registrar `review_basis: published_author_annotations` e `new_tcc_human_review: false`; o campo de revisor identifica a publicação.
- Preparar o treinamento após incorporar negativos apropriados e definir as partições.

Um ponto não fornece o contorno nem o tamanho completo do parasita. A importação não inventa caixas. Também não transforma qualquer região sem ponto em negativa.

Não há identificadores de animal ou lâmina nos CSVs consultados. As pastas originais têm 569 imagens elegíveis em `train` e 105 em `test`; isso não comprova independência biológica nem cria automaticamente a divisão do TCC. Há 95 imagens com divergência entre `n_structures` do resumo e a quantidade de linhas de estruturas. Essas divergências estão registradas e a cobertura continua `reference_complete: false`. A limitação afeta a avaliação de referência completa, separadamente da utilização de pontos positivos no treinamento.

### Como repetir sem perder trabalho

Na pasta principal do projeto, usando o ambiente instalado:

```powershell
.\.venv\Scripts\python.exe scripts/import_public_annotations.py --output-dir data/annotations/public_import_recheck
```

O importador recusa sobrescrever uma saída existente, verifica os hashes das fontes e confere o inventário elegível. Se o inventário for relocalizado para outro computador, passe seu caminho com `--inventory`. Use a referência produzida para o mesmo inventário ou preserve os IDs na transferência.

Para o experimento, copie a referência positiva como ponto de partida de `data/annotations/experimento_reference_v2.json`, acrescente apenas negativos sustentados pela fonte/revisão e preserve a procedência de ambos. Depois siga o [guia de treinamento](guia_treinamento.md). Só os pontos positivos, isoladamente, ainda não permitem treinar o classificador binário.

<a id="negativos"></a>

## Fontes de negativos

Atualizado em 24/09/2026. Foi preparado um subconjunto externo de **36 campos de esfregaço fino humano: 13 negativos e 23 positivos na referência publicada**, com 30 caixas de parasitas e identificação de participante/lâmina. Eles não substituem a base principal de camundongos. Não foi encontrado um conjunto público de lâminas de camundongos comprovadamente negativos para *T. cruzi*, com aquisição equivalente à base principal.

### LABIMED: campos sem parasitas, com procedência

O [depósito Zenodo 15007339](https://zenodo.org/records/15007339) contém imagens e tabelas de identificação e caixas. A [seção Dataset/Image labeling do artigo](https://doi.org/10.1371/journal.pntd.0012955) descreve campos positivos e negativos, coloração Giemsa e anotação dos parasitas. Todos os participantes são positivos: **campo sem parasita visível não significa lâmina ou participante sem Chagas**. Selecionamos apenas `Blood_thin`, excluindo sangue espesso e líquor.

A licença do depósito, confirmada pela [API oficial](https://zenodo.org/api/records/15007339), é **CC BY-NC 4.0**. Manter atribuição aos autores e registrar o uso não comercial. A licença do artigo não substitui a licença do conjunto de imagens.

Os números abaixo foram calculados diretamente das tabelas originais com checksum conferido. “Negativo” usa a ausência de caixas no inventário completo **em conjunto com o protocolo de anotação publicado**; não é inferido apenas porque falta um arquivo local de anotação.

| Participante (`caseId`) | Campos positivos, coleção fina completa | Campos negativos, coleção fina completa |
| --- | ---: | ---: |
| `8RGvX4eyf1` | 3 | 0 |
| `EkTCPvQKmR` | 126 | 0 |
| `NEjC0RzC4K` | 4 | 175 |
| `iCN9FDDeVI` | 2 | 0 |
| **Total** | **135** | **175** |

**Limitação decisiva: os 175 campos negativos pertencem a uma única pessoa**, distribuídos em oito preparações. Portanto, esta coleção sozinha não permite treino, validação e teste todos com negativos e independência entre participantes. Não distribuir imagens dessa pessoa entre partições para aparentar independência. Os 36 arquivos baixados cobrem os quatro participantes e as 13 preparações de sangue fino; são um subconjunto inicial para inspeção e desenvolvimento, não um teste representativo.

### Arquivos locais e reprodução

Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe scripts/fetch_negative_candidates.py --limit 36 --max-mb 210
.\.venv\Scripts\python.exe scripts/import_labimed_annotations.py
```

O download foi concluído. A seleção ocupa aproximadamente 201 MB comprimidos e foi recuperada por partes, sem baixar o ZIP completo de 3,91 GB. Reexecutar o download reutiliza os pixels locais depois de verificar sua integridade. O importador recusa sobrescrever resultados: use `--output-dir data/annotations/labimed_public_v2` para uma nova versão.

| Arquivo/pasta | Conteúdo |
| --- | --- |
| `data/external_candidates/labimed/images/` | 36 imagens originais, 4128 × 3096 pixels |
| `data/external_candidates/labimed/selection.csv` | Seleção, hashes SHA-256, campos, participantes e preparações |
| `data/external_candidates/labimed/download_report.json` | Contagens, licença e limitações |
| `data/external_candidates/labimed/assets.csv` / `bboxes.csv` | Tabelas originais completas |
| `data/annotations/labimed_public/inventory.csv` | Manifesto importável, agrupado por participante |
| `data/annotations/labimed_public/annotations.json` | Referência publicada no formato do TCC |
| `data/annotations/labimed_public/import_report.json` | Auditoria e distribuição por participante |

O importador confere os hashes dos metadados/pixels, grupos, contagens, dimensões e limites das caixas. Preserva as coordenadas originais `xmin,ymin,xmax,ymax`, interpretadas como `xyxy` com limite final exclusivo, sem redimensionar. A procedência é `published_author_annotations`, com `new_tcc_human_review=false`: a referência completa é a publicada, sem alegar nova revisão local. A verificação do download usa tamanho, CRC32 da entrada ZIP e SHA-256 local; o MD5 do ZIP inteiro não é recalculado no download seletivo. Nenhuma partição final é criada pelo importador.

Links diretos: [assets.csv](https://zenodo.org/api/records/15007339/files/assets.csv/content), [bboxes.csv](https://zenodo.org/api/records/15007339/files/bboxes.csv/content), [images.zip](https://zenodo.org/api/records/15007339/files/images.zip/content).

Auditoria local de 24/09/2026: os 36 arquivos foram decodificados integralmente; reconstruir a importação reproduziu exatamente o manifesto, as anotações e o relatório existentes. Três testes automatizados passaram: preservação do participante positivo em campos negativos, rejeição de pixels modificados e rejeição de metadados publicados modificados. Essa auditoria verifica a importação, não constitui revisão parasitológica.

### Outras fontes avaliadas

| Fonte | Classe e agrupamento | Licença e situação |
| --- | --- | --- |
| [NIH/NLM: sangue fino](https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html) | 193 participantes; 45 não infectados no estudo de malária. O rótulo celular `Uninfected` não prova que o participante seja controle. O estudo não comprova ausência específica de *T. cruzi*. | [Licença oficial](https://data.lhncbc.nlm.nih.gov/public/Malaria/NIH-NLM-ThinBloodSmearsPf/Data%20License%20Agreement.docx): permite reutilização sob condições de atribuição e preservação dos avisos. Metadados/licença salvos; nenhuma imagem promovida a negativo de Chagas. |
| [Tryp](https://figshare.com/articles/dataset/22825787) | A coleção investiga *T. brucei brucei*, com sangue espesso sem coloração; aparência e alvo diferentes. | [API oficial](https://api.figshare.com/v2/articles/22825787): CC BY 4.0; ZIP de 4,65 GB não baixado. Não selecionada para a comparação principal. |

Os documentos NIH estão em `data/raw/external_candidates/nih_thin/`. Não considerar o nome da pasta nem o zero na contagem de hemácias infectadas como confirmação diagnóstica de Chagas.

### O que falta para um experimento defensável

Para o classificador de recortes, revisar negativos nas próprias imagens de camundongos mantém origem e aquisição compartilhadas com os positivos. Para medir falsos alarmes por campo, a referência LABIMED fornece negativos públicos, mas sua concentração em um participante precisa aparecer no desenho experimental e nos resultados. Para afirmar desempenho em lâminas/doadores negativos, obter controles confirmados e documentados, preferencialmente com a mesma preparação da base principal.

Não formar automaticamente “todos os positivos de camundongo versus todos os negativos humanos”: diferenças de espécie, câmera e laboratório poderiam virar o sinal aprendido. A divisão deve preservar grupos antes de extrair recortes. O [guia de treinamento](guia_treinamento.md) apresenta o fluxo; estes arquivos tornam a preparação reproduzível, mas não eliminam a limitação de grupos negativos independentes.
