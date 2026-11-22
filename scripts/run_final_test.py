"""Abertura única do teste final (passo 9 do roteiro de correção do viés).

Orquestra, sem alterar nenhum método congelado:
1. confere que todos os arquivos de data/protocol/protocolo_congelado.json mantêm o SHA-256;
2. monta o manifesto e a referência das 105 imagens de teste (pontos publicados);
3. roda A e B com --split test, com as mesmas opções da comparação de desenvolvimento;
4. gera per_image.csv no formato de src/tcc_reporting.py: positivas do teste + os 253
   negativos de outra aquisição já avaliados com os MESMOS checkpoints congelados
   (resultado auxiliar previsto no plano, seção 2), reaproveitados sem nova inferência;
5. grava data/protocol/teste_aberto.json; uma segunda execução é recusada.

A análise (scripts/paired_analysis.py --evaluation-set teste_final) e a amostra de precisão
(scripts/sample_precision_review.py sample --final-test) rodam depois, com os scripts congelados.

Exemplo:
  python scripts/run_final_test.py --output-dir experiments/final_test_20261014 ^
      --dev-comparison experiments/comparison/a_vs_b_hardneg_20261013
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROTOCOL = ROOT / "data/protocol/protocolo_congelado.json"
OPENED = ROOT / "data/protocol/teste_aberto.json"
PRIMARY = ROOT / "data/splits/experimento/images.csv"
REFERENCE = ROOT / "data/annotations/experimento_reference_v2.json"
MODEL_A = ROOT / "models/model_a/model_trained.keras"
MODEL_B = ROOT / "experiments/runs/b_atual/best.keras"
EXPECTED_IMAGES, EXPECTED_POINTS = 105, 441
NEGATIVE_COHORTS = {"kaggle_negative_val": 73, "barcelona_negative": 180}
PER_IMAGE_FIELDS = ["image_id", "cohort", "system", "status", "original_decision", "candidates",
                    "classified_regions", "positive_regions", "false_positive_regions", "reference_points",
                    "matched_proposals", "matched_positive_regions", "algorithm_seconds", "error", "image_class"]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def check_frozen():
    frozen = read_json(PROTOCOL)
    if frozen.get("test_opened") is not False:
        raise ValueError("Protocolo congelado não registra teste fechado.")
    changed = []
    for name, digest in frozen["sha256"].items():
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        if sha(path) != digest:
            changed.append(name)
    if changed:
        raise ValueError(f"Arquivos congelados alterados (desvio de protocolo): {changed}")
    if frozen["sha256"]["models/model_a/model_trained.keras"] != sha(MODEL_A):
        raise ValueError("A difere do congelado.")
    if sha(MODEL_B) != frozen["sha256"][next(k for k in frozen["sha256"] if k.replace("\\", "/").endswith("b_atual/best.keras"))]:
        raise ValueError("B difere do congelado.")
    return frozen


def prepare_test(output):
    from src import data_protocol as dp

    rows = [r for r in dp.read_manifest(PRIMARY) if r["split"] == "test" and not r.get("duplicate_of")]
    if len(rows) != EXPECTED_IMAGES:
        raise ValueError(f"Teste com {len(rows)} imagens; esperado {EXPECTED_IMAGES}.")
    refs = dp.load_annotations(REFERENCE, dp.read_manifest(PRIMARY))
    entries = []
    for row in rows:
        entry = refs[row["image_id"]]
        if entry.get("whole_image_label") != 1:
            raise ValueError(f"Imagem de teste sem rótulo positivo: {row['image_id']}")
        entries.append(entry)
        row["cohort"] = "positive_test"
    points = sum(len(e.get("positives", [])) for e in entries)
    if points != EXPECTED_POINTS:
        raise ValueError(f"Teste com {points} pontos; esperado {EXPECTED_POINTS}.")
    output.mkdir(parents=True, exist_ok=False)
    dp.write_manifest(rows, output / "images.csv", list(dict.fromkeys(k for r in rows for k in r)))
    payload = {"schema_version": 1, "coordinate_convention": "xyxy_half_open", "images": entries}
    dp.validate_annotations(payload, rows)
    save_json(output / "annotations.json", payload)
    return rows


def run_models(output):
    environment = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    for key in ("A", "B"):
        script = "run_model_a.py" if key == "A" else "run_model_b.py"
        command = [sys.executable, "-u", str(ROOT / "scripts" / script), "--manifest", str(output / "images.csv"),
                   "--split", "test", "--output-dir", str(output / key)]
        command += (["--model", str(MODEL_A), "--threads", "2"] if key == "A"
                    else ["--checkpoint", str(MODEL_B), "--compiled", "--image-mode", "none"])
        print("START " + key, flush=True)
        with (output / f"{key}.stdout.log").open("w", encoding="utf-8") as out, \
                (output / f"{key}.stderr.log").open("w", encoding="utf-8") as err:
            result = subprocess.run(command, cwd=ROOT, env=environment, stdout=out, stderr=err)
        if result.returncode:
            raise RuntimeError(f"{key} falhou (código {result.returncode}); ver logs.")
        print("DONE " + key, flush=True)


def build_per_image(output, rows, dev_dir):
    from src import data_protocol as dp
    from src.detection_evaluation import load_prediction_run
    from src.tcc_reporting import cohort_metrics, write_csv

    annotations = dp.load_annotations(output / "annotations.json", rows)
    per_image, summary = [], {}
    for system, model in (("A", MODEL_A), ("B", MODEL_B)):
        entries, origin = load_prediction_run(output / system / "predictions.json", system, "test",
                                              sha(output / "images.csv"))
        artifact = origin["artifact"]
        if artifact.get("checkpoint_sha256", artifact.get("sha256")) != sha(model):
            raise ValueError(f"Previsões de {system} não vêm do checkpoint congelado.")
        by_id = {e["image_id"]: e for e in entries}
        if set(by_id) != {r["image_id"] for r in rows} or len(by_id) != len(entries):
            raise ValueError(f"IDs de {system} não correspondem ao teste.")
        metrics, details = cohort_metrics(rows, annotations, [by_id[r["image_id"]] for r in rows])
        summary[system] = {k: v for k, v in metrics.items()}
        for r in details:
            per_image.append(dict(
                image_id=r["image_id"], cohort="positive_test", system=system, status=r["status"],
                original_decision=r["original_decision"], candidates=r["n_candidates"],
                classified_regions=r["n_regions"], positive_regions=r["n_positive_regions"],
                false_positive_regions=r["false_positive_regions"], reference_points=r["reference_points"],
                matched_proposals=r["matched_proposals"], matched_positive_regions=r["matched_positive_regions"],
                algorithm_seconds=r["timings"].get("total_seconds"), error=r.get("error") or "",
                image_class="positive"))
    # Negativos de outra aquisição: mesmos checkpoints congelados, já avaliados no desenvolvimento.
    dev_protocol = read_json(dev_dir / "protocol.json")
    for system, model in (("A", MODEL_A), ("B", MODEL_B)):
        if dev_protocol["checkpoint"][system]["sha256"] != sha(model):
            raise ValueError(f"Comparação de desenvolvimento usou outro checkpoint de {system}.")
    with (dev_dir / "per_image.csv").open(encoding="utf-8-sig", newline="") as stream:
        dev_rows = [r for r in csv.DictReader(stream) if r["cohort"] in NEGATIVE_COHORTS]
    for cohort, n in NEGATIVE_COHORTS.items():
        for system in ("A", "B"):
            got = sum(r["cohort"] == cohort and r["system"] == system for r in dev_rows)
            if got != n:
                raise ValueError(f"{cohort}/{system}: {got} linhas; esperado {n}.")
    if any(r["image_class"] != "negative" for r in dev_rows):
        raise ValueError("Linha não negativa entre os negativos reaproveitados.")
    per_image += [{k: r.get(k, "") for k in PER_IMAGE_FIELDS} for r in dev_rows]
    write_csv(output / "per_image.csv", per_image)
    save_json(output / "summary_test_positives.json", summary)
    return summary, len(dev_rows) // 2


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--dev-comparison", required=True, type=Path)
    parser.add_argument("--confirm", required=True, help='Digite "abrir teste" para confirmar a abertura única.')
    args = parser.parse_args()
    if args.confirm != "abrir teste":
        parser.error('Confirmação ausente: use --confirm "abrir teste".')
    if OPENED.exists():
        raise FileExistsError("Teste final já foi aberto; nova abertura não é permitida.")
    frozen = check_frozen()
    output = args.output_dir.resolve()
    started = datetime.now(timezone.utc).isoformat()
    # O registro de abertura é gravado antes de ler o teste: mesmo se algo falhar, a abertura fica registrada.
    save_json(OPENED, {"opened_at": started, "status": "em_execucao", "output_dir": str(output),
                       "protocol_sha256": sha(PROTOCOL), "protocol_frozen_at": frozen["frozen_at"]})
    rows = prepare_test(output)
    run_models(output)
    summary, negatives = build_per_image(output, rows, args.dev_comparison.resolve())
    record = read_json(OPENED)
    record.update(status="concluido", finished_at=datetime.now(timezone.utc).isoformat(),
                  test_images=len(rows), auxiliary_negative_images=negatives,
                  per_image_sha256=sha(output / "per_image.csv"),
                  predictions_sha256={s: sha(output / s / "predictions.json") for s in ("A", "B")})
    save_json(OPENED, record)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
