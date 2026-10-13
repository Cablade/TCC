"""Congela o protocolo antes da abertura do teste de 105 imagens.

Registra o SHA-256 de tudo o que define a avaliação final (plano estatístico,
metodologia, scripts de análise, checkpoints, configuração, manifestos e
anotações) em data/protocol/protocolo_congelado.json. Recusa sobrescrever um
congelamento existente e recusa congelar sem a evidência das etapas anteriores.

  python scripts/freeze_protocol.py ^
      --checkpoint-b experiments/runs/b_atual/best.keras ^
      --precision-validation data/annotations/precision_B_val/precision.json ^
      --model-a-check experiments/validation/model_a_original_domain_20261013/summary.json ^
      --seeds experiments/runs/b_hardneg_s42 experiments/runs/b_hardneg_s123 ... ^
      --confirm "congelar"
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FROZEN_FILES = [
    "docs/plano_estatistico.md", "docs/metodologia.md",
    "src/paired_stats.py", "src/detection_evaluation.py", "src/model_a.py", "src/model_b.py",
    "src/segmentation.py", "src/data_pipeline.py",
    "scripts/paired_analysis.py", "scripts/sample_precision_review.py", "scripts/run_model_a.py",
    "scripts/run_model_b.py", "scripts/compare_model_versions.py",
    "data/splits/experimento/test.csv", "models/model_a/model_trained.keras",
]
OUTPUT = ROOT / "data/protocol/protocolo_congelado.json"


def main():
    from src.data_pipeline import file_sha256

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checkpoint-b", required=True, type=Path)
    parser.add_argument("--precision-validation", required=True, type=Path)
    parser.add_argument("--model-a-check", required=True, type=Path)
    parser.add_argument("--seeds", nargs="+", required=True, type=Path)
    parser.add_argument("--extra", nargs="*", default=[], help="Outros arquivos a congelar (configs, manifestos).")
    parser.add_argument("--confirm", required=True, help='Digite "congelar" para confirmar.')
    args = parser.parse_args()
    if args.confirm != "congelar":
        parser.error('Confirmação ausente: use --confirm "congelar".')
    if OUTPUT.exists():
        raise FileExistsError("Protocolo já congelado; mudanças agora são desvios e devem ser relatadas.")
    run_dir = args.checkpoint_b.parent
    meta = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    if meta.get("synthetic") is not False or meta.get("status") != "complete":
        raise ValueError("Checkpoint do B não vem de treino real concluído.")
    if meta["checkpoint_sha256"] != file_sha256(args.checkpoint_b):
        raise ValueError("Checkpoint difere do selecionado no treino.")
    if len(args.seeds) < 2:
        raise ValueError("Informe as execuções de todas as sementes declaradas.")
    files = FROZEN_FILES + [str(p) for p in args.extra] + [
        str(args.checkpoint_b), str(run_dir / "config.json"), str(args.precision_validation), str(args.model_a_check)]
    hashes = {}
    for name in files:
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        if not path.exists():
            raise FileNotFoundError(f"Arquivo a congelar ausente: {name}")
        hashes[name] = file_sha256(path)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    except OSError:
        commit, dirty = None, None
    record = {"frozen_at": datetime.now(timezone.utc).isoformat(), "git_commit": commit, "git_dirty": dirty,
              "model_b_run": meta["run_name"], "model_b_seed": meta["seed"],
              "seed_runs": [str(p) for p in args.seeds], "decision_rule_b": "any argmax(scores)==1",
              "bootstrap": {"resamples": 10000, "seed": 20261013, "confidence": 0.95},
              "precision_sample": {"n": 200, "seed": 20261013, "blind": True},
              "mcnemar_family": ["positivas_teste", "negativos_outra_aquisicao"], "alpha": 0.05,
              "test_opened": False, "sha256": hashes}
    OUTPUT.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Protocolo congelado em {OUTPUT} ({len(hashes)} arquivos).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
