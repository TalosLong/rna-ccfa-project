#!/usr/bin/env python3
"""Execute the frozen R2/B2 global hard-constraint refolding baseline."""

from __future__ import annotations

import argparse
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
    ConstraintBuildError,
    ViennaRNAConfig,
    build_constraint_string,
    canonical_sha256,
    pair_capability_flags,
    parse_and_validate_output,
    query_rnafold_version,
    run_constrained_rnafold,
)
from rna_ccfa.simulated_evidence import (
    DENSITY_GRID_PERCENT,
    EVIDENCE_SEEDS,
    PROTOCOL_VERSION,
    validate_evidence_manifest,
)
from rna_ccfa.structure import validate_pairs


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
MANIFESTS = ROOT / "results/evidence_guidance/e0/clean_manifests.jsonl"
INTEGRITY = ROOT / "results/global_constrained_refolding_r2/integrity"
ELIGIBILITY = INTEGRITY / "r2_manifest_eligibility_v1_0_2.csv"
ELIGIBILITY_SUMMARY = INTEGRITY / "r2_eligibility_summary_v1_0_2.json"
MATCHED_B1 = INTEGRITY / "r2_matched_b1_view_v1_0_2.csv"
DEFAULT_OUT = ROOT / "results/global_constrained_refolding_r2"

EXPECTED_MANIFEST_SHA256 = "c743913d8d0b44cbccaba74b68bebaeb1551a4095d1ae51782435c12e96d11ca"
EXPECTED_ELIGIBILITY_SHA256 = "a2361b58c7326ca7674cbbdcdce3c6f8c517efcffc159cdf4b5ae0abccbfbfe3"
EXPECTED_MATCHED_B1_SHA256 = "f616ab7591d6615de1fd815a9499f3c8c53616c76d5a47e79872d170eaaa6a46"
EXPECTED_COUNTS = {
    "manifest_count": 7260,
    "pair_eligible": 3523,
    "pair_ineligible": 107,
    "unpaired_eligible": 3630,
    "eligible_total": 7153,
}
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row)) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        if fields:
            writer.writeheader()
            writer.writerows(rows)


def load_rna_references() -> dict[str, dict[str, Any]]:
    references: dict[str, dict[str, Any]] = {}
    source_counts: Counter[str] = Counter()
    record_count = 0
    with NORMALIZED.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            record_count += 1
            source = record["source_model"]["name"]
            if source not in SOURCES:
                raise AssertionError(f"unexpected Legacy121 source: {source}")
            source_counts[source] += 1
            sequence = record["sequence"]
            truth = validate_pairs(record["ground_truth_structure"]["pairs"], sequence=sequence)
            reference = {
                "rna_id": record["rna_id"],
                "sequence": sequence,
                "ground_truth_pairs": truth,
            }
            previous = references.setdefault(record["rna_id"], reference)
            if previous != reference:
                raise AssertionError(f"inconsistent sequence/GT copies for {record['rna_id']}")
    if record_count != 363 or len(references) != 121:
        raise AssertionError(f"Legacy121 matrix mismatch: records={record_count}, RNAs={len(references)}")
    if source_counts != Counter({source: 121 for source in SOURCES}):
        raise AssertionError(f"Legacy121 source counts mismatch: {source_counts}")
    return references


