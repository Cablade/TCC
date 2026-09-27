"""Gera uma figura-resumo da validação preliminar A x B para o TCC."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib

# Exportação de arquivos não depende de janela gráfica nem da instalação Tcl/Tk.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


STATUS_LABELS = {
    "predicao_positiva": "Sinalizada",
    "sem_regioes": "Sem regiões",
    "regioes_sem_predicao_positiva": "Regiões sem suspeita",
    "erro": "Erro",
}


def status_counts(system: dict) -> dict:
    counts = system["status_counts"]
    if set(counts) - set(STATUS_LABELS):
        raise ValueError("Estado de execução desconhecido; atualizar a legenda.")
    if any(value < 0 for value in counts.values()) or sum(counts.values()) != system["n_images"]:
        raise ValueError("Contagem de estados incompatível com o número de imagens.")
    return {key: counts.get(key, 0) for key in STATUS_LABELS}


def load_inputs(result_path: Path, epochs_path: Path) -> tuple[dict, list[dict]]:
    result = json.loads(result_path.read_text(encoding="utf-8-sig"))
    with epochs_path.open(encoding="utf-8-sig", newline="") as stream:
        epochs = list(csv.DictReader(stream))
    return result, epochs


def make_figure(result: dict, epochs: list[dict], output: Path) -> dict:
    systems = result["systems"]
    names = ["A original", "B reduzido"]
    colors = ["#2f6690", "#d1495b"]
    counts = [status_counts(systems[name[0]]) for name in names]
    n_images = systems["A"]["n_images"]
    if n_images != systems["B"]["n_images"]:
        raise ValueError("A e B devem ter o mesmo número de imagens.")
    figure, axes = plt.subplots(
        2, 2, figsize=(11, 7.2), constrained_layout=True)

    # Painel A: histórico do treinamento supervisionado do B.
    epoch = np.array([int(row["epoch"]) + 1 for row in epochs])
    axes[0, 0].plot(epoch, [float(row["accuracy"])
                    for row in epochs], label="Treino", color="#2f6690")
    axes[0, 0].plot(epoch, [float(row["val_accuracy"])
                    for row in epochs], label="Validação", color="#d1495b")
    axes[0, 0].set(title="(A) Acurácia do treinamento de B",
                   xlabel="Época", ylabel="Acurácia")
    axes[0, 0].set_ylim(0, 1.01)
    axes[0, 0].legend(frameon=False)

    # Painel B: decisão por imagem. Todas as imagens desta validação têm referência positiva.
    x = np.arange(len(names))
    bottom = np.zeros(len(names))
    for status, color in zip(STATUS_LABELS, ("#2f6690", "#d9d9d9", "#75aa78", "#d1495b")):
        values = np.array([item[status] for item in counts])
        if values.sum():
            axes[0, 1].bar(x, values, bottom=bottom, label=STATUS_LABELS[status], color=color)
            for index, value in enumerate(values):
                if value:
                    axes[0, 1].text(index, bottom[index] + value / 2, str(value),
                                    ha="center", va="center", color="black" if status == "sem_regioes" else "white")
        bottom += values
    axes[0, 1].set(title=f"(B) Estados em {n_images} imagens",
                   ylabel="Número de imagens", xticks=x, xticklabels=names)
    axes[0, 1].set_ylim(0, max(n_images * 1.1, 1))
    axes[0, 1].legend(frameon=False)

    # Painel C: propostas e regiões classificadas, sem chamar desconhecidos de negativos.
    candidates = [sum(item["n_candidates"] for item in systems[name[0]]["per_image"])
                  for name in names]
    positive_regions = [sum(item["n_positive_regions"] for item in systems[name[0]]["per_image"])
                        for name in names]
    other_regions = [total - positive for total,
                     positive in zip(candidates, positive_regions)]
    axes[1, 0].bar(x, positive_regions, label="Suspeitas", color="#2f6690")
    axes[1, 0].bar(x, other_regions, bottom=positive_regions,
                   label="Outras propostas", color="#d9d9d9")
    axes[1, 0].set(title="(C) Regiões propostas e classificadas",
                   ylabel="Regiões", xticks=x, xticklabels=names)
    axes[1, 0].set_ylim(0, max(max(candidates) * 1.18, 1))
    for index, (total, positive) in enumerate(zip(candidates, positive_regions)):
        axes[1, 0].text(index, total + max(candidates) * .02,
                        f"{total:,} propostas\n{positive:,} suspeitas".replace(",", "."),
                        ha="center", va="bottom", fontsize=9)
    axes[1, 0].legend(frameon=False)

    # Painel D: tempo da inferência sem leitura/escrita de imagens.
    means = [systems[name[0]]["timing_seconds"]["total_seconds"]["mean"]
             for name in names]
    bars = axes[1, 1].bar(names, means, color=colors)
    axes[1, 1].set(title="(D) Tempo médio por imagem",
                   ylabel="Segundos", ylim=(0, max(means) * 1.25))
    for bar, value in zip(bars, means):
        axes[1, 1].text(bar.get_x() + bar.get_width() / 2, value,
                        f"{value:.2f} s", ha="center", va="bottom")

    for axis in axes.flat:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.2)
        axis.set_axisbelow(True)
    figure.suptitle(
        "Comparação preliminar dos sistemas A e B na validação", fontsize=14)
    figure.savefig(output.with_suffix(".png"), dpi=300, bbox_inches="tight")
    figure.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(figure)

    summary = {
        "figure_scope": "validacao_preliminar",
        "n_images": systems["A"]["n_images"],
        "systems": {
            name[0]: {
                "candidate_regions": sum(item["n_candidates"] for item in systems[name[0]]["per_image"]),
                "positive_regions": sum(item["n_positive_regions"] for item in systems[name[0]]["per_image"]),
                "no_region_images": status_counts(systems[name[0]])["sem_regioes"],
                "status_counts": status_counts(systems[name[0]]),
                "mean_seconds_per_image": systems[name[0]]["timing_seconds"]["total_seconds"]["mean"],
            }
            for name in names
        },
        "limitations": [
            "As imagens pertencem à validação e participaram da seleção de B.",
            "A referência de pontos não é exaustiva; regiões não associadas não são automaticamente falsos positivos.",
            "Todas as imagens têm referência positiva; não há estimativa de especificidade.",
            "O teste reservado não foi avaliado.",
        ],
    }
    output.with_name(output.name + "_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--complete", action="store_true", help="Gera todas as figuras, CSVs, legendas e índice a partir das execuções auditadas.")
    parser.add_argument("--output-dir", type=Path, help="Pasta nova obrigatória com --complete.")
    parser.add_argument("--result", type=Path, default=ROOT /
                        "experiments/results/comparacao_val_reduced_01.json")
    parser.add_argument("--epochs", type=Path, default=ROOT /
                        "experiments/runs/b_real_cpu_01/epochs.csv")
    parser.add_argument("--output", type=Path, default=ROOT /
                        "tcc/figuras/figura_comparacao_validacao")
    args = parser.parse_args()
    if args.complete:
        if args.output_dir is None:
            parser.error("--complete exige --output-dir com uma pasta nova")
        from src.tcc_reporting import build_report
        summary = build_report(ROOT, args.output_dir)
        print(json.dumps({"figures": len(summary["figures"]), "coverage": summary["coverage"], "output": str(args.output_dir)}, ensure_ascii=False))
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result, epochs = load_inputs(args.result, args.epochs)
    summary = make_figure(result, epochs, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
