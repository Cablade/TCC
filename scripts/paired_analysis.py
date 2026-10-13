"""Análise estatística pareada A × B a partir de per_image.csv (docs/plano_estatistico.md).

Uso:
  python scripts/paired_analysis.py \
      --per-image experiments/comparison/<execucao>/per_image.csv \
      --output experiments/comparison/<execucao>/stats.json \
      [--precision-review B=caminho/decisoes_B.csv --precision-review A=caminho/decisoes_A.csv]

Não executa modelos; só lê resultados já gravados. Se a execução for de
desenvolvimento, o relatório leva esse rótulo e não vale como resultado final.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_pipeline import file_sha256  # noqa: E402
from src.paired_stats import (holm_adjust, image_decision_tests, paired_table,  # noqa: E402
                              point_metrics, reviewed_precision, stratified_bootstrap)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def fmt(value, percent=True):
    if value is None:
        return "—"
    return f"{100 * value:.1f}%" if percent else f"{value:.3f}"


def markdown(report):
    lines = [f"# Análise pareada A × B ({report['evaluation_set']})", "",
             f"{report['bootstrap']['n_images']} imagens ({report['bootstrap']['n_positive']} positivas, "
             f"{report['bootstrap']['n_negative']} negativas); bootstrap com "
             f"{report['bootstrap']['n_resamples']} réplicas, semente {report['bootstrap']['seed']}.", "",
             "| Métrica | A | B | B − A (IC 95%) |", "| --- | ---: | ---: | ---: |"]
    m = report["bootstrap"]["metrics"]
    names = {"coverage": "Cobertura dos pontos", "sensitivity": "Imagens positivas sinalizadas",
             "specificity": "Imagens negativas sem alarme",
             "false_regions_per_negative": "Regiões positivas por imagem negativa"}
    for key, label in names.items():
        percent = key != "false_regions_per_negative"
        cell = lambda s: (f"{fmt(m[s]['estimate'], percent)} "
                          f"[{fmt(m[s]['ci_low'], percent)}; {fmt(m[s]['ci_high'], percent)}]")
        lines.append(f"| {label} | {cell(key + '_A')} | {cell(key + '_B')} | {cell(key + '_diff_B_minus_A')} |")
    lines += ["", "| McNemar (decisão por imagem) | Só A acerta | Só B acerta | p exato | p Holm |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for name, test in report["mcnemar"].items():
        holm = (f"{report['mcnemar_holm'][name]:.4g}" if name in report["mcnemar_holm"]
                else "descritivo")
        lines.append(f"| {name} | {test['only_A_correct']} | {test['only_B_correct']} | "
                     f"{test['p_value']:.4g} | {holm} |")
    for system, precision in report.get("precision", {}).items():
        p = precision["metrics"]["precision"]
        lines += ["", f"Precisão revisada de {system}: {fmt(p['estimate'])} "
                      f"[{fmt(p['ci_low'])}; {fmt(p['ci_high'])}], {precision['n_regions']} regiões em "
                      f"{precision['n_images']} imagens ({precision['incerto']} incertas)."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-image", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--evaluation-set", choices=["desenvolvimento", "teste_final"], default="desenvolvimento")
    parser.add_argument("--resamples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20261013)
    parser.add_argument("--precision-review", action="append", default=[],
                        help="SISTEMA=decisoes.csv (colunas image_id,decision) da amostra revisada.")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Saída já existe; escolha outro caminho para preservar a análise anterior.")
    table = paired_table(read_csv(args.per_image))
    tests = image_decision_tests(table)
    # Família pré-declarada: positivas e negativas; "todas" é descritivo.
    family = {k: v["p_value"] for k, v in tests.items() if k in {"positivas", "negativas"}}
    report = {"evaluation_set": args.evaluation_set,
              "per_image_csv": str(args.per_image), "per_image_sha256": file_sha256(args.per_image),
              "bootstrap": stratified_bootstrap(table, point_metrics, n_resamples=args.resamples, seed=args.seed),
              "mcnemar": tests, "mcnemar_holm": holm_adjust(family),
              "notes": ["Unidade de reamostragem: imagem inteira; pareamento A/B preservado.",
                        "Cobertura usa a referência parcial publicada; não estima precisão.",
                        "Erros de execução saem do McNemar e são relatados em excluded_pairs_with_error."]}
    precision = {}
    for item in args.precision_review:
        system, _, path = item.partition("=")
        if system not in {"A", "B"} or not path:
            parser.error("--precision-review espera A=arquivo.csv ou B=arquivo.csv")
        precision[system] = reviewed_precision(read_csv(path), n_resamples=args.resamples, seed=args.seed)
        precision[system]["source"] = path
        precision[system]["source_sha256"] = file_sha256(path)
    if precision:
        report["precision"] = precision
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
