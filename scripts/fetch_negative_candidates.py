"""Fetch a bounded, reproducible LABIMED thin-smear subset using HTTP ranges.

Published field labels are inferred from the complete assets table and parasite
boxes, in conjunction with the authors' stated annotation protocol. They are
not diagnoses of uninfected donors. No active training manifest is changed.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import struct
import time
import urllib.error
import urllib.request
import zlib
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
API = "https://zenodo.org/api/records/15007339"
PINNED = {
    "assets.csv": "b13a71d6e73c0008041225aa6307c923",
    "bboxes.csv": "9fa2f1c0025d5c0280c440d5f0be3be5",
    "images.zip": "cdcc1c803eaf1a8857be555fc1134822",
}
PAPER = "https://doi.org/10.1371/journal.pntd.0012955"


def request(url: str, start: int | None = None, end: int | None = None) -> bytes:
    headers = {"User-Agent": "TCC-dataset-research/1.0"}
    if start is not None:
        headers["Range"] = f"bytes={start}-{end}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
                if start is not None:
                    expected = f"bytes {start}-{end}/"
                    if response.status != 206 or not response.headers.get("Content-Range", "").startswith(expected):
                        raise ValueError("Server did not honor the exact range; refusing full archive download")
                    body = response.read(end - start + 2)
                    if len(body) != end - start + 1:
                        raise ValueError("Incomplete or oversized range response")
                    return body
                return response.read(2_000_001)
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
            time.sleep(min(30, int(exc.headers.get("Retry-After", "5"))))
    raise RuntimeError("Request retries exhausted")


def load_metadata(folder: Path) -> tuple[list[dict], list[dict], dict]:
    record_path = folder / "15007339.json"
    record = json.loads(request(API))
    files = {item["key"]: item for item in record["files"]}
    for name, checksum in PINNED.items():
        if files[name]["checksum"] != "md5:" + checksum:
            raise ValueError(f"Published file changed: {name}; inspect before using")
    record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    tables = []
    for name in ("assets.csv", "bboxes.csv"):
        path = folder / name
        content = path.read_bytes() if path.exists() else request(files[name]["links"]["self"])
        if hashlib.md5(content).hexdigest() != PINNED[name]:
            raise ValueError(f"Checksum mismatch: {name}")
        path.write_bytes(content)
        tables.append(list(csv.DictReader(io.StringIO(content.decode("utf-8-sig")))))
    return *tables, files["images.zip"]


def zip_directory(file: dict, folder: Path) -> dict[str, dict]:
    size = file["size"]
    tail = request(file["links"]["self"], size - min(size, 1_000_000), size - 1)
    end = tail.rfind(b"PK\x05\x06")
    if end < 0:
        raise ValueError("ZIP directory footer missing")
    _, disk, directory_disk, disk_count, count, length, offset, _ = struct.unpack_from("<4s4H2IH", tail, end)
    if disk or directory_disk or disk_count != count or offset == 0xFFFFFFFF:
        raise ValueError("Unsupported multipart/ZIP64 archive")
    relative = offset - (size - len(tail))
    central = tail[relative:relative + length] if relative >= 0 else request(file["links"]["self"], offset, offset + length - 1)
    entries = {}
    pos = 0
    for _ in range(count):
        values = struct.unpack_from("<4s6H3I5H2I", central, pos)
        if values[0] != b"PK\x01\x02":
            raise ValueError("Invalid ZIP directory entry")
        n, extra, comment = values[10:13]
        name = central[pos + 46:pos + 46 + n].decode("utf-8")
        if name.startswith("images/") and not name.endswith("/"):
            base = Path(name).name
            if base in entries:
                raise ValueError(f"Duplicate ZIP basename: {base}")
            entries[base] = dict(member=name, flags=values[3], method=values[4], crc32=values[7], compressed_size=values[8], size=values[9], offset=values[-1])
        pos += 46 + n + extra + comment
    (folder / "zip_directory.json").write_text(json.dumps(entries, indent=2), encoding="utf-8")
    return entries


def selection(assets: list[dict], counts: collections.Counter, limit: int) -> list[dict]:
    """Cycle patient/class strata, then slide IDs; preserve scarce patients."""
    buckets = collections.defaultdict(lambda: collections.defaultdict(list))
    for row in sorted(assets, key=lambda r: (r["caseId"], r["sampleId"], r["assetFile"])):
        if row["sample_type"] == "Blood_thin":
            buckets[(row["caseId"], bool(counts[row["assetFile"]]))][row["sampleId"]].append(row)
    queues = []
    for key in sorted(buckets):
        slides = buckets[key]
        queue = []
        while any(slides.values()):
            for slide in sorted(slides):
                if slides[slide]:
                    queue.append(slides[slide].pop(0))
        queues.append(queue)
    result = []
    while any(queues) and len(result) < limit:
        for queue in queues:
            if queue and len(result) < limit:
                result.append(queue.pop(0))
    return result


def fetch_image(file: dict, entry: dict, target: Path) -> tuple[str, int, int]:
    def validate(data: bytes) -> tuple[str, int, int]:
        if len(data) != entry["size"] or zlib.crc32(data) & 0xFFFFFFFF != entry["crc32"]:
            raise ValueError(f"ZIP CRC/size mismatch: {target.name}")
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            return hashlib.sha256(data).hexdigest(), *image.size
    if target.exists():
        return validate(target.read_bytes())
    offset = entry["offset"]
    head = request(file["links"]["self"], offset, offset + 29)
    values = struct.unpack("<4s5H3I2H", head)
    if values[0] != b"PK\x03\x04" or entry["flags"] & 1:
        raise ValueError("Unsupported/encrypted ZIP entry")
    offset += 30 + values[-2] + values[-1]
    compressed = request(file["links"]["self"], offset, offset + entry["compressed_size"] - 1)
    if entry["method"] == 8:
        data = zlib.decompress(compressed, -15)
    elif entry["method"] == 0:
        data = compressed
    else:
        raise ValueError("Unsupported ZIP compression")
    result = validate(data)
    target.write_bytes(data)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/external_candidates/labimed")
    parser.add_argument("--limit", type=int, default=30, help="Maximum thin-smear images; 310 selects all")
    parser.add_argument("--max-mb", type=int, default=200, help="Hard ceiling for selected compressed image bytes")
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()
    if args.limit < 1 or args.max_mb < 1:
        parser.error("--limit and --max-mb must be positive")
    folder = args.output.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    assets, boxes, archive = load_metadata(folder)
    if len({a["assetFile"] for a in assets}) != len(assets):
        raise ValueError("Duplicate asset identifiers")
    if {b["label_str"] for b in boxes} != {"Tripanosoma"}:
        raise ValueError("Unexpected annotation labels")
    if {b["assetFile"] for b in boxes} - {a["assetFile"] for a in assets}:
        raise ValueError("Boxes without corresponding assets")
    counts = collections.Counter(b["assetFile"] for b in boxes)
    selected = selection(assets, counts, args.limit)
    entries = zip_directory(archive, folder)
    total = sum(entries[a["assetFile"]]["compressed_size"] for a in selected)
    if total > args.max_mb * 1_000_000:
        raise ValueError(f"Selection is {total / 1e6:.1f} MB, above --max-mb {args.max_mb}; no images downloaded")
    rows = []
    images = folder / "images"
    images.mkdir(exist_ok=True)
    for index, asset in enumerate(selected, 1):
        name = asset["assetFile"]
        entry = entries[name]
        digest, width, height = ("", "", "") if args.metadata_only else fetch_image(archive, entry, images / name)
        rows.append(dict(**asset, parasite_bbox_count=counts[name], published_field_label="positive" if counts[name] else "negative", label_basis="published_assets_and_bboxes_with_authors_annotation_protocol", donor_status="positive", status="metadata_only" if args.metadata_only else "downloaded_public_reference_not_active", image_path=(images / name).as_posix(), sha256=digest, width=width, height=height, archive_member=entry["member"]))
        print(f"{index}/{len(selected)} {name}", flush=True)
    with (folder / "selection.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = dict(source="https://zenodo.org/records/15007339", paper=PAPER, license="CC-BY-NC-4.0", metadata_md5=PINNED, selected=len(rows), positive=sum(r["published_field_label"] == "positive" for r in rows), negative=sum(r["published_field_label"] == "negative" for r in rows), case_ids=sorted({r["caseId"] for r in rows}), sample_ids=sorted({r["sampleId"] for r in rows}), compressed_bytes=total, metadata_only=args.metadata_only, limitations="All donors positive. Field labels use the published reference; no independent local expert review. External human acquisition differs from active murine data. No training split automatically assigned. Full ZIP MD5 not verified by selective download; entry CRC32 and local SHA256 recorded.")
    (folder / "download_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
