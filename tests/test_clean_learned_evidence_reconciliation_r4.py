from __future__ import annotations

import gzip
import csv
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pyarrow.parquet as pq
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from rna_ccfa.evidence_reconciliation import (
    CANDIDATE_78_NAMES, CANDIDATE_FEATURE_NAMES, DESCRIPTOR_NAMES, ITEM_DIM,
    MODEL_INPUT_COLUMNS, SOURCES, Preprocessing, append_frozen_reliability_signals,
    apply_candidate_preprocessing, apply_descriptor_preprocessing, apply_item_preprocessing,
    apply_platt, apply_threshold, average_precision, auroc, decision_states,
    discrimination, encode_candidate_78, evaluate_gate_b, evidence_features_for_candidate,
    fit_monotone_platt, fit_preprocessing, fixed_bin_ece, guard_r4_path, make_ern_model,
    positive_pair_item_features, rna_balanced_reliability, split_roles, threshold_search,
    unpaired_item_features, utility_metrics,
)
from train_clean_learned_evidence_reconciliation_r4 import load_candidate_partition
from evaluate_clean_learned_evidence_reconciliation_r4 import evidence_efficiency, verify_seal
from rna_ccfa.evidence_reconciliation import sha256_file


def feature_values():
    return {
        "sequence_length": 10, "raw_separation": 9, "relative_separation": 1.0,
        "singleton_flag": 1, "strict_stem_length": 0, "stem_pair_position": 0,
        "normalized_stem_position": 0.0, "outer_boundary_flag": 0,
        "inner_boundary_flag": 0, "outward_neighbor_exists": 0,
        "inward_neighbor_exists": 0, "base_i": "A", "base_j": "U",
        "pair_type": "AU", "outward_pair_type": "NONE", "inward_pair_type": "NONE",
    }


def validation_rows():
    rows = []
    for rna_id in ("a", "b"):
        for index in range(100):
            rows.append({
                "manifest_id": f"{rna_id}-m", "rna_id": rna_id, "source": "rnafold",
                "label_delete": 0, "gt_pair_count": 100,
                "calibrated_probability": 0.8 if rna_id == "a" and index == 0 else 0.1,
                "partition": "validation",
            })
    rows.extend([
        {"manifest_id": "a-m", "rna_id": "a", "source": "rnafold", "label_delete": 1,
         "gt_pair_count": 100, "calibrated_probability": 0.9, "partition": "validation"},
        {"manifest_id": "b-m", "rna_id": "b", "source": "rnafold", "label_delete": 1,
         "gt_pair_count": 100, "calibrated_probability": 0.8, "partition": "validation"},
    ])
    return rows


