"""Mostra o que falta para treinar B; não treina nem transforma pendências em rótulos."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import data_protocol as dp  # noqa: E402


def resolve_paths(config, root=ROOT):
    return {key: (Path(config[key]) if Path(config[key]).is_absolute() else root / config[key])
            for key in ("image_manifest", "annotations", "crop_manifest", "model_config", "output_dir")}


def check_data(config, root=ROOT):
    from src import data_pipeline
    from src.segmentation import localization_hash
    from src.train import load_config

    paths = resolve_paths(config, root)
    result = {"checks": [], "warnings": [], "counts": {}, "ready_data": False,
              "evaluation_reference_ready": False}
    def check(name, ok, detail):
        result["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
    for key in ("image_manifest", "annotations", "crop_manifest", "model_config"):
        check(key, paths[key].is_file(), str(paths[key]))
    name = config["run_name"]
    valid_name = bool(name) and Path(name).name == name and name not in {".", ".."}
    check("new_run", valid_name and not (paths["output_dir"] / name).exists(),
          "Nome simples e pasta de execução nova: " + str(paths["output_dir"] / name))
    if not all(item["ok"] for item in result["checks"]):
        return result
    try:
        images = dp.read_manifest(paths["image_manifest"])
        dp.validate_partitions(images)
        from src.dataset_policy import validate_active_images, validate_supplementary_crops
        policy = config.get("supplementary_policy")
        if policy and not Path(policy).is_absolute(): policy = root / policy
        validate_active_images(images, root=root, supplementary_policy=policy)
        check("authorized_source", True, "ZIP público, IDs e reserva do teste conferidos.")
        check("partitions", True, "IDs, hashes e grupos sem duplicação entre partições.")
        result["counts"]["images"] = dict(Counter(row["split"] for row in images))
        result["counts"]["groups"] = {
            split: len({row["group_id"] for row in images if row["split"] == split}) for split in dp.SPLITS}
        if any(row["group_level"] == "imagem_original" for row in images):
            result["warnings"].append("Há grupos por imagem original; isso não demonstra independência entre animais/lâminas. Consulte o protocolo da divisão.")
        annotations = dp.load_annotations(paths["annotations"], images)
        reviewed = [entry for entry in annotations.values() if entry["review_status"] == "reviewed"]
        result["counts"]["reviewed_images"] = len(reviewed)
        result["counts"]["pending_images"] = len(images) - len(reviewed)
        if len(reviewed) < len(images):
            result["warnings"].append("Há imagens sem referência revisada; seus candidatos desconhecidos não podem entrar no treino.")
        crops = data_pipeline.load_split(paths["crop_manifest"])
        model_config = load_config(paths["model_config"])
        data_pipeline.validate_crop_manifest(crops, images, annotations,
            localization_hash(model_config["localization"]), data_pipeline.file_sha256(paths["annotations"]))
        if policy:
            validate_supplementary_crops(crops, policy, root)
        from src.class_balance import resolve_class_weights
        train_labels = crops.loc[crops["split"] == "train", "label"].astype(int)
        result["resolved_class_weights"] = resolve_class_weights(train_labels,
            model_config.get("class_weights"), model_config["training"].get("max_class_weight"))
        check("crop_provenance", True, "Rótulos, grupos, hashes dos recortes e configuração conferidos.")
        for split in ("train", "val"):
            labels = crops.loc[crops["split"] == split, "label"].astype(int)
            counts = {str(label): int(count) for label, count in labels.value_counts().items()}
            result["counts"][f"{split}_crops"] = counts
            origins = {str(label): int(crops.loc[(crops["split"] == split) & (crops["label"] == label),
                                                "image_id"].nunique()) for label in (0, 1)}
            result["counts"][f"{split}_source_images_by_class"] = origins
            if origins["0"] < 10:
                result["warnings"].append(f"{split}: negativos vêm de apenas {origins['0']} imagens; muitos recortes não representam muitos animais independentes.")
            check(f"{split}_classes", set(labels) == {0, 1}, f"Recortes por classe em {split}: {counts}")
        for split in dp.SPLITS:
            ids = [row["image_id"] for row in images if row["split"] == split]
            result["counts"][f"{split}_reference"] = dict(Counter(
                str(annotations.get(i, {}).get("whole_image_label")) for i in ids))
        test = [row for row in images if row["split"] == "test"]
        result["evaluation_reference_ready"] = bool(test) and all(
            annotations.get(row["image_id"], {}).get("review_status") == "reviewed"
            and annotations[row["image_id"]].get("reference_complete") for row in test)
        if not result["evaluation_reference_ready"]:
            result["warnings"].append("Referência completa de teste ainda não disponível. Isto é separado da viabilidade de treinar B.")
        train_cfg = model_config["training"]
        shape = model_config["model"]["input_shape"]
        check("model_input", list(shape[:2]) == list(model_config["data"]["image_size"])
              and shape[2] == 3 and model_config["model"]["num_classes"] == 2,
              "Entrada RGB, dimensão de resize e duas classes compatíveis.")
        check("training_config", train_cfg["batch_size"] > 0 and train_cfg["epochs"] > 0
              and train_cfg["selection_monitor"] == "val_loss" and train_cfg["selection_mode"] == "min",
              "Lote/épocas positivos; seleção por menor val_loss.")
    except Exception as exc:
        check("validation", False, f"{type(exc).__name__}: {exc}")
    result["ready_data"] = all(item["ok"] for item in result["checks"])
    return result


def check_runtime(require_gpu=False):
    result = {"checked": True, "ok": False, "require_gpu": require_gpu}
    try:
        import tensorflow as tf
        import keras
        result.update(python=sys.version.split()[0], tensorflow=tf.__version__, keras=keras.__version__)
        devices = tf.config.list_physical_devices("GPU")
        result["gpus"] = [device.name for device in devices]
        if not tf.__version__.startswith("2.15.") or not keras.__version__.startswith("2.15."):
            raise RuntimeError("Este projeto foi preparado para TensorFlow/Keras 2.15; use as dependências fornecidas.")
        if require_gpu and not devices:
            raise RuntimeError("TensorFlow não encontrou GPU. Consulte docs/ambiente.md para CPU no Windows ou GPU NVIDIA em Linux/WSL2.")
        if devices:
            for device in devices:
                tf.config.experimental.set_memory_growth(device, True)
            with tf.device("/GPU:0"):
                product = tf.matmul(tf.ones((8, 8)), tf.ones((8, 8)))
            if "GPU" not in product.device:
                raise RuntimeError("Operação não foi executada na GPU.")
            result["operation_device"] = product.device
            result["operation_value"] = float(product[0, 0].numpy())
        result["ok"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/experiment_b_original_negatives.json")
    parser.add_argument("--check-runtime", action="store_true")
    parser.add_argument("--require-gpu", action="store_true")
    parser.add_argument("--runtime-only", action="store_true", help="Verifica o ambiente antes de copiar os dados.")
    parser.add_argument("--output", type=Path, default=ROOT / "data/protocol/training_readiness.json")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    if args.runtime_only:
        result = {"checks": [], "warnings": [], "ready_data": None}
    else:
        result = check_data(config)
    runtime_requested = args.check_runtime or args.require_gpu or args.runtime_only
    result["runtime"] = check_runtime(args.require_gpu or config.get("require_gpu", False)) if runtime_requested else {"checked": False, "ok": None}
    result["ready_to_train"] = result["ready_data"] is True and result["runtime"]["ok"] is True
    result["created_at"] = datetime.now(timezone.utc).isoformat()
    result["experiment"] = str(args.config.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for item in result["checks"]:
        print(f"{'OK' if item['ok'] else 'PENDENTE'}: {item['name']} - {item['detail']}")
    for warning in result["warnings"]:
        print(f"OBSERVACAO: {warning}")
    if runtime_requested:
        print("AMBIENTE: " + json.dumps(result["runtime"], ensure_ascii=False))
    print("PRONTO PARA TREINAR: " + ("SIM" if result["ready_to_train"] else "AINDA NAO / AMBIENTE NAO VERIFICADO"))
    print(f"Relatorio: {args.output}")
    ok = (args.runtime_only or result["ready_data"]) and (not runtime_requested or result["runtime"]["ok"])
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
