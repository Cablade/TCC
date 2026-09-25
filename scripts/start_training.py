"""Confere dados e ambiente e inicia B com a mesma configuração conferida."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_training_ready import check_data, check_runtime, resolve_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", type=Path, default=ROOT / "configs/experiment_cpu.json")
    parser.add_argument("--check-only", action="store_true", help="Confere tudo sem iniciar treinamento.")
    args = parser.parse_args()
    config = json.loads(args.experiment.read_text(encoding="utf-8-sig"))
    result = check_data(config)
    result["runtime"] = check_runtime(config.get("require_gpu", False))
    result["ready_to_train"] = result["ready_data"] and result["runtime"]["ok"]
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    result["experiment"] = str(args.experiment.resolve())
    output = ROOT / "data/protocol" / f"readiness_{args.experiment.stem}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in result["checks"]:
        print(f"{'OK' if item['ok'] else 'PENDENTE'}: {item['name']} - {item['detail']}", flush=True)
    for warning in result["warnings"]:
        print(f"OBSERVAÇÃO: {warning}", flush=True)
    print("AMBIENTE: " + json.dumps(result["runtime"], ensure_ascii=False), flush=True)
    if not result["ready_to_train"]:
        print(f"Treino não iniciado. Resolva as pendências em {output}.", flush=True)
        return 2
    if args.check_only:
        print("Dados e ambiente conferidos; treino não iniciado (--check-only).", flush=True)
        return 0
    paths = resolve_paths(config)
    command = [sys.executable, str(ROOT / "scripts/train_model_b.py"),
               "--image-manifest", str(paths["image_manifest"]),
               "--crop-manifest", str(paths["crop_manifest"]),
               "--annotations", str(paths["annotations"]),
               "--config", str(paths["model_config"]),
               "--run-name", config["run_name"], "--output-dir", str(paths["output_dir"])]
    return subprocess.run(command, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
