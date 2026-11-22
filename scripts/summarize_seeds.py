"""Resume repetições do B com sementes diferentes (variação de treino, não amostras independentes).

  python scripts/summarize_seeds.py experiments/runs/b_hardneg_s42 experiments/runs/b_hardneg_s123 ...

Lê metadata.json e epochs.csv de cada execução e informa, por semente, a época
selecionada, val_loss, acurácia de validação nessa época e tempo de treino; ao
final, média, desvio padrão, mínimo e máximo. A semente principal declarada no
protocolo continua sendo o modelo avaliado; as demais medem estabilidade.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
import statistics
import sys


def run_summary(run_dir: Path) -> dict:
    meta = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    if meta.get("synthetic") is not False or meta.get("status") != "complete":
        raise ValueError(f"Execução incompleta ou sintética: {run_dir}")
    with (run_dir / "epochs.csv").open(encoding="utf-8-sig", newline="") as stream:
        epochs = list(csv.DictReader(stream))
    selected = int(meta["selected_epoch"])  # 1-based em src/train.py; epochs.csv começa em 0
    row = next(r for r in epochs if int(r["epoch"]) == selected - 1)
    if abs(float(row["val_loss"]) - float(meta["selected_val_loss"])) > 1e-6:
        raise ValueError(f"epochs.csv não confere com metadata.json em {run_dir}")
    return {"run": run_dir.name, "seed": meta["seed"], "selected_epoch": selected, "epochs_run": len(epochs),
            "val_loss": float(row["val_loss"]), "val_accuracy": float(row["val_accuracy"]),
            "training_minutes": meta.get("training_seconds", 0) / 60, "checkpoint_sha256": meta["checkpoint_sha256"]}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    rows = [run_summary(Path(p)) for p in argv]
    if len({r["seed"] for r in rows}) != len(rows):
        raise ValueError("Sementes repetidas entre execuções.")
    print("| Execução | Semente | Época | val_loss | Acurácia val | Minutos |")
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for r in rows:
        print(f"| {r['run']} | {r['seed']} | {r['selected_epoch']} | {r['val_loss']:.4f} | "
              f"{100 * r['val_accuracy']:.2f}% | {r['training_minutes']:.1f} |")
    for key in ("val_loss", "val_accuracy"):
        values = [r[key] for r in rows]
        sd = statistics.stdev(values) if len(values) > 1 else 0.0
        print(f"{key}: média {statistics.mean(values):.4f}, DP {sd:.4f}, "
              f"mín {min(values):.4f}, máx {max(values):.4f} (n={len(values)} sementes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
