#!/usr/bin/env python3
"""Build frozen B0/B1 matched views from v1.0.2 eligible manifest IDs only."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INTEGRITY = ROOT / "results/global_constrained_refolding_r2/integrity"
ELIGIBILITY = INTEGRITY / "r2_manifest_eligibility_v1_0_2.csv"
ELIGIBILITY_SUMMARY = INTEGRITY / "r2_eligibility_summary_v1_0_2.json"
B1 = ROOT / "results/evidence_guidance/stage_e1/per_rna_evidence_results.csv"
PAIR_CHANNEL = "POSITIVE_PAIR_EVIDENCE"
UNPAIRED_CHANNEL = "UNPAIRED_NUCLEOTIDE_EVIDENCE"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row)) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        if fields:
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    eligibility_summary = json.loads(ELIGIBILITY_SUMMARY.read_text(encoding="utf-8"))
    if file_sha256(ELIGIBILITY) != eligibility_summary["eligibility_csv_sha256"]:
        raise AssertionError("v1.0.2 eligibility CSV hash mismatch")
    with ELIGIBILITY.open(encoding="utf-8", newline="") as handle:
        eligibility_rows = list(csv.DictReader(handle))
    eligible_ids = {
        row["manifest_id"]
        for row in eligibility_rows
        if row["eligibility_status"] == "R2_ELIGIBLE"
    }
    if len(eligible_ids) != (
        int(eligibility_summary["pair_eligible_count"])
        + int(eligibility_summary["unpaired_eligible_count"])
    ):
        raise AssertionError("v1.0.2 eligible ID count disagrees with eligibility summary")

    with B1.open(encoding="utf-8", newline="") as handle:
        all_rows = list(csv.DictReader(handle))
    matched_b1 = [row for row in all_rows if row["manifest_id"] in eligible_ids]
    matched_b0 = [row for row in matched_b1 if row["condition"] == "ORIGINAL"]
    primary_b1 = [
        row
        for row in matched_b1
        if (
            row["evidence_channel"] == PAIR_CHANNEL
            and row["condition"] == "PAIR_HARD_ENFORCE"
        )
        or (
            row["evidence_channel"] == UNPAIRED_CHANNEL
            and row["condition"] == "UNPAIRED_HARD_DELETE"
        )
    ]
    expected_source_rows = len(eligible_ids) * 3
    if len(matched_b0) != expected_source_rows or len(primary_b1) != expected_source_rows:
        raise AssertionError("matched B0/primary-B1 rows do not equal eligible manifests x sources")
    if {row["manifest_id"] for row in matched_b0} != eligible_ids:
        raise AssertionError("matched B0 manifest IDs differ from v1.0.2 eligible IDs")
    if {row["manifest_id"] for row in primary_b1} != eligible_ids:
        raise AssertionError("matched primary B1 manifest IDs differ from v1.0.2 eligible IDs")

    b1_path = INTEGRITY / "r2_matched_b1_view_v1_0_2.csv"
    b0_path = INTEGRITY / "r2_matched_b0_view_v1_0_2.csv"
    write_csv(b1_path, matched_b1)
    write_csv(b0_path, matched_b0)
    summary = {
        "protocol_version": "global_constrained_refolding_r2_protocol_v1.0.2",
        "eligibility_csv_sha256": file_sha256(ELIGIBILITY),
        "source_b1_results_sha256": file_sha256(B1),
        "eligible_manifest_id_count": len(eligible_ids),
        "matched_b1_all_condition_rows": len(matched_b1),
        "matched_b0_rows": len(matched_b0),
        "matched_primary_b1_rows": len(primary_b1),
        "matched_b1_view_sha256": file_sha256(b1_path),
        "matched_b0_view_sha256": file_sha256(b0_path),
        "selection_rule": "manifest-ID filter using coordinate-only v1.0.2 R2_ELIGIBLE status",
        "b1_rerun": False,
        "b1_retuned": False,
        "performance_used_for_eligibility": False,
        "external77_accessed": False,
    }
    summary_path = INTEGRITY / "r2_matched_universe_summary_v1_0_2.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
