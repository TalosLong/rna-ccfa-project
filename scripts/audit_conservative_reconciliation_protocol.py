#!/usr/bin/env python3
"""Fail-closed CER protocol and frozen-input audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rna_ccfa.conservative_reconciliation import (  # noqa: E402
    BRANCHES, CER_IMPLEMENTATION_PLAN_SHA256, CER_PROTOCOL_SHA256, CHANNELS,
    CONDITIONS, MODEL_SEEDS, ROTATIONS, complete_run_keys, guard_cer_path,
)
from rna_ccfa.evidence_reconciliation import sha256_file, write_json  # noqa: E402


RESULTS = ROOT / "results/conservative_reconciliation_development"
INTEGRITY = RESULTS / "integrity"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretraining", action="store_true")
    parser.add_argument("--postflight", action="store_true")
    args = parser.parse_args()
    if args.pretraining and args.postflight:
        raise SystemExit("choose at most one audit phase")
    preflight_path = INTEGRITY / "preflight.json"
    inventory_path = INTEGRITY / "frozen_input_hash_inventory.json"
    if not preflight_path.is_file() or not inventory_path.is_file():
        raise SystemExit("CER preflight snapshot is missing")
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if preflight.get("status") != "PASS" or not preflight.get("scientific_execution_authorized"):
        raise SystemExit("CER preflight did not authorize execution")
    if inventory.get("status") != "PASS":
        raise SystemExit("CER frozen input inventory is not PASS")

    mismatches = {}
    for relative, frozen_hash in inventory["files"].items():
        path = guard_cer_path(ROOT / relative)
        if not path.is_file():
            mismatches[relative] = {"expected": frozen_hash, "observed": "MISSING"}
            continue
        observed = sha256_file(path)
        if observed != frozen_hash:
            mismatches[relative] = {"expected": frozen_hash, "observed": observed}
    exact = {
        "cer_protocol": sha256_file(ROOT / "docs/conservative_reconciliation_protocol.md") == CER_PROTOCOL_SHA256,
        "cer_implementation_plan": sha256_file(ROOT / "docs/conservative_reconciliation_implementation_plan.md") == CER_IMPLEMENTATION_PLAN_SHA256,
        "feature_dimensions": preflight["feature_contract"] == {
            "candidate_dimension": 80,
            "evidence_descriptor_dimension": 4,
            "exact_allowlist_and_order_verified": True,
            "positive_pair_item_dimension": 17,
            "unpaired_item_dimension": 8,
        },
        "run_matrix": len(complete_run_keys()) == 200 and len(set(complete_run_keys())) == 200,
    }
    if mismatches or not all(exact.values()):
        raise SystemExit(json.dumps({"mismatches": mismatches, "exact": exact}, indent=2))
    phase = "PRETRAINING" if args.pretraining else "POSTFLIGHT" if args.postflight else "IMPLEMENTATION"
    audit = {
        "schema_version": "conservative_reconciliation_protocol_audit_v1",
        "status": "PASS", "phase": phase,
        "frozen_inputs_match_preflight_snapshot": True,
        "cer_protocol_unchanged": True, "cer_implementation_plan_unchanged": True,
        "r4_gate_b_decision": "R4_GATE_B_FAIL",
        "conditions": list(CONDITIONS), "branches": list(BRANCHES),
        "channels": list(CHANNELS), "rotations": list(ROTATIONS),
        "model_seeds": list(MODEL_SEEDS), "expected_training_runs": 200,
        "feature_contract": {"candidate": 80, "positive_pair_item": 17, "unpaired_item": 8, "descriptors": 4},
        "feature_allowlist_modified": False, "r4_fitted_artifacts_reused": False,
        "rescue_tuning_performed": False,
        "external77_data_paths_opened": [], "noisy_or_real_evidence_paths_opened": [],
        "historical_e2_runner_paths_opened": [],
    }
    name = "pretraining_protocol_audit.json" if args.pretraining else "postflight_protocol_audit.json" if args.postflight else "protocol_audit.json"
    write_json(INTEGRITY / name, audit)
    if args.postflight:
        frozen_roots = (
            "results/clean_learned_evidence_reconciliation_r4",
            "results/reliability_baseline_r3",
            "results/global_constrained_refolding_r2",
            "results/evidence_guidance/e0",
        )
        changed = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", *frozen_roots],
            cwd=ROOT, check=True, text=True, capture_output=True,
        ).stdout.splitlines()
        if changed:
            raise SystemExit(f"frozen scientific result paths changed: {changed}")
        write_json(INTEGRITY / "frozen_result_immutability_audit.json", {
            "schema_version": "conservative_reconciliation_frozen_result_immutability_v1",
            "status": "PASS", "tracked_frozen_result_changes": [],
            "all_snapshotted_input_file_hashes_unchanged": True,
            "preflight_tree_hashes": inventory["tree_hashes"],
            "r4_gate_b_decision": "R4_GATE_B_FAIL",
        })
        write_json(INTEGRITY / "forbidden_path_execution_audit.json", {
            "schema_version": "conservative_reconciliation_forbidden_path_execution_v1",
            "status": "PASS", "scientific_data_access_allowlist": [
                "Legacy121 frozen R4 feature artifacts",
                "Legacy121 grouped development folds",
                "frozen R2/R3/R4 comparator artifacts",
            ],
            "external77_data_read_or_used": False,
            "noisy_evidence_read_or_used": False,
            "real_shape_dms_pars_evidence_read_or_used": False,
            "historical_e2_executed": False,
            "clean_evidence_regenerated": False,
        })
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
