"""Figuras descritivas rastreáveis; não executa modelos nem abre o teste reservado."""
from collections import Counter
import csv
import hashlib
import html
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from PIL import Image

from .data_protocol import read_image_bytes
from .detection_evaluation import load_prediction_run, match_one_to_one

COLORS = ["#28628e", "#c64d50"]
NAMES = ["A original", "B reduzido"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def paired_ids(a, b, expected):
    ids = []
    for rows in (a, b):
        current = [x["image_id"] for x in rows]
        if len(current) != len(set(current)) or set(current) != set(expected):
            raise ValueError("IDs ausentes, extras ou duplicados no pareamento.")
        ids.append(current)
    return sorted(expected)


def coverage_rows(predictions, annotations):
    output = []
    for system, items in predictions.items():
        for image_id in sorted(items):
            item = items[image_id]
            refs = annotations[image_id]["positives"]
            boxes = [r["bbox"] for r in item["regions"] if r["class_id"] == 1]
            proposals = [r["bbox"] for r in item["candidates"]]
            output.append(dict(system=system, image_id=image_id, reference_points=len(refs),
                               matched_proposals=len(match_one_to_one(proposals, refs)["pairs"]),
                               matched_positive_regions=len(match_one_to_one(boxes, refs)["pairs"])))
    return output


def build_report(root, output):
    if output.exists():
        raise FileExistsError("Escolha pasta nova para preservar a edição anterior.")
    manifest = root / "data/splits/experimento/images.csv"
    external_manifest = root / "data/protocol/labimed_external_20260927/images.csv"
    annotations_path = root / "data/annotations/experimento_reference_v2.json"
    comparison_path = root / "experiments/results/comparacao_val_reduced_01.json"
    epochs_path = root / "experiments/runs/b_real_cpu_01/epochs.csv"
    metadata_path = root / "experiments/runs/b_real_cpu_01/metadata.json"
    review_path = root / "experiments/reviews/b_external_false_positives_20260927_v2/review_reconstructed.json"
    field_review_path = root / "experiments/reviews/ab_external_negatives_20260927/review_reconstructed.json"
    inputs = [manifest, external_manifest, annotations_path, comparison_path, epochs_path, metadata_path,
              review_path, field_review_path]
    images = read_csv(manifest)
    external_images = read_csv(external_manifest)
    refs = {x["image_id"]: x for x in read_json(annotations_path)["images"]}
    val_ids = {x["image_id"] for x in images if x["split"] == "val"}
    external_ids = {x["image_id"] for x in external_images}
    predictions, external = {}, {}
    source_paths = {}
    for system, val_name, ext_name in [("A", "a_val_02_controlled", "a_labimed_neg_20260927"),
                                       ("B", "b_val_reduced_01", "b_labimed_neg_20260927")]:
        for name, dest, split, source_manifest in [(val_name, predictions, "val", manifest),
                                                   (ext_name, external, "development", external_manifest)]:
            path = root / "experiments/runs" / name / "predictions.json"
            entries, provenance = load_prediction_run(path, system, split, sha(source_manifest))
            inputs.append(path)
            dest[system] = {row["image_id"]: row for row in entries}
            # Verificar antes que dicionários possam ocultar duplicatas.
            if len(dest[system]) != len(entries):
                raise ValueError("Predições duplicadas.")
            source_paths[name] = path
    ordered = paired_ids(list(predictions["A"].values()), list(predictions["B"].values()), val_ids)
    paired_ids(list(external["A"].values()), list(external["B"].values()), external_ids)
    comparison = read_json(comparison_path)
    for key, path in {"manifest": manifest, "annotations": annotations_path,
                      "predictions_a": source_paths["a_val_02_controlled"],
                      "predictions_b": source_paths["b_val_reduced_01"]}.items():
        if comparison["input_sha256"][key] != sha(path):
            raise ValueError("Relatório não corresponde às entradas atuais.")
    meta = read_json(metadata_path)
    checkpoint = root / "experiments/runs/b_real_cpu_01/best.keras"
    if sha(checkpoint) != meta["checkpoint_sha256"]:
        raise ValueError("Checkpoint B alterado.")
    inputs.append(checkpoint)
    epochs = read_csv(epochs_path)
    crops_path = root / "data/processed/b_real_02_reduced/crops.csv"
    inputs.append(crops_path)
    crops = read_csv(crops_path)
    recovered = read_json(review_path)
    field_review = read_json(field_review_path)
    if (recovered["predictions_B_sha256"] != sha(source_paths["b_labimed_neg_20260927"])
            or recovered["manifest_sha256"] != sha(external_manifest)
            or field_review["manifest_sha256"] != sha(external_manifest)
            or {x["image_id"] for x in field_review["images"]} != external_ids):
        raise ValueError("Revisão reconstruída não corresponde aos dados externos.")
    output.mkdir(parents=True)
    figures = []

    def save(fig, name, caption):
        for ax in fig.axes:
            if ax.axison:
                ax.spines[["top", "right"]].set_visible(False)
        fig.savefig(output / (name + ".png"), dpi=230, bbox_inches="tight")
        fig.savefig(output / (name + ".pdf"), bbox_inches="tight")
        plt.close(fig)
        figures.append({"name": name, "caption": caption})

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), layout="constrained")
    splits = Counter(x["split"] for x in images)
    bars = axes[0].bar(["Treino", "Validação", "Teste reservado"], [splits[k] for k in ("train", "val", "test")], color=[COLORS[0], COLORS[1], "#8d969e"])
    axes[0].bar_label(bars)
    axes[0].set(title="Imagens originais por partição", ylabel="Imagens", ylim=(0, max(splits.values()) * 1.16))
    crop_counts = Counter((x["split"], x["label"]) for x in crops)
    for i, label in enumerate(("1", "0")):
        values = [crop_counts[(s,label)] for s in ("train", "val")]
        bars = axes[1].bar(np.arange(2) + (i-.5)*.36, values, .36, label="Positivos" if label == "1" else "Negativos", color=COLORS[i])
        axes[1].bar_label(bars)
    axes[1].set(title="Recortes utilizados por B", xticks=[0,1], xticklabels=["Treino", "Validação"], ylabel="Recortes", ylim=(0,max(crop_counts.values())*1.25))
    axes[1].legend(frameon=False)
    save(fig, "01_composicao", "Divisão por imagem original. Recortes não são unidades biológicas independentes. O teste aparece apenas como contagem do manifesto; seus pixels não foram abertos.")

    fig, ax = plt.subplots(figsize=(7, 4.8), layout="constrained")
    bottom = np.zeros(2)
    for status, label, color in [("predicao_positiva", "Sinalizada", COLORS[0]), ("sem_regioes", "Sem regiões", "#cad2d9"),
                                  ("regioes_sem_predicao_positiva", "Regiões sem suspeita", "#7ea589"), ("erro", "Erro", COLORS[1])]:
        vals = [sum(x["status"] == status for x in predictions[s].values()) for s in ("A", "B")]
        if sum(vals):
            ax.bar(NAMES, vals, bottom=bottom, label=label, color=color)
            for i,v in enumerate(vals):
                if v: ax.text(i, bottom[i]+v/2, str(v), ha="center", va="center")
        bottom += vals
    ax.set(title="Estados de execução na validação", ylabel="Imagens", ylim=(0, len(ordered)*1.22))
    ax.legend(frameon=False, loc="upper left")
    save(fig, "02_estados", "Estados nas mesmas 114 imagens positivas de validação. Sinalizar um campo não comprova localizar seu parasita; não há especificidade estimável neste conjunto.")

    coverage = coverage_rows(predictions, refs)
    write_csv(output / "cobertura_por_imagem.csv", coverage)
    coverage_totals = {s: {key: sum(x[key] for x in coverage if x["system"] == s) for key in ("reference_points", "matched_proposals", "matched_positive_regions")} for s in ("A","B")}
    fig, ax = plt.subplots(figsize=(8, 4.7), layout="constrained")
    for i,key in enumerate(("matched_proposals", "matched_positive_regions")):
        vals = [coverage_totals[s][key] for s in ("A","B")]
        bars = ax.bar(np.arange(2)+(i-.5)*.35, vals, .35, label=["Cobertos pelas propostas", "Cobertos pelas regiões positivas"][i], color=COLORS[i])
        ax.bar_label(bars)
    total_points = coverage_totals["A"]["reference_points"]
    ax.axhline(total_points, linestyle="--", color="#525c66", label=f"{total_points} pontos publicados")
    ax.set(xticks=[0,1], xticklabels=NAMES, ylabel="Pontos associados uma única vez", ylim=(0,total_points*1.35), title="Cobertura dos pontos disponíveis")
    ax.legend(frameon=False, loc="upper left")
    save(fig, "03_cobertura", "Associação um a um de cardinalidade máxima; ponto contido na caixa com extremos direito/inferior exclusivos. Referência parcial: cobertura dos pontos disponíveis, não sensibilidade geral. Regiões sem associação não são automaticamente falsos positivos.")

    per_image = []
    for cohort, dataset in (("validacao", predictions), ("externos", external)):
        for s in ("A", "B"):
            for image_id in sorted(dataset[s]):
                r = dataset[s][image_id]
                per_image.append(dict(cohort=cohort, system=s, image_id=image_id, status=r["status"],
                    candidates=len(r["candidates"]), positive_regions=sum(z["class_id"]==1 for z in r["regions"]),
                    seconds=r["timings"]["total_seconds"],
                    localization_seconds=r["timings"].get("localization_seconds"),
                    classification_seconds=r["timings"].get("classification_seconds"),
                    preprocessing_seconds=r["timings"].get("preprocessing_seconds")))
    write_csv(output / "resultados_por_imagem.csv", per_image)
    val = {s: [r for r in per_image if r["cohort"] == "validacao" and r["system"] == s] for s in ("A", "B")}
    fig, axes = plt.subplots(1,2, figsize=(11,4.5), layout="constrained")
    for ax, key, title in zip(axes, ("candidates", "positive_regions"), ("Propostas por imagem", "Regiões positivas por imagem")):
        ax.boxplot([[r[key] for r in val[s]] for s in ("A","B")], labels=NAMES, showfliers=False)
        for i,s in enumerate(("A","B"),1):
            vals = [r[key] for r in val[s]]
            ax.scatter(i+np.linspace(-.14,.14,len(vals)), vals, color=COLORS[i-1], s=10, alpha=.5)
        ax.set(title=title, ylabel="Regiões", ylim=(0,None))
    save(fig, "04_candidatos", "Cada ponto é uma imagem de validação. Caixas mostram quartis e mediana; pontos incluem os extremos. O volume de regiões não equivale ao número de parasitas.")

    fig, axes = plt.subplots(1,3,figsize=(13,4.3),layout="constrained")
    times = [[r["seconds"] for r in val[s]] for s in ("A","B")]
    axes[0].boxplot(times, labels=NAMES)
    axes[0].set(title="Tempo por imagem", ylabel="Segundos", ylim=(0,None))
    axes[1].scatter(times[0], times[1], s=16, alpha=.7, color=COLORS[1])
    maximum = max(max(times[0]), max(times[1]))*1.05
    axes[1].plot([0,maximum],[0,maximum],"--",color="#666",label="Tempos iguais")
    axes[1].set(title="Mesmas imagens pareadas", xlabel="A (s)", ylabel="B (s)", xlim=(0,maximum), ylim=(0,maximum))
    axes[1].legend(frameon=False)
    bottoms=np.zeros(2)
    for key,label,color in [("localization_seconds","Localização",COLORS[0]),("classification_seconds","Classificação",COLORS[1]),("preprocessing_seconds","Pré-processamento","#dba650")]:
        values=[sum(r[key] or 0 for r in val[s]) for s in ("A","B")]
        axes[2].bar(NAMES,values,bottom=bottoms,label=label,color=color)
        bottoms+=values
    axes[2].set(title="Tempo acumulado por etapa", ylabel="Segundos")
    axes[2].legend(frameon=False)
    save(fig,"05_tempos","Tempos do algoritmo nas execuções registradas, sem exportação de imagens. Pareamento por image_id; inclui primeiras chamadas. Não é benchmark repetido com aquecimento. Etapas registradas podem não somar exatamente o total por haver overhead.")

    fig,axes=plt.subplots(1,2,figsize=(10,4.5),layout="constrained")
    n_external=len(external_ids)
    alarms=[sum(r["status"]=="predicao_positiva" for r in external[s].values()) for s in ("A","B")]
    bars=axes[0].bar(NAMES,alarms,color=COLORS)
    axes[0].bar_label(bars,labels=[f"{n}/{n_external}" for n in alarms])
    axes[0].set(title="Campos externos sinalizados",ylabel="Campos",ylim=(0,n_external*1.2))
    axes[1].boxplot([[sum(r["class_id"]==1 for r in item["regions"]) for _,item in sorted(external[s].items())] for s in ("A","B")],labels=NAMES)
    axes[1].set(title="Regiões positivas por campo externo",ylabel="Regiões",ylim=(0,None))
    donors=len({r["case_id"] for r in external_images})
    slides=len({r["slide_id"] for r in external_images})
    save(fig,"06_externos",f"Diagnóstico separado: {n_external} campos LABIMED humanos, {donors} caso(s), {slides} lâminas. Ausência de parasita visível relatada por Caio; registro reconstruído da conversa. Não são pacientes negativos independentes nem teste intocado. Não misturar à validação murina.")

    fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout="constrained")
    epoch=[int(r["epoch"])+1 for r in epochs]
    for ax,key,title in [(axes[0],"accuracy","Acurácia nos recortes"),(axes[1],"loss","Perda de treinamento")]:
        for prefix,label,color in [("","Treino",COLORS[0]),("val_","Validação",COLORS[1])]:
            ax.plot(epoch,[float(r[prefix+key]) for r in epochs],label=label,color=color)
        ax.axvline(meta["selected_epoch"],color="#666",linestyle="--",label=f'Época selecionada: {meta["selected_epoch"]}')
        ax.set(title=title,xlabel="Época",ylabel=key)
        ax.legend(frameon=False,fontsize=8)
    axes[0].set_ylim(0,1.03)
    save(fig,"07_treinamento","Histórico exclusivo do B reduzido. Checkpoint escolhido pela menor val_loss, não pela maior acurácia. Há 740 recortes positivos e 38 negativos na validação; acurácia isolada é insuficiente. Não há histórico comparável de treinamento de A.")

    # Seleção determinística de exemplos, não amostra representativa de desempenho.
    examples=[]
    for category in ("A_suspeita_sem_ponto", "B_suspeita_com_ponto", "B_ponto_sem_deteccao"):
        system="A" if category.startswith("A") else "B"
        for image_id in ordered:
            item=predictions[system][image_id]
            positive=[r for r in item["regions"] if r["class_id"]==1]
            match=match_one_to_one([r["bbox"] for r in positive],refs[image_id]["positives"])
            if category=="A_suspeita_sem_ponto" and match["unmatched_predictions"]:
                box=positive[match["unmatched_predictions"][0]]["bbox"]; point=None
            elif category=="B_suspeita_com_ponto" and match["pairs"]:
                pair=match["pairs"][0]; box=positive[pair["prediction_index"]]["bbox"]; point=refs[image_id]["positives"][pair["reference_index"]]["point"]
            elif category=="B_ponto_sem_deteccao" and match["unmatched_references"]:
                point=refs[image_id]["positives"][match["unmatched_references"][0]]["point"]
                row=next(r for r in images if r["image_id"]==image_id)
                box=[max(0,int(point[0])-112),max(0,int(point[1])-112),min(int(row["width"]),int(point[0])+112),min(int(row["height"]),int(point[1])+112)]
            else: continue
            examples.append(dict(category=category,image_id=image_id,bbox=box,point=point))
            break
    first=min(recovered["regions"],key=lambda r:r["id"])
    examples.append(dict(category="B_externo_sem_parasita_visivel",image_id=first["image_id"],bbox=first["bbox"],point=None))
    all_images={r["image_id"]:r for r in images+external_images}
    labels={"A_suspeita_sem_ponto":"A: suspeita sem ponto associado", "B_suspeita_com_ponto":"B: suspeita associada a ponto", "B_ponto_sem_deteccao":"B: ponto sem região positiva associada", "B_externo_sem_parasita_visivel":"B externo: sem parasita visível (Caio)"}
    for i,item in enumerate(examples,1):
        row=all_images[item["image_id"]]
        if row["split"] not in ("val","development"):
            raise ValueError("Proibido abrir imagem de teste para ilustração.")
        raw=read_image_bytes(row["path"])
        if hashlib.sha256(raw).hexdigest()!=row["sha256"]: raise ValueError("Imagem fonte alterada.")
        image=np.array(Image.open(io.BytesIO(raw)).convert("RGB"))
        x1,y1,x2,y2=map(int,item["bbox"])
        fig,axes=plt.subplots(1,2,figsize=(10,5.3),layout="constrained")
        axes[0].imshow(image)
        axes[0].add_patch(Rectangle((x1,y1),x2-x1,y2-y1,fill=False,edgecolor="#ffb000",linewidth=2))
        axes[0].set_title("Campo e área de inspeção (amarelo)")
        axes[1].imshow(image[y1:y2,x1:x2]); axes[1].set_title("Pixels originais do recorte")
        if item["point"]:
            px,py=item["point"]
            axes[0].plot(px,py,"+",color="#00ffdd",ms=9)
            axes[1].plot(px-x1,py-y1,"+",color="#00a89b",ms=12)
        for ax in axes: ax.axis("off")
        fig.suptitle(labels[item["category"]])
        save(fig,f"08_exemplo_{i:02d}",f'{labels[item["category"]]}. Image ID: {item["image_id"]}; caixa {item["bbox"]}. Seleção pelo primeiro ID elegível ordenado (externo: FP001). Cruz indica ponto publicado quando disponível. Área amarela é de inspeção; no exemplo de ponto perdido, não é proposta do modelo. Sem associação não comprova falso positivo na referência parcial.')

    metrics={s: dict(total_seconds=sum(r["seconds"] for r in val[s]),median_seconds=float(np.median([r["seconds"] for r in val[s]])),
                     candidate_regions=sum(r["candidates"] for r in val[s]),positive_regions=sum(r["positive_regions"] for r in val[s])) for s in ("A","B")}
    summary=dict(scope="exploratory_development_not_final_test", validation_images=len(ordered),external_images=n_external,
                 coverage=coverage_totals,validation=metrics,external_signaled=dict(zip(("A","B"),alarms)),
                 external_cases=donors,external_slides=slides,selected_epoch=meta["selected_epoch"],examples=examples,
                 input_sha256={p.relative_to(root).as_posix():sha(p) for p in inputs},figures=figures,
                 limitations=["Referência pontual parcial", "Validação usada na seleção de B", "Independência biológica desconhecida na base murina", "Externos de desenvolvimento e domínio diferente", "Revisões reconstruídas da declaração do usuário; não nova adjudicação especializada"])
    (output/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    markdown=["# Figuras e legendas — comparação exploratória A × B", "", "Geradas de predições existentes, sem treino, nova inferência ou abertura de pixels do teste. Os CSVs e summary.json permitem conferir números e hashes.",""]
    cards=[]
    for f in figures:
        name=f["name"]; caption=f["caption"]
        markdown += [f"## {name}","",caption,"",f"[PDF]({name}.pdf) · [PNG]({name}.png)",""]
        cards.append(f'<section><h2>{html.escape(name)}</h2><a href="{name}.pdf">PDF</a><p>{html.escape(caption)}</p><img loading="lazy" src="{name}.png" alt="{html.escape(name)}"></section>')
    (output/"LEIA-ME.md").write_text("\n".join(markdown),encoding="utf-8")
    (output/"index.html").write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Figuras do TCC</title><style>body{font:17px system-ui;max-width:1100px;margin:32px auto;padding:20px;color:#213547}img{width:100%}section{margin:40px 0;border-top:1px solid #ccd;padding-top:20px}p{line-height:1.6}</style><h1>Comparação exploratória A × B</h1><p>Validação e diagnóstico externo apresentados separadamente. Resultados não demonstram superioridade geral nem especificidade clínica.</p>'+''.join(cards)+'</html>',encoding="utf-8")
    return summary
