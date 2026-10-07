"""Gera as figuras atuais de A original e B atual para o TCC."""
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


def current_comparison():
    setup=ROOT/'configs/comparison_a_vs_b.json'
    return ROOT/json.loads(setup.read_text('utf-8-sig'))['output_dir'] if setup.exists() else ROOT/'experiments/comparison/a_vs_b'


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


def main():
    parser=argparse.ArgumentParser(description="Gera figuras de A original e B atual a partir de inferências concluídas.")
    parser.add_argument("--comparison",type=Path,default=current_comparison())
    parser.add_argument('--all',action='store_true',help='Atualiza as avaliações disponíveis dos dois checkpoints atuais e o índice de figuras.')
    args=parser.parse_args()
    from src.tcc_reporting import build_report
    comparisons = [args.comparison.resolve()]
    if args.all:
        current = current_comparison()
        active_protocol = json.loads((current/'protocol.json').read_text('utf-8-sig'))
        comparisons = [current]
        for candidate in sorted((ROOT/'experiments/comparison').iterdir()):
            protocol_path = candidate/'protocol.json'
            if candidate == current or not protocol_path.is_file():
                continue
            protocol = json.loads(protocol_path.read_text('utf-8-sig'))
            if all(protocol['checkpoint'][system]['sha256'] == active_protocol['checkpoint'][system]['sha256']
                   for system in ('A', 'B')):
                comparisons.append(candidate)
    for comparison in comparisons:
        protocol=json.loads((comparison/'protocol.json').read_text('utf-8-sig'))
        if protocol['evaluation']=='development_robustness_only':
            from scripts.compare_robustness import summarize
            summarize(comparison)
        elif protocol['evaluation']=='external_development_only':
            from scripts.compare_external_negatives import summarize
            summarize(comparison)
        else:
            report=build_report(ROOT,comparison)
            print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
    if args.all:
        out = ROOT/'tcc/figuras'
        report = json.loads((current_comparison()/'report.json').read_text('utf-8-sig'))
        groups = report['class_summary']
        description = f"{groups['positive']['A']['n_images']} imagens positivas e {groups['negative']['A']['n_images']} imagens negativas"
        timing = report['protocol']['timing']
        cards = []
        for comparison in comparisons[1:]:
            page_path = out/comparison.name/'index.html'
            if page_path.is_file():
                from html import escape
                label = escape(comparison.name)
                cards.append(f'<article><h2>Avaliação adicional: {label}</h2><a href="{label}/index.html">Abrir avaliação</a></article>')
        page = f'''<!doctype html>
<html lang="pt-BR">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Figuras A × B para o TCC</title>
<style>
body {{font:17px system-ui;max-width:900px;margin:40px auto;padding:20px;background:#edf2f5;color:#203548;line-height:1.6}}
article {{background:white;border-radius:10px;padding:20px;margin:20px 0}}
a {{color:#175c87}}
</style>
<h1>Comparações A original × B atual</h1>
<p>Comparação dos dois modelos</p>
<article><h2>Comparação atual: {report['paired_images']} originais</h2>
<p>{description}. Mesmos IDs para A e B; cobertura positiva, falsos alarmes e tempo. {timing}</p>
<a href="{current_comparison().name}/index.html">Abrir comparação atual</a></article>
{''.join(cards)}
<p>As 105 imagens do teste final permanecem reservadas.</p>
<p>Resultados antigos preservados no <a href="../../archive/README.md">arquivo histórico</a>.</p>
</html>'''
        (out/'index.html').write_text(page,encoding='utf-8')
        print('INDEX '+str(out/'index.html'))
    return 0


if __name__=="__main__": raise SystemExit(main())
