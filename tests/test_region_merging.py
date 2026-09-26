import hashlib
import json
from copy import deepcopy

import numpy as np
import pytest

from src.segmentation import merge_overlapping_regions, localization_hash, localization_config, propose_regions


def candidate(box, area=12):
    return {"bbox": box, "proposal_bbox": list(box), "area": area}


def test_merging_preserves_every_original_box_and_does_not_mutate_inputs():
    rng = np.random.default_rng(42)
    original = [candidate([int(x), int(y), int(x)+100, int(y)+100]) for x, y in rng.integers(0, 800, (150, 2))]
    before = deepcopy(original)
    merged = merge_overlapping_regions(original, 192)
    assert original == before
    assert len(merged) < len(original)
    for row in original:
        x1, y1, x2, y2 = row['bbox']
        assert any(a <= x1 and b <= y1 and x2 <= c and y2 <= d for a, b, c, d in [r['bbox'] for r in merged])
    assert all(r['bbox'][2]-r['bbox'][0] <= 192 and r['bbox'][3]-r['bbox'][1] <= 192 for r in merged)
    assert sum(r['merged_candidates'] for r in merged) == len(original)
    assert merge_overlapping_regions(list(reversed(original)), 192) == merged


def test_disjoint_large_and_empty_regions():
    assert merge_overlapping_regions([], 192) == []
    rows = [candidate([0, 0, 100, 100]), candidate([100, 0, 200, 100]), candidate([500, 500, 800, 800])]
    result = merge_overlapping_regions(rows, 192)
    assert [r['bbox'] for r in result] == [r['bbox'] for r in rows]


def test_old_hash_is_preserved_and_new_strategy_has_distinct_hash():
    legacy = {"method":"blackhat_otsu", "kernel_size":31, "min_contrast":8, "min_area":8,
              "max_area":2500, "min_crop_size":100, "context_fraction":0.5, "border_policy":"clip"}
    assert localization_hash(legacy) == hashlib.sha256(json.dumps(legacy, sort_keys=True).encode()).hexdigest()
    assert localization_hash(legacy) == localization_hash({**legacy, 'merge_max_size': None})
    assert localization_hash(legacy) != localization_hash({**legacy, 'merge_max_size': 192})
    for bad in [99, 100.5, True, '192']:
        with pytest.raises(ValueError, match='merge_max_size'):
            localization_config({'merge_max_size': bad})


def test_integrated_localizer_keeps_coverage():
    image = np.full((300, 300, 3), 240, dtype=np.uint8)
    for x, y in [(60,60),(90,80),(100,100),(200,200)]:
        image[y:y+5,x:x+5] = 25
    baseline, _ = propose_regions(image)
    merged, diagnostics = propose_regions(image, {'merge_max_size':192})
    assert len(merged) < len(baseline)
    assert diagnostics['candidates_before_merge'] == len(baseline)
    for row in baseline:
        x1,y1,x2,y2 = row['bbox']
        assert any(a<=x1 and b<=y1 and x2<=c and y2<=d for a,b,c,d in [r['bbox'] for r in merged])