def load_eligibility() -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    if file_sha256(ELIGIBILITY) != EXPECTED_ELIGIBILITY_SHA256:
        raise AssertionError("frozen R2 eligibility CSV hash mismatch")
    if file_sha256(MATCHED_B1) != EXPECTED_MATCHED_B1_SHA256:
        raise AssertionError("frozen matched B1 view hash mismatch")
    with ELIGIBILITY.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_id = {row["manifest_id"]: row for row in rows}
    if len(rows) != EXPECTED_COUNTS["manifest_count"] or len(by_id) != len(rows):
        raise AssertionError("frozen eligibility row count/uniqueness mismatch")
    summary = json.loads(ELIGIBILITY_SUMMARY.read_text(encoding="utf-8"))
    expected_summary = {
        "protocol_version": R2_PROTOCOL_VERSION,
        "manifest_source_sha256": EXPECTED_MANIFEST_SHA256,
        "clean_manifest_count": 7260,
        "pair_manifest_count": 3630,
        "pair_eligible_count": 3523,
        "pair_capability_ineligible_unique_count": 107,
        "pair_crossing_flag_count": 87,
        "pair_minimum_loop_flag_count": 20,
        "pair_crossing_minimum_loop_overlap_count": 0,
        "unpaired_manifest_count": 3630,
        "unpaired_eligible_count": 3630,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            raise AssertionError(f"eligibility summary mismatch for {key}: {summary.get(key)!r}")
    return by_id, summary


def load_and_validate_manifests(references: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if file_sha256(MANIFESTS) != EXPECTED_MANIFEST_SHA256:
        raise AssertionError("frozen clean manifest suite hash mismatch")
    manifests = []
    observed_ids: set[str] = set()
    with MANIFESTS.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            manifest = json.loads(line)
            if manifest["manifest_id"] in observed_ids:
                raise AssertionError(f"duplicate manifest ID: {manifest['manifest_id']}")
            observed_ids.add(manifest["manifest_id"])
            if manifest["protocol_version"] != PROTOCOL_VERSION or manifest["schema_version"] != PROTOCOL_VERSION:
                raise AssertionError("manifest protocol version mismatch")
            if manifest["evidence_channel"] not in (PAIR_CHANNEL, UNPAIRED_CHANNEL):
                raise AssertionError("manifest channel outside frozen set")
            if int(manifest["density_percent"]) not in DENSITY_GRID_PERCENT:
                raise AssertionError("manifest density outside frozen grid")
            if int(manifest["evidence_seed"]) not in EVIDENCE_SEEDS:
                raise AssertionError("manifest evidence seed outside frozen set")
            if int(manifest["noise_level_percent"]) != 0:
                raise AssertionError("R2 runner accepts clean evidence only")
            reference = references.get(manifest["rna_id"])
            if reference is None:
                raise AssertionError(f"manifest RNA absent from Legacy121: {manifest['rna_id']}")
            if int(manifest["sequence_length"]) != len(reference["sequence"]):
                raise AssertionError(f"manifest sequence length mismatch: {manifest['manifest_id']}")
            payload = dict(manifest)
            observed_hash = payload.pop("manifest_payload_sha256")
            if canonical_sha256(payload) != observed_hash:
                raise AssertionError(f"manifest payload hash mismatch: {manifest['manifest_id']}")
            validate_evidence_manifest(
                manifest,
                sequence=reference["sequence"],
                ground_truth_pairs=reference["ground_truth_pairs"],
            )
            manifests.append(manifest)
    manifests.sort(key=lambda row: row["manifest_id"])
    if len(manifests) != EXPECTED_COUNTS["manifest_count"]:
        raise AssertionError(f"expected 7260 manifests, found {len(manifests)}")
    return manifests


def delivered_items(manifest: dict[str, Any]) -> tuple[list[tuple[int, int]], list[int]]:
    if manifest["evidence_channel"] == PAIR_CHANNEL:
        pairs = [
            (int(item["delivered_evidence_item"]["i"]), int(item["delivered_evidence_item"]["j"]))
            for item in manifest["items"]
        ]
        return pairs, []
    positions = [int(item["delivered_evidence_item"]["i"]) for item in manifest["items"]]
    return [], positions


def execute_one(
    manifest: dict[str, Any],
    eligibility: dict[str, str],
    reference: dict[str, Any],
    *,
    config: ViennaRNAConfig,
    version: str,
) -> dict[str, Any]:
    sequence = reference["sequence"]
    pairs, positions = delivered_items(manifest)
    base: dict[str, Any] = {
        "protocol_version": R2_PROTOCOL_VERSION,
        "manifest_id": manifest["manifest_id"],
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "rna_id": manifest["rna_id"],
        "channel": manifest["evidence_channel"],
        "density_percent": int(manifest["density_percent"]),
        "evidence_seed": int(manifest["evidence_seed"]),
        "evidence_item_count": int(manifest["delivered_item_count"]),
        "sequence_length": len(sequence),
        "sequence_sha256": hashlib.sha256(sequence.encode("ascii")).hexdigest(),
        "delivered_pair_items_zero_based": [list(pair) for pair in pairs],
        "delivered_unpaired_items_zero_based": positions,
        "vienna_pair_positions_one_based": [[i + 1, j + 1] for i, j in pairs],
        "vienna_unpaired_positions_one_based": [position + 1 for position in positions],
        "eligibility_status": eligibility["eligibility_status"],
        "eligibility_reason": eligibility["reason"],
        "rnafold_binary": config.binary,
        "rnafold_version": version,
        "rnafold_config": config.as_dict(),
        "constraint": None,
        "constraint_mode": None,
        "folding_input_sha256": None,
        "source_identity_used_for_folding": False,
        "source_prediction_used_for_folding": False,
    }
    if eligibility["manifest_payload_sha256"] != manifest["manifest_payload_sha256"]:
        return {
            **base,
            "status": "MANIFEST_ELIGIBILITY_HASH_MISMATCH",
            "status_detail": "eligibility payload hash differs from clean manifest",
            "command": [],
            "stdin": "",
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "runtime_seconds": 0.0,
            "attempt_count": 0,
            "output_dbn": None,
            "pairs_zero_based": None,
            "output_sha256": None,
            "output_valid": False,
            "constraint_satisfied": False,
        }
    capability_ineligible_statuses = {
        "R2_INELIGIBLE_CROSSING_EVIDENCE",
        "R2_INELIGIBLE_MINIMUM_LOOP_EVIDENCE",
        "R2_INELIGIBLE_MULTIPLE_CAPABILITIES",
    }
    if eligibility["eligibility_status"] in capability_ineligible_statuses:
        if manifest["evidence_channel"] != PAIR_CHANNEL:
            raise AssertionError(
                f"frozen capability-ineligible row is not pair evidence: {manifest['manifest_id']}"
            )
        flags = pair_capability_flags(pairs, len(sequence))
        observed_status = (
            "R2_INELIGIBLE_MULTIPLE_CAPABILITIES"
            if flags["crossing_flag"] and flags["minimum_loop_flag"]
            else "R2_INELIGIBLE_CROSSING_EVIDENCE"
            if flags["crossing_flag"]
            else "R2_INELIGIBLE_MINIMUM_LOOP_EVIDENCE"
            if flags["minimum_loop_flag"]
            else "R2_ELIGIBLE"
        )
        if observed_status != eligibility["eligibility_status"]:
            raise AssertionError(
                f"coordinate capability status mismatch: {manifest['manifest_id']}"
            )
        return {
            **base,
            "status": eligibility["eligibility_status"],
            "status_detail": eligibility["reason"],
            "command": [],
            "stdin": "",
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "runtime_seconds": 0.0,
            "attempt_count": 0,
            "output_dbn": None,
            "pairs_zero_based": None,
            "output_sha256": None,
            "output_valid": False,
            "constraint_satisfied": False,
        }
    if eligibility["eligibility_status"] != "R2_ELIGIBLE":
        raise AssertionError(f"unknown frozen eligibility status: {eligibility['eligibility_status']}")
    try:
        constraint = build_constraint_string(len(sequence), pairs, positions)
    except ConstraintBuildError as exc:
        return {
            **base,
            "status": exc.status,
            "status_detail": str(exc),
            "command": [],
            "stdin": "",
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "runtime_seconds": 0.0,
            "attempt_count": 0,
            "output_dbn": None,
            "pairs_zero_based": None,
            "output_sha256": None,
            "output_valid": False,
            "constraint_satisfied": False,
        }
    zero_density = int(manifest["density_percent"]) == 0
    if zero_density and (pairs or positions or set(constraint) != {"."}):
        raise AssertionError("zero-density manifest unexpectedly contains evidence")
    cli_constraint = None if zero_density else constraint
    command = config.command(constrained=cli_constraint is not None)
    folding_input = {
        "sequence": sequence,
        "constraint": cli_constraint,
        "command": command,
        "rnafold_version": version,
        "config": config.as_dict(),
    }
    base.update(
        {
            "constraint": constraint,
            "constraint_mode": "UNCONSTRAINED_ZERO_DENSITY" if zero_density else "HARD_CONSTRAINT",
            "folding_input_sha256": canonical_sha256(folding_input),
        }
    )
    run = run_constrained_rnafold(
        sequence,
        cli_constraint,
        record_id=manifest["manifest_id"],
        config=config,
    )
    parsed = parse_and_validate_output(
        run,
        sequence=sequence,
        forced_pairs=pairs,
        forced_unpaired=positions,
    )
    return {**base, **parsed}


def runtime_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: defaultdict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["channel"], row["density_percent"], row["status"])].append(row)
    output = []
    for (channel, density, status), group in sorted(grouped.items()):
        times = [float(row["runtime_seconds"]) for row in group]
        output.append(
            {
                "channel": channel,
                "density_percent": density,
                "status": status,
                "realization_count": len(group),
                "total_runtime_seconds": sum(times),
                "mean_runtime_seconds": sum(times) / len(times),
                "min_runtime_seconds": min(times),
                "max_runtime_seconds": max(times),
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    config = ViennaRNAConfig()
    version_audit = query_rnafold_version(config)
    references = load_rna_references()
    eligibility, eligibility_summary = load_eligibility()
    manifests = load_and_validate_manifests(references)
    if set(eligibility) != {manifest["manifest_id"] for manifest in manifests}:
        raise AssertionError("eligibility and clean manifest ID universes differ")

    rows: list[dict[str, Any]] = []
    for index, manifest in enumerate(manifests, start=1):
        row = execute_one(
            manifest,
            eligibility[manifest["manifest_id"]],
            references[manifest["rna_id"]],
            config=config,
            version=version_audit["version"],
        )
        rows.append(row)
        if index % 500 == 0:
            print(json.dumps({"handled": index, "total": len(manifests), "status_counts": Counter(r["status"] for r in rows)}, sort_keys=True), flush=True)

    status_counts = Counter(row["status"] for row in rows)
    eligible_rows = [row for row in rows if row["eligibility_status"] == "R2_ELIGIBLE"]
    capability_ineligible_statuses = {
        "R2_INELIGIBLE_CROSSING_EVIDENCE",
        "R2_INELIGIBLE_MINIMUM_LOOP_EVIDENCE",
        "R2_INELIGIBLE_MULTIPLE_CAPABILITIES",
    }
    skipped_rows = [row for row in rows if row["status"] in capability_ineligible_statuses]
    failed_rows = [
        row for row in rows
        if row["status"] != "PASS" and row["status"] not in capability_ineligible_statuses
    ]
    parsed_rows = [
        {
            "manifest_id": row["manifest_id"],
            "manifest_payload_sha256": row["manifest_payload_sha256"],
            "rna_id": row["rna_id"],
            "channel": row["channel"],
            "density_percent": row["density_percent"],
            "evidence_seed": row["evidence_seed"],
            "evidence_item_count": row["evidence_item_count"],
            "constraint": row["constraint"],
            "constraint_mode": row["constraint_mode"],
            "folding_input_sha256": row["folding_input_sha256"],
            "output_dbn": row["output_dbn"],
            "pairs_zero_based_json": json.dumps(row["pairs_zero_based"], separators=(",", ":")) if row["pairs_zero_based"] is not None else "",
            "output_sha256": row["output_sha256"],
            "runtime_seconds": row["runtime_seconds"],
            "status": row["status"],
            "output_valid": row["output_valid"],
            "constraint_satisfied": row["constraint_satisfied"],
        }
        for row in rows
    ]
    failure_view = [
        {
            "manifest_id": row["manifest_id"],
            "rna_id": row["rna_id"],
            "channel": row["channel"],
            "density_percent": row["density_percent"],
            "evidence_seed": row["evidence_seed"],
            "evidence_item_count": row["evidence_item_count"],
            "eligibility_status": row["eligibility_status"],
            "status": row["status"],
            "status_detail": row["status_detail"],
            "return_code": row["return_code"],
            "stderr": row["stderr"],
        }
        for row in rows
        if row["status"] != "PASS"
    ]

    write_jsonl(output_root / "raw/execution_records.jsonl", rows)
    write_csv(output_root / "parsed/b2_structures.csv", parsed_rows)
    write_csv(output_root / "integrity/failed_skipped_realizations.csv", failure_view)
    write_csv(output_root / "summaries/runtime_summary.csv", runtime_summary(rows))

    integrity = {
        "status": "PASS" if not failed_rows else "PARTIAL",
        "protocol_version": R2_PROTOCOL_VERSION,
        "rnafold_version_audit": version_audit,
        "rnafold_config": config.as_dict(),
        "retry_policy": {"retry_count": config.retry_count, "adaptive_retry": False},
        "input_hashes": {
            "clean_manifests_jsonl": file_sha256(MANIFESTS),
            "r2_manifest_eligibility_csv": file_sha256(ELIGIBILITY),
            "r2_matched_b1_view_csv": file_sha256(MATCHED_B1),
            "normalized_legacy121_predictions_jsonl": file_sha256(NORMALIZED),
        },
        "eligibility_protocol_version": eligibility_summary["protocol_version"],
        "protocol_realization_count": len(rows),
        "eligible_realization_count": len(eligible_rows),
        "executed_rnafold_count": sum(int(row["attempt_count"] > 0) for row in rows),
        "pass_count": status_counts["PASS"],
        "capability_ineligible_skip_count": len(skipped_rows),
        "ineligible_crossing_skip_count": status_counts[
            "R2_INELIGIBLE_CROSSING_EVIDENCE"
        ],
        "ineligible_minimum_loop_skip_count": status_counts[
            "R2_INELIGIBLE_MINIMUM_LOOP_EVIDENCE"
        ],
        "ineligible_multiple_capabilities_skip_count": status_counts[
            "R2_INELIGIBLE_MULTIPLE_CAPABILITIES"
        ],
        "technical_failure_count": len(failed_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "output_validation_pass_count": sum(row["output_valid"] is True for row in eligible_rows),
        "constraint_satisfaction_pass_count": sum(row["constraint_satisfied"] is True for row in eligible_rows),
        "unexpected_constraint_violation_count": sum(row["status"] == "CONSTRAINT_SATISFACTION_FAIL" for row in rows),
        "source_identity_used_for_folding": False,
        "source_prediction_used_for_folding": False,
        "learned_model_trained": False,
        "historical_e2_executed": False,
        "external77_accessed": False,
    }
    write_json(output_root / "integrity/execution_integrity_summary.json", integrity)
    print(json.dumps(integrity, indent=2, sort_keys=True))
    if failed_rows:
        raise SystemExit(2)
    if status_counts != Counter(
        {
            "PASS": 7153,
            "R2_INELIGIBLE_CROSSING_EVIDENCE": 87,
            "R2_INELIGIBLE_MINIMUM_LOOP_EVIDENCE": 20,
        }
    ):
        raise AssertionError(f"unexpected final status counts: {status_counts}")


if __name__ == "__main__":
    main()
