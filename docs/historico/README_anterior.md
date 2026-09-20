> DOCUMENTO HISTÓRICO — substituído em 2026-09-20 pelo protocolo A × B em ../metodologia.md. Preservado para rastreabilidade, incluindo alterações locais anteriores. Afirmações de execução, dados, autorização e conclusões abaixo são registros antigos; não constituem verificações desta revisão.

# TCC — Análise Comparativa de Modelos de IA para Detecção de Doença de Chagas

> Estudo comparativo entre o modelo de classificação utilizado pela Fuzzylab/FIOCRUZ (ResNet-50) e uma proposta com EfficientNet-B0 + técnicas modernas de treinamento, aplicado à classificação de núcleos de *Trypanosoma cruzi* em imagens de esfregaço sanguíneo.

**Autores:** Victor Jacques, Caio Milão
**Orientador:** Prof. Rogério Mandelli
**Instituição:** UVA — Universidade Veiga de Almeida
**Curso:** Ciência da Computação
---

## Resumo da pesquisa

Comparamos dois modelos de classificação binária de núcleos celulares:

- **Modelo A (referência):** ResNet-50 com base congelada, transfer learning de pesos ImageNet, sem data augmentation, treinado pela equipe Fuzzylab/FIOCRUZ.
- **Modelo B (proposto):** EfficientNet-B0 com fine-tuning, data augmentation (Albumentations), AdamW + cosine annealing, label smoothing e regularização ajustada.

Ambos os modelos compartilham o mesmo pipeline de pré-processamento (segmentação por cor via OpenCV) e o mesmo conjunto de teste, isolando a etapa de classificação como variável sob análise.

## Dataset

Utilizamos o dataset público **"Image dataset from Automatic analysis of Trypanosoma cruzi"** (Morais et al., 2021), disponível no Zenodo:

- DOI: [10.5281/zenodo.5123062](https://doi.org/10.5281/zenodo.5123062)
- Licença: Creative Commons CC-BY 4.0
- ~1,3 GB de imagens de esfregaço fino corado com Giemsa

Veja [`data/README.md`](data/README.md) para instruções de download e organização.

## Como reproduzir

### Pré-requisitos

- Python 3.10+
- GPU (opcional). Observação: suporte a GPU do TensorFlow varia por SO/instalação; no Windows, o caminho mais estável costuma ser via WSL2 + NVIDIA.
- ~5 GB de espaço em disco

### Setup

```bash
# Clone do repositório
git clone <url-do-repo>
cd tcc-chagas

# Ambiente virtual
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

# Dependências
pip install -r requirements.txt

# Baixar dataset (siga instruções em data/README.md)
```

### Quickstart (Windows / PowerShell)

Do zero até o primeiro treino do Modelo B (CPU/GPU, conforme seu TensorFlow):

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

# 1) Baixe e organize o dataset (ver data/README.md)

# 2) Gerar ROIs (recortes) e manifest
python notebooks\gerar_rois.py --dry-run
python notebooks\gerar_rois.py

# 3) Treinar Modelo B e salvar métricas
python scripts\train_model_b.py --config configs\model_b.yaml --run-name model_b
```

Arquivos gerados:

- `data/processed/` (ROIs)
- `data/splits/` (CSV de splits)
- `experiments/checkpoints/` (checkpoint do modelo)
- `experiments/results/` (métricas em JSON)

### Ordem de execução dos notebooks

1. `notebooks/01_exploracao_dataset.ipynb` — inspeção e estatísticas do Zenodo
2. `notebooks/gerar_rois.py` — geração de ROIs (recortes) + negativos amostrados + `manifest.csv`
3. `scripts/train_model_b.py` — treino do Modelo B via CLI (gera `data/splits/` automaticamente)
4. `notebooks/05_analise_estatistica.ipynb` — Wilcoxon, métricas finais, gráficos (WIP)

Observação: os notebooks `02_pipeline_segmentacao.ipynb`, `03_modelo_a_baseline.ipynb` e `04_modelo_b_treino.ipynb` ainda estão com células `TODO` e servem como rascunho/roteiro.

## Estrutura

```
tcc-chagas/
├── data/             # dados brutos e processados (não versionados)
├── notebooks/        # exploração e experimentos numerados
├── src/              # código modular reutilizável
├── configs/          # hiperparâmetros por experimento (YAML)
├── experiments/      # logs, checkpoints, resultados (não versionados)
├── docs/             # proposta, decisões técnicas, referências
└── tcc/              # texto final do TCC
```

## Documentação

- [`docs/proposta_v3.md`](docs/proposta_v3.md) — proposta atual (estratégia A1/A2/B)
- [`docs/proposta_v2.md`](docs/proposta_v2.md) — proposta enviada ao orientador em maio/2026
- [`docs/cronograma.md`](docs/cronograma.md) — plano de trabalho de Mai a Dez de 2026
- [`docs/decisoes_tecnicas.md`](docs/decisoes_tecnicas.md) — registro de decisões técnicas (decision log)
- [`docs/referencias.md`](docs/referencias.md) — bibliografia

## Status

- [x] Proposta aprovada pelo orientador (v2 em `docs/proposta_v2.md`)
- [x] Autorização formal Fuzzylab/FIOCRUZ
- [x] Download e organização do dataset
- [x] Geração de ROIs via anotações (script)
- [x] Treino do Modelo B via CLI (baseline inicial)
- [ ] Replicação do Modelo A (WIP)
- [ ] Análise estatística
- [ ] Escrita do TCC

## Licença

Código sob licença MIT (ver `LICENSE`). Dataset sob CC-BY 4.0 (creditar Morais et al., 2021).

