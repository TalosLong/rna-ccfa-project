#!/usr/bin/env python3
"""Freeze R2 v1.0.2 capability eligibility from evidence coordinates only."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from rna_ccfa.global_refolding_r2 import (
    PAIR_CHANNEL,
    R2_PROTOCOL_VERSION,
    UNPAIRED_CHANNEL,
    pair_capability_flags,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "results/evidence_guidance/e0/clean_manifests.jsonl"
OUT = ROOT / "results/global_constrained_refolding_r2/integrity"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row)) if rows else []
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        if fields:
            writer.writeheader()
            writer.writerows(rows)


def delivered_pairs(manifest: dict[str, Any]) -> list[tuple[int, int]]:
    return [
        (
            int(item["delivered_evidence_item"]["i"]),
            int(item["delivered_evidence_item"]["j"]),
        )
        for item in manifest["items"]
    ]


def validate_unpaired_coordinates(manifest: dict[str, Any]) -> None:
    length = int(manifest["sequence_length"])
    positions = [int(item["delivered_evidence_item"]["i"]) for item in manifest["items"]]
    if len(positions) != len(set(positions)):
        raise AssertionError(f"duplicate unpaired coordinate: {manifest['manifest_id']}")
    if any(position < 0 or position >= length for position in positions):
        raise AssertionError(f"out-of-bounds unpaired coordinate: {manifest['manifest_id']}")


def classify(manifest: dict[str, Any]) -> dict[str, Any]:
    channel = manifest["evidence_channel"]
    if channel == PAIR_CHANNEL:
        flags = pair_capability_flags(delivered_pairs(manifest), int(manifest["sequence_length"]))
        crossing_flag = bool(flags["crossing_flag"])
        minimum_loop_flag = bool(flags["minimum_loop_flag"])
        minimum_pair_separation = flags["minimum_pair_separation"]
        if crossing_flag and minimum_loop_flag:
            status = "R2_INELIGIBLE_MULTIPLE_CAPABILITIES"
            reason = "delivered exact-pair set contains crossing and minimum-loop-incompatible pairs"
        elif crossing_flag:
            status = "R2_INELIGIBLE_CROSSING_EVIDENCE"
            reason = "delivered exact-pair set contains a crossing relation"
        elif minimum_loop_flag:
            status = "R2_INELIGIBLE_MINIMUM_LOOP_EVIDENCE"
            reason = "delivered exact-pair set contains a pair with j-i<=3"
        else:
            status = "R2_ELIGIBLE"
            reason = "all delivered exact pairs are noncrossing and satisfy j-i>3"
        crossing_status = "FAIL" if crossing_flag else "PASS"
        minimum_loop_status = "FAIL" if minimum_loop_flag else "PASS"
    elif channel == UNPAIRED_CHANNEL:
        validate_unpaired_coordinates(manifest)
        crossing_flag = False
        minimum_loop_flag = False
        minimum_pair_separation = None
        crossing_status = "NOT_APPLICABLE"
        minimum_loop_status = "NOT_APPLICABLE"
        status = "R2_ELIGIBLE"
        reason = "unpaired channel has no v1.0.2 capability blocker"
    else:
        raise AssertionError(f"unexpected evidence channel: {channel}")
    return {
        "manifest_id": manifest["manifest_id"],
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "rna_id": manifest["rna_id"],
        "channel": channel,
        "density_percent": int(manifest["density_percent"]),
        "evidence_seed": int(manifest["evidence_seed"]),
        "item_count": int(manifest["delivered_item_count"]),
        "sequence_length": int(manifest["sequence_length"]),
        "crossing_status": crossing_status,
        "minimum_loop_status": minimum_loop_status,
        "crossing_flag": crossing_flag,
        "minimum_loop_flag": minimum_loop_flag,
        "minimum_pair_separation": minimum_pair_separation,
        "validity_status": "PASS",
        "eligibility_status": status,
        "reason": reason,
    }


def grouped_coverage(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: defaultdict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    output = []
    for key, group in sorted(groups.items()):
        eligible = [row for row in group if row["eligibility_status"] == "R2_ELIGIBLE"]
        output.append(
            {
                **dict(zip(keys, key)),
                "total_manifest_count": len(group),
                "eligible_manifest_count": len(eligible),
                "ineligible_manifest_count": len(group) - len(eligible),
                "rna_count": len({row["rna_id"] for row in group}),
                "eligible_rna_count": len({row["rna_id"] for row in eligible}),
            }
        )
    return output


def audit() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    with MANIFESTS.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            manifest = json.loads(line)
            if int(manifest["noise_level_percent"]) != 0:
                continue
            rows.append(classify(manifest))
    rows.sort(key=lambda row: row["manifest_id"])
    if len(rows) != 7260 or len({row["manifest_id"] for row in rows}) != 7260:
        raise AssertionError("frozen clean manifest count/uniqueness mismatch")
    pair_rows = [row for row in rows if row["channel"] == PAIR_CHANNEL]
    unpaired_rows = [row for row in rows if row["channel"] == UNPAIRED_CHANNEL]
    if len(pair_rows) != 3630 or len(unpaired_rows) != 3630:
        raise AssertionError("frozen channel manifest counts changed")
    if any(row["eligibility_status"] != "R2_ELIGIBLE" for row in unpaired_rows):
        raise AssertionError("v1.0.2 found an unexpected unpaired capability blocker")

    coverage_by_rna_density = grouped_coverage(rows, ("channel", "rna_id", "density_percent"))
    zero_coverage = [
        row for row in coverage_by_rna_density if row["eligible_manifest_count"] == 0
    ]
    primary_counts = Counter(row["eligibility_status"] for row in pair_rows)
    crossing_flag_count = sum(bool(row["crossing_flag"]) for row in pair_rows)
    minimum_loop_flag_count = sum(bool(row["minimum_loop_flag"]) for row in pair_rows)
    overlap_count = sum(
        bool(row["crossing_flag"]) and bool(row["minimum_loop_flag"]) for row in pair_rows
    )
    excluded_pair_count = sum(row["eligibility_status"] != "R2_ELIGIBLE" for row in pair_rows)
    summary: dict[str, Any] = {
        "protocol_version": R2_PROTOCOL_VERSION,
        "policy": (
            "whole-manifest capability eligibility: noncrossing and every exact pair j-i>3; "
            "retain independent crossing/minimum-loop flags"
        ),
        "manifest_source": str(MANIFESTS.relative_to(ROOT)),
        "manifest_source_sha256": file_sha256(MANIFESTS),
        "clean_manifest_count": len(rows),
        "pair_manifest_count": len(pair_rows),
        "pair_eligible_count": primary_counts["R2_ELIGIBLE"],
        "pair_capability_ineligible_unique_count": excluded_pair_count,
        "pair_crossing_flag_count": crossing_flag_count,
        "pair_minimum_loop_flag_count": minimum_loop_flag_count,
        "pair_crossing_minimum_loop_overlap_count": overlap_count,
        "pair_primary_status_counts": dict(sorted(primary_counts.items())),
        "unpaired_manifest_count": len(unpaired_rows),
        "unpaired_eligible_count": sum(
            row["eligibility_status"] == "R2_ELIGIBLE" for row in unpaired_rows
        ),
        "affected_rna_ids_crossing": sorted(
            {row["rna_id"] for row in pair_rows if row["crossing_flag"]}
        ),
        "affected_rna_ids_minimum_loop": sorted(
            {row["rna_id"] for row in pair_rows if row["minimum_loop_flag"]}
        ),
        "coverage_by_channel": grouped_coverage(rows, ("channel",)),
        "coverage_by_density": grouped_coverage(rows, ("channel", "density_percent")),
        "coverage_by_seed": grouped_coverage(rows, ("channel", "evidence_seed")),
        "coverage_by_density_seed": grouped_coverage(
            rows, ("channel", "density_percent", "evidence_seed")
        ),
        "coverage_by_rna": grouped_coverage(rows, ("channel", "rna_id")),
        "coverage_by_rna_density": coverage_by_rna_density,
        "zero_coverage_rna_density_count": len(zero_coverage),
        "zero_coverage_rna_density_strata": zero_coverage,
        "exclusion_count_by_rna": [
            {
                "rna_id": rna_id,
                "crossing_flag_manifest_count": sum(
                    row["rna_id"] == rna_id and bool(row["crossing_flag"]) for row in pair_rows
                ),
                "minimum_loop_flag_manifest_count": sum(
                    row["rna_id"] == rna_id and bool(row["minimum_loop_flag"])
                    for row in pair_rows
                ),
                "unique_capability_ineligible_manifest_count": sum(
                    row["rna_id"] == rna_id and row["eligibility_status"] != "R2_ELIGIBLE"
                    for row in pair_rows
                ),
            }
            for rna_id in sorted(
                {
                    row["rna_id"]
                    for row in pair_rows
                    if row["eligibility_status"] != "R2_ELIGIBLE"
                }
            )
        ],
        "eligibility_inputs": [
            "manifest metadata", "delivered evidence coordinates", "frozen solver capability rules"
        ],
        "performance_inputs_read": False,
        "source_identity_read": False,
        "external77_accessed": False,
        "formal_performance_metric_computed": False,
    }
    return rows, summary


def main() -> None:
    rows, summary = audit()
    eligibility_path = OUT / "r2_manifest_eligibility_v1_0_2.csv"
    write_csv(eligibility_path, rows)
    summary["eligibility_csv_sha256"] = file_sha256(eligibility_path)
    summary_path = OUT / "r2_eligibility_summary_v1_0_2.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                key: summary[key]
                for key in (
                    "pair_manifest_count",
                    "pair_eligible_count",
                    "pair_capability_ineligible_unique_count",
                    "pair_crossing_flag_count",
                    "pair_minimum_loop_flag_count",
                    "pair_crossing_minimum_loop_overlap_count",
                    "pair_primary_status_counts",
                    "unpaired_eligible_count",
                    "zero_coverage_rna_density_count",
                )
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
