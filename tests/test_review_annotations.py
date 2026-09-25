import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PIL import Image
import pytest

from scripts.review_annotations import ReviewStore, make_server
from src import data_protocol as dp


@pytest.fixture
def store(tmp_path):
    image = tmp_path / "image.png"
    Image.new("RGB", (100, 80), "white").save(image)
    rows = dp.build_inventory([image])["images"]
    rows[0]["split"] = "train"
    inventory = tmp_path / "inventory.csv"
    dp.write_manifest(rows, inventory)
    payload = dp.annotation_template(rows)
    payload["images"][0]["positives"] = [{"annotation_id": "p1", "point": [50, 40]}]
    source = tmp_path / "source.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    return ReviewStore(inventory, source, tmp_path / "reviewed.json")


def request_for(store, **changes):
    return dict(image_id=store.rows[0]["image_id"], reviewer="Revisor de teste sintético",
                confirmed=True, bbox=[0, 0, 20, 20], **changes)


def test_save_resume_remove_preserves_original_and_completeness(store):
    original_bytes = store.source.read_bytes()
    result = store.change(request_for(store))
    entry = result["annotation"]
    assert entry["positives"] == [{"annotation_id": "p1", "point": [50, 40]}]
    assert entry["reference_complete"] is False
    assert entry["whole_image_label"] is None
    assert entry["review_status"] == "pending"
    assert dp.candidate_label([0, 0, 10, 10], entry) == 0
    assert dp.candidate_label([60, 50, 70, 60], entry) is None
    resumed = ReviewStore(store.inventory_path, store.source, store.output)
    resumed.change(request_for(resumed, action="remove", annotation_id=entry["negative_regions"][0]["annotation_id"]))
    assert resumed.payload["images"][0]["negative_regions"] == []
    assert len(resumed.payload["visual_review"]["history"]) == 2
    assert store.source.read_bytes() == original_bytes
    assert store.output.with_name(store.output.name + ".bak").exists()


@pytest.mark.parametrize("changes", [
    {"reviewer": " "}, {"confirmed": False}, {"bbox": [40, 30, 60, 50]},
    {"bbox": [0, 0, 101, 20]}, {"bbox": [0, 0, 0, 20]}, {"image_id": []},
])
def test_reject_invalid_review_without_writing(store, changes):
    request = request_for(store)
    request.update(changes)
    with pytest.raises(ValueError):
        store.change(request)
    assert not store.output.exists()


def test_test_partition_hidden_and_blocked(store):
    store.rows[0]["split"] = "test"
    assert store.list_images() == []
    with pytest.raises(ValueError, match="teste"):
        store.change(request_for(store))


def test_resume_rejects_modified_positive(store):
    store.change(request_for(store))
    payload = json.loads(store.output.read_text(encoding="utf-8"))
    payload["images"][0]["positives"] = []
    store.output.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="referência original"):
        ReviewStore(store.inventory_path, store.source, store.output)


def test_detect_external_changes_and_original_output_path(store):
    with pytest.raises(ValueError, match="diferente"):
        ReviewStore(store.inventory_path, store.source, store.source)
    store.output.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="mudou fora"):
        store.change(request_for(store))


def test_http_reads_image_and_requires_session_for_write(store):
    server = make_server(store, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base + "/") as response:
            assert b"<canvas" in response.read()
        with urlopen(base + "/api/state") as response:
            state = json.load(response)
        with urlopen(base + "/api/image?id=" + store.rows[0]["image_id"]) as response:
            assert response.read().startswith(b"\x89PNG")
        data = json.dumps(request_for(store)).encode()
        with pytest.raises(HTTPError) as error:
            urlopen(Request(base + "/api/review", data=data, method="POST"))
        assert error.value.code == 403
        with urlopen(Request(base + "/api/review", data=data, method="POST",
                            headers={"X-Review-Token": state["token"]})) as response:
            assert json.load(response)["saved"] is True
        with pytest.raises(HTTPError) as error:
            urlopen(Request(base + "/api/state", headers={"Host": "example.invalid"}))
        assert error.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
