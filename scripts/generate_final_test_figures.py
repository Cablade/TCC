"""Figuras do teste final (A como entregue × B com negativos difíceis) para o TCC.

Lê apenas resultados já calculados; não executa modelos nem altera nada congelado:
  experiments/final_test_20261014/{stats.json, per_image.csv, A|B/predictions.json, images.csv, annotations.json}
  data/annotations/precision_teste_final_20261014/{A,B}/{queue.json, decisions.csv}
  experiments/comparison/{a_vs_b_barcelona20_20261006, a_vs_b_hardneg_20261013}/summary.csv (B antes × depois)
  experiments/runs/b_atual e b_hardneg_s* (treino e sementes)

Saída: tcc/figuras/teste_final_20261014/ (PNG 200 dpi + PDF, index.html, LEIA-ME.md, summary.json).
"""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
import shutil
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RUN = ROOT / "experiments/final_test_20261014"
PRECISION = ROOT / "data/annotations/precision_teste_final_20261014"
DEV_OLD = ROOT / "experiments/comparison/a_vs_b_barcelona20_20261006"
DEV_NEW = ROOT / "experiments/comparison/a_vs_b_hardneg_20261013"
OUT = ROOT / "tcc/figuras/teste_final_20261014"
COLORS = {"A": "#28628e", "B": "#c64d50"}
NAMES = {"A": "Modelo A (entregue)", "B": "Modelo B (proposto)"}
SEEDS = (42, 123, 456, 789, 1024)


def hashlib_sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def pct(x):
    return f"{100 * x:.1f}%"


