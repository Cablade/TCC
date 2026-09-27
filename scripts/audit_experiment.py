"""Auditoria local de artefatos e inventário de scripts, sem executar modelos."""
from pathlib import Path
import argparse
from collections import Counter
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root):
    def read(path):
        return json.loads((root / path).read_text(encoding="utf-8-sig"))

    result = read("experiments/results/comparacao_val_reduced_01.json")
    paths = dict(manifest="data/splits/experimento/images.csv",
                 annotations="data/annotations/experimento_reference_v2.json",
                 predictions_a="experiments/runs/a_val_02_controlled/predictions.json",
                 predictions_b="experiments/runs/b_val_reduced_01/predictions.json")
    checks = {name: {"path": path, "sha256": digest(root / path),
                     "matches_report": digest(root / path) == result["input_sha256"][name]}
              for name, path in paths.items()}
    meta = read("experiments/runs/b_real_cpu_01/metadata.json")
    with (root / "data/processed/b_real_02_reduced/crops.csv").open(encoding="utf-8-sig", newline="") as f:
        counts = Counter((row["split"], row["label"]) for row in csv.DictReader(f))
    runs = {}
    for name in ("a_val_01", "a_val_02_controlled", "b_val_reduced_01",
                 "a_labimed_neg_20260927", "b_labimed_neg_20260927"):
        path = root / "experiments/runs" / name / "predictions.json"
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        items = payload["images"]
        runs[name] = {"sha256": digest(path), "image_ids": [x["image_id"] for x in items],
                      "status_counts": dict(Counter(x["status"] for x in items)),
                      "positive_regions": sum(r.get("class_id") == 1 for x in items for r in x["regions"])}
    files = [root / "README.md"]
    for folder in ("docs", "scripts", "src", "tests", "notebooks", "dashboard"):
        files.extend(p for p in (root / folder).rglob("*") if p.is_file() and
                     p.suffix in {".md", ".py", ".ipynb", ".html", ".js", ".cmd"})
    contents = {p: p.read_text(encoding="utf-8-sig", errors="replace") for p in files}
    inventory = []
    for script in sorted((root / "scripts").glob("*.py")):
        refs = [p.relative_to(root).as_posix() for p, text in contents.items()
                if p != script and (script.name in text or "scripts." + script.stem in text)]
        inventory.append({"path": script.relative_to(root).as_posix(),
                          "bytes": script.stat().st_size, "text_references": refs})
    expected = [
        "experiments/reviews/ab_external_negatives_20260927/index.html",
        "experiments/reviews/ab_external_negatives_20260927/revisao_negativos_externos_20260927.json",
        "experiments/reviews/b_external_false_positives_20260927_v2/index.html",
        "experiments/reviews/b_external_false_positives_20260927_v2/revisao_falsos_positivos_b_20260927.json",
        "scripts/audit_a_review.py", "scripts/export_ab_review.py",
        "scripts/export_external_false_positives.py", "scripts/record_fp_review.py"]
    pairs = [("validation", "a_val_02_controlled", "b_val_reduced_01"),
             ("external", "a_labimed_neg_20260927", "b_labimed_neg_20260927")]
    paired = {label: {"same_unique_ids": set(runs[a]["image_ids"]) == set(runs[b]["image_ids"])
                     and all(len(runs[n]["image_ids"]) == len(set(runs[n]["image_ids"])) for n in (a, b)),
                     "n_images": len(runs[a]["image_ids"])} for label, a, b in pairs}
    return {"purpose": "local_artifact_audit_not_model_evaluation", "comparison_inputs": checks,
            "checkpoint_B_matches_metadata": digest(root / "experiments/runs/b_real_cpu_01/best.keras") == meta["checkpoint_sha256"],
            "selected_epoch": meta["selected_epoch"], "training_seconds": meta["training_seconds"],
            "crops": {f"{split}/{label}": count for (split, label), count in counts.items()},
            "paired": paired, "runs": runs, "scripts": inventory,
            "missing_expected_artifacts": [p for p in expected if not (root / p).is_file()],
            "limitations": ["Ausência de referência textual não comprova desuso de um script.",
                            "Integridade de artefatos não confirma rótulos biológicos nem independência entre animais."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Escolha um destino novo para preservar a auditoria anterior.")
    report = audit(ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"runs", "scripts"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
