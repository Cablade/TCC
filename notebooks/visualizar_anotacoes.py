"""
Visualiza uma imagem do dataset com as anotações sobrepostas, colorindo
cada estrutura de uma cor distinta. Ajuda a entender o que cada classe
do supply.csv significa anatomicamente.
"""

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS = ROOT / "data" / "raw" / "annotations" / "supply.csv"
IMAGES_TRAIN = ROOT / "data" / "raw" / "train"
OUTPUT_DIR = ROOT / "data" / "raw" / "annotations"

# Imagem para visualizar (a que tem MAIS anotações para o exemplo ser rico)
TARGET = None  # auto

# Cores BGR-like (na verdade RGB no PIL) para cada classe
COLORS = {
    "NUCLEUS":               (255,  50,  50),    # vermelho
    "KINETOPLAST":           ( 50, 150, 255),    # azul
    "NUCLEUS_CELL_BODY":     (255, 130,  30),    # laranja
    "KINETOPLAST_CELL_BODY": (100, 200, 255),    # azul claro
    "T_CRUZI":               (180,  50, 255),    # roxo
}

def main():
    df = pd.read_csv(ANNOTATIONS)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Escolhe a imagem com mais anotações pra ter um exemplo rico
    if TARGET is None:
        counts = df.groupby("filename").size().sort_values(ascending=False)
        target = counts.index[0]
        print(f"Imagem auto-escolhida (mais anotações): {target} ({counts.iloc[0]} anotações)")
    else:
        target = TARGET

    img_path = IMAGES_TRAIN / target
    if not img_path.exists():
        print(f"ERRO: imagem não encontrada: {img_path}")
        return

    img = Image.open(img_path).convert("RGB")
    print(f"Resolução: {img.size}")

    annots = df[df["filename"] == target]
    print(f"Anotações nesta imagem: {len(annots)}")
    print(f"Distribuição: {annots['structure'].value_counts().to_dict()}")

    # Desenha cada anotação como um círculo + label
    draw = ImageDraw.Draw(img)
    radius = 40
    line_width = 6
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except OSError:
        font = ImageFont.load_default()

    for _, row in annots.iterrows():
        x, y = int(row["x"]), int(row["y"])
        color = COLORS.get(row["structure"], (255, 255, 0))
        # Círculo aberto
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            outline=color, width=line_width,
        )
        # Cruz no centro
        draw.line([x - 8, y, x + 8, y], fill=color, width=3)
        draw.line([x, y - 8, x, y + 8], fill=color, width=3)

    # Legenda no canto superior esquerdo
    legend_padding = 30
    legend_y = legend_padding
    for cls, color in COLORS.items():
        if cls in annots["structure"].values:
            draw.rectangle(
                [legend_padding, legend_y, legend_padding + 60, legend_y + 60],
                fill=color, outline=(255, 255, 255), width=3,
            )
            draw.text(
                (legend_padding + 80, legend_y + 8),
                f"{cls} ({(annots['structure']==cls).sum()})",
                fill=(255, 255, 255), font=font,
            )
            legend_y += 80
            
    # Reduz pra ficar viável de visualizar (3456 acaba ficando gigante)
    preview = img.resize((1152, 1536), Image.LANCZOS)

    out_path = OUTPUT_DIR / f"preview_{target.replace('.jpg', '')}.png"
    preview.save(out_path, optimize=True)
    print(f"\nSalvo em: {out_path}")
    print("Abra o arquivo pra ver a imagem anotada.")


if __name__ == "__main__":
    main()
