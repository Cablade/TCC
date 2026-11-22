"""Restringe os comandos reais ao conteúdo do ZIP autorizado neste TCC."""
from pathlib import Path
import json

from . import data_protocol as dp
from .data_pipeline import file_sha256

ROOT = Path(__file__).resolve().parents[1]


def supplementary_inventory(policy_path, root=ROOT):
    path = Path(policy_path)
    if not path.is_absolute(): path = root / path
    policy = json.loads(path.read_text(encoding="utf-8-sig"))
    if "policies" in policy:
        if not isinstance(policy["policies"], list) or not policy["policies"]:
            raise ValueError("Lista de políticas suplementares vazia/inválida.")
        inventory, policies = {}, {}
        for child in policy["policies"]:
            child_policy, child_rows = supplementary_inventory(child, root)
            if "policies" in child_policy or set(inventory) & set(child_rows):
                raise ValueError("Políticas aninhadas ou IDs suplementares repetidos.")
            inventory.update(child_rows)
            policies.update({identifier: child_policy for identifier in child_rows})
        return {**policy, "source": sorted({p["source"] for p in policies.values()}),
                "_by_image": policies}, inventory
    source = policy.get("source")
    kaggle = source == "https://www.kaggle.com/datasets/paultimothymooney/blood-cells"
    barcelona = source == "https://data.mendeley.com/datasets/snkd93bnjr/1"
    if (policy.get("negative_only") is not True or not (kaggle or barcelona)
            or (kaggle and policy.get("allowed_member_prefix") != "dataset-master/dataset-master/JPEGImages/")):
        raise ValueError("Política suplementar não corresponde aos originais autorizados.")
    inventory_path = Path(policy["inventory"])
    if not inventory_path.is_absolute(): inventory_path = root / inventory_path
    if file_sha256(inventory_path) != policy["inventory_sha256"]:
        raise ValueError("Inventário de originais suplementares alterado.")
    if kaggle and file_sha256(policy["archive"]) != policy["expected_archive_sha256"]:
        raise ValueError("ZIP suplementar não corresponde aos bytes inventariados.")
    rows = dp.read_manifest(inventory_path)
    if len({r["image_id"] for r in rows}) != len(rows):
        raise ValueError("IDs repetidos no inventário suplementar.")
    if barcelona:
        for key in ("approval", "reviewed", "partition_manifest"):
            target = Path(policy[key])
            if not target.is_absolute(): target = root / target
            if file_sha256(target) != policy[key + "_sha256"]:
                raise ValueError("Reserva/aprovação Barcelona alterada: " + key)
        approval_path = Path(policy["approval"])
        if not approval_path.is_absolute(): approval_path = root / approval_path
        approval = json.loads(approval_path.read_text(encoding="utf-8-sig"))
        identifiers = {r["image_id"] for r in rows}
        if (approval.get("status") != "complete" or approval.get("training_allowed") is not True
                or len(rows) != 20 or set(approval.get("training_image_ids", [])) != identifiers
                or policy.get("allowed_splits") != ["train"]):
            raise ValueError("Somente as 20 imagens Barcelona explicitamente reservadas podem treinar.")
        partition_path = Path(policy["partition_manifest"])
        if not partition_path.is_absolute(): partition_path = root / partition_path
        partition = dp.read_manifest(partition_path)
        if len(partition) != 200 or {r["image_id"] for r in partition if r["split"] == "train"} != identifiers:
            raise ValueError("Reserva Barcelona incompatível com a divisão 20/180.")
        dp.validate_partitions(partition)
        reviewed_path = Path(policy["reviewed"])
        if not reviewed_path.is_absolute(): reviewed_path = root / reviewed_path
        references = dp.load_annotations(reviewed_path, rows)
        for row in rows:
            ref = references[row["image_id"]]
            if (row["split"] != "train" or ref["whole_image_label"] != 0
                    or ref["review_status"] != "reviewed" or not ref["reference_complete"]):
                raise ValueError("Barcelona exige revisão negativa completa e reserva de treino.")
    return policy, {row["image_id"]: row for row in rows}


