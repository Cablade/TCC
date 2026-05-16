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
- GPU NVIDIA com CUDA 11.8+ (opcional, mas altamente recomendado)
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

### Ordem de execução dos notebooks

1. `notebooks/01_exploracao_dataset.ipynb` — inspeção e estatísticas do Zenodo
2. `notebooks/02_pipeline_segmentacao.ipynb` — geração de ROIs via segmentação OpenCV
3. `notebooks/03_modelo_a_baseline.ipynb` — replicação e avaliação do Modelo A
4. `notebooks/04_modelo_b_treino.ipynb` — treino do Modelo B com k-fold
5. `notebooks/05_analise_estatistica.ipynb` — Wilcoxon, métricas finais, gráficos

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

- [`docs/proposta_v2.md`](docs/proposta_v2.md) — proposta refinada enviada ao orientador
- [`docs/cronograma.md`](docs/cronograma.md) — plano de trabalho de Mai a Dez de 2026
- [`docs/decisoes_tecnicas.md`](docs/decisoes_tecnicas.md) — registro de decisões técnicas (decision log)
- [`docs/referencias.md`](docs/referencias.md) — bibliografia

## Status

- [x] Proposta aprovada pelo orientador (v2 em `docs/proposta_v2.md`)
- [x] Autorização formal Fuzzylab/FIOCRUZ
- [x] Download e organização do dataset
- [ ] Replicação do Modelo A
- [ ] Implementação do Modelo B
- [ ] Análise estatística
- [ ] Escrita do TCC

## Licença

Código sob licença MIT (ver `LICENSE`). Dataset sob CC-BY 4.0 (creditar Morais et al., 2021).
