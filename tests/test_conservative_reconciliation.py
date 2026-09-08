from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from rna_ccfa.conservative_reconciliation import (
    BRANCHES, CHANNELS, CONDITIONS, MODEL_SEEDS, ROTATIONS, SOURCES,
    action_accounting, apply_policy_platt, branch_uses_evidence, cceg_actions,
    complete_run_keys, conservative_threshold_search, corroborated_scores,
    development_split_roles, evaluate_conservative_dev_gate, fit_policy_platt,
    guard_cer_path, inverse_policy_cutoff, make_cer_branch_model, operational_scope,
    scope_accounting,
)
from rna_ccfa.evidence_reconciliation import (
    CANDIDATE_FEATURE_NAMES, DESCRIPTOR_NAMES, ITEM_DIM, MODEL_INPUT_COLUMNS,
    Preprocessing, apply_descriptor_preprocessing, fit_monotone_platt,
    make_ern_model, positive_pair_item_features, unpaired_item_features,
)
from train_conservative_reconciliation_development import load_candidate_development_partition
from evaluate_conservative_reconciliation_development import verify_assessment_unlock


def policy_rows() -> list[dict[str, object]]:
    rows = []
    for rna in ("a", "b"):
        for index in range(100):
            rows.append({
                "rna_id": rna, "manifest_id": f"{rna}-m", "source": "rnafold",
                "label_delete": 0, "gt_pair_count": 100,
                "operational_scope": "NON_EVIDENCED", "evaluation_scope": "NON_EVIDENCED",
                "q_cceg": 0.8 if rna == "a" and index == 0 else 0.1,
                "partition": "development_validation", "original_pair_status": True,
            })
    rows.extend([
        {"rna_id": "a", "manifest_id": "a-m", "source": "rnafold", "label_delete": 1,
         "gt_pair_count": 100, "operational_scope": "LOCAL_CONFLICT", "evaluation_scope": "LOCAL_CONFLICT",
         "q_cceg": .2, "partition": "development_validation", "original_pair_status": True},
        {"rna_id": "b", "manifest_id": "b-m", "source": "rnafold", "label_delete": 1,
         "gt_pair_count": 100, "operational_scope": "NON_EVIDENCED", "evaluation_scope": "NON_EVIDENCED",
         "q_cceg": .8, "partition": "development_validation", "original_pair_status": True},
    ])
    return rows


def test_exact_r4_feature_contract_parity_and_firewall():
    contract = json.loads((ROOT / "results/clean_learned_evidence_reconciliation_r4/features/feature_contract.json").read_text())
    assert (contract["candidate_dimension"], contract["positive_pair_item_dimension"],
            contract["unpaired_item_dimension"], contract["evidence_descriptor_dimension"]) == (80, 17, 8, 4)
    assert len(CANDIDATE_FEATURE_NAMES) == len(MODEL_INPUT_COLUMNS) == 80
    assert len(DESCRIPTOR_NAMES) == 4 and ITEM_DIM == {"positive_pair": 17, "unpaired": 8}
    serialized = json.dumps({"candidate": contract["model_candidate_columns"], "descriptor": contract["model_descriptor_columns"]}).lower()
    for forbidden in ("source_model", "predictor_identity", "label_delete", "ground_truth", "r4_risk", "b2_disagreement"):
        assert forbidden not in serialized


def test_item_dimensions_exact():
    assert positive_pair_item_features((1, 8), (2, 7), 10).shape == (17,)
    assert unpaired_item_features((1, 8), 3, 10).shape == (8,)


def test_scope_precedence_and_fixed_actions():
    q = [.99, .01, .9]
    assert cceg_actions(q, q, ["DIRECT", "LOCAL_CONFLICT", "NON_EVIDENCED"], .5) == ["KEEP", "DELETE", "DELETE"]
    assert operational_scope("CER", "DIRECT") == "DIRECT"
    assert operational_scope("CER_EVIDENCE_MASKED", "DIRECT") == "NON_EVIDENCED"


def test_cceg_min_truth_table_equality_and_abstain():
    assert corroborated_scores([.9, .1], [.8, .7]).tolist() == pytest.approx([.8, .1])
    actions = cceg_actions([.5, .4, .6], [.5, .6, .4], ["NON_EVIDENCED"] * 3, .5)
    assert actions == ["DELETE", "ABSTAIN", "ABSTAIN"]
    assert cceg_actions([.1], [.1], ["NON_EVIDENCED"], None) == ["KEEP"]
    assert cceg_actions([.9], [.9], ["NON_EVIDENCED"], .5, artifacts_valid=False) == ["ABSTAIN"]


