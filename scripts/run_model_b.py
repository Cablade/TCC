"""Executa B em imagens inteiras do manifesto; mantém falhas e casos sem regiões."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", help="Por padrão usa config.json salvo junto de best.keras.")
    parser.add_argument("--split", choices=["train", "val", "test", "development"], default="test")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--compiled", action="store_true", help="Executa a mesma rede em grafo TensorFlow; registra o modo nos resultados.")
    image_options = parser.add_mutually_exclusive_group()
    image_options.add_argument("--image-mode", choices=['original', 'overlay', 'none'], default='original',
                               help="Padrão: PNG inteiro sem marcações; overlay desenha caixas; none não grava PNG.")
    image_options.add_argument("--no-overlays", action="store_true", help="Compatibilidade: equivale a --image-mode none.")
    args = parser.parse_args()
    image_mode = 'none' if args.no_overlays else args.image_mode
    import tensorflow as tf
    from PIL import Image, ImageDraw
    from src.data_protocol import read_manifest, validate_partitions, read_image_rgb, read_image_bytes
    from src.data_pipeline import file_sha256
    from src.model_b import predict_image_b
    from src.segmentation import localization_hash
    from src.train import load_config, versions
    from src.prediction_exports import save_original_png, write_review_csvs
    import hashlib

    tf.config.threading.set_inter_op_parallelism_threads(2)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    checkpoint = Path(args.checkpoint).resolve()
    saved_config_path = checkpoint.parent / "config.json"
    training_metadata_path = checkpoint.parent / "metadata.json"
    training_metadata = (json.loads(training_metadata_path.read_text(encoding="utf-8"))
                         if training_metadata_path.exists() else {})
    if training_metadata.get("synthetic") and args.split == "test":
        raise ValueError("Checkpoint sintético não pode produzir resultado de teste real; use development para smoke.")
    if args.split == "test":
        if training_metadata.get("synthetic") is not False or training_metadata.get("status") != "complete":
            raise ValueError("Teste real exige treinamento concluído e metadados de origem reais.")
        if training_metadata.get("checkpoint_sha256") != file_sha256(checkpoint):
            raise ValueError("Checkpoint difere do artefato selecionado no treino.")
    saved_config = json.loads(saved_config_path.read_text(encoding="utf-8")) if saved_config_path.exists() else None
    cfg = load_config(args.config) if args.config else saved_config
    if cfg is None:
        parser.error("Checkpoint sem config.json; forneça a configuração usada no treino com --config.")
    if saved_config and localization_hash(cfg["localization"]) != localization_hash(saved_config["localization"]):
        raise ValueError("Localização difere da configuração que gerou os recortes de treino.")
    rows = read_manifest(args.manifest)
    validate_partitions(rows)
    if args.split == "test":
        from src.dataset_policy import validate_active_images
        validate_active_images(rows)
    rows = [row for row in rows if row["split"] == args.split]
    if not rows:
        raise ValueError(f"Nenhuma imagem na partição {args.split}; não usar development como test.")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = output_dir / "predictions.json"
    if predictions_path.exists():
        raise FileExistsError("predictions.json já existe; use outro --output-dir.")
    load_start = time.perf_counter()
    classifier = tf.keras.models.load_model(checkpoint)
    load_seconds = time.perf_counter() - load_start
    if tuple(classifier.input_shape[1:]) != tuple(cfg["model"]["input_shape"]):
        raise ValueError("Entrada do checkpoint difere da configuração.")
    if args.compiled:
        from src.model_b import compiled_inference
        classifier = compiled_inference(classifier, tuple(cfg["model"]["input_shape"]))
    predictions = []
    exports = {}
    for image_index, row in enumerate(rows, 1):
        print(f"[{image_index}/{len(rows)}] {row['image_id']}: processando...", flush=True)
        start = time.perf_counter()
        image = None
        try:
            if hashlib.sha256(read_image_bytes(row["path"])).hexdigest() != row["sha256"]:
                raise ValueError("Hash da imagem difere do manifesto.")
            image = read_image_rgb(row["path"])
            if image.shape[:2] != (int(row["height"]), int(row["width"])):
                raise ValueError("Dimensões diferem do inventário.")
            result = predict_image_b(image, classifier, cfg, row["image_id"])
            result["timings"]["io_and_inference_seconds"] = time.perf_counter() - start
        except Exception as exc:
            result = {"image_id": row["image_id"], "status": "erro", "regions": [], "candidates": [],
                      "original_decision": None, "error": f"{type(exc).__name__}: {exc}",
                      "timings": {"io_and_inference_seconds": time.perf_counter() - start}}
        # A falha na gravação não altera uma decisão já calculada pelo modelo.
        export_start = time.perf_counter()
        exported = {'image_file': '', 'export_error': ''}
        try:
            if image is not None and image_mode == 'original':
                exported['image_file'] = save_original_png(image, output_dir, row['image_id'])
            elif image is not None and image_mode == 'overlay':
                overlay = Image.fromarray(image)
                draw = ImageDraw.Draw(overlay)
                for region in result["regions"]:
                    x1, y1, x2, y2 = region["bbox"]
                    draw.rectangle((x1, y1, x2 - 1, y2 - 1),
                                   outline="red" if region["class_id"] == 1 else "blue", width=3)
                safe_id = hashlib.sha256(str(row["image_id"]).encode()).hexdigest()[:16]
                overlay.save(output_dir / f"{safe_id}_overlay.png")
                exported['image_file'] = f"{safe_id}_overlay.png"
        except Exception as exc:
            exported['export_error'] = f'{type(exc).__name__}: {exc}'
        exported['export_seconds'] = time.perf_counter() - export_start if image_mode != 'none' else 0.0
        exports[row['image_id']] = exported
        result['timings']['overlay_seconds'] = exported['export_seconds'] if image_mode == 'overlay' else 0.0
        predictions.append(result)
        print(f"[{image_index}/{len(rows)}] {result['status']}; "
              f"{len(result['candidates'])} candidatos; "
              f"{result['timings']['io_and_inference_seconds']:.1f}s", flush=True)
    metadata = {"system": "B", "split": args.split, "manifest_sha256": file_sha256(args.manifest),
                "trained_on_synthetic_data": training_metadata.get("synthetic"),
                "checkpoint_sha256": file_sha256(checkpoint), "checkpoint_bytes": checkpoint.stat().st_size,
                "config": cfg, "versions": versions(), "model_load_seconds": load_seconds,
                "hardware": [device.name for device in tf.config.list_physical_devices()],
                "scores_are_calibrated_probabilities": False, "decision_rule": "any argmax(scores)==1"}
    metadata['execution_mode'] = 'tf_function' if args.compiled else 'eager'
    metadata['overlays_saved'] = image_mode == 'overlay'
    metadata['image_mode'] = image_mode
    metadata['export_errors'] = sum(bool(entry['export_error']) for entry in exports.values())
    metadata['tensorflow_threads'] = {'intra_op': 2, 'inter_op': 2}
    payload = {"schema_version": 1, "system": "B", "images": predictions, "artifact": metadata}
    predictions_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    fields = ["image_id", "status", "candidates", "classified_regions", "positive_regions",
              "original_decision", "total_seconds", "error"]
    with (output_dir / "per_image.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({"image_id": row["image_id"], "status": row["status"],
                          "candidates": len(row["candidates"]), "classified_regions": len(row["regions"]),
                          "positive_regions": sum(region["class_id"] == 1 for region in row["regions"]),
                          "original_decision": row["original_decision"],
                          "total_seconds": row["timings"]["io_and_inference_seconds"],
                          "error": row.get("error", "")} for row in predictions)
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    write_review_csvs(predictions, output_dir, exports)
    errors = sum(r["status"] == "erro" for r in predictions)
    print(json.dumps({"images": len(predictions), "errors": errors,
                      "predictions": str(predictions_path)}, ensure_ascii=False))
    return int(errors > 0 or metadata['export_errors'] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
