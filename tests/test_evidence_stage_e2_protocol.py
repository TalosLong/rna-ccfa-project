from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_evidence_guidance_stage_e2_protocol",
    ROOT / "scripts/audit_evidence_guidance_stage_e2_protocol.py",
)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def contract(name: str) -> dict:
    return json.loads((ROOT / "results/evidence_guidance/stage_e2_protocol" / name).read_text())


def test_complete_protocol_audit_passes() -> None:
    result = AUDIT.run_audit()
    assert result["status"] == "PASS"
    assert result["current_training_runs"] == 0
    assert result["external77_accessed"] is False


def test_architecture_dimensions_are_exact() -> None:
    architecture = contract("architecture.json")
    assert architecture["candidate_encoder"]["layers"][0]["in_features"] == 78
    assert architecture["candidate_encoder"]["output_dimension"] == 64
    assert architecture["evidence_item_encoder"]["item_input_dimensions"] == {
        "E2_PAIR": 17,
        "E2_UNPAIRED": 8,
    }
    assert architecture["evidence_aggregation"]["pooled_dimension"] == 64
    assert architecture["fusion"]["input_dimension"] == 130
    assert architecture["fusion"]["layers"][-1]["out_features"] == 1


def test_primary_feature_contract_is_source_agnostic_and_gt_restricted() -> None:
    feature = contract("feature_contract.json")
    assert feature["candidate_base"]["encoded_dimension"] == 78
    assert feature["authoritative_v1_feature_schema_hash"] == "36659d621b443d5217273681cfce77061e0f0d1fd8c3e6c226813f129d06a1c2"
    assert feature["candidate_base"]["categorical_one_hot_dimension"] == 67
    assert "GG" not in feature["candidate_base"]["categorical_vocabularies"]["inward_pair_type"]
    assert feature["candidate_base"]["source_model_included"] is False
    assert feature["model_input_allowlist"] == [
        "sequence",
        "immutable_original_predicted_pairs",
        "delivered_clean_evidence_items",
    ]
    assert feature["evidence_count_descriptors"]["nominal_density_included"] is False
    assert feature["evidence_count_descriptors"]["eligible_universe_size_included"] is False


def test_empty_and_masked_evidence_use_same_zero_representation() -> None:
    architecture = contract("architecture.json")
    assert architecture["complete_empty_evidence_block"] == "66_exact_zeros_after_preprocessing"
    assert architecture["masked_control"]["same_checkpoint"] is True
    assert architecture["masked_control"]["retraining"] is False
    assert architecture["masked_control"]["separate_recalibration"] is False


def test_threshold_is_shared_and_density_global() -> None:
    threshold = contract("threshold_contract.json")
    assert threshold["same_threshold_for"] == ["E2_WITH_EVIDENCE", "E2_EVIDENCE_MASKED"]
    assert threshold["density_conditional_threshold_allowed"] is False
    assert threshold["source_conditional_threshold_allowed"] is False
    assert threshold["eligibility"]["must_hold_separately_at_every_density"] == [0, 1, 5, 10, 20, 50]


def test_gate_has_unique_binary_paths_and_locked_external_data() -> None:
    gate = contract("stage_e2_go_no_go.json")
    assert len(gate["channel_criteria"]) == 10
    assert len({criterion["id"] for criterion in gate["channel_criteria"]}) == 10
    assert gate["required_NA_result"] == "FAIL"
    assert gate["missing_run_result"] == "FAIL"
    assert gate["external77_authorized"] is False


def test_aggregation_keeps_rna_as_biological_unit() -> None:
    evaluation = contract("evaluation_contract.json")
    aggregation = evaluation["aggregation"]
    assert aggregation["biological_unit"] == "RNA"
    assert aggregation["evidence_seeds_are_biological_replicates"] is False
    assert aggregation["model_seeds_are_biological_replicates"] is False
    assert evaluation["density_interpretation"]["primary_moderate"] == [5, 10, 20]


def test_training_contract_records_no_current_training() -> None:
    training = contract("training_contract.json")
    assert training["training_started"] is False
    assert training["current_new_training_runs"] == 0
    assert training["future_primary_runs_total"] == 50
    assert training["noise_level_percent"] == 0
