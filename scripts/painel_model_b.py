"""Painel local do Modelo B: escolha uma imagem do computador e veja as regiões suspeitas.

Uso, a partir da raiz do repositório:
  python scripts/painel_model_b.py

Abre uma página no navegador, atendida só neste computador (127.0.0.1). A imagem não sai da
máquina e nada é gravado em disco. Os escores são a saída softmax do B, sem calibração: não são
probabilidade de infecção nem diagnóstico. O B foi avaliado só em imagens do mesmo tipo das do
Zenodo 5123062; em outras imagens o resultado não tem desempenho conhecido.
"""

from __future__ import annotations

import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
import threading
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Valores registrados em data/protocol/protocolo_congelado.json.
CHECKPOINT_SHA256 = "b4d9d7ee4434143857513fe25796dc7264f716c39adf2c7b889d228ce7c133f8"
CONFIG_SHA256 = "2fd34d3b351aa4e28f8add20f4099162bd7765a8ca2d811a37169f178f33a737"
MAX_BYTES = 40 * 1024 * 1024
MAX_PIXELS = 50_000_000

PAGE = """<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Modelo B - demonstração</title>
<style>
body{font:16px system-ui;margin:24px auto;max-width:1100px;padding:0 16px;color:#203548;background:#f3f6f8}
section{background:#fff;padding:18px;border-radius:8px;margin:14px 0}
img{max-width:100%;border:1px solid #cdd7df}
button{font:inherit;padding:8px 18px}
.aviso{background:#fff6df;border-left:4px solid #d99a00}
table{border-collapse:collapse}td,th{border:1px solid #cdd7df;padding:6px 12px;text-align:right}
#erro{color:#b00020}.grande{font-size:22px;margin:4px 0}
</style>
<h1>Modelo B: regiões suspeitas de <i>T. cruzi</i></h1>
<section><input type="file" id="arquivo" accept=".jpg,.jpeg,.png,.tif,.tiff,.bmp">
<button id="rodar">Analisar</button> <span id="estado"></span><p id="erro"></p></section>
<section class="aviso">Uso em pesquisa, não é diagnóstico.</section>
<section id="saida" hidden>
<p class="grande" id="resumo"></p><p id="detalhe"></p><img id="marcada" alt="Imagem com as regiões marcadas">
<h2>Regiões suspeitas</h2><table><thead><tr><th>Nº</th><th>Escore</th><th>x1, y1, x2, y2</th></tr></thead>
<tbody id="linhas"></tbody></table></section>
<script>
const el = id => document.getElementById(id);
const pct = v => (100 * v).toFixed(1).replace('.', ',') + '%';
el('rodar').onclick = async () => {
  const f = el('arquivo').files[0];
  el('erro').textContent = ''; el('saida').hidden = true;
  if (!f) { el('erro').textContent = 'Escolha uma imagem.'; return; }
  if (f.size > 40 * 1024 * 1024) { el('erro').textContent = 'Arquivo acima de 40 MB.'; return; }
  el('rodar').disabled = true; el('estado').textContent = 'Analisando...';
  try {
    const r = await fetch('/analisar', {method: 'POST', body: f, headers: {'Content-Type': 'application/octet-stream'}});
    const d = await r.json();
    if (d.erro) throw new Error(d.erro);
    el('resumo').textContent = d.suspeitas.length
      ? d.suspeitas.length + ' regiões suspeitas; maior escore: ' + pct(d.maior_escore)
      : 'Nenhuma região suspeita' + (d.maior_escore === null ? '' : '; maior escore: ' + pct(d.maior_escore));
    el('detalhe').textContent = f.name + ', ' + d.largura + ' x ' + d.altura + ' px, '
      + d.candidatas + ' regiões candidatas, ' + d.segundos.toFixed(1).replace('.', ',') + ' s';
    el('marcada').src = 'data:image/jpeg;base64,' + d.imagem;
    const tb = el('linhas'); tb.replaceChildren();
    for (const s of d.suspeitas) {
      const tr = tb.insertRow();
      for (const t of [s.numero, pct(s.escore), s.caixa.join(', ')]) tr.insertCell().textContent = t;
    }
    el('saida').hidden = false;
  } catch (e) { el('erro').textContent = e.message; }
  el('rodar').disabled = false; el('estado').textContent = '';
};
</script></html>"""


