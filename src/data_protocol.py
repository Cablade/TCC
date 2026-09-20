"""Inventário, partições e anotações do protocolo A × B (sem TensorFlow).

As coordenadas são pixels da imagem original: [x1, y1, x2, y2), com
limites direito/inferior exclusivos. Caminhos ZIP são ``zip://arquivo!membro``.
Nenhuma rotina deste módulo apaga ou modifica os dados de origem.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import random
import zipfile
from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence


UNKNOWN = "desconhecida"
SPLITS = ("train", "val", "test", "development")
INVENTORY_FIELDS = (
    "image_id", "path", "sha256", "width", "height", "source",
    "group_id", "group_level", "duplicate_of",
)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def _text(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return str(value).strip()


def read_manifest(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_manifest(rows: Sequence[Mapping], path: str | Path, fields=None) -> None:
    """Escreve cabeçalhos mesmo quando a partição está vazia."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(INVENTORY_FIELDS)
        if any("split" in row for row in rows):
            fields.append("split")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_image_bytes(path: str | Path) -> bytes:
    locator = str(path)
    if locator.startswith("zip://"):
        archive, separator, member = locator[6:].partition("!")
        if not separator or not member:
            raise ValueError(f"Caminho ZIP inválido: {locator}")
        with zipfile.ZipFile(archive) as stream:
            matches = [info for info in stream.infolist() if info.filename == member]
            if len(matches) != 1:
                raise ValueError(f"Membro ZIP ausente ou ambíguo: {member}")
            return stream.read(matches[0])
    return Path(locator).read_bytes()


def read_image_rgb(path: str | Path):
    """Retorna RGB uint8, sem transpor EXIF ou mudar coordenadas da imagem."""
    import numpy as np
    from PIL import Image

    with Image.open(io.BytesIO(read_image_bytes(path))) as image:
        return np.asarray(image.convert("RGB")).copy()


def _image_locations(inputs: Sequence[str | Path]) -> list[str]:
    locations = set()
    for supplied in inputs:
        root = Path(supplied).resolve()
        if not root.exists():
            raise FileNotFoundError(root)
        files = sorted(root.rglob("*")) if root.is_dir() else [root]
        for path in files:
            if not path.is_file():
                continue
            if path.suffix.lower() == ".zip":
                with zipfile.ZipFile(path) as archive:
                    names = [item.filename for item in archive.infolist() if not item.is_dir()]
                    counts = Counter(names)
                    for name in sorted(names):
                        if Path(name).suffix.lower() in IMAGE_EXTENSIONS:
                            if counts[name] != 1:
                                raise ValueError(f"Nome de imagem repetido dentro do ZIP: {path}!{name}")
                            locations.add(f"zip://{path.as_posix()}!{name}")
            elif path.suffix.lower() in IMAGE_EXTENSIONS:
                locations.add(path.as_posix())
    return sorted(locations)