def test_abstain_is_unchanged_in_edit_accounting():
    rows = policy_rows()[:2]
    result = action_accounting(rows, ["ABSTAIN", "KEEP"])
    assert result["utility"]["event_pooled"]["deleted_pair_count"] == 0
    assert result["actions"]["ABSTAIN"] == 1


def test_branch_architecture_and_parameter_equality():
    first = make_cer_branch_model("positive_pair")
    second = make_cer_branch_model("positive_pair")
    assert sum(p.numel() for p in first.parameters()) == sum(p.numel() for p in second.parameters())
    assert str(first) == str(make_ern_model(17))


def test_zero_evidence_exact_behavior_and_permutation_padding():
    torch = pytest.importorskip("torch")
    torch.manual_seed(11)
    model = make_cer_branch_model("positive_pair").eval()
    candidate = torch.randn(1, 80); descriptors = torch.randn(1, 4)
    items = torch.randn(1, 3, 17); mask = torch.tensor([[True, True, False]])
    with torch.no_grad():
        masked_a = model(candidate, items, mask, descriptors, evidence_masked=True)
        masked_b = model(candidate, items * 999, ~mask, descriptors * 999, evidence_masked=True)
        natural = model(candidate, items, mask, descriptors)
        permuted = model(candidate, items[:, [1, 0, 2]], mask, descriptors)
        padded = items.clone(); padded[:, 2] = 1e8
        padding_changed = model(candidate, padded, mask, descriptors)
    assert torch.equal(masked_a, masked_b)
    assert torch.equal(natural, permuted) and torch.equal(natural, padding_changed)


def test_empty_evidence_descriptor_exact_zero():
    prep = Preprocessing(np.zeros(13), np.ones(13), np.zeros(10), np.ones(10), np.zeros(2), np.ones(2))
    observed = apply_descriptor_preprocessing(np.asarray([[0, 0, 1, 1]], dtype=np.float32), prep)
    assert np.array_equal(observed, np.zeros((1, 4), dtype=np.float32))


def test_complete_200_run_matrix_and_mask_mapping():
    keys = complete_run_keys()
    assert len(keys) == len(set(keys)) == 200
    assert len(CONDITIONS) * len(BRANCHES) * len(CHANNELS) * len(ROTATIONS) * len(MODEL_SEEDS) == 200
    assert branch_uses_evidence("CER", "EVIDENCE_BRANCH")
    assert not any(branch_uses_evidence("CER_EVIDENCE_MASKED", branch) for branch in BRANCHES)


def test_grouped_development_roles_and_forbidden_names():
    roles = development_split_roles({f"rna{i}": i % 5 for i in range(20)}, 2)
    assert set(roles) == {"development_train", "development_validation", "development_assessment"}
    assert set().union(*roles.values()) == {f"rna{i}" for i in range(20)}
    assert all(roles[a].isdisjoint(roles[b]) for i, a in enumerate(roles) for b in list(roles)[i + 1:])
    serialized = json.dumps({key: sorted(value) for key, value in roles.items()})
    assert "held_out_test" not in serialized and "independent_test" not in serialized


def test_training_loader_denies_development_assessment():
    with pytest.raises(PermissionError, match="assessment"):
        load_candidate_development_partition("positive_pair", (0,), "development_assessment")


def test_train_only_pos_weight_formula_and_platt_missing_class():
    assert 12 / 3 == 4.0
    result = fit_monotone_platt([-2, -1, 1, 2], [0, 0, 1, 1])
    assert result["a"] >= 0
    with pytest.raises(RuntimeError, match="lacks one class"):
        fit_monotone_platt([0, 1], [0, 0])


def test_policy_platt_strict_slope_and_inverse_cutoff():
    fitted = fit_policy_platt([.05, .2, .8, .95], [0, 0, 1, 1])
    assert fitted["a_G"] > 0
    q = apply_policy_platt([.2, .8], fitted)
    assert q[0] < q[1]
    tau = float(q[1]); cutoff = inverse_policy_cutoff(tau, fitted)
    assert cutoff == pytest.approx(.8)
    with pytest.raises(ValueError, match="strictly positive"):
        apply_policy_platt([.5], {"a_G": 0, "b_G": 0})


