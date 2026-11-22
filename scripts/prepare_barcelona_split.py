"""Reserva 20 negativos Barcelona para próximo treino e 180 para comparação; não treina."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp
from src.data_pipeline import file_sha256, load_split, validate_crop_manifest
from src.negative_partition import split_barcelona, assert_disjoint_training_comparison

BATCH = ROOT / "data/annotations/barcelona_originals_review"
PARTITION = ROOT / "data/protocol/barcelona_split_20261006"
DESTINATION = ROOT / "data/processed/b_next"
POLICY = ROOT / "configs/negative_source_barcelona_training.json"
BUNDLE = ROOT / "configs/negative_sources_originals.json"
COMPARISON = ROOT / "configs/comparison_a_vs_b.json"


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def relative(path):
    return path.relative_to(ROOT).as_posix()


def select_candidates(candidates, limit=4):
    """Mesmo limite e diversidade de contexto usados nos originais Kaggle."""
    pending = list(candidates)
    selected = []
    while pending and len(selected) < limit:
        if not selected:
            index = max(range(len(pending)), key=lambda i: pending[i]["area"])
        else:
            def separation(i):
                b = pending[i]["bbox"]
                cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                return min((cx - (s["bbox"][0] + s["bbox"][2]) / 2) ** 2
                           + (cy - (s["bbox"][1] + s["bbox"][3]) / 2) ** 2 for s in selected)
            index = max(range(len(pending)), key=separation)
        selected.append(pending.pop(index))
    return selected


def write_partition_preview(assignments, destination=PARTITION):
    setup=ROOT/'configs/comparison_a_vs_b.json'
    output=json.loads(setup.read_text('utf-8'))['output_dir'].split('/')[-1] if setup.exists() else 'a_vs_b_barcelona'
    trained=(DESTINATION/'trained_in.json').exists()
    labels={'basophil':'Basófilos','eosinophil':'Eosinófilos','erythroblast':'Eritroblastos',
            'ig':'Granulócitos imaturos','lymphocyte':'Linfócitos','monocyte':'Monócitos',
            'neutrophil':'Neutrófilos','platelet':'Plaquetas'}
    sections=[]
    for split,title in [('train','20 originais reservados para os negativos do treino'),
                        ('development','180 originais destinados à comparação')]:
        cards=[]
        for row in sorted((r for r in assignments if r['split']==split),key=lambda r:(r['cell_type'],r['image_id'])):
            image=os.path.relpath(row['path'],destination).replace('\\','/')
            cards.append(f'<article><img loading="lazy" src="{html.escape(image,quote=True)}" alt="{row["image_id"]}"><p>{labels[row["cell_type"]]}</p><small>{row["image_id"]}</small></article>')
        sections.append('<h2>'+title+'</h2><div class="grid">'+''.join(cards)+'</div>')
    page='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Barcelona — divisão 20/180</title><style>body{font:16px system-ui;margin:24px;color:#203548;background:#edf2f5;line-height:1.5}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:15px}article{background:white;padding:12px;border-radius:8px;overflow-wrap:anywhere}img{width:100%;height:250px;object-fit:contain}small{font-size:11px}</style><h1>Barcelona: 20 para treino, 180 para comparação</h1><p>Todas as imagens foram aprovadas por Caio como sem parasita visível. Semente 42; seleção por tipos celulares, sem consultar previsões. Nenhum novo treino realizado. As 180 restantes entram na comparação junto às 73 negativas Kaggle e 114 positivas.</p><p>Arquivos <a href="training.csv">20 do treino</a> · <a href="comparison.csv">180 da comparação</a> · <a href="assignments.csv">Divisão completa</a> · <a href="../../../tcc/figuras/a_vs_b_barcelona/index.html">Comparação atual</a></p>'+''.join(sections)+'</html>'
    page=page.replace('a_vs_b_barcelona/index.html',output+'/index.html')
    if trained:
        page=page.replace('Nenhum novo treino realizado.','O B foi retreinado com os 20 originais destinados ao treino (80 recortes negativos).')
    (destination/'index.html').write_text(page,encoding='utf-8')


def prepare():
    from PIL import Image
    from src.segmentation import propose_regions, crop_region, localization_hash
    from src.train import load_config
    from src.dataset_policy import validate_active_images, validate_supplementary_crops
    from notebooks.gerar_rois import CROP_FIELDS

    for target in (PARTITION, DESTINATION, POLICY, BUNDLE, COMPARISON):
        if target.exists():
            raise FileExistsError("Preparo já existe; não sobrescrever: " + str(target))
    approval = json.loads((BATCH / "human_approval_all_originals.json").read_text(encoding="utf-8"))
    if approval["status"] != "complete" or approval["images_confirmed"] != 200:
        raise ValueError("Exige a aprovação das 200 imagens por Caio.")
    for key, name in [("inventory_sha256", "inventory.csv"), ("reviewed_sha256", "reviewed.json")]:
        if approval[key] != file_sha256(BATCH / name):
            raise ValueError("Revisão/inventário original alterado.")
    original = dp.read_manifest(BATCH / "inventory.csv")
    refs = dp.load_annotations(BATCH / "reviewed.json", original)
    if any(r["whole_image_label"] != 0 or r["review_status"] != "reviewed"
           or not r["reference_complete"] for r in refs.values()):
        raise ValueError("Exige referência negativa completa de todas as imagens.")
    assignments = split_barcelona(original)
    training = [r for r in assignments if r["split"] == "train"]
    comparison = [r for r in assignments if r["split"] == "development"]
    previous = ROOT / "data/processed/b_real_01"
    base_images = dp.read_manifest(previous / "images.csv")
    assert_disjoint_training_comparison(training, comparison + base_images)
    for row in original:
        if file_sha256(row["path"]) != row["sha256"]:
            raise ValueError("JPEG original alterado: " + row["image_id"])
    model_paths = [ROOT / "models/model_a/model_trained.keras", ROOT / "experiments/runs/b_val_01/best.keras"]
    protected_paths = model_paths + [previous / n for n in ("images.csv", "annotations.json", "crops.csv")]
    protected = {relative(p): file_sha256(p) for p in protected_paths}
    PARTITION.mkdir(parents=True)
    for name, rows in [("assignments.csv", assignments), ("training.csv", training), ("comparison.csv", comparison)]:
        dp.write_manifest(rows, PARTITION / name, list(rows[0]))
    envelope = lambda rows: dict(schema_version=1, coordinate_convention="xyxy_half_open",
                                images=[deepcopy(refs[r["image_id"]]) for r in rows])
    save(PARTITION / "training_annotations.json", envelope(training))
    save(PARTITION / "comparison_annotations.json", envelope(comparison))
    save(PARTITION / "authorization.json", dict(status="complete", created_at=datetime.now(timezone.utc).isoformat(),
        reviewer="Caio", authorization="dessas 200 imagens separe 20 para entrar nas negativas do treino, e então adicione o restante que sobrou no teste de comparação junto ao Kaggle, mas ainda não treine o modelo B, só faça isso pfvr!",
        review_basis="prior_human_approval_of_all_200_and_explicit_new_usage_request",
        training_allowed=True, training_started=False, training_image_ids=[r["image_id"] for r in training],
        comparison_image_ids=[r["image_id"] for r in comparison],
        assignments_sha256=file_sha256(PARTITION / "assignments.csv"),
        original_approval_sha256=file_sha256(BATCH / "human_approval_all_originals.json"),
        selection="Semente 42; 2 ou 3 originais por tipo celular, sem consultar previsões; reserva feita após diagnóstico dos 200.",
        evaluation="development_only_not_independent_final_test", clinical_diagnosis=False))
    save(POLICY, dict(source="https://data.mendeley.com/datasets/snkd93bnjr/1", negative_only=True,
        inventory=relative(PARTITION / "training.csv"), inventory_sha256=file_sha256(PARTITION / "training.csv"),
        approval=relative(PARTITION / "authorization.json"), approval_sha256=file_sha256(PARTITION / "authorization.json"),
        reviewed=relative(PARTITION / "training_annotations.json"), reviewed_sha256=file_sha256(PARTITION / "training_annotations.json"),
        partition_manifest=relative(PARTITION / "assignments.csv"), partition_manifest_sha256=file_sha256(PARTITION / "assignments.csv"),
        image_root=relative(BATCH / "images"), allowed_splits=["train"], max_crops_per_image=4))
    save(BUNDLE, dict(schema_version=1, policies=["configs/negative_source_kaggle_originals.json", relative(POLICY)]))
    save(COMPARISON, dict(output_dir="experiments/comparison/a_vs_b_barcelona",
        barcelona_manifest=relative(PARTITION / "comparison.csv"),
        barcelona_annotations=relative(PARTITION / "comparison_annotations.json"),
        barcelona_authorization=relative(PARTITION / "authorization.json"),
        barcelona_manifest_sha256=file_sha256(PARTITION / "comparison.csv"),
        barcelona_annotations_sha256=file_sha256(PARTITION / "comparison_annotations.json"),
        barcelona_authorization_sha256=file_sha256(PARTITION / "authorization.json"),
        next_training_manifest=relative(DESTINATION / "images.csv"),
        expected_cohorts=dict(positive_val=114, kaggle_negative_val=73, barcelona_negative=180)))
    combined = base_images + training
    dp.validate_partitions(combined)
    validate_active_images(combined, supplementary_policy=BUNDLE)
    base_reference = json.loads((previous / "annotations.json").read_text(encoding="utf-8-sig"))
    reference = deepcopy(base_reference)
    reference["images"].extend(deepcopy(refs[r["image_id"]]) for r in training)
    annotations = dp.validate_annotations(reference, combined)
    cfg = load_config(ROOT / "configs/model_b_cpu_original_negatives.yaml")
    localization_sha = localization_hash(cfg["localization"])
    old_crops = load_split(previous / "crops.csv")
    validate_crop_manifest(old_crops, base_images, dp.load_annotations(previous / "annotations.json", base_images),
                           localization_sha, file_sha256(previous / "annotations.json"))
    DESTINATION.mkdir(parents=True)
    fields = list(dict.fromkeys(k for r in combined for k in r))
    dp.write_manifest(combined, DESTINATION / "images.csv", fields)
    save(DESTINATION / "annotations.json", reference)
    annotation_sha = file_sha256(DESTINATION / "annotations.json")
    crops = old_crops.to_dict("records")
    for crop in crops:
        crop["annotation_sha256"] = annotation_sha
    for row in training:
        pixels = dp.read_image_rgb(row["path"])
        candidates, _ = propose_regions(pixels, cfg["localization"])
        selected = select_candidates(candidates)
        if not selected:
            raise ValueError("Imagem sem candidatos; não criar recortes arbitrários: " + row["image_id"])
        for candidate in selected:
            bbox = candidate["bbox"]
            key = "barcelona_" + hashlib.sha256((row["image_id"] + str(bbox)).encode()).hexdigest()[:24]
            path = DESTINATION / "train/0" / (key + ".png")
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(crop_region(pixels, bbox)).save(path)
            crops.append(dict(crop_id=key, image_id=row["image_id"], path=str(path), label=0, split="train",
                group_id=row["group_id"], source_sha256=row["sha256"], crop_sha256=file_sha256(path),
                bbox=json.dumps(bbox), localization_sha256=localization_sha, annotation_sha256=annotation_sha,
                review_status="reviewed"))
    dp.write_manifest(crops, DESTINATION / "crops.csv", CROP_FIELDS)
    final_crops = load_split(DESTINATION / "crops.csv")
    validate_crop_manifest(final_crops, combined, annotations, localization_sha, annotation_sha)
    validate_supplementary_crops(final_crops, BUNDLE)
    reserved = [r for r in combined if r["split"] == "train"]
    assert_disjoint_training_comparison(reserved, comparison + [r for r in base_images if r["split"] == "val"])
    if any(file_sha256(ROOT / p) != digest for p, digest in protected.items()):
        raise ValueError("Artefato protegido mudou durante o preparo.")
    experiment_path = ROOT / "configs/experiment_b_original_negatives.json"
    experiment = json.loads(experiment_path.read_text(encoding="utf-8-sig"))
    save(DESTINATION / "previous_experiment_config.json", experiment)
    experiment.update(name="b_next_barcelona20", image_manifest=relative(DESTINATION / "images.csv"),
        annotations=relative(DESTINATION / "annotations.json"), crop_manifest=relative(DESTINATION / "crops.csv"),
        supplementary_policy=relative(BUNDLE), run_name="b_next")
    save(experiment_path, experiment)
    report = dict(created_at=datetime.now(timezone.utc).isoformat(), ready_data=True, training_started=False,
        training_images_added=20, comparison_images=180, kaggle_comparison_images=73,
        positive_comparison_images=114, total_comparison_images=367,
        training_by_cell_type=dict(Counter(r["cell_type"] for r in training)),
        comparison_by_cell_type=dict(Counter(r["cell_type"] for r in comparison)),
        added_negative_crops=len(crops) - len(old_crops),
        crop_counts=dict(Counter(f'{r["split"]}/{r["label"]}' for r in crops)),
        max_barcelona_crops_per_image=4, over_sampling=False, under_sampling=False,
        old_crops_shared_without_pixel_copies=True, test_105_unchanged=True, checkpoints_unchanged=True,
        protected_sha256=protected, selection_uses_model_predictions=False,
        biological_independence_proven=False,
        note="As 180 foram examinadas no diagnóstico anterior; comparação de desenvolvimento. Nenhum treino foi iniciado.")
    save(DESTINATION / "assembly.json", report)
    save(PARTITION / "report.json", report)
    write_partition_preview(assignments)
    return report


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(prepare(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