def build_inventory(inputs: Sequence[str | Path], metadata: Sequence[Mapping] = ()) -> dict:
    """Hash SHA-256 dos bytes; duplicatas permanecem no inventário/exclusões.

    Metadados são associados pelo caminho exato, nunca pelo nome do arquivo.
    Na ausência de grupo confiável, usa-se a imagem original e registra-se a
    limitação. IDs são estáveis para o mesmo caminho e conteúdo.
    """
    from PIL import Image

    locations = _image_locations(inputs)
    by_path = {}
    for entry in metadata:
        key = _text(entry.get("path"))
        if not key or key in by_path:
            raise ValueError("Metadados exigem path único e não vazio")
        by_path[key] = entry
    unknown_paths = set(by_path) - set(locations)
    if unknown_paths:
        raise ValueError(f"Metadados sem imagem correspondente: {sorted(unknown_paths)}")

    rows, exclusions, errors = [], [], []
    first_by_hash = {}
    for locator in locations:
        raw = read_image_bytes(locator)
        digest = hashlib.sha256(raw).hexdigest()
        image_id = "img_" + hashlib.sha256((locator + "\0" + digest).encode()).hexdigest()[:24]
        width = height = UNKNOWN
        try:
            with Image.open(io.BytesIO(raw)) as image:
                width, height = image.size
                image.verify()
        except Exception as error:
            errors.append({"image_id": image_id, "path": locator, "error": str(error)})
        meta = by_path.get(locator, {})
        group_id, group_level = _text(meta.get("group_id")), _text(meta.get("group_level"))
        if group_id and group_level not in {"animal", "lamina", "imagem_original"}:
            raise ValueError(f"group_level deve identificar animal, lamina ou imagem_original: {locator}")
        if not group_id:
            group_id, group_level = image_id, "imagem_original"
        duplicate_of = first_by_hash.get(digest, "")
        row = dict(image_id=image_id, path=locator, sha256=digest, width=width, height=height,
                   source=_text(meta.get("source")) or UNKNOWN, group_id=group_id,
                   group_level=group_level, duplicate_of=duplicate_of)
        rows.append(row)
        if duplicate_of:
            exclusions.append({**row, "reason": "sha256_identico"})
        else:
            first_by_hash[digest] = image_id
    return {"images": rows, "exclusions": exclusions, "errors": errors,
            "summary": inventory_summary(rows)}


def inventory_summary(rows: Sequence[Mapping]) -> dict:
    unique = [row for row in rows if not _text(row.get("duplicate_of"))]
    return {
        "files": len(rows), "unique_images": len(unique), "duplicates": len(rows) - len(unique),
        "groups": len({_text(row.get("group_id")) for row in unique}),
        "group_levels": dict(Counter(_text(row.get("group_level")) for row in unique)),
        "sources": dict(Counter(_text(row.get("source")) for row in unique)),
        "dimensions": dict(Counter(f"{row.get('width')}x{row.get('height')}" for row in unique)),
        "classes": "desconhecidas: requerem anotações revisadas",
        "limitation": "Grupos imagem_original não asseguram independência entre animais/lâminas.",
    }


def validate_partitions(rows: Sequence[Mapping]) -> None:
    """Rejeita duplicatas e vazamento de imagem/hash/grupo antes dos recortes."""
    ids, hashes, groups = {}, {}, {}
    for row in rows:
        image_id, digest = _text(row.get("image_id")), _text(row.get("sha256")).lower()
        group, split = _text(row.get("group_id")), _text(row.get("split"))
        if not image_id or not group or not _text(row.get("path")):
            raise ValueError("Partições exigem image_id, path e group_id explícitos")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):
            raise ValueError(f"SHA-256 inválido: {image_id}")
        if split not in SPLITS:
            raise ValueError(f"Partição inválida: {image_id}: {split}")
        if _text(row.get("duplicate_of")):
            raise ValueError(f"Duplicata deve constar só no manifesto de exclusão: {image_id}")
        if image_id in ids or digest in hashes:
            raise ValueError(f"Imagem ou conteúdo repetido nas partições: {image_id}")
        if group in groups and groups[group] != split:
            raise ValueError(f"Grupo presente em partições diferentes: {group}")
        if _text(row.get("group_level")) not in {"animal", "lamina", "imagem_original"}:
            raise ValueError(f"Nível de agrupamento inválido: {image_id}")
        for dimension in ("width", "height"):
            value = float(row.get(dimension, 0))
            if not math.isfinite(value) or value <= 0 or value != int(value):
                raise ValueError(f"Dimensão inválida: {image_id}/{dimension}")
        ids[image_id], hashes[digest], groups[group] = split, split, split