def overlay_panel(ax, pixels, regions, points, color, title):
    """Desenha regiões positivas (cor do sistema) e pontos publicados (amarelo) sobre uma cópia reduzida."""
    canvas = Image.fromarray(pixels)
    draw = ImageDraw.Draw(canvas)
    width = max(4, canvas.width // 400)
    for r in regions:
        if r["class_id"] == 1:
            draw.rectangle(list(map(int, r["bbox"])), outline=color, width=width)
    for x, y in points:
        rad = width * 4
        draw.ellipse([x - rad, y - rad, x + rad, y + rad], outline=(255, 214, 0), width=width)
    canvas.thumbnail((1200, 1200))
    ax.imshow(canvas)
    ax.axis("off")
    ax.set_title(title, fontsize=9)


def main():
    import argparse
    from src import data_protocol as dp

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--antes-depois", choices=["desenvolvimento", "teste"], default="desenvolvimento",
                        help="Imagens da figura B antes × depois: desenvolvimento (já avaliadas pelos dois B) ou "
                             "teste (exige experiments/final_test_20261014/B_anterior/predictions.json).")
    args = parser.parse_args()
    stats = read_json(RUN / "stats.json")
    boot = stats["bootstrap"]["metrics"]
    prec = stats["precision"]
    per_image = read_csv(RUN / "per_image.csv")
    test_rows = [r for r in per_image if r["cohort"] == "positive_test"]
    OUT.mkdir(parents=True, exist_ok=True)
    figures = []

    def save(fig, name, caption):
        for ax in fig.axes:
            if ax.axison:
                ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight")
        fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
        plt.close(fig)
        figures.append({"name": name, "caption": caption})

    def ci_bars(ax, values, title, ylabel, fmt=pct, ylim=1.0):
        x = np.arange(2)
        est = [v["estimate"] for v in values]
        err = [[e - v["ci_low"] for e, v in zip(est, values)], [v["ci_high"] - e for e, v in zip(est, values)]]
        bars = ax.bar(x, est, color=[COLORS["A"], COLORS["B"]], yerr=err, capsize=6, ecolor="#333")
        for bar, v in zip(bars, values):
            ax.annotate(f"{fmt(v['estimate'])}\n[{fmt(v['ci_low'])}; {fmt(v['ci_high'])}]",
                        (bar.get_x() + bar.get_width() / 2, v["ci_high"]), ha="center", va="bottom",
                        fontsize=8, xytext=(0, 4), textcoords="offset points")
        ax.set(xticks=x, xticklabels=[NAMES["A"], NAMES["B"]], title=title, ylabel=ylabel, ylim=(0, ylim * 1.15))
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.set_yticks(np.linspace(0, 1, 6))

    # 01 — desfechos primários lado a lado.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    ci_bars(axes[0], [boot["coverage_A"], boot["coverage_B"]],
            "Cobertura dos 441 pontos publicados", "Pontos cobertos")
    precision = {s: prec[s]["metrics"]["precision"] for s in ("A", "B")}
    ci_bars(axes[1], [precision["A"], precision["B"]], "Precisão por região (revisão cega)",
            "Regiões com parasita")
    save(fig, "01_desfechos_primarios",
         "Teste final: 105 imagens murinas, 441 pontos publicados. Cobertura: pontos associados um a um a regiões "
         "positivas; IC 95% por bootstrap pareado de imagens (10.000 réplicas). Precisão: amostra revisada às cegas "
         f"(A: todas as {prec['A']['n_regions']} regiões; B: {prec['B']['n_regions']} de "
         f"{sum(int(r['positive_regions']) for r in test_rows if r['system'] == 'B')}), IC por bootstrap de imagens.")

    # 02 — decisão por imagem: positivas do teste e negativos de outra aquisição.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    ci_bars(axes[0], [boot["sensitivity_A"], boot["sensitivity_B"]],
            f"Imagens positivas sinalizadas (n={stats['bootstrap']['n_positive']})", "Proporção")
    ci_bars(axes[1], [boot["specificity_A"], boot["specificity_B"]],
            f"Negativos sem alarme (n={stats['bootstrap']['n_negative']}, auxiliar)", "Proporção")
    mc = stats["mcnemar"]
    save(fig, "02_decisao_por_imagem",
         f"McNemar exato nas positivas: só A acerta {mc['positivas']['only_A_correct']}, só B acerta "
         f"{mc['positivas']['only_B_correct']} (p Holm = {stats['mcnemar_holm']['positivas']:.2g}). Negativos de outra "
         "aquisição (73 Kaggle, 180 Barcelona) avaliados com os mesmos checkpoints; resultado auxiliar.")

    # 03 — carga de regiões positivas por imagem do teste.
    fig, ax = plt.subplots(figsize=(7, 4.3))
    series = [[int(r["positive_regions"]) for r in test_rows if r["system"] == s] for s in ("A", "B")]
    box = ax.boxplot(series, labels=[NAMES["A"], NAMES["B"]], patch_artist=True)
    for patch, s in zip(box["boxes"], ("A", "B")):
        patch.set_facecolor(COLORS[s])
        patch.set_alpha(.55)
    pts = sum(int(r["reference_points"]) for r in test_rows if r["system"] == "A") / len(series[0])
    ax.axhline(pts, color="#555", linestyle="--", label=f"Pontos publicados por imagem (média {pts:.1f})")
    ax.set(title="Regiões positivas por imagem (teste)", ylabel="Regiões")
    ax.legend(fontsize=8)
    save(fig, "03_regioes_por_imagem",
         "Distribuição por imagem. A referência publicada é parcial: com precisão revisada de cerca de 53%, o B "
         "sinaliza mais parasitas do que os pontos publicados.")

    # 04 — avanço do treinamento: B antes e depois dos negativos difíceis (mesmas imagens de desenvolvimento).
    def dev(path):
        return {(r["image_class"], r["system"]): r for r in read_csv(path / "summary.csv")}
    old, new = dev(DEV_OLD), dev(DEV_NEW)
    scope = (f"Desenvolvimento ({new[('positive', 'B')]['n_images']} campos murinos de validação e 253 negativos "
             "humanos), mesmas imagens nas duas execuções.")
    if args.antes_depois == "teste":
        from src.detection_evaluation import load_prediction_run
        from src.tcc_reporting import cohort_metrics
        rows = dp.read_manifest(RUN / "images.csv")
        refs_t = dp.load_annotations(RUN / "annotations.json", rows)
        for key, path in (("old", RUN / "B_anterior/predictions.json"), ("new", RUN / "B/predictions.json")):
            entries, _ = load_prediction_run(path, "B", "test", hashlib_sha(RUN / "images.csv"))
            by_id = {e["image_id"]: e for e in entries}
            metrics, _ = cohort_metrics(rows, refs_t, [by_id[r["image_id"]] for r in rows])
            target = old if key == "old" else new
            target[("positive", "B")] = {k: str(v) for k, v in metrics.items()}
        scope = (f"Positivas: as {len(rows)} imagens do teste final, com o B anterior (arquivado) executado nelas só "
                 "para esta figura descritiva. Negativos: 253 imagens humanas de outra aquisição.")
    n_pos = int(new[("positive", "B")]["n_images"])
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    labels = ["B anterior", "B com negativos\ndifíceis"]
    for ax, values, title, ylabel, fmt in [
        (axes[0], [int(old[("positive", "B")]["positive_regions"]) / n_pos, int(new[("positive", "B")]["positive_regions"]) / n_pos],
         "Regiões positivas por campo murino", "Regiões por imagem", "{:.1f}"),
        (axes[1], [int(old[("positive", "B")]["matched_positive_regions"]), int(new[("positive", "B")]["matched_positive_regions"])],
         f"Pontos cobertos (de {old[('positive', 'B')]['reference_points']})", "Pontos", "{:d}"),
        (axes[2], [int(old[("negative", "B")]["false_positive_regions"]), int(new[("negative", "B")]["false_positive_regions"])],
         f"Regiões em {new[('negative', 'B')]['n_images']} negativos humanos", "Regiões", "{:d}")]:
        bars = ax.bar(labels, values, color=["#d9a3a4", COLORS["B"]])
        ax.bar_label(bars, labels=[fmt.format(v) for v in values], padding=3)
        ax.set(title=title, ylabel=ylabel, ylim=(0, max(values + [1]) * 1.25))
    save(fig, "04_avanco_treinamento_B",
         scope + " A mineração e revisão de 517 negativos difíceis murinos (só treino) reduziu as regiões por "
         "campo sem perder cobertura e zerou os alarmes em negativos humanos.")

    # 05 — estabilidade entre sementes.
    vals, accs = [], []
    for seed in SEEDS:
        run = ROOT / f"experiments/runs/b_hardneg_s{seed}"
        if seed == 42:
            run = ROOT / "experiments/runs/b_atual"
        meta, hist = read_json(run / "metadata.json"), read_json(run / "history.json")
        vals.append(meta["selected_val_loss"])
        accs.append(hist["val_accuracy"][meta["selected_epoch"] - 1])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, values, title, fmt in [(axes[0], vals, "val_loss na época escolhida", "{:.4f}"),
                                   (axes[1], [100 * a for a in accs], "Acurácia de validação (%)", "{:.2f}")]:
        bars = ax.bar([str(s) for s in SEEDS], values, color=[COLORS["B"]] + ["#d9a3a4"] * 4)
        ax.bar_label(bars, labels=[fmt.format(v) for v in values], padding=3, fontsize=8)
        ax.axhline(np.mean(values), color="#555", linestyle="--", label=f"média {np.mean(values):.4g}")
        lo, hi = min(values), max(values)
        ax.set(title=title, xlabel="Semente", ylim=(lo - (hi - lo) * 2 - 1e-3, hi + (hi - lo) * 2 + 1e-3))
        ax.legend(fontsize=8)
    save(fig, "05_estabilidade_sementes",
         "Cinco treinos do B com sementes declaradas antes do treino; a semente 42 (destacada) é o modelo avaliado "
         "no teste. Validação de 1.070 recortes.")

    # 06 — curvas de treinamento do B avaliado.
    meta, hist = read_json(ROOT / "experiments/runs/b_atual/metadata.json"), read_json(ROOT / "experiments/runs/b_atual/history.json")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    epochs = np.arange(1, len(hist["loss"]) + 1)
    for ax, key, title in [(axes[0], "loss", "Perda"), (axes[1], "accuracy", "Acurácia dos recortes")]:
        ax.plot(epochs, hist[key], label="Treino")
        ax.plot(epochs, hist["val_" + key], label="Validação")
        ax.axvline(meta["selected_epoch"], linestyle="--", color="#555", label="Época selecionada")
        ax.set(title=title, xlabel="Época")
        ax.legend(fontsize=8)
    save(fig, "06_treinamento_B",
         f"B avaliado ({meta['run_name']}): EfficientNet-B0, AdamW, cosseno, época escolhida por menor val_loss "
         f"(época {meta['selected_epoch']}). Sem histórico de treino comparável do A.")

    # 07 — tempo por imagem.
    fig, ax = plt.subplots(figsize=(7, 4.3))
    times = [[float(r["algorithm_seconds"]) for r in test_rows if r["system"] == s] for s in ("A", "B")]
    ax.boxplot(times, labels=[NAMES["A"], NAMES["B"]])
    for i, t in enumerate(times, 1):
        ax.annotate(f"mediana {np.median(t):.2f} s", (i, np.median(t)), xytext=(28, 0), textcoords="offset points",
                    fontsize=8, va="center")
    ax.set(title="Tempo de processamento por imagem (teste)", ylabel="Segundos")
    save(fig, "07_tempo",
         "Execução única em CPU, duas threads, B em grafo TensorFlow; inclui a primeira imagem e exclui leitura e "
         "exportação. Descritivo, não é benchmark repetido.")

    # 08 — overlays lado a lado (A | B) nas mesmas imagens: 3 positivas do teste e 2 negativas de outra aquisição.
    images = {r["image_id"]: r for r in dp.read_manifest(RUN / "images.csv")}
    refs = dp.load_annotations(RUN / "annotations.json", list(images.values()))
    preds = {s: {e["image_id"]: e for e in read_json(RUN / s / "predictions.json")["images"]} for s in ("A", "B")}
    n_pos_b = {i: sum(r["class_id"] == 1 for r in preds["B"][i]["regions"]) for i in images}
    a_hits = sorted(i for i in images if any(r["class_id"] == 1 for r in preds["A"][i]["regions"]))
    by_load = sorted(images, key=lambda i: (n_pos_b[i], i))
    chosen = []
    for image_id in (max(a_hits or list(images), key=lambda i: (len(refs[i]["positives"]), i)),  # A sinalizou algo
                     by_load[len(by_load) // 2],                                                  # carga mediana do B
                     max(images, key=lambda i: (len(refs[i]["positives"]), i))):                  # mais pontos
        if image_id not in chosen:
            chosen.append(image_id)
    examples = [("teste", i, images[i], refs[i], preds["A"][i], preds["B"][i]) for i in chosen]
    dev_rows = {r["image_id"]: r for r in dp.read_manifest(DEV_NEW / "images.csv")}
    dev_preds = {s: {e["image_id"]: e for e in read_json(DEV_NEW / s / "predictions.json")["images"]} for s in ("A", "B")}
    for cohort, label in (("kaggle_negative_val", "negativo Kaggle"), ("barcelona_negative", "negativo Barcelona")):
        image_id = min(i for i, r in dev_rows.items() if r["cohort"] == cohort)
        examples.append((label, image_id, dev_rows[image_id], {"positives": []},
                         dev_preds["A"][image_id], dev_preds["B"][image_id]))
    from matplotlib.patches import Patch
    for n, (label, image_id, row, ref, pa, pb) in enumerate(examples, 1):
        pixels = dp.read_image_rgb(row["path"])
        points = [tuple(map(int, p["point"])) for p in ref["positives"]]
        fig, axes = plt.subplots(1, 2, figsize=(11, 7))
        for ax, s, pred in ((axes[0], "A", pa), (axes[1], "B", pb)):
            k = sum(r["class_id"] == 1 for r in pred["regions"])
            color = (40, 98, 142) if s == "A" else (198, 77, 80)
            overlay_panel(ax, pixels, pred["regions"], points, color, f"{NAMES[s]}: {k} regiões positivas")
        fig.legend(handles=[Patch(edgecolor="#ffd600", facecolor="none", label="Ponto publicado"),
                            Patch(edgecolor=COLORS["A"], facecolor="none", label="Região positiva do A"),
                            Patch(edgecolor=COLORS["B"], facecolor="none", label="Região positiva do B")],
                   loc="lower center", ncol=3, fontsize=8, frameon=False)
        title = label[0].upper() + label[1:]
        fig.suptitle(f"{title}: {len(points)} pontos publicados" if label == "teste"
                     else f"{title} (outra aquisição, auxiliar)")
        source = "Zenodo, CC BY 4.0" if label == "teste" else row.get("source", "")
        save(fig, f"08_overlay_{n}",
             f"{image_id} ({source}). A e B sobre a mesma imagem. Seleção determinística: positivas do teste = a com "
             "mais pontos entre as que o A sinalizou, a de carga mediana do B e a com mais pontos; negativas = a "
             "primeira de cada fonte por identificador. Ilustrativo, não é amostra representativa.")

    # 09 — recortes revisados: acertos e falsos alarmes.
    groups = []
    for s in ("A", "B"):
        queue = read_json(PRECISION / s / "queue.json")
        decisions = {r["candidate_id"]: r["decision"] for r in read_csv(PRECISION / s / "decisions.csv")}
        items = sorted(queue["items"], key=lambda i: i["candidate_id"])
        for decision, label in (("parasita", "contém parasita"), ("nao_parasita", "falso alarme")):
            chosen = [i for i in items if decisions.get(i["candidate_id"]) == decision][:4]
            if chosen:
                groups.append((f"{NAMES[s]}: {label}", s, chosen))
    fig, axes = plt.subplots(len(groups), 4, figsize=(9, 2.4 * len(groups)))
    axes = np.atleast_2d(axes)
    for row, (title, s, chosen) in enumerate(groups):
        for col in range(4):
            ax = axes[row, col]
            ax.axis("off")
            if col < len(chosen):
                ax.imshow(Image.open(PRECISION / s / chosen[col]["crop_file"]))
        axes[row, 0].set_title(title, loc="left", fontsize=9, pad=10)
    fig.subplots_adjust(hspace=.35)
    save(fig, "09_recortes_revisados",
         "Recortes da revisão cega do teste, os primeiros de cada categoria em ordem de identificador (seleção "
         "determinística, não escolhida a dedo). O A não teve nenhuma região revisada como parasita.")

    # Exemplos e página.
    p = {s: prec[s] for s in ("A", "B")}
    f1 = {s: (2 * p[s]["metrics"]["precision"]["estimate"] * boot[f"coverage_{s}"]["estimate"]
              / (p[s]["metrics"]["precision"]["estimate"] + boot[f"coverage_{s}"]["estimate"])
              if p[s]["metrics"]["precision"]["estimate"] + boot[f"coverage_{s}"]["estimate"] else 0.0)
          for s in ("A", "B")}
    table = [
        ("Cobertura dos pontos publicados", boot["coverage_A"], boot["coverage_B"], boot["coverage_diff_B_minus_A"]),
        ("Precisão revisada por região", p["A"]["metrics"]["precision"], p["B"]["metrics"]["precision"], None),
        ("Imagens positivas sinalizadas", boot["sensitivity_A"], boot["sensitivity_B"], boot["sensitivity_diff_B_minus_A"]),
        ("Negativos sem alarme (auxiliar)", boot["specificity_A"], boot["specificity_B"], boot["specificity_diff_B_minus_A"]),
    ]
    fmt = lambda v: f"{pct(v['estimate'])} [{pct(v['ci_low'])}; {pct(v['ci_high'])}]" if v else "—"
    md = ["# Teste final — Modelo A (entregue) × Modelo B (proposto)", "",
          f"105 imagens murinas de teste (441 pontos publicados), abertas uma única vez após o congelamento do "
          f"protocolo; 253 negativos humanos de outra aquisição como resultado auxiliar. IC 95% por bootstrap "
          f"pareado de imagens (10.000 réplicas, semente {stats['bootstrap']['seed']}).", "",
          "| Desfecho | A | B | B − A |", "| --- | ---: | ---: | ---: |"]
    md += [f"| {name} | {fmt(a)} | {fmt(b)} | {fmt(d)} |" for name, a, b, d in table]
    md += [f"| F1 aproximado (derivado) | {f1['A']:.2f} | {f1['B']:.2f} | — |", "",
           f"Precisão do A: 0 de {p['A']['nao_parasita'] + p['A']['parasita']} regiões decididas; IC exato "
           "(Clopper-Pearson) 0% [0; 14,8%].",
           f"Concordância entre avaliadores (50 regiões): ver data/annotations/precision_teste_final_20261014/"
           "kappa_segundo_avaliador/kappa.json.", ""]
    md += [f"- **{f['name']}**: {f['caption']}" for f in figures]
    (OUT / "LEIA-ME.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    rows = "".join(f"<tr><td>{html.escape(n)}</td><td>{fmt(a)}</td><td>{fmt(b)}</td><td>{fmt(d)}</td></tr>"
                   for n, a, b, d in table)
    charts = "".join(f'<section><h2>{f["name"]}</h2><a href="{f["name"]}.pdf">PDF</a>'
                     f'<img class="grafico" src="{f["name"]}.png"><p>{html.escape(f["caption"])}</p></section>'
                     for f in figures)
    page = ('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" '
            'content="width=device-width,initial-scale=1"><title>Teste final A × B</title><style>body{font:16px '
            'system-ui;background:#edf2f5;color:#203548;margin:24px;line-height:1.5}section{background:white;'
            'padding:18px;margin:18px 0;border-radius:8px}table{border-collapse:collapse;background:white}td,th'
            '{padding:10px;border:1px solid #cdd7df}.grafico{display:block;max-width:100%;width:1100px}</style>'
            '<h1>Teste final: Modelo A (entregue) × Modelo B (proposto)</h1><p>105 imagens murinas de teste, '
            '441 pontos publicados; 253 negativos humanos como resultado auxiliar.</p><table><tr><th>Desfecho</th>'
            f'<th>A</th><th>B</th><th>B − A</th></tr>{rows}<tr><td>F1 aproximado</td><td>{f1["A"]:.2f}</td>'
            f'<td>{f1["B"]:.2f}</td><td>—</td></tr></table>{charts}</html>')
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps({"stats_sha256": stats["per_image_sha256"], "f1": f1,
                                                  "figures": figures}, indent=2, ensure_ascii=False) + "\n",
                                      encoding="utf-8")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
