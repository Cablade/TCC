# Análise exploratória do supply.csv (Data S1 do paper Morais et al. 2022).


from collections import Counter
from pathlib import Path

import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS = ROOT / "data" / "raw" / "annotations" / "supply.csv"
IMAGES_TRAIN = ROOT / "data" / "raw" / "train"
IMAGES_TEST = ROOT / "data" / "raw" / "test"


def main():
    print("=" * 70)
    print("ANÁLISE DAS ANOTAÇÕES (Data S1)")
    print("=" * 70)

    if not ANNOTATIONS.exists():
        print(f"ERRO: arquivo não encontrado: {ANNOTATIONS}")
        return

    df = pd.read_csv(ANNOTATIONS)
    print(f"\nArquivo: {ANNOTATIONS.name}")
    print(f"Total de anotações: {len(df):,}")
    print(f"Colunas: {list(df.columns)}")
    print("\n" + "-" * 70)
    print("1. DISTRIBUIÇÃO DE CLASSES")
    print("-" * 70)
    classes = df["structure"].value_counts()
    for cls, count in classes.items():
        print(f"  {cls:28s} {count:>6,}  ({count/len(df)*100:5.1f}%)")
    print("\n" + "-" * 70)
    print("2. DISTRIBUIÇÃO TRAIN/TEST")
    print("-" * 70)
    sets = df["set"].value_counts()
    for s, count in sets.items():
        print(f"  {s:10s} {count:>6,}  ({count/len(df)*100:5.1f}%)")
    # Cross-tab classe × set
    print("\nCross-tab (classe × split):")
    ct = pd.crosstab(df["structure"], df["set"], margins=True)
    print(ct.to_string())
    print("\n" + "-" * 70)
    print("3. COBERTURA DAS IMAGENS")
    print("-" * 70)
    images_annotated = set(df["filename"].unique())
    print(f"Imagens distintas em anotações: {len(images_annotated):,}")
    images_train = set(p.name for p in IMAGES_TRAIN.glob("*.jpg"))
    images_test = set(p.name for p in IMAGES_TEST.glob("*.jpg"))
    images_disk = images_train | images_test
    print(f"Imagens no disco (train+test): {len(images_disk):,}")
    print(f"  - train: {len(images_train):,}")
    print(f"  - test:  {len(images_test):,}")
    print(f"\nInterseção (anotadas E no disco): "
          f"{len(images_annotated & images_disk):,}")
    print(f"Anotadas mas SEM imagem no disco: "
          f"{len(images_annotated - images_disk):,}")
    print(f"Imagem no disco mas SEM anotação: "
          f"{len(images_disk - images_annotated):,}")
    # Distribuição de anotações por imagem
    per_image = df.groupby("filename").size()
    print(f"\nAnotações por imagem:")
    print(f"  min={per_image.min()}, mediana={int(per_image.median())}, "
          f"máx={per_image.max()}, média={per_image.mean():.1f}")
    print("\n" + "-" * 70)
    print("4. COORDENADAS (resolução)")
    print("-" * 70)
    print(f"x:  min={df['x'].min():>6}  max={df['x'].max():>6}  "
          f"mediana={int(df['x'].median()):>6}")
    print(f"y:  min={df['y'].min():>6}  max={df['y'].max():>6}  "
          f"mediana={int(df['y'].median()):>6}")
    print(f"new_x:  min={df['new_x'].min():>6}  max={df['new_x'].max():>6}  "
          f"mediana={int(df['new_x'].median()):>6}")
    print(f"new_y:  min={df['new_y'].min():>6}  max={df['new_y'].max():>6}  "
          f"mediana={int(df['new_y'].median()):>6}")
    # Compara com tamanho real de uma imagem do disco
    sample_image_name = sorted(images_train)[0] if images_train else None
    if sample_image_name:
        sample_path = IMAGES_TRAIN / sample_image_name
        img = Image.open(sample_path)
        print(f"\nResolução da imagem '{sample_image_name}': "
              f"{img.size} (largura × altura)")
        print(f"  → coordenadas 'x,y' batem com {img.size}? "
              f"{'sim' if df['x'].max() <= img.size[0] and df['y'].max() <= img.size[1] else 'não'}")
        print(f"  → coordenadas 'new_x,new_y' batem com {img.size}? "
              f"{'sim' if df['new_x'].max() <= img.size[0] and df['new_y'].max() <= img.size[1] else 'não'}")
    print("\n" + "-" * 70)
    print("5. DIAGNÓSTICO RESUMIDO")
    print("-" * 70)
    classes_set = set(df["structure"].unique())
    print(f"\nClasses encontradas: {sorted(classes_set)}")
    print("\nProposta de mapeamento binário pro nosso classificador:")
    print("  → POSITIVO (parasita):  KINETOPLAST, NUCLEUS, KINETOPLAST_CELL_BODY, NUCLEUS_CELL_BODY")
    print("  → NEGATIVO (unknown):   ?")
    print("\nObservação: o supply.csv parece conter SÓ anotações positivas.")
    print("Os exemplos 'unknown' do paper provavelmente foram extraídos de")
    print("regiões não-marcadas das imagens. Confirmar inspecionando.")

if __name__ == "__main__":
    main()
