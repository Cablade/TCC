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
    parser.add_argument('--all',action='store_true',help='Atualiza as três avaliações concluídas e cria a página de acesso às figuras.')
    args=parser.parse_args()
    from src.tcc_reporting import build_report
    comparisons=([current_comparison(),ROOT/'experiments/comparison/robustez_a_vs_b',ROOT/'experiments/comparison/barcelona_a_vs_b']
                 if args.all else [args.comparison.resolve()])
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
        out=ROOT/'tcc/figuras'
        report=json.loads((current_comparison()/'report.json').read_text('utf-8-sig'))
        cohorts=report['protocol']['cohorts']; expanded='barcelona_negative' in cohorts
        link=current_comparison().name
        comparison_text=(f"{cohorts['positive_val']} positivas e {cohorts['kaggle_negative_val']} negativas Kaggle"
                         +(f" + {cohorts['barcelona_negative']} Barcelona." if expanded else '.'))
        state=('20 imagens Barcelona reservadas para os negativos do próximo treino; 180 usadas na comparação. O B ainda não foi retreinado.'
               if expanded else 'Nenhuma das 200 imagens Barcelona participa do treino.')
        page=f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Figuras A × B para o TCC</title><style>body{{font:17px system-ui;max-width:900px;margin:40px auto;padding:20px;background:#edf2f5;color:#203548;line-height:1.6}}article{{background:white;border-radius:10px;padding:20px;margin:20px 0}}a{{color:#175c87}}</style><h1>Comparações A original × B atual</h1><p>Somente dois modelos. {state} Fontes apresentadas separadamente; desenvolvimento já examinado, sem independência de pacientes/lâminas demonstrada.</p><article><h2>Comparação atual — {report['paired_images']} originais</h2><p>{comparison_text} Mesmos IDs para A e B; cobertura positiva, falsos alarmes e tempo herdado. Resultados anteriores ao próximo treino.</p><a href="{link}/index.html">Abrir comparação atual</a></article><article><h2>Robustez nas duas classes — lote anterior</h2><p>114 positivas e 73 negativas Kaggle, com rotação 90°, espelho horizontal e brilho × 0,85: 561 versões. Relatório sobre 187 originais; Barcelona não está neste ensaio já concluído. Versões não contam como novos campos independentes.</p><a href="robustez_a_vs_b/index.html">Abrir robustez</a></article><article><h2>Histórico: diagnóstico das 200 Barcelona</h2><p>Diagnóstico anterior à reserva 20/180, com células individuais enquadradas. Não usar as 200 como denominador da comparação atual.</p><a href="barcelona_a_vs_b/index.html">Abrir diagnóstico anterior</a></article><article><h2>Histórico: comparação original de 187 imagens</h2><a href="a_vs_b/index.html">Abrir lote anterior sem Barcelona</a></article><p>As 105 imagens do teste final permanecem reservadas. LABIMED permanece no histórico, excluído após inspeção dos resultados a pedido do autor.</p></html>'''
        (out/'index.html').write_text(page,encoding='utf-8')
        print('INDEX '+str(out/'index.html'))
    return 0


if __name__=="__main__": raise SystemExit(main())