def validate_supplementary_crops(crops, policy_path, root=ROOT):
    policy, inventory = supplementary_inventory(policy_path, root)
    for identifier in set(crops["image_id"]) & set(inventory):
        child = policy.get("_by_image", {}).get(identifier, policy)
        external = crops[crops["image_id"] == identifier]
        if (set(external["label"].astype(int)) != {0}
                or len(external) > int(child["max_crops_per_image"])
                or ("split" in external and not set(external["split"]) <= set(child.get("allowed_splits", ["train", "val", "development"])) )):
            raise ValueError("Originais externos aceitam somente negativos, partições autorizadas e no máximo quatro recortes por imagem.")


def validate_active_images(rows, *, root=ROOT, supplementary_policy=None):
    config = json.loads((root / "configs/dataset.json").read_text(encoding="utf-8-sig"))
    inventory = root / config["output_dir"] / "eligible_inventory.csv"
    allowed = {row["image_id"]: row for row in dp.read_manifest(inventory)}
    supplemental, external = (supplementary_inventory(supplementary_policy, root)
                              if supplementary_policy is not None else ({}, {}))
    reservation = json.loads((root / "data/annotations/negative_preselection_v1/development_reservation.json").read_text(encoding="utf-8-sig"))
    reserved_ids = {row["image_id"] for row in reservation["images"]}
    reserved_hashes = {row["sha256"] for row in reservation["images"]}
    reserved_groups = {row["group_id"] for row in rows
                       if row["image_id"] in reserved_ids or row["sha256"] in reserved_hashes}
    archives = set()
    if not rows:
        raise ValueError("Manifesto real vazio.")
    for row in rows:
        original = allowed.get(row["image_id"])
        if original is None and row["image_id"] in external:
            original = external[row["image_id"]]
            child = supplemental.get("_by_image", {}).get(row["image_id"], supplemental)
            if any(str(row.get(key)) != str(original[key]) for key in
                   ("sha256", "width", "height", "source", "group_id", "path")):
                raise ValueError("Imagem suplementar fora do inventário ou grupo/conteúdo alterado.")
            locator = row["path"].replace("\\", "/")
            if child["source"] == "https://www.kaggle.com/datasets/paultimothymooney/blood-cells":
                if not locator.startswith("zip://") or "!" not in locator:
                    raise ValueError("Original suplementar deve vir do ZIP inventariado.")
                member = locator.split("!", 1)[1]
                if not member.startswith(child["allowed_member_prefix"]) or member != original["original_member"]:
                    raise ValueError("Versão aumentada ou membro externo não autorizado.")
            else:
                source_path = Path(row["path"]).resolve()
                image_root = (root / child["image_root"]).resolve()
                if not source_path.is_relative_to(image_root) or file_sha256(source_path) != row["sha256"]:
                    raise ValueError("Original Barcelona fora da pasta autorizada ou pixels alterados.")
            if row.get("split") not in set(child.get("allowed_splits", ["train", "val", "development"])):
                raise ValueError("Originais externos examinados não podem integrar o teste.")
            continue
        if original is None or any(str(row.get(key)) != str(original[key])
                                   for key in ("sha256", "width", "height", "source")):
            raise ValueError("Imagem fora do inventário público autorizado ou identidade alterada.")
        locator = row["path"].replace("\\", "/")
        if not locator.startswith("zip://") or "!" not in locator:
            raise ValueError("Imagem real deve apontar para o ZIP público autorizado.")
        archive, member = locator[6:].split("!", 1)
        if member != original["path"].split("!", 1)[1]:
            raise ValueError("Membro do ZIP diverge do inventário autorizado.")
        archives.add(Path(archive))
        if row.get("split") == "test" and (row["image_id"] in reserved_ids
                or row["sha256"] in reserved_hashes or row["group_id"] in reserved_groups):
            raise ValueError("Imagem/grupo examinado no desenvolvimento não pode integrar o teste.")
    # O nome pode mudar durante transporte; somente bytes idênticos são aceitos.
    for archive in archives:
        if file_sha256(archive) != config["expected_sha256"]:
            raise ValueError("ZIP não corresponde ao conteúdo público autorizado.")
    result = {"images": len(rows), "archives": len(archives), "source": config["source"]}
    if supplementary_policy is not None:
        result.update(supplementary_images=sum(row["image_id"] in external for row in rows),
                      supplementary_source=supplemental["source"])
    return result