def assign_splits(rows: Sequence[Mapping], *, assignments: Mapping[str, str] | None = None,
                  counts: Mapping[str, int] | None = None, seed: int = 42) -> list[dict]:
    """Divide grupos, nunca recortes. Sem proporção ou contagem padrão.

    Grupos não atribuídos ficam explicitamente em development. Se development
    for fornecido em counts, as contagens devem abranger todos os grupos.
    """
    if (assignments is None) == (counts is None):
        raise ValueError("Forneça exatamente assignments ou counts explícitos")
    unique = [dict(row) for row in rows if not _text(row.get("duplicate_of"))]
    group_ids = sorted({_text(row.get("group_id")) for row in unique})
    if not group_ids or "" in group_ids:
        raise ValueError("Inventário sem grupos válidos")
    if assignments is not None:
        unknown = set(assignments) - set(group_ids)
        if unknown or any(value not in SPLITS for value in assignments.values()):
            raise ValueError(f"Atribuições inválidas; grupos desconhecidos: {sorted(unknown)}")
        selected = dict(assignments)
    else:
        assert counts is not None
        if (set(counts) - set(SPLITS) or not counts or
                any(isinstance(value, bool) or not isinstance(value, int) or value < 0
                    for value in counts.values())):
            raise ValueError("Contagens devem ser inteiros não negativos por partição válida")
        total = sum(counts.values())
        if total > len(group_ids) or ("development" in counts and total != len(group_ids)):
            raise ValueError(f"Contagens incompatíveis com os {len(group_ids)} grupos disponíveis")
        shuffled = group_ids.copy()
        random.Random(seed).shuffle(shuffled)
        selected, offset = {}, 0
        for split in SPLITS:
            count = counts.get(split, 0)
            selected.update({group: split for group in shuffled[offset:offset + count]})
            offset += count
    for row in unique:
        row["split"] = selected.get(_text(row["group_id"]), "development")
    validate_partitions(unique)
    return unique


def validate_bbox(bbox, width=None, height=None) -> tuple[float, float, float, float]:
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError("bbox deve ser [x1,y1,x2,y2]")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or
           not math.isfinite(value) for value in bbox):
        raise ValueError("Coordenadas da caixa devem ser números finitos")
    x1, y1, x2, y2 = map(float, bbox)
    if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
        raise ValueError(f"Caixa vazia/inválida: {bbox}")
    if (width is not None and x2 > float(width)) or (height is not None and y2 > float(height)):
        raise ValueError(f"Caixa fora da imagem: {bbox}")
    return x1, y1, x2, y2


def boxes_intersect(a, b) -> bool:
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def point_in_box(point, bbox) -> bool:
    return bbox[0] <= point[0] < bbox[2] and bbox[1] <= point[1] < bbox[3]


def annotation_intersects_box(positive: Mapping, bbox) -> bool:
    return boxes_intersect(positive["bbox"], bbox) if "bbox" in positive else point_in_box(positive["point"], bbox)


def validate_negative_box(bbox, positives: Sequence[Mapping]) -> bool:
    """True se TODO o recorte está livre de intersecções com positivos conhecidos.

    Esta verificação geométrica não confirma que uma região é negativa.
    """
    validate_bbox(bbox)
    return not any(annotation_intersects_box(positive, bbox) for positive in positives)


def annotation_template(rows: Sequence[Mapping]) -> dict:
    return {"schema_version": 1, "coordinate_convention": "xyxy_half_open", "images": [
        {"image_id": row["image_id"], "width": int(row["width"]), "height": int(row["height"]),
         "review_status": "pending", "reviewer": None, "reference_complete": False,
         "whole_image_label": None, "positives": [], "negative_regions": []}
        for row in rows if not _text(row.get("duplicate_of"))]}


