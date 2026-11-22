import hashlib
import json
from pathlib import Path

import pytest

from scripts.promote_model_b import promote


def run(path,content,status='complete'):
    path.mkdir(parents=True)
    (path/'best.keras').write_bytes(content)
    digest=hashlib.sha256(content).hexdigest()
    (path/'metadata.json').write_text(json.dumps(dict(status=status,synthetic=False,checkpoint_sha256=digest,manifests={})))
    return digest


def test_incomplete_training_never_moves_or_replaces_current_model(tmp_path):
    current=tmp_path/'experiments/runs/b_val_01';candidate=current.parent/'b_next'
    run(current,b'old');run(candidate,b'new',status='running')
    archive=tmp_path/'archive/old'
    with pytest.raises(ValueError,match='incompleta'):promote(tmp_path,candidate,current,archive)
    assert (current/'best.keras').read_bytes()==b'old'
    assert candidate.is_dir() and not archive.exists()


def test_successful_promotion_preserves_old_bytes_and_moves_new_to_current(tmp_path):
    current=tmp_path/'experiments/runs/b_val_01';candidate=current.parent/'b_next'
    old=run(current,b'old');new=run(candidate,b'new')
    archive=tmp_path/'archive/old'
    comparison=tmp_path/'experiments/comparison/previous';comparison.mkdir(parents=True)
    (comparison/'protocol.json').write_text(json.dumps(dict(checkpoint={'B':dict(path=str(current/'best.keras'),sha256=old)})))
    result=promote(tmp_path,candidate,current,archive)
    assert result['status']=='complete' and result['new_checkpoint_sha256']==new
    assert (archive/'b_val_01/best.keras').read_bytes()==b'old'
    assert (current/'best.keras').read_bytes()==b'new' and not candidate.exists()
    assert json.loads((comparison/'protocol.json').read_text())['checkpoint']['B']['path']==str(archive/'b_val_01/best.keras')


def test_archive_destination_must_be_inside_workspace_archive(tmp_path):
    current=tmp_path/'experiments/runs/b_val_01';candidate=current.parent/'b_next'
    run(current,b'old');run(candidate,b'new')
    with pytest.raises(ValueError,match='Destinos'):promote(tmp_path,candidate,current,tmp_path/'not_archive')
    assert current.is_dir() and candidate.is_dir()