def load_classifier(checkpoint):
    import tensorflow as tf
    from src.data_pipeline import file_sha256
    from src.model_b import compiled_inference

    config_path = checkpoint.parent / "config.json"
    if file_sha256(checkpoint) != CHECKPOINT_SHA256 or file_sha256(config_path) != CONFIG_SHA256:
        raise ValueError("best.keras ou config.json difere do artefato congelado no protocolo.")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    model = tf.keras.models.load_model(checkpoint)
    return compiled_inference(model, tuple(config["model"]["input_shape"])), config


def analyze(data, classifier, config):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
    from src.model_b import predict_image_b

    try:
        source = Image.open(io.BytesIO(data))
    except UnidentifiedImageError:
        raise ValueError("o arquivo não é uma imagem suportada.") from None
    with source:
        if source.width * source.height > MAX_PIXELS:
            raise ValueError("Imagem grande demais (limite de 50 megapixels).")
        pixels = np.asarray(source.convert("RGB")).copy()
    result = predict_image_b(pixels, classifier, config, "painel")
    if result["status"] == "erro":
        raise ValueError(result["error"])
    # Decisão do protocolo: classe 1 vence no argmax. O escore serve só para ordenar e mostrar.
    suspects = sorted((r for r in result["regions"] if r["class_id"] == 1), key=lambda r: -r["scores"][1])
    canvas = Image.fromarray(pixels)
    draw = ImageDraw.Draw(canvas)
    width = max(3, canvas.width // 400)
    font = ImageFont.load_default(size=max(14, canvas.width // 60))
    for number, region in enumerate(suspects, 1):
        x1, y1, x2, y2 = region["bbox"]
        draw.rectangle((x1, y1, x2 - 1, y2 - 1), outline="red", width=width)
        label = f"{number}: {100 * region['scores'][1]:.0f}%"
        box = draw.textbbox((x1 + width, y1 + width), label, font=font)
        draw.rectangle(box, fill="red")
        draw.text((x1 + width, y1 + width), label, fill="white", font=font)
    canvas.thumbnail((2000, 2000))
    buffer = io.BytesIO()
    canvas.save(buffer, "JPEG", quality=90)
    return {
        "largura": int(pixels.shape[1]), "altura": int(pixels.shape[0]),
        "candidatas": len(result["candidates"]),
        "maior_escore": max((r["scores"][1] for r in result["regions"]), default=None),
        "segundos": result["timings"]["total_seconds"],
        "suspeitas": [{"numero": n, "escore": r["scores"][1], "caixa": [int(v) for v in r["bbox"]]}
                      for n, r in enumerate(suspects, 1)],
        "imagem": base64.b64encode(buffer.getvalue()).decode("ascii"),
    }


def make_handler(classifier, config, port):
    lock = threading.Lock()
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def reply_json(self, status, payload):
            self.reply(status, json.dumps(payload).encode("utf-8"), "application/json")

        def allowed(self):
            # Recusa pedidos vindos de outros sites ou de outro nome de host.
            origin = self.headers.get("Origin")
            return self.headers.get("Host") in hosts and (
                origin is None or origin in {f"http://{host}" for host in hosts})

        def do_GET(self):
            if not self.allowed() or self.path != "/":
                return self.reply(404, b"", "text/plain")
            self.reply(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")

        def do_POST(self):
            self.close_connection = True
            if not self.allowed() or self.path != "/analisar":
                return self.reply_json(404, {"erro": "Endereço inválido."})
            try:
                size = int(self.headers.get("Content-Length", ""))
            except ValueError:
                size = 0
            if not 0 < size <= MAX_BYTES:
                return self.reply_json(413, {"erro": "Arquivo vazio ou acima de 40 MB."})
            try:
                data = self.rfile.read(size)
                with lock:
                    payload = analyze(data, classifier, config)
            except Exception as exc:
                return self.reply_json(400, {"erro": f"Não foi possível analisar: {exc}"})
            self.reply_json(200, payload)

        def log_message(self, *args):
            pass

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "experiments/runs/b_atual/best.keras")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    print("Carregando o Modelo B...", flush=True)
    classifier, config = load_classifier(args.checkpoint)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(classifier, config, args.port))
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Painel em {url} (Ctrl+C encerra)", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
