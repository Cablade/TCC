"""Prepara originais Kaggle para revisão e monta B2 apenas após confirmação humana."""
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import html
import io
import json
from pathlib import Path, PurePosixPath
import random
import sys
import zipfile

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp
from src.data_pipeline import file_sha256, load_split, validate_crop_manifest
from src.segmentation import propose_regions, crop_region, localization_hash
from src.train import load_config

SOURCE = "https://www.kaggle.com/datasets/paultimothymooney/blood-cells"
PREFIX = "dataset-master/dataset-master/JPEGImages/"
BATCH = ROOT / "data/annotations/kaggle_originals_20261005"
POLICY = ROOT / "configs/negative_source_kaggle_originals.json"


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def original_members(names):
    return sorted(n for n in names if n.startswith(PREFIX) and
                  PurePosixPath(n).parent.as_posix() == PREFIX.rstrip("/") and
                  PurePosixPath(n).name.startswith("BloodImage_") and n.lower().endswith(".jpg"))


def visual_hash(image):
    small = np.array(image.convert("L").resize((9, 8), Image.Resampling.BILINEAR))
    return int.from_bytes(np.packbits(small[:, 1:] > small[:, :-1]).tobytes(), "big")


def similarity_groups(values, distance=4):
    # Agrupamento conservador para impedir versões quase idênticas em partições distintas.
    parents = list(range(len(values)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]; i = parents[i]
        return i
    for i, a in enumerate(values):
        for j in range(i):
            if (a ^ values[j]).bit_count() <= distance:
                parents[find(i)] = find(j)
    return [find(i) for i in range(len(values))]


def prepare(archive, output=BATCH, policy=POLICY):
    if output.exists() or policy.exists():
        raise FileExistsError("Lote/política já existe; não sobrescrever a revisão.")
    config = load_config(ROOT / "configs/model_b_cpu_original_negatives.yaml")
    rows, decoded, duplicates, errors, seen = [], [], [], [], {}
    with zipfile.ZipFile(archive) as source:
        members = original_members(source.namelist())
        for name in members:
            raw = source.read(name)
            try:
                image = Image.open(io.BytesIO(raw)).convert("RGB")
                pixels = np.array(image)
            except Exception as exc:
                errors.append({"member": name, "error": str(exc)}); continue
            pixel_hash = hashlib.sha256(str(pixels.shape).encode() + pixels.tobytes()).hexdigest()
            if pixel_hash in seen:
                duplicates.append({"member": name, "same_pixels_as": seen[pixel_hash]}); continue
            seen[pixel_hash] = name
            digest = hashlib.sha256(raw).hexdigest()
            rows.append(dict(image_id="kaggle_original_"+digest[:24],
                path=f"zip://{archive.resolve().as_posix()}!{name}", sha256=digest,
                width=image.width, height=image.height, source=SOURCE,
                group_id="", group_level="imagem_original",
                split="development", duplicate_of="", original_member=name,
                decoded_sha256=pixel_hash, dhash=f"{visual_hash(image):016x}"))
            decoded.append(pixels)
        augmented_count = sum(n.startswith("dataset2-master/") and n.lower().endswith((".jpg", ".jpeg", ".png")) for n in source.namelist())
    if not rows: raise ValueError("ZIP sem imagens originais legíveis.")
    groups = similarity_groups([int(r["dhash"],16) for r in rows])
    for row, group in zip(rows, groups):
        row["group_id"] = "kaggle_similarity_" + rows[group]["sha256"][:24]
    output.mkdir(parents=True)
    inventory = output / "inventory.csv"
    dp.write_manifest(rows, inventory, list(rows[0]))
    template = dp.annotation_template(rows)
    save(output / "source_annotations.json", template)
    suggestions = []
    (output / "crops").mkdir()
    cards = []
    for row, pixels in zip(rows, decoded):
        candidates, _ = propose_regions(pixels, config["localization"])
        # Distribuir contexto no campo, em vez de priorizar somente uma célula.
        selected = []
        while candidates and len(selected) < 4:
            if not selected:
                index = max(range(len(candidates)), key=lambda i: candidates[i]["area"])
            else:
                def separation(i):
                    b=candidates[i]["bbox"]; cx=(b[0]+b[2])/2; cy=(b[1]+b[3])/2
                    return min((cx-(s["bbox"][0]+s["bbox"][2])/2)**2 + (cy-(s["bbox"][1]+s["bbox"][3])/2)**2 for s in selected)
                index = max(range(len(candidates)), key=separation)
            selected.append(candidates.pop(index))
        for index, candidate in enumerate(selected):
            key=f"K{len(suggestions)+1:04d}"
            path=output/"crops"/(key+".png")
            Image.fromarray(crop_region(pixels, candidate["bbox"])).save(path)
            suggestions.append(dict(candidate_id=key,image_id=row["image_id"],bbox=candidate["bbox"],
                source_sha256=row["sha256"],review_status="pending",label=None,
                crop_path="crops/"+path.name,crop_sha256=file_sha256(path)))
            cards.append(f'<article><h2>{key}</h2><img loading="lazy" src="crops/{key}.png" alt="{key}"><p>{html.escape(row["original_member"])}<br>Pendente — sem rótulo de treino.</p></article>')
    queue=dict(source_annotation_sha256=file_sha256(output/"source_annotations.json"),
               localization_sha256=localization_hash(config["localization"]), candidates=suggestions)
    save(output/"suggestions.json",queue)
    save(output/"development_reservation.json",dict(images=rows,excluded_from_future_test=True,
                                                    purpose="original_negative_review"))
    report=dict(source=SOURCE,archive_sha256=file_sha256(archive),original_files=len(members),
                usable_originals=len(rows),excluded_augmented_images=augmented_count,
                exact_pixel_duplicates=duplicates,decode_errors=errors,
                similarity_groups=len(set(groups)),candidates=len(suggestions),max_candidates_per_image=4,
                chagas_labels_in_source=False,review_required=True,ready_to_train=False,
                localization_sha256=queue["localization_sha256"],original_subset_prefix=PREFIX)
    save(output/"preparation.json",report)
    save(policy,dict(source=SOURCE,archive=str(archive.resolve()),expected_archive_sha256=file_sha256(archive),
                     inventory=inventory.relative_to(ROOT).as_posix(),inventory_sha256=file_sha256(inventory),
                     allowed_member_prefix=PREFIX,negative_only=True,allowed_splits=["train","val","development"],
                     max_crops_per_image=4))
    (output/"index.html").write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Originais para revisão</title><style>body{font:16px system-ui;margin:24px;color:#243446;background:#edf1f4}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}article{background:white;padding:12px;overflow-wrap:anywhere}img{width:100%;height:230px;object-fit:contain}</style><h1>Células originais — candidatos a negativos</h1><p>Os cartões são recortes originais, sem aumentos. Ainda não têm rótulo de treino. Para confirmar regiões, execute o arquivo abrir_revisao.cmd desta pasta. Os dados entram somente após confirmação humana.</p><main>'+''.join(cards)+'</main></html>',encoding="utf-8")
    (output/"abrir_revisao.cmd").write_text('@echo off\r\ncd /d "%~dp0..\\..\\.."\r\n".venv\\Scripts\\python.exe" scripts\\review_annotations.py --batch data\\annotations\\kaggle_originals_20261005 --port 8766\r\npause\r\n',encoding="utf-8")
    return report


def assemble(batch=BATCH):
    from src.dataset_policy import validate_active_images
    from notebooks.gerar_rois import CROP_FIELDS
    destination=ROOT/"data/processed/b_real_01"
    if destination.exists(): raise FileExistsError("Dados já montados; preserve o conjunto atual.")
    reviewed = batch/"reviewed.json"
    if not reviewed.is_file(): raise ValueError("Revisão humana ainda não foi salva; abra abrir_revisao.cmd e confirme regiões.")
    from scripts.review_annotations import ReviewStore
    store=ReviewStore(batch/"inventory.csv",batch/"source_annotations.json",reviewed,batch/"suggestions.json")
    external=store.rows
    annotations=dp.load_annotations(reviewed,external)
    cfg=load_config(ROOT/"configs/model_b_cpu_original_negatives.yaml")
    pending_queue=json.loads((batch/"suggestions.json").read_text(encoding="utf-8-sig"))
    if pending_queue["localization_sha256"]!=localization_hash(cfg["localization"]): raise ValueError("Localização mudou; refazer candidatos e revisão.")
    approved={}
    for item in pending_queue["candidates"]:
        if dp.candidate_label(item["bbox"],annotations[item["image_id"]])==0:
            approved.setdefault(item["image_id"],[]).append(item)
    selected=[r.copy() for r in external if r["image_id"] in approved]
    groups=sorted({r["group_id"] for r in selected})
    if len(groups)<20: raise ValueError("Confirme negativos de pelo menos 20 grupos originais para uma divisão inicial viável (mínimo operacional, não garantia científica).")
    random.Random(42).shuffle(groups)
    val_groups=set(groups[:max(4,round(len(groups)*.2))])
    for row in selected: row["split"]="val" if row["group_id"] in val_groups else "train"
    original_images=dp.read_manifest(ROOT/"data/splits/experimento/images.csv")
    combined=original_images+selected
    validate_active_images(combined,supplementary_policy=POLICY)
    dp.validate_partitions(combined)
    original_ref=json.loads((ROOT/"data/annotations/experimento_reference_v2.json").read_text(encoding="utf-8-sig"))
    reference=deepcopy(original_ref)
    reference["images"].extend(annotations[r["image_id"]] for r in selected)
    original_crops=load_split(ROOT/"data/processed/b_real_01/crops.csv")
    original_crops=original_crops[original_crops["image_id"].isin({r["image_id"] for r in original_images})].copy()
    original_crops["annotation_sha256"]=file_sha256(ROOT/"data/annotations/experimento_reference_v2.json")
    validate_crop_manifest(original_crops,original_images,dp.validate_annotations(original_ref,original_images),
        localization_hash(cfg["localization"]),file_sha256(ROOT/"data/annotations/experimento_reference_v2.json"))
    destination=ROOT/"data/processed/b_real_01"
    if destination.exists(): raise FileExistsError("Destino já existe; preserve o experimento montado.")
    destination.mkdir(parents=True)
    reference_path=destination/"annotations.json"; save(reference_path,reference)
    images_path=destination/"images.csv"; dp.write_manifest(combined,images_path,list(original_images[0]))
    annotation_hash=file_sha256(reference_path)
    crops=original_crops.to_dict("records")
    for crop in crops: crop["annotation_sha256"]=annotation_hash
    for row in selected:
        pixels=dp.read_image_rgb(row["path"])
        for item in approved[row["image_id"]][:4]:
            key="kaggle_"+hashlib.sha256((row["image_id"]+str(item["bbox"])).encode()).hexdigest()[:24]
            path=destination/row["split"]/"0"/(key+".png"); path.parent.mkdir(parents=True,exist_ok=True)
            Image.fromarray(crop_region(pixels,item["bbox"])).save(path)
            crops.append(dict(crop_id=key,image_id=row["image_id"],path=str(path),label=0,
                split=row["split"],group_id=row["group_id"],source_sha256=row["sha256"],crop_sha256=file_sha256(path),
                bbox=json.dumps(item["bbox"]),localization_sha256=localization_hash(cfg["localization"]),
                annotation_sha256=annotation_hash,review_status="reviewed"))
    crop_manifest=destination/"crops.csv"
    dp.write_manifest(crops,crop_manifest,CROP_FIELDS)
    validate_crop_manifest(load_split(crop_manifest),combined,dp.validate_annotations(reference,combined),
                           localization_hash(cfg["localization"]),annotation_hash)
    report=dict(image_groups=len(groups),counts=dict(Counter(f'{r["split"]}/{r["label"]}' for r in crops)),
                added_negatives=len(crops)-len(original_crops),max_external_crops_per_image=4,
                test_preserved=True,over_sampling=False,under_sampling=False,
                one_pass_per_epoch=True,review_sha256=file_sha256(reviewed))
    save(destination/"assembly.json",report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,default=ROOT/"data/external_candidates/kaggle_blood_cells/source_v6.zip")
    parser.add_argument("--assemble",action="store_true")
    args=parser.parse_args()
    print(json.dumps(assemble() if args.assemble else prepare(args.archive),ensure_ascii=False,indent=2))


if __name__=="__main__": main()
