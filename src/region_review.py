"""Fila de revisão humana de regiões: recortes, contexto e página HTML local.

Usado na mineração de negativos difíceis (treino) e na estimativa de precisão
por amostra (validação). A página não mostra escore nem ponto anotado, para que
a decisão do revisor não seja influenciada pelo modelo. As decisões são
exportadas em JSON ligado ao SHA-256 da fila; nada é gravado na referência
até um script de mesclagem conferir esse vínculo.
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

import numpy as np

CONTEXT_FACTOR = 3
CONTEXT_MAX_SIDE = 600


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_region_views(image_rgb: np.ndarray, bbox, output_dir: Path, candidate_id: str) -> dict:
    """Grava o recorte exato (PNG) e uma vista de contexto com a caixa desenhada (JPEG)."""
    from PIL import Image, ImageDraw
    from .segmentation import crop_region

    output_dir = Path(output_dir)
    crop_path = output_dir / "crops" / f"{candidate_id}.png"
    context_path = output_dir / "context" / f"{candidate_id}.jpg"
    crop_path.parent.mkdir(parents=True, exist_ok=True)
    context_path.parent.mkdir(parents=True, exist_ok=True)
    crop = crop_region(image_rgb, bbox)
    Image.fromarray(crop).save(crop_path)
    x1, y1, x2, y2 = map(int, bbox)
    h, w = image_rgb.shape[:2]
    side = max(x2 - x1, y2 - y1) * CONTEXT_FACTOR
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    left, top = max(0, cx - side // 2), max(0, cy - side // 2)
    right, bottom = min(w, left + side), min(h, top + side)
    context = Image.fromarray(image_rgb[top:bottom, left:right].copy())
    draw = ImageDraw.Draw(context)
    draw.rectangle((x1 - left, y1 - top, x2 - left - 1, y2 - top - 1), outline=(255, 215, 0), width=4)
    context.thumbnail((CONTEXT_MAX_SIDE, CONTEXT_MAX_SIDE))
    context.save(context_path, quality=90)
    return {"crop_file": crop_path.relative_to(output_dir).as_posix(),
            "context_file": context_path.relative_to(output_dir).as_posix(),
            "crop_sha256": sha256_bytes(crop_path.read_bytes())}


def write_queue(output_dir: Path, metadata: dict, items: list[dict]) -> str:
    """Grava queue.json e devolve seu SHA-256, que as decisões precisam citar."""
    ids = [item["candidate_id"] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate_id repetido na fila.")
    path = Path(output_dir) / "queue.json"
    if path.exists():
        raise FileExistsError("queue.json já existe; use outra pasta para preservar a fila anterior.")
    path.write_text(json.dumps({**metadata, "items": items}, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return sha256_bytes(path.read_bytes())


def load_decisions(queue_path: Path, decisions_path: Path, allowed: set[str]) -> tuple[dict, dict]:
    """Confere o vínculo decisões ↔ fila e devolve (fila, {candidate_id: decisão})."""
    queue_path, decisions_path = Path(queue_path), Path(decisions_path)
    queue = json.loads(queue_path.read_text(encoding="utf-8-sig"))
    payload = json.loads(decisions_path.read_text(encoding="utf-8-sig"))
    if payload.get("queue_sha256") != sha256_bytes(queue_path.read_bytes()):
        raise ValueError("As decisões não foram feitas sobre esta fila (SHA-256 diferente).")
    if not str(payload.get("reviewer", "")).strip():
        raise ValueError("Decisões exigem identificar o revisor.")
    known = {item["candidate_id"] for item in queue["items"]}
    decisions = {}
    for entry in payload.get("decisions", []):
        candidate_id, decision = entry.get("candidate_id"), entry.get("decision")
        if candidate_id not in known:
            raise ValueError(f"Decisão para região fora da fila: {candidate_id}")
        if decision not in allowed:
            raise ValueError(f"Decisão inválida: {decision}")
        if candidate_id in decisions:
            raise ValueError(f"Decisão repetida: {candidate_id}")
        decisions[candidate_id] = {**entry, "reviewer": payload["reviewer"]}
    return queue, decisions


_PAGE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f6f4;--fg:#1d1d1b;--muted:#6b6b66;--card:#fff;--line:#ddd;--accent:#2f5d8a}
@media (prefers-color-scheme: dark){:root{--bg:#161615;--fg:#ecebe6;--muted:#a3a29b;--card:#22221f;--line:#3a3a36;--accent:#86b2dc}}
body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;margin:0;padding:16px}
main{max-width:1100px;margin:0 auto}
.views{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}
.views figure{margin:0;background:var(--card);border:1px solid var(--line);padding:8px;border-radius:6px}
.views img{display:block;max-width:100%;image-rendering:auto}
#crop{width:336px}
figcaption{color:var(--muted);font-size:13px;margin-top:4px}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}
button{font:inherit;padding:8px 14px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
button.sel{outline:3px solid var(--accent)}
#status{color:var(--muted)}
.help{color:var(--muted);font-size:13px}
input{font:inherit;padding:6px}
</style></head><body><main>
<h1>__TITLE__</h1>
<p class="help">__INSTRUCTIONS__</p>
<p>Revisor: <input id="reviewer" placeholder="nome"> <span id="status"></span></p>
<div class="views">
 <figure><img id="crop" alt="recorte"><figcaption>Recorte exato avaliado pelo modelo</figcaption></figure>
 <figure><img id="context" alt="contexto"><figcaption>Contexto (caixa amarela = recorte)</figcaption></figure>
</div>
<div class="bar" id="choices"></div>
<div class="bar">
 <button id="prev">← Anterior</button><button id="next">Próxima →</button>
 <button id="nextOpen">Próxima sem decisão</button><button id="export">Exportar decisões (JSON)</button>
</div>
<p class="help">Atalhos: __KEYS__, ← e → para navegar. O progresso fica salvo neste navegador; exporte ao terminar.</p>
</main>
<script>
const QUEUE_SHA = "__QUEUE_SHA__";
const ITEMS = __ITEMS__;
const OPTIONS = __OPTIONS__;
const KEY = "review_" + QUEUE_SHA;
let state = {reviewer: "", decisions: {}, index: 0};
try { const saved = localStorage.getItem(KEY); if (saved) state = JSON.parse(saved); } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
const $ = id => document.getElementById(id);
$("reviewer").value = state.reviewer || "";
$("reviewer").oninput = e => { state.reviewer = e.target.value; save(); };
OPTIONS.forEach((option, i) => {
  const b = document.createElement("button");
  b.textContent = `${i + 1} · ${option.label}`; b.dataset.value = option.value;
  b.onclick = () => decide(option.value); $("choices").appendChild(b);
});
function show() {
  const item = ITEMS[state.index];
  $("crop").src = item.crop_file; $("context").src = item.context_file;
  const current = state.decisions[item.candidate_id]?.decision;
  [...$("choices").children].forEach(b => b.classList.toggle("sel", b.dataset.value === current));
  const done = Object.keys(state.decisions).length;
  $("status").textContent = `Região ${state.index + 1} de ${ITEMS.length} · ${done} decididas`;
  save();
}
function decide(value) {
  const item = ITEMS[state.index];
  state.decisions[item.candidate_id] = {decision: value, reviewed_at: new Date().toISOString()};
  if (state.index < ITEMS.length - 1) state.index++;
  show();
}
$("prev").onclick = () => { if (state.index > 0) state.index--; show(); };
$("next").onclick = () => { if (state.index < ITEMS.length - 1) state.index++; show(); };
$("nextOpen").onclick = () => {
  const i = ITEMS.findIndex(item => !state.decisions[item.candidate_id]);
  if (i >= 0) { state.index = i; show(); }
};
document.onkeydown = e => {
  if (e.target.tagName === "INPUT") return;
  const n = parseInt(e.key, 10);
  if (n >= 1 && n <= OPTIONS.length) decide(OPTIONS[n - 1].value);
  if (e.key === "ArrowLeft") $("prev").onclick();
  if (e.key === "ArrowRight") $("next").onclick();
};
$("export").onclick = () => {
  if (!state.reviewer.trim()) { alert("Preencha o nome do revisor."); return; }
  const decisions = ITEMS.filter(item => state.decisions[item.candidate_id])
    .map(item => ({candidate_id: item.candidate_id, ...state.decisions[item.candidate_id]}));
  const blob = new Blob([JSON.stringify({queue_sha256: QUEUE_SHA, reviewer: state.reviewer.trim(),
    exported_at: new Date().toISOString(), total_items: ITEMS.length, decisions}, null, 2)],
    {type: "application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
  a.download = "decisions.json"; a.click();
};
show();
</script></body></html>
"""


def write_review_page(output_dir: Path, queue_sha256: str, items: list[dict], *, title: str,
                      instructions: str, options: list[tuple[str, str]]) -> Path:
    """Página estática; abre direto do disco e lê crops/ e context/ por caminho relativo."""
    public = [{"candidate_id": item["candidate_id"], "crop_file": item["crop_file"],
               "context_file": item["context_file"]} for item in items]
    keys = ", ".join(f"{i + 1} = {label}" for i, (_, label) in enumerate(options))
    page = (_PAGE.replace("__TITLE__", html.escape(title))
            .replace("__INSTRUCTIONS__", html.escape(instructions))
            .replace("__KEYS__", html.escape(keys))
            .replace("__QUEUE_SHA__", queue_sha256)
            .replace("__ITEMS__", json.dumps(public))
            .replace("__OPTIONS__", json.dumps([{"value": v, "label": l} for v, l in options],
                                               ensure_ascii=False)))
    path = Path(output_dir) / "revisao.html"
    path.write_text(page, encoding="utf-8")
    return path
