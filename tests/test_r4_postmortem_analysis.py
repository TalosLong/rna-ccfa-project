from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze_r4_failure_mechanisms import (  # noqa: E402
    FROZEN_HASHES,
    boundary_status,
    calibrated_risk_bin,
    p2_agreement_bin,
    p4_risk_bin,
    risk_difference_bin,
    sequence_separation_bin,
    stem_position_bin,
)
from rna_ccfa.evidence_reconciliation import sha256_file  # noqa: E402


POSTMORTEM = ROOT / "results/clean_learned_evidence_reconciliation_r4/postmortem"


def load_summary() -> dict:
    return json.loads((POSTMORTEM / "diagnostic_summary.json").read_text())


def load_breakdowns() -> list[dict[str, str]]:
    with (POSTMORTEM / "diagnostic_breakdowns.csv").open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_postmortem_bin_contracts_are_fixed_and_total():
    assert [sequence_separation_bin(value) for value in (4, 9, 10, 19, 20, 49, 50, 99, 100)] == [
        "04-09", "04-09", "10-19", "10-19", "20-49", "20-49", "50-99", "50-99", "100+",
    ]
    assert stem_position_bin(1, 0) == "SINGLETON"
    assert stem_position_bin(0, 0.25) == "[0.25,0.50)"
    assert boundary_status(0, 1, 1) == "BOTH_BOUNDARIES"
    assert p2_agreement_bin(0.5) == "1_of_2_other_sources"
    with pytest.raises(AssertionError):
        p2_agreement_bin(0.25)
    assert p4_risk_bin(0.9) == "[0.00,0.10)"
    assert calibrated_risk_bin(1.0) == "[0.9,1.0]"
    assert risk_difference_bin(0.02) == "[0.02,0.10)"


def test_postmortem_reverifies_every_frozen_input_hash():
    summary = load_summary()
    assert summary["frozen_input_hashes"] == FROZEN_HASHES
    for relative, expected in FROZEN_HASHES.items():
        assert sha256_file(ROOT / relative) == expected


def test_postmortem_preserves_gate_and_scientific_firewall():
    summary = load_summary()
    assert summary["status"] == "POSTHOC_DIAGNOSTIC_COMPLETE"
    assert summary["analysis_role"] == "DESCRIPTIVE_HYPOTHESIS_GENERATION_ONLY"
    assert summary["frozen_gate_b_decision_unchanged"] == "R4_GATE_B_FAIL"
    assert summary["gate_b_miss"]["preservation_gap"] == pytest.approx(0.00031758517091728944)
    assert summary["gate_b_miss"]["excess_mean_lost_tp_event_scale"] == pytest.approx(82.77)
    assert summary["gate_b_miss"]["threshold_rescue_permitted"] is False
    assert set(summary["scientific_firewall"].values()) == {False}


def test_scope_attribution_accounts_for_net_ern_minus_b4_effect():
    summary = load_summary()["ern_vs_b4_attribution_mean_per_seed"]
    assert summary["net_additional_removed_fp"] == pytest.approx(4464.6)
    assert summary["local_conflict_additional_removed_fp"] == pytest.approx(2500.6)
    assert summary["non_evidenced_additional_removed_fp"] == pytest.approx(1964.0)
    assert summary["fraction_of_net_additional_fp_removal_from_local_conflict"] == pytest.approx(
        2500.6 / 4464.6
    )
    assert summary["non_evidenced_additional_lost_tp"] == pytest.approx(696.2)
    assert summary["direct_change_in_lost_tp"] == pytest.approx(-122.0)
    assert summary["net_additional_lost_tp"] == pytest.approx(696.2 - 122.0)


def test_required_diagnostic_dimensions_and_scope_partition_are_present():
    rows = load_breakdowns()
    dimensions = {row["dimension"] for row in rows}
    assert {
        "scope", "source", "channel", "evidence_density", "sequence_separation",
        "stem_position", "boundary_status", "pair_type", "p2_agreement", "p4_bpp_risk",
        "calibrated_ern_risk", "ern_minus_b4_risk",
    } <= dimensions
    scopes = {row["stratum"]: row for row in rows if row["dimension"] == "scope"}
    assert set(scopes) == {"DIRECT", "LOCAL_CONFLICT", "NON_EVIDENCED"}
    assert sum(float(row["mean_event_count_per_seed"]) for row in scopes.values()) == pytest.approx(310838)
    assert float(scopes["LOCAL_CONFLICT"]["ern_modification_precision"]) == pytest.approx(1.0)
    assert float(scopes["NON_EVIDENCED"]["mean_delta_lost_tp_per_seed"]) == pytest.approx(696.2)


def test_channel_difference_is_recorded_without_posthoc_selection():
    summary = load_summary()
    stability = summary["channel_stability"]
    assert stability == {
        "positive_pair_higher_preservation_seed_summaries": 4,
        "seed_summary_comparisons": 5,
        "positive_pair_higher_preservation_fold_summaries": 3,
        "fold_summary_comparisons": 5,
        "positive_pair_higher_preservation_fold_seed_cells": 12,
        "fold_seed_comparisons": 25,
    }
    assert summary["scientific_firewall"]["seed_or_channel_selected"] is False


def test_authoritative_state_records_exact_future_branch_and_independence_boundary():
    paths = (
        "AGENTS.md", "CONTEXT.md", "STATUS.md", "tasks/TODO.md", "plan/research_plan.md",
        "plan/timeline.md", "docs/reboot_v2_decisions.md",
        "docs/reboot_v2_claim_evidence_map.md", "docs/r4_failure_analysis_and_future_decision.md",
    )
    contents = {path: (ROOT / path).read_text() for path in paths}
    for text in contents.values():
        assert "NEW_HYPOTHESIS_JUSTIFIED_PROTOCOL_NOT_FROZEN" in text
        assert "R4_GATE_B_FAIL" in text
    for path in ("AGENTS.md", "STATUS.md", "tasks/TODO.md", "plan/research_plan.md"):
        assert "FREEZE_NEW_PROSPECTIVE_CONSERVATIVE_RECONCILIATION_PROTOCOL" in contents[path]
    postmortem = contents["docs/r4_failure_analysis_and_future_decision.md"]
    assert "Legacy121-only result may be promoted as independent validation" in postmortem
    assert "external77 remains a one-shot independent test" in postmortem
    assert "R5_NOT_AUTHORIZED" in postmortem
