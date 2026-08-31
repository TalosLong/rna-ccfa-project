from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from rna_ccfa.global_refolding_r2 import (
    ConstraintBuildError,
    ViennaRNAConfig,
    build_constraint_string,
    minimum_loop_compatible,
    pair_capability_flags,
    parse_and_validate_output,
    run_constrained_rnafold,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_r2_manifest_eligibility_v1_0_2",
    ROOT / "scripts/audit_r2_manifest_eligibility_v1_0_2.py",
)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def pair_item(i: int, j: int) -> dict:
    return {"delivered_evidence_item": {"i": i, "j": j}}


def pair_manifest(pairs: list[tuple[int, int]], *, length: int = 20) -> dict:
    return {
        "manifest_id": "toy",
        "manifest_payload_sha256": "toy-hash",
        "rna_id": "toy-rna",
        "evidence_channel": "POSITIVE_PAIR_EVIDENCE",
        "density_percent": 5,
        "evidence_seed": 101,
        "delivered_item_count": len(pairs),
        "sequence_length": length,
        "items": [pair_item(i, j) for i, j in pairs],
    }


@pytest.mark.parametrize("pair", [(0, 2), (0, 3)])
def test_minimum_loop_incompatible_boundaries(pair: tuple[int, int]) -> None:
    assert minimum_loop_compatible(pair) is False
    row = AUDIT.classify(pair_manifest([pair]))
    assert row["minimum_loop_flag"] is True
    assert row["eligibility_status"] == "R2_INELIGIBLE_MINIMUM_LOOP_EVIDENCE"


def test_minimum_loop_first_compatible_boundary() -> None:
    assert minimum_loop_compatible((0, 4)) is True
    row = AUDIT.classify(pair_manifest([(0, 4)]))
    assert row["minimum_loop_flag"] is False
    assert row["eligibility_status"] == "R2_ELIGIBLE"


def test_nested_long_pairs_empty_and_single_valid_are_eligible() -> None:
    assert AUDIT.classify(pair_manifest([]))["eligibility_status"] == "R2_ELIGIBLE"
    assert AUDIT.classify(pair_manifest([(1, 8)]))["eligibility_status"] == "R2_ELIGIBLE"
    nested = AUDIT.classify(pair_manifest([(0, 15), (1, 14), (2, 13)]))
    assert nested["eligibility_status"] == "R2_ELIGIBLE"


def test_crossing_and_short_flags_are_both_retained() -> None:
    row = AUDIT.classify(pair_manifest([(0, 6), (3, 9), (10, 13)]))
    assert row["crossing_flag"] is True
    assert row["minimum_loop_flag"] is True
    assert row["eligibility_status"] == "R2_INELIGIBLE_MULTIPLE_CAPABILITIES"


def test_capability_classification_is_input_order_invariant() -> None:
    pairs = [(0, 12), (2, 8), (14, 18)]
    first = pair_capability_flags(pairs, 20)
    second = pair_capability_flags(list(reversed(pairs)), 20)
    assert first == second
    assert first == {
        "crossing_flag": False,
        "minimum_loop_flag": False,
        "minimum_pair_separation": 4,
    }


def test_constraint_builder_fails_closed_on_minimum_loop_pair() -> None:
    with pytest.raises(ConstraintBuildError) as error:
        build_constraint_string(5, [(0, 3)], [])
    assert error.value.status == "UNSUPPORTED_MINIMUM_LOOP_CONSTRAINT"


def test_vienna_rna_minimum_loop_boundary_under_frozen_command() -> None:
    config = ViennaRNAConfig()

    incompatible_run = run_constrained_rnafold(
        "GAACU", "(..).", record_id="r2_v1_0_2_incompatible", config=config
    )
    incompatible = parse_and_validate_output(
        incompatible_run, sequence="GAACU", forced_pairs=[(0, 3)]
    )
    assert incompatible["status"] == "CONSTRAINT_SATISFACTION_FAIL"
    assert "minimum loop size settings of 3nt" in incompatible["stderr"]

    compatible_constraint = build_constraint_string(5, [(0, 4)], [])
    compatible_run = run_constrained_rnafold(
        "GAAAC", compatible_constraint, record_id="r2_v1_0_2_compatible", config=config
    )
    compatible = parse_and_validate_output(
        compatible_run, sequence="GAAAC", forced_pairs=[(0, 4)]
    )
    assert compatible["status"] == "PASS"
    assert compatible["constraint_satisfied"] is True


def test_full_v1_0_2_audit_is_coordinate_only_and_deterministic() -> None:
    script = ROOT / "scripts/audit_r2_manifest_eligibility_v1_0_2.py"
    completed = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, check=True
    )
    summary = json.loads(completed.stdout)
    assert summary["pair_manifest_count"] == 3630
    assert summary["unpaired_eligible_count"] == 3630
    assert summary["pair_eligible_count"] == (
        summary["pair_manifest_count"]
        - summary["pair_capability_ineligible_unique_count"]
    )
