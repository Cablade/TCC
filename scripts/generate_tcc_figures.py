"""Gera uma figura-resumo da validação preliminar A x B para o TCC."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]


def load_inputs(result_path: Path, epochs_path: Path) -> tuple[dict, list[dict]]:
    result = json.loads(result_path.read_text(encoding="utf-8-sig"))
    with epochs_path.open(encoding="utf-8-sig", newline="") as stream:
        epochs = list(csv.DictReader(stream))
    return result, epochs


def make_figure(result: dict, epochs: list[dict], output: Path) -> dict:
    systems = result["systems"]
    names = ["A original", "B reduzido"]
    colors = ["#2f6690", "#d1495b"]
    positive = [systems[name[0]]["status_counts"].get("predicao_positiva", 0)
                for name in names]
    no_regions = [systems[name[0]]["n_images"] - value
                  for name, value in zip(names, positive)]
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
    axes[0, 0].set_ylim(0.7, 1.01)
    axes[0, 0].legend(frameon=False)

    # Painel B: decisão por imagem. Todas as imagens desta validação têm referência positiva.
    x = np.arange(len(names))
    axes[0, 1].bar(x, positive, label="Sinalizadas", color=colors)
    axes[0, 1].bar(x, no_regions, bottom=positive,
                   label="Sem regiões", color="#d9d9d9")
    axes[0, 1].set(title="(B) Decisão em 114 imagens",
                   ylabel="Número de imagens", xticks=x, xticklabels=names)
    axes[0, 1].set_ylim(0, 125)
    axes[0, 1].legend(frameon=False)

    # Painel C: propostas e regiões classificadas, sem chamar desconhecidos de negativos.
    candidates = [sum(item["n_candidates"] for item in systems[name[0]]["per_image"])
                  for name in names]
    positive_regions = [sum(item["n_positive_regions"] for item in systems[name[0]]["per_image"])
                        for name in names]
    other_regions = [total - positive for total,
                     positive in zip(candidates, positive_regions)]
    axes[1, 0].bar(x, positive_regions, label="Suspeitas", color=colors)
    axes[1, 0].bar(x, other_regions, bottom=positive_regions,
                   label="Outras propostas", color="#d9d9d9")
    axes[1, 0].set(title="(C) Regiões propostas e classificadas",
                   ylabel="Regiões", xticks=x, xticklabels=names)
    axes[1, 0].set_ylim(0, max(candidates) * 1.08)
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
                "no_region_images": systems[name[0]]["n_images"] - systems[name[0]]["status_counts"].get("predicao_positiva", 0),
                "mean_seconds_per_image": systems[name[0]]["timing_seconds"]["total_seconds"]["mean"],
            }
            for name in names
        },
        "limitations": [
            "As 114 imagens pertencem à validação e participaram da seleção de B.",
            "A referência de pontos não é exaustiva; pontos não associados não são automaticamente falsos positivos.",
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
    parser.add_argument("--result", type=Path, default=ROOT /
                        "experiments/results/comparacao_val_reduced_01.json")
    parser.add_argument("--epochs", type=Path, default=ROOT /
                        "experiments/runs/b_real_cpu_01/epochs.csv")
    parser.add_argument("--output", type=Path, default=ROOT /
                        "tcc/figuras/figura_comparacao_validacao")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result, epochs = load_inputs(args.result, args.epochs)
    summary = make_figure(result, epochs, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
