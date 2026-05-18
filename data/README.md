# Dataset

Os dados não são versionados no Git devido ao tamanho. Esta pasta deve ser preenchida localmente seguindo as instruções abaixo.

## Estrutura esperada

```
data/
├── raw/                          # Imagens originais do Zenodo + anotações
│   ├── train/                    # *.jpg (split do próprio dataset)
│   ├── test/                     # *.jpg (split do próprio dataset)
│   └── annotations/
│       ├── supply.csv            # Data S1 (anotações)
│       └── supply2.csv           # (opcional)
├── processed/                    # ROIs recortadas (script gerar_rois.py)
│   ├── train/
│   │   ├── positivo/             # *.png
│   │   └── negativo/             # *.png
│   ├── test/
│   │   ├── positivo/             # *.png
│   │   └── negativo/             # *.png
│   └── manifest.csv              # metadados das ROIs geradas
└── splits/                       # Divisões treino/val/teste (CSVs)
  ├── train.csv                 # colunas: path,label
  ├── val.csv
  └── test.csv
```

## Download do dataset Zenodo

**Fonte:** Morais, M. C. C., Silva, D. M. da, Oliveira, M. T., Lana, M. de, & Nakaya, H. I. (2021). *Image dataset from Automatic analysis of Trypanosoma cruzi: A machine learning approach for the detection of blood trypomastigotes in low resolution images*. Zenodo. https://doi.org/10.5281/zenodo.5123062

**Licença:** Creative Commons CC-BY 4.0 (atribuição obrigatória)

### Via interface web

1. Acesse https://zenodo.org/records/5123062
2. Baixe `trypoastigote_images.zip` (~1,3 GB)
3. Descompacte em `data/raw/` de forma que existam as pastas `data/raw/train/` e `data/raw/test/`

Observação: dependendo de como o ZIP vem organizado, pode ser necessário mover os arquivos após descompactar.

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

Após colocar as imagens em `data/raw/train` e `data/raw/test`, rode o gerador de ROIs:

```bash
python notebooks/gerar_rois.py --dry-run
python notebooks/gerar_rois.py
```

Isso vai preencher `data/processed/` e criar `data/processed/manifest.csv`.

Em seguida, para gerar `data/splits/*.csv` e treinar o Modelo B via CLI:

```bash
python scripts/train_model_b.py --config configs/model_b.yaml --run-name model_b
```
