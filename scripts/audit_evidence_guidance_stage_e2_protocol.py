#!/usr/bin/env python3
"""Validate frozen Stage E2 contracts without training or external data."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT / "results/evidence_guidance/stage_e2_protocol"
FOLDS = ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv"
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
E1_INTEGRITY = ROOT / "results/evidence_guidance/stage_e1/evaluation_integrity.json"
EXPECTED_VERSION = "evidence_guidance_stage_e2_v1"
EXPECTED_FOLD_HASH = "810b04a3963acc7637b60fcb5c2246c765fac334f809a5af9f8f050824ed974f"
EXPECTED_SUITE_HASH = "c743913d8d0b44cbccaba74b68bebaeb1551a4095d1ae51782435c12e96d11ca"
EXPECTED_V1_FEATURE_HASH = "36659d621b443d5217273681cfce77061e0f0d1fd8c3e6c226813f129d06a1c2"
CONTRACT_FILES = (
    "feature_contract.json",
    "architecture.json",
    "split_contract.json",
    "training_contract.json",
    "threshold_contract.json",
    "evaluation_contract.json",
    "stage_e2_go_no_go.json",
)


def load_contracts() -> dict[str, dict]:
    contracts = {}
    for name in CONTRACT_FILES:
        path = CONTRACT_ROOT / name
        if not path.is_file():
            raise AssertionError(f"missing E2 contract: {path}")
        payload = json.loads(path.read_text())
        if payload.get("protocol_version") != EXPECTED_VERSION:
            raise AssertionError(f"protocol version mismatch: {name}")
        if payload.get("status") != "FROZEN_BEFORE_E2_TRAINING":
            raise AssertionError(f"contract is not frozen: {name}")
        contracts[name] = payload
    return contracts


def audit_dimensions(contracts: dict[str, dict]) -> None:
    feature = contracts["feature_contract.json"]
    architecture = contracts["architecture.json"]
    base = feature["candidate_base"]
    vocabulary_dim = sum(len(v) for v in base["categorical_vocabularies"].values())
    category_dim = vocabulary_dim + len(base["categorical_vocabularies"])
    if vocabulary_dim != base["categorical_vocabulary_indicator_dimension"] or vocabulary_dim != 62:
        raise AssertionError("candidate vocabulary indicator dimension mismatch")
    if category_dim != base["categorical_one_hot_dimension"] or category_dim != 67:
        raise AssertionError("candidate categorical dimension mismatch")
    if len(base["numeric_fields"]) != 11 or base["encoded_dimension"] != 78:
        raise AssertionError("candidate input dimension mismatch")
    if "GG" in base["categorical_vocabularies"]["inward_pair_type"]:
        raise AssertionError("historical inward-neighbor vocabulary was silently changed")
    for channel, expected in (("E2_PAIR", 17), ("E2_UNPAIRED", 8)):
        item = feature["channels"][channel]
        actual = len(item["item_continuous_fields"]) + len(item["item_binary_fields"])
        if channel == "E2_PAIR":
            actual += len(item["relation_vocabulary"])
        if actual != expected or item["item_input_dimension"] != expected:
            raise AssertionError(f"{channel} item dimension mismatch")
    fusion = architecture["fusion"]
    if architecture["candidate_encoder"]["layers"][0]["in_features"] != 78:
        raise AssertionError("candidate encoder does not match authoritative v1 dimension")
    if 64 + 64 + 2 != fusion["input_dimension"] or fusion["input_dimension"] != 130:
        raise AssertionError("fusion dimension mismatch")
    if fusion["layers"][0] != {"type": "Linear", "in_features": 130, "out_features": 128}:
        raise AssertionError("fusion projection mismatch")
    if feature["authoritative_v1_feature_schema_hash"] != EXPECTED_V1_FEATURE_HASH:
        raise AssertionError("authoritative v1 feature hash mismatch")
    for fold in range(5):
        for seed in (17, 29, 41, 53, 67):
            config_path = ROOT / f"results/selective_refiner/v1/POOLED_SOURCE_AGNOSTIC/fold_{fold}/seed_{seed}/config.json"
            config = json.loads(config_path.read_text())
            if config["feature_schema_hash"] != EXPECTED_V1_FEATURE_HASH:
                raise AssertionError(f"v1 feature hash mismatch: {config_path}")


def audit_splits(contracts: dict[str, dict]) -> None:
    if hashlib.sha256(FOLDS.read_bytes()).hexdigest() != EXPECTED_FOLD_HASH:
        raise AssertionError("frozen fold hash mismatch")
    rows = list(csv.DictReader(FOLDS.open()))
    if len(rows) != 121 or len({row["rna_id"] for row in rows}) != 121:
        raise AssertionError("frozen fold RNA count/uniqueness mismatch")
    if Counter(int(row["fold"]) for row in rows) != Counter({0: 25, 1: 24, 2: 24, 3: 24, 4: 24}):
        raise AssertionError("frozen fold size mismatch")
    components: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        components[row["component_id"]].add(int(row["fold"]))
        if int(row["source_records_per_rna"]) != 3:
            raise AssertionError("RNA does not retain all source records")
    if any(len(folds) != 1 for folds in components.values()):
        raise AssertionError("identity component crosses folds")
    split = contracts["split_contract.json"]
    if split["fold_assignment_sha256"] != EXPECTED_FOLD_HASH or split["full_pair_realization_rows_per_channel"] != 158700:
        raise AssertionError("split contract mismatch")


def audit_data_and_locks(contracts: dict[str, dict]) -> None:
    e1 = json.loads(E1_INTEGRITY.read_text())
    if e1["status"] != "PASS" or e1["e2_progression_decision"] != "E2_PROTOCOL_JUSTIFIED":
        raise AssertionError("E1 does not justify E2 protocol")
    if e1["clean_suite_sha256"] != EXPECTED_SUITE_HASH or e1["external77_accessed"] is not False:
        raise AssertionError("E1 suite/lock mismatch")
    records = [json.loads(line) for line in NORMALIZED.open()]
    source_counts = Counter(record["source_model"]["name"] for record in records)
    if len(records) != 363 or set(source_counts.values()) != {121} or len(source_counts) != 3:
        raise AssertionError("Legacy121 source matrix mismatch")
    for contract in contracts.values():
        if contract.get("external77_allowed") is True or contract.get("external77_access_allowed") is True:
            raise AssertionError("external77 is not locked")
    if (ROOT / "results/evidence_guidance/stage_e2").exists():
        raise AssertionError("Stage E2 result directory exists before training")
    if contracts["training_contract.json"]["current_new_training_runs"] != 0:
        raise AssertionError("training contract does not record zero current runs")


def audit_threshold_and_gate(contracts: dict[str, dict]) -> None:
    threshold = contracts["threshold_contract.json"]
    if threshold["same_threshold_for"] != ["E2_WITH_EVIDENCE", "E2_EVIDENCE_MASKED"]:
        raise AssertionError("masked control threshold mismatch")
    if threshold["deployability_requirement_per_channel"] != "25/25_actual_validation_selected_thresholds":
        raise AssertionError("deployability contract mismatch")
    if threshold["no_eligible_threshold_policy"]["modification_precision"] is not None:
        raise AssertionError("abstention precision must be null")
    gate = contracts["stage_e2_go_no_go.json"]
    ids = [criterion["id"] for criterion in gate["channel_criteria"]]
    if ids != [f"{letter}_{name}" for letter, name in (
        ("A", "DEPLOYABILITY"),
        ("B", "MODERATE_MODIFICATION_PRECISION"),
        ("C", "MODERATE_POOLED_PRESERVATION"),
        ("D", "EVERY_SOURCE_PRESERVATION"),
        ("E", "FULL_MATCHED_DENSITY_BREADTH"),
        ("F", "NON_EVIDENCED_PROPAGATION_DENSITY_BREADTH"),
        ("G", "SOURCE_BREADTH"),
        ("H", "NON_EVIDENCED_MODIFICATION_PRECISION"),
        ("I", "NON_EVIDENCED_PRESERVATION"),
        ("J", "EVIDENCE_RESPONSIVENESS"),
    )]:
        raise AssertionError("gate criteria are missing, reordered, or duplicated")
    if gate["external77_authorized"] is not False or gate["required_NA_result"] != "FAIL":
        raise AssertionError("gate lock/NA semantics mismatch")


def run_audit() -> dict[str, object]:
    contracts = load_contracts()
    audit_dimensions(contracts)
    audit_splits(contracts)
    audit_data_and_locks(contracts)
    audit_threshold_and_gate(contracts)
    return {
        "status": "PASS",
        "protocol_version": EXPECTED_VERSION,
        "contracts_validated": len(contracts),
        "authoritative_v1_configs_audited": 25,
        "fold_sha256": EXPECTED_FOLD_HASH,
        "clean_suite_sha256": EXPECTED_SUITE_HASH,
        "rna_count": 121,
        "source_record_count": 363,
        "primary_future_training_runs": 50,
        "current_training_runs": 0,
        "external77_accessed": False,
        "noise_experiment_run": False,
        "pretraining_status": "READY_FOR_E2_TRAINING",
    }


def main() -> None:
    print(json.dumps(run_audit(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