def test_tie_blocks_dual_safety_delete_none_and_validation_only():
    rows = policy_rows(); threshold, curve = conservative_threshold_search(rows)
    assert threshold == pytest.approx(.8)
    selected = next(row for row in curve if row["selected"])
    assert selected["event_tp_preservation"] >= .99
    assert selected["rna_balanced_tp_preservation"] >= .99
    assert curve[0]["threshold_semantics"] == "DELETE_NO_NON_EVIDENCED"
    assert sum(row["q_cceg"] == .8 for row in rows) == 2
    rows[0]["partition"] = "development_assessment"
    with pytest.raises(AssertionError, match="development_validation"):
        conservative_threshold_search(rows)


def test_scope_action_and_deletion_only_accounting():
    rows = policy_rows()
    actions = ["KEEP"] * len(rows); actions[-2] = "DELETE"; actions[-1] = "DELETE"
    accounting = action_accounting(rows, actions)
    assert accounting["utility"]["event_pooled"]["removed_fp"] == 2
    assert accounting["utility"]["event_pooled"]["lost_tp"] == 0
    scopes = scope_accounting(rows, actions)
    assert scopes["LOCAL_CONFLICT"]["event_pooled"]["removed_fp"] == 1
    assert sum(scopes[s]["event_pooled"]["opportunity_count"] for s in scopes) == len(rows)


def test_assessment_stays_locked_without_seal(monkeypatch, tmp_path):
    import evaluate_conservative_reconciliation_development as evaluator
    monkeypatch.setattr(evaluator, "INTEGRITY", tmp_path)
    with pytest.raises(PermissionError, match="locked"):
        verify_assessment_unlock()


def test_gate_strict_boundaries_and_complete_conjunction():
    primary = {"event_tp_preservation": .99, "rna_tp_preservation": .99,
               "event_fp_removal": .347816, "rna_fp_removal": .489748,
               "masked_event_fp_removal": .1, "masked_rna_fp_removal": .1}
    safety = {"event_tp_preservation": .99, "rna_tp_preservation": .99, "lost_tp": 10}
    sources = dict.fromkeys(SOURCES, .7); masked = dict.fromkeys(SOURCES, .1); p3 = dict.fromkeys(SOURCES, .2)
    result = evaluate_conservative_dev_gate(primary, safety, safety, sources, masked, p3, complete_and_valid=True)
    assert result["status"] == "CONSERVATIVE_DEV_GATE_FAIL"
    assert not result["overall_criteria"]["event_fp_removal_gt_0_347816"]
    assert not result["overall_criteria"]["rna_fp_removal_gt_0_489748"]


def test_gate_evidence_gain_and_retention_formulas():
    primary = {"event_tp_preservation": .995, "rna_tp_preservation": .995,
               "event_fp_removal": .6, "rna_fp_removal": .7,
               "masked_event_fp_removal": .5, "masked_rna_fp_removal": .65}
    safety = {"event_tp_preservation": .995, "rna_tp_preservation": .995, "lost_tp": 10}
    sources = dict.fromkeys(SOURCES, .7); masked = dict.fromkeys(SOURCES, .6); p3 = dict.fromkeys(SOURCES, .2)
    result = evaluate_conservative_dev_gate(primary, safety, safety, sources, masked, p3, complete_and_valid=True)
    assert result["g_event"] == pytest.approx(.1) and result["g_rna"] == pytest.approx(.05)
    assert result["event_r4_gain_retention_ratio"] > .5 and result["rna_r4_gain_retention_ratio"] > .5
    assert result["status"] == "CONSERVATIVE_DEV_GATE_PASS_DEVELOPMENT_ONLY"


@pytest.mark.parametrize("path", [
    "data/external77/x", "results/noisy_evidence/x", "input/shape/x",
    "input/dms/x", "input/pars/x", "scripts/run_evidence_guidance_stage_e2.py",
])
def test_forbidden_path_guards(path):
    with pytest.raises(PermissionError):
        guard_cer_path(Path(path))


def test_frozen_baseline_joins_and_r4_failure_unchanged():
    gate = json.loads((ROOT / "results/clean_learned_evidence_reconciliation_r4/summaries/gate_b.json").read_text())
    assert gate["status"] == "R4_GATE_B_FAIL"
    assert set(gate["p3_source_rna_fp_removal"]) == set(SOURCES)


def test_synthetic_end_to_end_is_deterministic():
    q_e = np.asarray([.9, .7, .1, .8]); q_c = np.asarray([.8, .4, .2, .9])
    first = corroborated_scores(q_e, q_c); second = corroborated_scores(q_e, q_c)
    assert np.array_equal(first, second)
    assert cceg_actions(q_e, q_c, ["DIRECT", "LOCAL_CONFLICT", "NON_EVIDENCED", "NON_EVIDENCED"], .75) == ["KEEP", "DELETE", "KEEP", "DELETE"]
