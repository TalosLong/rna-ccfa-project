import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.audit_r2_manifest_eligibility import canonical_pairs, classify, crossing_count


def manifest(channel="POSITIVE_PAIR_EVIDENCE", items=None):
    return {
        "rna_id": "toy", "density_percent": 5, "evidence_seed": 101,
        "manifest_id": "toy", "manifest_payload_sha256": "x",
        "delivered_item_count": len(items or []), "evidence_channel": channel,
        "items": items or [],
    }


def pair(i, j):
    return {"delivered_evidence_item": {"i": i, "j": j}}


def test_nested_and_disjoint_are_eligible():
    assert classify(manifest(items=[pair(0, 9), pair(1, 8)]))["eligibility_status"] == "R2_ELIGIBLE"
    assert classify(manifest(items=[pair(0, 2), pair(4, 6)]))["eligibility_status"] == "R2_ELIGIBLE"


def test_crossing_and_multiple_crossings_are_ineligible():
    row = classify(manifest(items=[pair(0, 4), pair(2, 7), pair(5, 9)]))
    assert row["eligibility_status"] == "R2_INELIGIBLE_CROSSING_EVIDENCE"
    assert row["crossing_pair_count"] == 2


def test_empty_single_pair_and_unpaired_are_eligible():
    assert classify(manifest(items=[]))["eligibility_status"] == "R2_ELIGIBLE"
    assert classify(manifest(items=[pair(1, 3)]))["eligibility_status"] == "R2_ELIGIBLE"
    assert classify(manifest(channel="UNPAIRED_NUCLEOTIDE_EVIDENCE", items=[]))["eligibility_status"] == "R2_ELIGIBLE"


def test_order_and_index_orientation_invariant():
    a = [pair(8, 1), pair(9, 0)]
    b = list(reversed(a))
    assert canonical_pairs(a) == canonical_pairs(b) == [(0, 9), (1, 8)]
    assert crossing_count(canonical_pairs(a)) == 0


def test_full_audit_counts():
    script = Path(__file__).parents[1] / "scripts/audit_r2_manifest_eligibility.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["clean_manifest_count"] == 7260
    assert payload["pair_manifest_count"] == 3630
    assert payload["pair_eligible_count"] == 3543
    assert payload["pair_ineligible_crossing_count"] == 87