def validate_annotations(payload: Mapping, image_manifest: Sequence[Mapping] | None = None) -> dict[str, dict]:
    if payload.get("schema_version") != 1 or payload.get("coordinate_convention") != "xyxy_half_open":
        raise ValueError("Schema de anotações deve ser versão 1 / xyxy_half_open")
    if not isinstance(payload.get("images"), list):
        raise ValueError("Anotações devem conter images como lista")
    manifest = {str(row["image_id"]): row for row in image_manifest} if image_manifest is not None else None
    result = {}
    for entry in payload["images"]:
        image_id = _text(entry.get("image_id"))
        if not image_id or image_id in result:
            raise ValueError("image_id ausente ou duplicado nas anotações")
        width, height = entry.get("width"), entry.get("height")
        if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in (width, height)):
            raise ValueError(f"Dimensões inválidas: {image_id}")
        if manifest is not None and (image_id not in manifest or
                (width, height) != (int(manifest[image_id]["width"]), int(manifest[image_id]["height"]))):
            raise ValueError(f"Imagem/dimensões incompatíveis com inventário: {image_id}")
        if entry.get("review_status") not in {"pending", "reviewed"}:
            raise ValueError(f"Estado de revisão inválido: {image_id}")
        if entry["review_status"] == "reviewed" and not _text(entry.get("reviewer")):
            raise ValueError(f"Revisão exige identificar revisor: {image_id}")
        if not isinstance(entry.get("reference_complete"), bool):
            raise ValueError(f"reference_complete deve ser booleano: {image_id}")
        label = entry.get("whole_image_label")
        if label is not None and (isinstance(label, bool) or not isinstance(label, int) or label not in (0, 1)):
            raise ValueError(f"Rótulo de imagem deve ser null, 0 ou 1: {image_id}")
        positives, negatives = entry.get("positives", []), entry.get("negative_regions", [])
        if not isinstance(positives, list) or not isinstance(negatives, list):
            raise ValueError("positives e negative_regions devem ser listas")
        seen = set()
        for item in positives + negatives:
            annotation_id = _text(item.get("annotation_id"))
            if not annotation_id or annotation_id in seen:
                raise ValueError(f"annotation_id ausente/duplicado: {image_id}")
            seen.add(annotation_id)
        for positive in positives:
            if ("bbox" in positive) == ("point" in positive):
                raise ValueError("Positivo deve ter bbox OU point")
            if "bbox" in positive:
                validate_bbox(positive["bbox"], width, height)
            else:
                point = positive["point"]
                if (not isinstance(point, (list, tuple)) or len(point) != 2 or
                        any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in point) or
                        not (0 <= point[0] < width and 0 <= point[1] < height)):
                    raise ValueError(f"Ponto fora da imagem/inválido: {image_id}")
        for negative in negatives:
            validate_bbox(negative.get("bbox"), width, height)
            if negative.get("review_status") not in {"pending", "reviewed"}:
                raise ValueError("Negativo exige estado de revisão explícito")
            if negative["review_status"] == "reviewed" and not _text(negative.get("reviewer")):
                raise ValueError("Negativo confirmado exige revisor")
            if not validate_negative_box(negative["bbox"], positives):
                raise ValueError(f"Região negativa sobrepõe positivo: {image_id}/{negative['annotation_id']}")
        if label == 0 and positives:
            raise ValueError(f"Imagem negativa contém anotações positivas: {image_id}")
        if label == 1 and entry["reference_complete"] and not positives:
            raise ValueError(f"Imagem positiva com referência completa sem positivos: {image_id}")
        result[image_id] = dict(entry, positives=positives, negative_regions=negatives)
    return result


def load_annotations(path: str | Path, image_manifest: Sequence[Mapping] | None = None) -> dict[str, dict]:
    return validate_annotations(json.loads(Path(path).read_text(encoding="utf-8-sig")), image_manifest)


def candidate_label(bbox, annotation: Mapping) -> int | None:
    """Rótulo conservador de recorte: desconhecido é None, nunca negativo.

    Intersecção com positivo revisado rotula o recorte para classificação,
    não define a correspondência usada nas métricas de detecção.
    """
    validate_bbox(bbox, annotation["width"], annotation["height"])
    intersects = not validate_negative_box(bbox, annotation.get("positives", []))
    reviewed = annotation.get("review_status") == "reviewed" and bool(_text(annotation.get("reviewer")))
    if intersects:
        return 1 if reviewed else None
    if reviewed and annotation.get("reference_complete") and annotation.get("whole_image_label") == 0:
        return 0
    for negative in annotation.get("negative_regions", []):
        region = negative["bbox"]
        if (negative.get("review_status") == "reviewed" and _text(negative.get("reviewer")) and
                region[0] <= bbox[0] and region[1] <= bbox[1] and
                bbox[2] <= region[2] and bbox[3] <= region[3]):
            return 0
    return None
