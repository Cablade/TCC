# Dataset

Os dados não são versionados no Git devido ao tamanho. Esta pasta deve ser preenchida localmente seguindo as instruções abaixo.

## Estrutura esperada

```
data/
├── raw/                    # Imagens originais do Zenodo
│   └── trypoastigote_images/
│       └── *.jpg / *.png
├── processed/              # ROIs após segmentação OpenCV
│   ├── positivo/
│   └── negativo/
└── splits/                 # Divisões treino/val/teste (CSVs)
    ├── train.csv
    ├── val.csv
    └── test.csv
```

## Download do dataset Zenodo

**Fonte:** Morais, M. C. C., Silva, D. M. da, Oliveira, M. T., Lana, M. de, & Nakaya, H. I. (2021). *Image dataset from Automatic analysis of Trypanosoma cruzi: A machine learning approach for the detection of blood trypomastigotes in low resolution images*. Zenodo. https://doi.org/10.5281/zenodo.5123062

**Licença:** Creative Commons CC-BY 4.0 (atribuição obrigatória)

### Via interface web

1. Acesse https://zenodo.org/records/5123062
2. Baixe `trypoastigote_images.zip` (~1,3 GB)
3. Descompacte em `data/raw/`

### Via linha de comando

```bash
cd data/raw/
wget https://zenodo.org/records/5123062/files/trypoastigote_images.zip
unzip trypoastigote_images.zip
rm trypoastigote_images.zip
```

### Verificação de integridade

```bash
# MD5 oficial do arquivo
echo "3434fa22df03956c256f1203b683517e  trypoastigote_images.zip" | md5sum -c
```

## Datasets complementares (opcional)

- **ASH Image Bank — T. cruzi trypomastigote:** https://imagebank.hematology.org/

  Imagens adicionais para validação cruzada em domínio externo, se houver tempo.

## Próximos passos após download

Após colocar os arquivos em `data/raw/`, execute:

```bash
jupyter notebook notebooks/01_exploracao_dataset.ipynb
```

para gerar as estatísticas iniciais e validar a estrutura.

A geração de ROIs processadas e dos splits é feita pelo notebook `02_pipeline_segmentacao.ipynb`.
