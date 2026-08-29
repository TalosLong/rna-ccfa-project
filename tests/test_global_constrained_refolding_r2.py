from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_global_constrained_refolding_r2",
    ROOT / "scripts" / "audit_global_constrained_refolding_r2.py",
)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_project_to_vienna_coordinates_are_one_based() -> None:
    assert AUDIT.project_to_vienna(0) == 1
    assert AUDIT.project_to_vienna(8) == 9


def test_constraint_builder_preserves_exact_pair_and_unpaired_semantics() -> None:
    assert AUDIT.build_constraint_string(9, [(0, 8)], []) == "(.......)"
    assert AUDIT.build_constraint_string(9, [(1, 7)], [0, 8]) == "x(.....)x"
    assert AUDIT.build_constraint_string(12, [(0, 11), (1, 10)], []) == "((........))"


def test_constraint_builder_rejects_unsatisfiable_or_crossing_constraints() -> None:
    with pytest.raises(ValueError, match="crossing"):
        AUDIT.build_constraint_string(9, [(0, 5), (2, 7)], [])
    with pytest.raises(ValueError, match="paired and unpaired"):
        AUDIT.build_constraint_string(9, [(0, 8)], [0])


def test_rnafold_toy_sanity_suite_passes() -> None:
    results = AUDIT.toy_audit()
    assert len(results) == 7
    assert all(row["constraint_satisfied"] for row in results)


def test_clean_suite_crossing_audit_is_explicit_blocker() -> None:
    audit = AUDIT.crossing_manifest_audit()
    assert audit["clean_manifest_count"] == 7260
    assert audit["pair_channel_manifest_count"] == 3630
    assert audit["crossing_pair_manifest_count"] == 87
    assert audit["crossing_rna_count"] == 11
    assert audit["standard_non_pseudoknot_dbn_can_represent_all_pair_constraints"] is False