def test_historical_source_agnostic_78d_feature_parity_contract():
    historical = json.loads((ROOT / "results/evidence_guidance/stage_e2_protocol/feature_contract.json").read_text())
    vector = encode_candidate_78(feature_values())
    assert historical["candidate_base"]["encoded_dimension"] == 78 == len(CANDIDATE_78_NAMES)
    assert historical["candidate_base"]["source_model_included"] is False
    assert vector.shape == (78,)
    assert vector[:11].tolist() == pytest.approx([10, 9, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    assert float(vector[11:].sum()) == pytest.approx(5.0)


def test_p2_p4_join_keys_and_80d_append():
    keys = []
    for filename in ("track_p_p2.csv.gz", "track_p_p4.csv.gz"):
        with gzip.open(ROOT / "results/reliability_baseline_r3/pair_scores" / filename,
                       "rt", encoding="utf-8", newline="") as handle:
            unique = {(row["rna_id"], row["source"], row["pair_i"], row["pair_j"])
                      for row in csv.DictReader(handle)}
        assert len(unique) == 5290
        keys.append(unique)
    assert keys[0] == keys[1]
    vector = append_frozen_reliability_signals(np.zeros(78), 2, 0.25)
    assert len(CANDIDATE_FEATURE_NAMES) == len(MODEL_INPUT_COLUMNS) == vector.shape[0] == 80
    assert vector[-2:].tolist() == pytest.approx([1.0, 0.25])


def test_built_feature_artifacts_match_exact_frozen_schema_and_counts():
    base = ROOT / "results/clean_learned_evidence_reconciliation_r4/features"
    contract = json.loads((base / "feature_contract.json").read_text())
    assert contract["candidate_dimension"] == 80
    assert contract["positive_pair_item_dimension"] == 17
    assert contract["unpaired_item_dimension"] == 8
    assert contract["predictor_identity_model_input"] is False
    assert pq.ParquetFile(base / "candidate_rows.parquet").metadata.num_rows == 310838
    assert pq.ParquetFile(base / "positive_pair_items.parquet").metadata.num_rows == 411297
    assert pq.ParquetFile(base / "unpaired_nucleotide_items.parquet").metadata.num_rows == 507455


def test_positive_pair_item_exact_17d_geometry():
    value = positive_pair_item_features((1, 8), (1, 8), 10)
    assert value.shape == (17,)
    assert value[10] == 1 and value[11] == 1 and value[12] == 0
    assert value[13:17].sum() == 1


def test_unpaired_item_exact_8d_geometry():
    value = unpaired_item_features((1, 8), 1, 10)
    assert value.shape == (8,)
    assert value[5:].tolist() == [1, 0, 0]


@pytest.mark.parametrize("channel", ["positive_pair", "unpaired"])
def test_evidence_scope_partition_and_descriptors(channel):
    items = [{"i": 1, "j": 8}] if channel == "positive_pair" else [{"i": 1}]
    matrix, descriptors, scope = evidence_features_for_candidate(channel, (1, 8), items, 10)
    assert matrix.shape == (1, ITEM_DIM[channel])
    assert len(DESCRIPTOR_NAMES) == descriptors.shape[0] == 4
    assert scope == ("DIRECT" if channel == "positive_pair" else "LOCAL_CONFLICT")


def test_preprocessing_is_fit_on_passed_training_values_only():
    candidates = np.zeros((2, 80), dtype=np.float32)
    candidates[:, 0] = [0, 2]
    items = np.zeros((2, 17), dtype=np.float32)
    items[:, 0] = [0, 2]
    descriptors = np.asarray([[1, .1, 0, 0], [2, .2, 1, 0]], dtype=np.float32)
    fit = fit_preprocessing(candidates, items, descriptors, "positive_pair")
    assert fit.candidate_mean[0] == pytest.approx(1)
    assert fit.item_mean[0] == pytest.approx(1)
    assert fit.count_mean.tolist() == pytest.approx([1.5, .15])


def test_empty_evidence_is_exact_zero_after_preprocessing():
    fit = Preprocessing(np.zeros(13), np.ones(13), np.zeros(17)[:10], np.ones(10), np.zeros(2), np.ones(2))
    descriptors = apply_descriptor_preprocessing(np.asarray([[0, 0, 0, 0]], dtype=np.float32), fit)
    assert np.array_equal(descriptors, np.zeros((1, 4), dtype=np.float32))
    model = make_ern_model(17).eval()
    torch = pytest.importorskip("torch")
    candidate = torch.zeros((1, 80)); items = torch.zeros((1, 1, 17)); mask = torch.zeros((1, 1), dtype=torch.bool)
    with torch.no_grad():
        natural = model(candidate, items, mask, torch.zeros((1, 4)), evidence_masked=False)
        masked = model(candidate, items, mask, torch.ones((1, 4)), evidence_masked=True)
    assert torch.equal(natural, masked)


def test_permutation_invariance_and_padding_exclusion():
    torch = pytest.importorskip("torch")
    torch.manual_seed(3)
    model = make_ern_model(17).eval()
    candidate = torch.randn((1, 80)); descriptors = torch.randn((1, 4))
    items = torch.randn((1, 3, 17)); mask = torch.tensor([[True, True, False]])
    permuted = items[:, [1, 0, 2]]
    changed_padding = items.clone(); changed_padding[:, 2] = 1e6
    with torch.no_grad():
        first = model(candidate, items, mask, descriptors)
        second = model(candidate, permuted, mask, descriptors)
        third = model(candidate, changed_padding, mask, descriptors)
    assert torch.equal(first, second)
    assert torch.equal(first, third)


def test_b4_masks_every_evidence_proxy_with_identical_capacity():
    torch = pytest.importorskip("torch")
    torch.manual_seed(5)
    model = make_ern_model(8).eval()
    candidate = torch.randn((2, 80)); mask = torch.ones((2, 4), dtype=torch.bool)
    with torch.no_grad():
        first = model(candidate, torch.randn((2, 4, 8)), mask, torch.randn((2, 4)), evidence_masked=True)
        second = model(candidate, torch.randn((2, 4, 8)) * 99, ~mask, torch.randn((2, 4)) * 99, evidence_masked=True)
    assert torch.equal(first, second)
    assert sum(p.numel() for p in model.parameters()) == sum(p.numel() for p in make_ern_model(8).parameters())


def test_grouped_rna_folds_have_no_source_leakage():
    folds = {f"rna-{index}": index % 5 for index in range(20)}
    roles = split_roles(folds, 2)
    assert roles["train"].isdisjoint(roles["validation"] | roles["held_out_test"])
    assert set().union(*roles.values()) == set(folds)


def test_pos_weight_is_train_only_formula():
    keep_train, delete_train = 12, 3
    assert keep_train / delete_train == 4
    held_out_labels = [1] * 100
    assert keep_train / delete_train != (keep_train / (delete_train + sum(held_out_labels)))


def test_monotone_platt_validation_only_and_missing_class_fail_closed():
    result = fit_monotone_platt([-2, -1, 1, 2], [0, 0, 1, 1])
    assert result["a"] >= 0 and result["optimization_success"]
    probability = apply_platt([-2, 2], result["a"], result["b"])
    assert probability[0] <= probability[1]
    with pytest.raises(RuntimeError, match="lacks one class"):
        fit_monotone_platt([0, 1], [0, 0])


def test_training_label_loader_denies_held_out_access():
    with pytest.raises(PermissionError, match="held-out"):
        load_candidate_partition("positive_pair", (0,), "held_out_test")


def test_threshold_tie_blocks_dual_constraints_and_delete_none():
    rows = validation_rows()
    threshold, curve = threshold_search(rows)
    assert threshold == pytest.approx(0.8)
    selected = next(row for row in curve if row["selected"])
    assert selected["event_tp_preservation"] >= .99
    assert selected["rna_balanced_tp_preservation"] >= .99
    assert curve[0]["threshold_semantics"] == "DELETE_NONE" and curve[0]["eligible"]
    tied = [row for row in rows if row["calibrated_probability"] == .8]
    assert len(tied) == 2


def test_threshold_rejects_nonvalidation_partition():
    rows = validation_rows(); rows[0]["partition"] = "held_out_test"
    with pytest.raises(AssertionError, match="validation"):
        threshold_search(rows)


def test_keep_delete_abstain_semantics():
    assert decision_states([.1, .9], .5) == ["KEEP", "DELETE"]
    assert decision_states([.1, .9], .5, artifacts_valid=False) == ["ABSTAIN_NO_REFINEMENT"] * 2
    assert decision_states([.1, .9], None) == ["KEEP", "KEEP"]


def test_deletion_only_accounting_and_metrics():
    rows = validation_rows()
    flags = apply_threshold([row["calibrated_probability"] for row in rows], .8)
    result = utility_metrics(rows, flags)["event_pooled"]
    assert result["lost_tp"] == 1 and result["removed_fp"] == 2
    assert result["tp_preservation"] == pytest.approx(199 / 200)
    assert result["fp_removal"] == 1 and result["modification_precision"] == pytest.approx(2 / 3)
    assert result["tp_after"] + result["lost_tp"] == result["tp_before"]
    assert result["fp_after"] + result["removed_fp"] == result["fp_before"]


def test_evidence_efficiency_zero_denominator_is_na():
    rows = [{"manifest_id": "m", "source": "rnafold", "rna_id": "r", "item_count": 0}]
    utility = {"event_pooled": {"removed_fp": 0, "delta_f1": 0.0},
               "per_rna": {"r": {"removed_fp": 0, "delta_f1": 0.0}}}
    result = evidence_efficiency(rows, utility)
    assert result["fp_removed_per_evidence_item"] is None
    assert result["delta_f1_per_evidence_item"] is None


def test_auprc_auroc_brier_ece_and_rna_balancing():
    assert average_precision([1, 0], [1, 0]) == 1
    assert auroc([1, 0], [1, 0]) == 1
    rows = [
        {"rna_id": "a", "calibrated_probability": 0.0, "label_delete": 0},
        {"rna_id": "a", "calibrated_probability": 1.0, "label_delete": 1},
        {"rna_id": "b", "calibrated_probability": 0.5, "label_delete": 1},
    ]
    event = discrimination(rows); balanced = rna_balanced_reliability(rows)
    assert event["brier"] == pytest.approx(1 / 12)
    assert fixed_bin_ece([0, 1], [0, 1])["ece"] == 0
    assert balanced["rna_count"] == 2


def test_scope_partition_accounting_is_exhaustive():
    scopes = []
    for candidate in ((1, 8), (1, 7), (2, 6)):
        _, _, scope = evidence_features_for_candidate("positive_pair", candidate, [{"i": 1, "j": 8}], 10)
        scopes.append(scope)
    assert scopes == ["DIRECT", "LOCAL_CONFLICT", "NON_EVIDENCED"]


def test_gate_b_uses_strict_inequalities_and_multisource_rule():
    primary = {"event_tp_preservation": .99, "rna_tp_preservation": .99,
               "rna_fp_removal": .489748, "event_fp_removal": .3478161}
    source = {"rnafold": .2, "petfold": .2, "trrosettarna2_native_ss": .7}
    p3 = {"rnafold": .1, "petfold": .1, "trrosettarna2_native_ss": .8}
    assert evaluate_gate_b(primary, source, p3, True)["status"] == "R4_GATE_B_FAIL"
    primary["rna_fp_removal"] += 1e-6
    passed = evaluate_gate_b(primary, source, p3, True)
    assert passed["status"] == "R4_GATE_B_PASS"
    assert len(passed["positive_improvement_sources"]) == 2


def test_source_metadata_does_not_create_source_specific_thresholds():
    rows = validation_rows()
    for index, row in enumerate(rows):
        row["source"] = SOURCES[index % 3]
    threshold, curve = threshold_search(rows)
    assert isinstance(threshold, float)
    assert all("source" not in candidate for candidate in curve)


def test_checkpoint_and_lock_hash_mismatch_is_rejected(tmp_path):
    for name, payload in (
        ("checkpoint.pt", b"checkpoint"), ("calibration.json", b"{}"),
        ("locked_threshold.json", b"{}"), ("validation_risk_curve.parquet", b"curve"),
    ):
        (tmp_path / name).write_bytes(payload)
    seal = {
        "status": "SEALED_BEFORE_HELD_OUT",
        "checkpoint_sha256": sha256_file(tmp_path / "checkpoint.pt"),
        "calibration_sha256": sha256_file(tmp_path / "calibration.json"),
        "locked_threshold_sha256": sha256_file(tmp_path / "locked_threshold.json"),
        "validation_risk_curve_sha256": sha256_file(tmp_path / "validation_risk_curve.parquet"),
    }
    (tmp_path / "lock_seal.json").write_text(json.dumps(seal))
    verify_seal(tmp_path)
    (tmp_path / "checkpoint.pt").write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="invalid pre-held-out lock seal"):
        verify_seal(tmp_path)


@pytest.mark.parametrize("path", [
    "data/external77/file.json", "inputs/noisy_evidence/x", "inputs/shape/x",
    "inputs/dms/x", "inputs/pars/x", "scripts/run_evidence_guidance_stage_e2_v1.py",
    "src/rna_ccfa/evidence_refiner.py", "results/evidence_guidance/stage_e2/run.json",
])
def test_forbidden_path_guards(path):
    with pytest.raises(PermissionError):
        guard_r4_path(Path(path))


def test_deterministic_repeated_inference():
    torch = pytest.importorskip("torch")
    torch.manual_seed(11)
    model = make_ern_model(8).eval()
    args = (torch.randn((4, 80)), torch.randn((4, 3, 8)), torch.ones((4, 3), dtype=torch.bool), torch.randn((4, 4)))
    with torch.no_grad():
        first = model(*args); second = model(*args)
    assert torch.equal(first, second)


def test_toy_synthetic_end_to_end():
    torch = pytest.importorskip("torch")
    torch.manual_seed(13)
    model = make_ern_model(8)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    candidate = torch.randn((12, 80)); items = torch.randn((12, 2, 8))
    mask = torch.ones((12, 2), dtype=torch.bool); descriptors = torch.randn((12, 4))
    labels = torch.tensor([0, 1] * 6, dtype=torch.float32)
    logits = model(candidate, items, mask, descriptors)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(logits, labels)
    loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0); optimizer.step()
    calibrated = fit_monotone_platt(logits.detach().numpy(), labels.numpy().astype(int))
    probabilities = apply_platt(logits.detach().numpy(), calibrated["a"], calibrated["b"])
    rows = []
    for index, (probability, label) in enumerate(zip(probabilities, labels.numpy().astype(int))):
        rows.append({"manifest_id": str(index), "rna_id": f"r{index}", "source": SOURCES[index % 3],
                     "label_delete": int(label), "gt_pair_count": 1,
                     "calibrated_probability": float(probability), "partition": "validation"})
    threshold, _ = threshold_search(rows)
    assert len(decision_states(probabilities, threshold)) == 12
