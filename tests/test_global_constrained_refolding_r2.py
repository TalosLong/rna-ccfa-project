from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from rna_ccfa.global_refolding_r2 import (
    ConstraintBuildError,
    ViennaRNAConfig,
    build_constraint_string,
    full_refold_edit_decomposition,
    pair_scope_partition,
    parse_and_validate_output,
    project_to_vienna,
    run_constrained_rnafold,
    safe_ratio,
    unpaired_scope_partition,
)


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


def test_formal_adapter_coordinate_and_constraint_contract() -> None:
    assert project_to_vienna(0) == 1
    assert project_to_vienna(8) == 9
    assert build_constraint_string(9, [(0, 8)], []) == "(.......)"
    assert build_constraint_string(9, [(1, 7)], [0, 8]) == "x(.....)x"
    with pytest.raises(ConstraintBuildError, match="crossing") as error:
        build_constraint_string(9, [(0, 5), (2, 7)], [])
    assert error.value.status == "UNSUPPORTED_CROSSING_CONSTRAINT"


def test_formal_adapter_cli_and_parser_satisfy_hard_constraints() -> None:
    config = ViennaRNAConfig()
    sequence = "GGGAAACCC"
    constraint = build_constraint_string(len(sequence), [(0, 8)], [])
    run = run_constrained_rnafold(sequence, constraint, record_id="pytest_r2", config=config)
    result = parse_and_validate_output(run, sequence=sequence, forced_pairs=[(0, 8)])
    assert result["status"] == "PASS"
    assert result["constraint_satisfied"] is True
    assert [0, 8] in result["pairs_zero_based"]
    assert result["command"] == ["/usr/bin/RNAfold", "--noPS", "-C", "--enforceConstraint"]


def test_full_refold_accounting_and_na_policy() -> None:
    parts = full_refold_edit_decomposition(
        [(0, 9), (1, 8), (2, 7)],
        [(0, 9), (2, 7), (3, 6)],
        [(0, 9), (3, 6), (4, 5)],
        sequence_length=10,
    )
    assert parts["preserved_tp"] == {(0, 9)}
    assert parts["lost_tp"] == {(2, 7)}
    assert parts["removed_fp"] == {(1, 8)}
    assert parts["new_tp"] == {(3, 6)}
    assert parts["new_fp"] == {(4, 5)}
    assert safe_ratio(0, 0) is None
    assert safe_ratio(2, 4) == 0.5


def test_formal_scope_partitions_are_disjoint_and_exhaustive() -> None:
    truth = {(0, 9), (2, 7), (3, 6)}
    original = {(0, 9), (1, 8), (2, 7)}
    refolded = {(0, 9), (3, 6), (4, 5)}
    pair_scopes = pair_scope_partition(truth, original, refolded, {(0, 9)})
    assert set().union(*pair_scopes.values()) == truth | original | refolded
    assert not any(
        pair_scopes[a] & pair_scopes[b]
        for a in pair_scopes
        for b in pair_scopes
        if a < b
    )
    unpaired_scopes = unpaired_scope_partition(truth, original, refolded, {2})
    assert set().union(*unpaired_scopes.values()) == truth | original | refolded
    assert unpaired_scopes["DIRECT_EVIDENCE_EFFECT"] == set()
