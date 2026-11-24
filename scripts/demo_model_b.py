"""Demonstração do Modelo B em uma imagem pública do Zenodo (CC BY 4.0).

Uso, a partir da raiz do repositório:
  python scripts/demo_model_b.py --zip data/raw/trypoastigote_images.zip

Só lê imagens listadas em data/demo/teste_final_images.csv e confere o SHA-256 da imagem e do
modelo. Não altera nem recalcula resultados do teste final. Uma caixa vermelha é uma região que
o B classificou como suspeita; não é diagnóstico nem parasita confirmado.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Valores registrados em data/protocol/protocolo_congelado.json.
CHECKPOINT_SHA256 = "b4d9d7ee4434143857513fe25796dc7264f716c39adf2c7b889d228ce7c133f8"
CONFIG_SHA256 = "2fd34d3b351aa4e28f8add20f4099162bd7765a8ca2d811a37169f178f33a737"
# Imagem de carga mediana do B já usada em 08_overlay_2; não é a de melhor resultado.
DEFAULT_IMAGE = "img_0fa0fd46387df17132f14eae"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zip", type=Path, default=ROOT / "data/raw/trypoastigote_images.zip")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "experiments/runs/b_atual/best.keras")
    parser.add_argument("--image-id", default=DEFAULT_IMAGE)
    parser.add_argument("--output", type=Path, default=ROOT / "saida_demo/demo_modelo_b.png")
    args = parser.parse_args()

    import numpy as np
    import tensorflow as tf
    from PIL import Image, ImageDraw
    from src.data_pipeline import file_sha256
    from src.data_protocol import read_manifest
    from src.model_b import compiled_inference, predict_image_b

    if args.output.exists():
        parser.error(f"A saída já existe: {args.output}")
    rows = {row["image_id"]: row for row in read_manifest(ROOT / "data/demo/teste_final_images.csv")}
    if args.image_id not in rows:
        parser.error("Imagem fora da lista pública data/demo/teste_final_images.csv.")
    row = rows[args.image_id]
    config_path = args.checkpoint.parent / "config.json"
    if file_sha256(args.checkpoint) != CHECKPOINT_SHA256 or file_sha256(config_path) != CONFIG_SHA256:
        parser.error("best.keras ou config.json difere do artefato congelado no protocolo.")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    member = row["path"].split("!", 1)[1]
    with zipfile.ZipFile(args.zip) as archive:
        data = archive.read(member)
    if hashlib.sha256(data).hexdigest() != row["sha256"]:
        parser.error("Conteúdo da imagem difere do manifesto público.")
    with Image.open(io.BytesIO(data)) as source:
        pixels = np.asarray(source.convert("RGB")).copy()
    print(f"Imagem: {member} ({args.image_id}), {pixels.shape[1]} x {pixels.shape[0]} px")

    model = tf.keras.models.load_model(args.checkpoint)
    classifier = compiled_inference(model, tuple(config["model"]["input_shape"]))
    result = predict_image_b(pixels, classifier, config, args.image_id)
    if result["status"] == "erro":
        raise RuntimeError(result["error"])
    suspects = [region for region in result["regions"] if region["class_id"] == 1]
    print(f"Regiões candidatas: {len(result['candidates'])}")
    print(f"Regiões suspeitas:  {len(suspects)}")
    print(f"Tempo: {result['timings']['total_seconds']:.1f} s (CPU)")

    recorded = json.loads((ROOT / "experiments/final_test_20261014/B/predictions.json").read_text(encoding="utf-8"))
    previous = next((i for i in recorded["images"] if i["image_id"] == args.image_id), None)
    if previous is not None:
        expected = sorted(tuple(r["bbox"]) for r in previous["regions"] if r["class_id"] == 1)
        same = expected == sorted(tuple(r["bbox"]) for r in suspects)
        print(f"Mesmas caixas do registro do teste final ({len(expected)}): {'sim' if same else 'NÃO'}")

    canvas = Image.fromarray(pixels)
    draw = ImageDraw.Draw(canvas)
    width = max(4, canvas.width // 400)
    for region in suspects:
        x1, y1, x2, y2 = region["bbox"]
        draw.rectangle((x1, y1, x2 - 1, y2 - 1), outline="red", width=width)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output)
    print(f"Imagem marcada: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
