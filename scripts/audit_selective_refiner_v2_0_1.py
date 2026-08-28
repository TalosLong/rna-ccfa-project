#!/usr/bin/env python3
"""Audit v1 threshold availability and v2.0.1 gate completeness."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "results/selective_refiner/v1"
OUT = ROOT / "results/selective_refiner/v2_protocol_audit"
CONTRACT = OUT / "v2_go_no_go_v2_0_1.json"
VARIANTS = ("POOLED_SOURCE_AGNOSTIC", "POOLED_SOURCE_AWARE")
SEEDS = (17, 29, 41, 53, 67)


def main() -> None:
    rows = []
    counts = {}
    for variant in VARIANTS:
        deployable = 0
        for fold in range(5):
            for seed in SEEDS:
                path = V1 / variant / f"fold_{fold}" / f"seed_{seed}" / "selected_threshold.json"
                payload = json.loads(path.read_text(encoding="utf-8"))
                has_threshold = payload["threshold"] is not None
                deployable += has_threshold
                rows.append({
                    "variant": variant,
                    "fold": fold,
                    "seed": seed,
                    "selected_threshold": payload["threshold"],
                    "v1_status": payload["status"],
                    "deployable": str(has_threshold).lower(),
                    "v2_0_1_matched_behavior": "APPLY_THRESHOLD" if has_threshold else "ABSTAIN_NO_REFINEMENT",
                })
        counts[variant] = {"deployable": deployable, "nondeployable": 25 - deployable}

    if counts != {
        "POOLED_SOURCE_AGNOSTIC": {"deployable": 20, "nondeployable": 5},
        "POOLED_SOURCE_AWARE": {"deployable": 16, "nondeployable": 9},
    }:
        raise AssertionError(f"unexpected v1 threshold availability: {counts}")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    required = {
        "primary_condition", "matched_baseline", "abstention_semantics",
        "metric_aggregation", "absolute_gates", "matched_improvement_gates",
        "catastrophic_degradation", "binary_decision_policy", "external77_policy",
    }
    if not required.issubset(contract):
        raise AssertionError("v2.0.1 gate contract is incomplete")
    if contract["binary_decision_policy"]["undefined_required_gate"] != "FAIL":
        raise AssertionError("undefined required comparisons must resolve to FAIL")
    if contract["cross_threshold_deployability"]["required_actual_thresholds"] != 25:
        raise AssertionError("CROSS must obtain 25 actual validation-selected thresholds")
    if contract["external77_policy"] != "LOCKED_UNLESS_PRIMARY_V2_DEVELOPMENT_GATE_PASS":
        raise AssertionError("external77 lock changed")

    path = OUT / "v1_pooled_threshold_availability_v2_0_1.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"threshold_counts": counts, "gate_contract": "COMPLETE_BINARY", "v2_training_started": False, "external77_accessed": False}, indent=2))


if __name__ == "__main__":
    main()
