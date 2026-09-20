"""Avaliação pareada de sistemas completos em imagens originais.

Referências incompletas não produzem métricas supervisionadas de detecção.
Ausência de recortes ou de uma execução não remove a imagem do denominador.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence

from .data_protocol import point_in_box, validate_bbox, validate_partitions


STATUSES = {"sem_regioes", "regioes_sem_predicao_positiva", "predicao_positiva", "erro"}


def box_iou(a, b) -> float:
    a, b = validate_bbox(a), validate_bbox(b)
    intersection = max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / union


def match_one_to_one(boxes: Sequence, positives: Sequence[Mapping], iou_threshold: float = 0.5) -> dict:
    """Associação bipartida de cardinalidade máxima, com desempate determinístico.

    Não usa greedy: uma escolha local não deve impedir dois acertos válidos.
    Para caixas, IoU >= limiar; para pontos, inclusão em [x1,y1,x2,y2).
    Ordenam-se vizinhos por IoU decrescente e índice da anotação.
    """
    if not 0 < iou_threshold <= 1:
        raise ValueError("Limiar de IoU deve estar em (0,1]")
    normalized = [validate_bbox(box.get("bbox") if isinstance(box, Mapping) else box) for box in boxes]
    adjacency = []
    for box in normalized:
        compatible = []
        for index, positive in enumerate(positives):
            if "bbox" in positive:
                score = box_iou(box, positive["bbox"])
                eligible = score >= iou_threshold
            else:
                eligible = point_in_box(positive["point"], box)
                score = 1.0 if eligible else 0.0
            if eligible:
                compatible.append((index, score))
        adjacency.append([index for index, _ in sorted(compatible, key=lambda pair: (-pair[1], pair[0]))])

    # Busca de caminho aumentante iterativa: não depende do limite de recursão.
    matched_reference, matched_prediction = {}, {}
    for start in range(len(normalized)):
        queue, visited_predictions, visited_references = [start], {start}, set()
        parent_reference, free_reference = {}, None
        for prediction in queue:
            for reference in adjacency[prediction]:
                if reference in visited_references:
                    continue
                visited_references.add(reference)
                parent_reference[reference] = prediction
                if reference not in matched_reference:
                    free_reference = reference
                    break
                next_prediction = matched_reference[reference]
                if next_prediction not in visited_predictions:
                    visited_predictions.add(next_prediction)
                    queue.append(next_prediction)
            if free_reference is not None:
                break
        if free_reference is not None:
            reference = free_reference
            while True:
                prediction = parent_reference[reference]
                previous = matched_prediction.get(prediction)
                matched_reference[reference] = prediction
                matched_prediction[prediction] = reference
                if previous is None:
                    break
                reference = previous

    pairs = [{"prediction_index": prediction, "reference_index": reference}
             for prediction, reference in sorted(matched_prediction.items())]
    return {"pairs": pairs,
            "unmatched_predictions": [i for i in range(len(normalized)) if i not in matched_prediction],
            "unmatched_references": [i for i in range(len(positives)) if i not in matched_reference]}


def load_predictions(path: str | Path, expected_system: str | None = None) -> list[dict]:
    """Leitura de baixo nível para testes; avaliações CLI usam load_prediction_run."""
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        if expected_system and payload.get("system") != expected_system:
            raise ValueError(f"Esperado resultado do sistema {expected_system}")
        payload = payload.get("images")
    if not isinstance(payload, list):
        raise ValueError("Previsões devem conter images como lista")
    return payload


def load_prediction_run(path, expected_system, split, manifest_sha256, *, synthetic_fixture=False):
    """Fronteira da CLI: exige origem/partição, antes de extrair previsões."""
    payload = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(payload, dict) or payload.get('schema_version') != 1 or payload.get('system') != expected_system:
        raise ValueError('Resultado exige envelope schema_version=1, system e proveniência')
    artifact = payload.get('artifact', {})
    declared_split = payload.get('split', artifact.get('split'))
    declared_hash = payload.get('manifest_sha256', artifact.get('manifest_sha256'))
    if declared_split != split or declared_hash != manifest_sha256:
        raise ValueError('Partição/hash do manifesto não corresponde à execução de inferência')
    synthetic = payload.get('synthetic') is True or artifact.get('trained_on_synthetic_data') is True
    if synthetic_fixture:
        if payload.get('synthetic') is not True:
            raise ValueError('Modo fixture exige previsões artificiais explicitamente sintéticas')
    elif split == 'test' and (synthetic or (expected_system == 'B' and artifact.get('trained_on_synthetic_data') is not False)):
        raise ValueError('Teste final exige B com proveniência de treino real; resultados sintéticos não são avaliação final')
    if not isinstance(payload.get('images'), list):
        raise ValueError('Resultado deve conter images como lista')
    return payload['images'], {'system': expected_system, 'split': declared_split,
                               'manifest_sha256': declared_hash, 'synthetic': synthetic,
                               'artifact': artifact}


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def _detection_metrics(tp: int, fp: int, fn: int, n_images: int) -> dict:
    return {"tp": tp, "fp": fp, "fn": fn, "precision": _ratio(tp, tp + fp),
            "recall": _ratio(tp, tp + fn), "f1": _ratio(2 * tp, 2 * tp + fp + fn),
            "fp_per_image": _ratio(fp, n_images), "n_images": n_images}


def _validated_result(result: Mapping, image: Mapping) -> dict:
    status = result.get("status")
    if status not in STATUSES:
        raise ValueError(f"Status de inferência inválido: {status}")
    regions, candidates = result.get("regions", []), result.get("candidates", [])
    if not isinstance(regions, list) or not isinstance(candidates, list):
        raise ValueError("regions/candidates devem ser listas")
    for region in regions + candidates:
        validate_bbox(region.get("bbox"), image["width"], image["height"])
    for region in regions:
        if isinstance(region.get("class_id"), bool) or region.get("class_id") not in (0, 1):
            raise ValueError("class_id deve ser 0 ou 1")
    positives = [region for region in regions if region["class_id"] == 1]
    if status == "sem_regioes" and (regions or candidates):
        raise ValueError("sem_regioes incompatível com regiões/candidatos presentes")
    if status == "regioes_sem_predicao_positiva" and (positives or not regions):
        raise ValueError("Status negativo exige regiões classificadas e nenhuma positiva")
    if status == "predicao_positiva" and not positives:
        raise ValueError("predicao_positiva exige região positiva")
    return dict(result, regions=regions, candidates=candidates)


def evaluate_system(images: Sequence[Mapping], annotations: Mapping[str, Mapping],
                    predictions: Sequence[Mapping], *, iou_threshold: float = 0.5,
                    image_decision_rule: str = "any_positive_region") -> dict:
    """Mantém todos os IDs; erros contam como ausência de detecção, nunca TN.

    A matriz binária é condicionada às decisões disponíveis. Erros/abstenções
    são contabilizados separadamente por referência, com cobertura explícita.
    """
    if not 0 < iou_threshold <= 1:
        raise ValueError("Limiar de IoU deve estar em (0,1]")
    if image_decision_rule not in {"any_positive_region", "image_decision", "original_decision"}:
        raise ValueError("Regra de imagem desconhecida")
    image_ids = [str(image["image_id"]) for image in images]
    if len(set(image_ids)) != len(image_ids):
        raise ValueError("IDs repetidos no conjunto de avaliação")
    by_id = {}
    for result in predictions:
        image_id = str(result.get("image_id", ""))
        if not image_id or image_id in by_id:
            raise ValueError("ID ausente/repetido no resultado do sistema")
        by_id[image_id] = result
    unexpected = sorted(set(by_id) - set(image_ids))
    per_image = []
    tp = fp = fn = localized = n_reference = n_detection_images = 0
    confusion = [[0, 0], [0, 0]]
    unresolved_by_reference = {"0": 0, "1": 0}
    n_image_reference = 0
    stage_values = {}
    for image in images:
        image_id = str(image["image_id"])
        raw = by_id.get(image_id)
        if raw is None:
            result = {"image_id": image_id, "status": "erro", "error": "previsao_ausente",
                      "regions": [], "candidates": [], "original_decision": None, "timings": {}}
        else:
            try:
                result = _validated_result(raw, image)
            except (ValueError, TypeError, KeyError) as error:
                result = {"image_id": image_id, "status": "erro", "error": f"resultado_invalido: {error}",
                          "regions": [], "candidates": [], "original_decision": raw.get("original_decision"),
                          "timings": raw.get("timings", {})}
        failed = result["status"] == "erro"
        # Resultados parciais de execução falha não podem virar acertos.
        candidates = [] if failed else result["candidates"]
        positive_regions = [] if failed else [region for region in result["regions"] if region["class_id"] == 1]
        annotation = annotations.get(image_id)
        reviewed = bool(annotation and annotation.get("review_status") == "reviewed" and annotation.get("reviewer"))
        eligible = bool(reviewed and annotation.get("reference_complete"))
        row = {"image_id": image_id, "group_id": image.get("group_id"), "status": result["status"],
               "error": result.get("error"), "n_candidates": len(result["candidates"]),
               "n_regions": len(result["regions"]), "n_positive_regions": len(positive_regions),
               "original_decision": result.get("original_decision"), "timings": result.get("timings", {}),
               "detection_eligible": eligible, "detection": None, "localization": None,
               "reference_reason": "referencia_completa_revisada" if eligible else "referencia_ausente_incompleta_ou_nao_revisada"}
        if eligible:
            positives = annotation.get("positives", [])
            localization = match_one_to_one(candidates, positives, iou_threshold)
            detection = match_one_to_one(positive_regions, positives, iou_threshold)
            image_tp, image_fp, image_fn = len(detection["pairs"]), len(detection["unmatched_predictions"]), len(detection["unmatched_references"])
            tp, fp, fn = tp + image_tp, fp + image_fp, fn + image_fn
            localized += len(localization["pairs"])
            n_reference += len(positives)
            n_detection_images += 1
            row["detection"] = dict(_detection_metrics(image_tp, image_fp, image_fn, 1), matching=detection)
            row["localization"] = {"matched": len(localization["pairs"]), "parasites": len(positives),
                                   "missed": len(localization["unmatched_references"]), "matching": localization}
        label = annotation.get("whole_image_label") if reviewed else None
        decision = None
        if not failed:
            if image_decision_rule == "any_positive_region":
                decision = int(bool(positive_regions))
            else:
                candidate_decision = result.get(image_decision_rule)
                if isinstance(candidate_decision, (int, bool)) and candidate_decision in (0, 1):
                    decision = int(candidate_decision)
        row.update(whole_image_reference=label, whole_image_prediction=decision)
        if label is not None:
            n_image_reference += 1
            if decision is None:
                unresolved_by_reference[str(label)] += 1
            else:
                confusion[label][decision] += 1
        for stage, value in result.get("timings", {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
                stage_values.setdefault(stage, []).append(float(value))
        per_image.append(row)
    tn, image_fp = confusion[0]
    image_fn, image_tp = confusion[1]
    n_resolved = sum(map(sum, confusion))
    image_metrics = _detection_metrics(image_tp, image_fp, image_fn, n_resolved)
    image_metrics.pop("fp_per_image")
    image_metrics.update(confusion_matrix=confusion if n_image_reference else None, confusion_labels=[0, 1],
                         accuracy=_ratio(tn + image_tp, n_resolved), n_reference=n_image_reference,
                         n_resolved=n_resolved, n_unresolved=n_image_reference - n_resolved,
                         unresolved_by_reference=unresolved_by_reference,
                         decision_coverage=_ratio(n_resolved, n_image_reference),
                         decision_rule=image_decision_rule,
                         note="Métricas binárias condicionadas às decisões disponíveis; erros não contam como negativos.")
    return {
        "n_images": len(images), "status_counts": dict(Counter(row["status"] for row in per_image)),
        "prediction_ids_outside_evaluation": unexpected,
        "localization": {"matched": localized, "parasites": n_reference, "missed": n_reference - localized,
                         "recall": _ratio(localized, n_reference), "n_images": n_detection_images},
        "detection": _detection_metrics(tp, fp, fn, n_detection_images), "whole_image": image_metrics,
        "timing_seconds": {stage: {"count": len(values), "total": sum(values), "mean": sum(values) / len(values)}
                           for stage, values in stage_values.items()},
        "per_image": per_image,
    }


def compare_systems(manifest: Sequence[Mapping], annotations: Mapping[str, Mapping],
                    predictions_a: Sequence[Mapping], predictions_b: Sequence[Mapping], *,
                    split: str = "test", iou_threshold: float = 0.5,
                    image_decision_rule: str = "any_positive_region") -> dict:
    validate_partitions(manifest)
    images = [row for row in manifest if row["split"] == split]
    if not images:
        raise ValueError(f"Nenhuma imagem na partição reservada '{split}'")
    outputs = {name: evaluate_system(images, annotations, predictions, iou_threshold=iou_threshold,
                                    image_decision_rule=image_decision_rule)
               for name, predictions in (("A", predictions_a), ("B", predictions_b))}
    groups = {str(image["group_id"]) for image in images}
    return {"schema_version": 1, "evaluation_split": split, "image_ids": [image["image_id"] for image in images],
            "n_groups": len(groups), "group_levels": dict(Counter(image["group_level"] for image in images)),
            "matching": {"boxes": "iou_greater_or_equal", "iou_threshold": iou_threshold,
                         "points": "inside_xyxy_half_open", "association": "maximum_cardinality_one_to_one"},
            "failure_policy": "Ausência/falha permanece no relatório e contribui FN para cada positivo de referência completa; imagem inteira fica indefinida.",
            "confidence_intervals": {"status": "nao_calculados", "reason": "Exigem planejamento e número suficiente de grupos independentes; recortes e sementes não são novas amostras."},
            "systems": outputs}
