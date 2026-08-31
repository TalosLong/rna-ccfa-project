#!/usr/bin/env python3
"""Reproduce the R2 execution blocker and zero-density integrity audits.

This script performs no B0/B1/B2 metric analysis and changes no eligibility
classification. It only audits the completed fixed-command execution records.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "results/global_constrained_refolding_r2"
RAW = R2 / "raw/execution_records.jsonl"
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
OUT = R2 / "integrity"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    execution = [json.loads(line) for line in RAW.open(encoding="utf-8") if line.strip()]
    if len(execution) != 7260:
        raise AssertionError(f"expected 7260 execution records, found {len(execution)}")
    failures = [row for row in execution if row["status"] == "CONSTRAINT_SATISFACTION_FAIL"]
    if len(failures) != 20:
        raise AssertionError(f"expected 20 observed constraint failures, found {len(failures)}")
    offending: dict[tuple[str, int, int], set[str]] = defaultdict(set)
    for row in failures:
        warning = str(row["stderr"])
        if "violate minimum loop size settings of 3nt, omitting constraint" not in warning:
            raise AssertionError(f"failure lacks minimum-loop warning: {row['manifest_id']}")
        missing = []
        for pair in row["delivered_pair_items_zero_based"]:
            i, j = map(int, pair)
            if j - i - 1 < 3:
                missing.append((i, j))
                offending[(row["rna_id"], i, j)].add(row["manifest_id"])
        if len(missing) != 1 or f"missing_forced_pairs={missing}" not in row["status_detail"]:
            raise AssertionError(f"failure is not exactly explained by one short-loop pair: {row['manifest_id']}")

    zero_rows = [row for row in execution if row["density_percent"] == 0]
    zero_by_rna: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in zero_rows:
        zero_by_rna[row["rna_id"]].append(row)
    zero_audit = []
    zero_pairs: dict[str, set[tuple[int, int]]] = {}
    for rna_id, rows in sorted(zero_by_rna.items()):
        output_hashes = {row["output_sha256"] for row in rows}
        input_hashes = {row["folding_input_sha256"] for row in rows}
        passed = (
            len(rows) == 10
            and {row["status"] for row in rows} == {"PASS"}
            and len(output_hashes) == 1
            and len(input_hashes) == 1
        )
        zero_audit.append(
            {
                "rna_id": rna_id,
                "realization_count": len(rows),
                "channel_count": len({row["channel"] for row in rows}),
                "evidence_seed_count": len({row["evidence_seed"] for row in rows}),
                "unique_folding_input_count": len(input_hashes),
                "unique_output_count": len(output_hashes),
                "identity_pass": passed,
            }
        )
        if not passed:
            raise AssertionError(f"zero-density reproducibility failed for {rna_id}")
        zero_pairs[rna_id] = {tuple(pair) for pair in rows[0]["pairs_zero_based"]}

    historical: dict[str, set[tuple[int, int]]] = {}
    with NORMALIZED.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record["source_model"]["name"] == "rnafold":
                historical[record["rna_id"]] = {
                    tuple(pair) for pair in record["predicted_structure"]["pairs"]
                }
    if set(historical) != set(zero_pairs):
        raise AssertionError("historical RNAfold and R2 zero-density RNA universes differ")
    historical_audit = [
        {
            "rna_id": rna_id,
            "historical_pair_count": len(historical[rna_id]),
            "r2_zero_pair_count": len(zero_pairs[rna_id]),
            "exact_pair_set_identity": historical[rna_id] == zero_pairs[rna_id],
            "context_only_not_r2_failure": True,
        }
        for rna_id in sorted(zero_pairs)
    ]

    blocker = {
        "status": "R2_EXECUTION_PARTIAL_BLOCKED_MINIMUM_LOOP_CONSTRAINT",
        "formal_metric_analysis_started": False,
        "raw_execution_sha256": sha256(RAW),
        "protocol_realization_count": len(execution),
        "eligible_execution_count": sum(row["eligibility_status"] == "R2_ELIGIBLE" for row in execution),
        "pass_count": sum(row["status"] == "PASS" for row in execution),
        "frozen_crossing_skip_count": sum(row["status"] == "R2_INELIGIBLE_CROSSING_EVIDENCE" for row in execution),
        "constraint_satisfaction_failure_count": len(failures),
        "affected_rna_count": len({row["rna_id"] for row in failures}),
        "affected_rna_ids": sorted({row["rna_id"] for row in failures}),
        "failure_count_by_density": {
            str(key): value for key, value in sorted(Counter(row["density_percent"] for row in failures).items())
        },
        "failure_count_by_channel": dict(sorted(Counter(row["channel"] for row in failures).items())),
        "offending_pairs": [
            {
                "rna_id": rna_id,
                "pair_zero_based": [i, j],
                "pair_one_based": [i + 1, j + 1],
                "enclosed_nucleotide_count": j - i - 1,
                "affected_manifest_count": len(manifest_ids),
                "affected_manifest_ids": sorted(manifest_ids),
            }
            for (rna_id, i, j), manifest_ids in sorted(offending.items())
        ],
        "failure_classification": "SOLVER_HARD_CONSTRAINT_REPRESENTABILITY_MINIMUM_LOOP_SIZE",
        "transient_process_failure": False,
        "same_command_retry_can_resolve": False,
        "reason": (
            "ViennaRNA 2.4.17 warns that each forced pair encloses only two nucleotides, "
            "violates the frozen minimum loop size of three nucleotides, and is omitted."
        ),
        "resolution_boundary": (
            "Any resolution requires a prospective decision that changes eligibility, delivered-evidence "
            "semantics, or frozen ViennaRNA model settings; no such change is made here."
        ),
        "zero_density_realization_count": len(zero_rows),
        "zero_density_rna_count": len(zero_audit),
        "zero_density_reproducibility_pass": all(row["identity_pass"] for row in zero_audit),
        "historical_rnafold_vs_r2_zero_identity_count": sum(
            row["exact_pair_set_identity"] for row in historical_audit
        ),
        "historical_rnafold_vs_r2_zero_total": len(historical_audit),
        "historical_rnafold_vs_r2_zero_identity_rate": sum(
            row["exact_pair_set_identity"] for row in historical_audit
        ) / len(historical_audit),
        "external77_accessed": False,
        "learned_model_trained": False,
    }
    write_csv(OUT / "zero_density_identity_audit.csv", zero_audit)
    write_csv(OUT / "historical_rnafold_vs_r2_zero_audit.csv", historical_audit)
    (OUT / "execution_blocker_audit.json").write_text(
        json.dumps(blocker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(blocker, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
