from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evaluate_evidence_guidance_stage_e1",
    ROOT / "scripts" / "evaluate_evidence_guidance_stage_e1.py",
)
assert SPEC is not None and SPEC.loader is not None
E1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(E1)


def test_pair_scopes_are_disjoint_and_exhaustive() -> None:
    gt = {(0, 9), (1, 8), (2, 7)}
    original = {(0, 9), (1, 7), (3, 6)}
    refined = {(0, 9), (1, 8), (3, 6)}
    scopes = E1.pair_scope_partition(gt, original, refined, {(1, 8)})
    assert not (scopes[E1.SCOPES[0]] & scopes[E1.SCOPES[1]])
    assert not (scopes[E1.SCOPES[0]] & scopes[E1.SCOPES[2]])
    assert not (scopes[E1.SCOPES[1]] & scopes[E1.SCOPES[2]])
    assert set().union(*scopes.values()) == gt | original | refined


def test_unpaired_scopes_are_disjoint_and_exhaustive() -> None:
    gt = {(0, 9), (1, 8)}
    original = {(0, 9), (2, 7)}
    refined = {(0, 9)}
    scopes = E1.unpaired_scope_partition(gt, original, refined, {2})
    assert scopes[E1.SCOPES[0]] == set()
    assert scopes[E1.SCOPES[1]] == {(2, 7)}
    assert scopes[E1.SCOPES[2]] == {(0, 9), (1, 8)}
    assert set().union(*scopes.values()) == gt | original | refined


def test_hard_transformations_do_not_change_non_evidenced_pairs() -> None:
    original = {(0, 9), (1, 7), (3, 6)}
    evidence = {(1, 8)}
    refined = E1.apply_condition(
        "PAIR_HARD_ENFORCE",
        E1.POSITIVE_PAIR_EVIDENCE,
        original,
        evidence,
        set(),
        10,
    )
    scopes = E1.pair_scope_partition({(0, 9), (1, 8)}, original, refined, evidence)
    assert refined == {(0, 9), (1, 8), (3, 6)}
    assert (original & scopes[E1.SCOPES[2]]) == (refined & scopes[E1.SCOPES[2]])


def test_zero_evidence_is_identity_for_all_hard_conditions() -> None:
    original = {(0, 9), (1, 8)}
    for condition, channel in (
        ("PAIR_PROTECT_ONLY", E1.POSITIVE_PAIR_EVIDENCE),
        ("PAIR_HARD_ENFORCE", E1.POSITIVE_PAIR_EVIDENCE),
        ("UNPAIRED_HARD_DELETE", E1.UNPAIRED_NUCLEOTIDE_EVIDENCE),
    ):
        assert E1.apply_condition(condition, channel, original, set(), set(), 10) == original


def test_committed_integrity_summary_records_frozen_guards() -> None:
    import json

    integrity = json.loads(
        (ROOT / "results/evidence_guidance/stage_e1/evaluation_integrity.json").read_text()
    )
    assert integrity["status"] == "PASS"
    assert integrity["clean_manifest_count"] == 7260
    assert integrity["normalized_source_record_count"] == 363
    assert integrity["zero_density_hard_condition_equality_checks"] == 5445
    assert integrity["new_neural_training_runs"] == 0
    assert integrity["external77_accessed"] is False
    assert integrity["non_evidenced_unchanged_failures"] == 0
