#!/usr/bin/env python3
"""Validate and reuse R2 outputs on the amended v1.0.2 eligible universe."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from rna_ccfa.global_refolding_r2 import (
    PAIR_CHANNEL,
    R2_PROTOCOL_VERSION,
    ViennaRNAConfig,
    build_constraint_string,
    canonical_sha256,
    parse_and_validate_output,
)


ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT / "results/global_constrained_refolding_r2"
RAW = R2 / "raw/execution_records.jsonl"
MANIFESTS = ROOT / "results/evidence_guidance/e0/clean_manifests.jsonl"
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
ELIGIBILITY = R2 / "integrity/r2_manifest_eligibility_v1_0_2.csv"
ELIGIBILITY_SUMMARY = R2 / "integrity/r2_eligibility_summary_v1_0_2.json"
MATCHED_SUMMARY = R2 / "integrity/r2_matched_universe_summary_v1_0_2.json"


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


def load_sequences() -> dict[str, str]:
    sequences: dict[str, str] = {}
    source_counts: dict[str, int] = {}
    with NORMALIZED.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            rna_id = record["rna_id"]
            sequence = record["sequence"]
            if rna_id in sequences and sequences[rna_id] != sequence:
                raise AssertionError(f"inconsistent Legacy121 sequence copies: {rna_id}")
            sequences[rna_id] = sequence
            source = record["source_model"]["name"]
            source_counts[source] = source_counts.get(source, 0) + 1
    if len(sequences) != 121 or sorted(source_counts.values()) != [121, 121, 121]:
        raise AssertionError("Legacy121 sequence/source matrix mismatch")
    return sequences


def delivered_items(manifest: dict[str, Any]) -> tuple[list[tuple[int, int]], list[int]]:
    if manifest["evidence_channel"] == PAIR_CHANNEL:
        return [
            (
                int(item["delivered_evidence_item"]["i"]),
                int(item["delivered_evidence_item"]["j"]),
            )
            for item in manifest["items"]
        ], []
    return [], [
        int(item["delivered_evidence_item"]["i"]) for item in manifest["items"]
    ]


def main() -> None:
    config = ViennaRNAConfig()
    eligibility_summary = json.loads(ELIGIBILITY_SUMMARY.read_text(encoding="utf-8"))
    matched_summary = json.loads(MATCHED_SUMMARY.read_text(encoding="utf-8"))
    if eligibility_summary["protocol_version"] != R2_PROTOCOL_VERSION:
        raise AssertionError("eligibility protocol is not v1.0.2")
    if file_sha256(ELIGIBILITY) != eligibility_summary["eligibility_csv_sha256"]:
        raise AssertionError("v1.0.2 eligibility hash mismatch")
    if matched_summary["eligibility_csv_sha256"] != file_sha256(ELIGIBILITY):
        raise AssertionError("matched universe does not use frozen v1.0.2 eligibility")
    with ELIGIBILITY.open(encoding="utf-8", newline="") as handle:
        eligibility = {row["manifest_id"]: row for row in csv.DictReader(handle)}
    manifests = {
        manifest["manifest_id"]: manifest
        for manifest in (
            json.loads(line) for line in MANIFESTS.open(encoding="utf-8") if line.strip()
        )
    }
    historical = {
        row["manifest_id"]: row
        for row in (json.loads(line) for line in RAW.open(encoding="utf-8") if line.strip())
    }
    if len(eligibility) != 7260 or set(eligibility) != set(manifests) or set(historical) != set(manifests):
        raise AssertionError("manifest/eligibility/historical execution universes differ")
    sequences = load_sequences()

    eligible_output_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    validation_failures: list[dict[str, Any]] = []
    command_config_hashes: set[str] = set()
    for manifest_id in sorted(manifests):
        manifest = manifests[manifest_id]
        eligibility_row = eligibility[manifest_id]
        old = historical[manifest_id]
        sequence = sequences[manifest["rna_id"]]
        pairs, positions = delivered_items(manifest)
        basic_checks = {
            "manifest_payload_sha256": old["manifest_payload_sha256"]
            == manifest["manifest_payload_sha256"],
            "rna_id": old["rna_id"] == manifest["rna_id"],
            "channel": old["channel"] == manifest["evidence_channel"],
            "density_percent": int(old["density_percent"]) == int(manifest["density_percent"]),
            "evidence_seed": int(old["evidence_seed"]) == int(manifest["evidence_seed"]),
            "evidence_item_count": int(old["evidence_item_count"])
            == int(manifest["delivered_item_count"]),
            "sequence_length": int(old["sequence_length"]) == len(sequence),
            "sequence_sha256": old["sequence_sha256"]
            == hashlib.sha256(sequence.encode("ascii")).hexdigest(),
            "delivered_pairs": old["delivered_pair_items_zero_based"]
            == [list(pair) for pair in pairs],
            "delivered_unpaired": old["delivered_unpaired_items_zero_based"] == positions,
        }
        failed_basic = sorted(key for key, passed in basic_checks.items() if not passed)
        if failed_basic:
            validation_failures.append(
                {"manifest_id": manifest_id, "reason": f"basic provenance mismatch: {failed_basic}"}
            )
            continue

        if eligibility_row["eligibility_status"] != "R2_ELIGIBLE":
            excluded_rows.append(
                {
                    "manifest_id": manifest_id,
                    "rna_id": manifest["rna_id"],
                    "channel": manifest["evidence_channel"],
                    "density_percent": manifest["density_percent"],
                    "evidence_seed": manifest["evidence_seed"],
                    "eligibility_status_v1_0_2": eligibility_row["eligibility_status"],
                    "crossing_flag": eligibility_row["crossing_flag"],
                    "minimum_loop_flag": eligibility_row["minimum_loop_flag"],
                    "historical_execution_status": old["status"],
                    "historical_record_preserved": True,
                    "entered_metric_universe": False,
                }
            )
            continue

        try:
            constraint = build_constraint_string(len(sequence), pairs, positions)
        except ValueError as exc:
            validation_failures.append(
                {"manifest_id": manifest_id, "reason": f"eligible constraint rebuild failed: {exc}"}
            )
            continue
        zero_density = int(manifest["density_percent"]) == 0
        cli_constraint = None if zero_density else constraint
        command = config.command(constrained=not zero_density)
        expected_stdin = f">{manifest_id}\n{sequence}\n"
        if not zero_density:
            expected_stdin += f"{constraint}\n"
        folding_input = {
            "sequence": sequence,
            "constraint": cli_constraint,
            "command": command,
            "rnafold_version": config.expected_version,
            "config": config.as_dict(),
        }
        command_config_hash = canonical_sha256(
            {
                "command": command,
                "rnafold_version": config.expected_version,
                "config": config.as_dict(),
            }
        )
        command_config_hashes.add(command_config_hash)
        provenance_checks = {
            "status_pass": old["status"] == "PASS",
            "output_valid": old["output_valid"] is True,
            "constraint_satisfied": old["constraint_satisfied"] is True,
            "constraint": old["constraint"] == constraint,
            "constraint_mode": old["constraint_mode"]
            == ("UNCONSTRAINED_ZERO_DENSITY" if zero_density else "HARD_CONSTRAINT"),
            "command": old["command"] == command,
            "stdin": old["stdin"] == expected_stdin,
            "return_code": old["return_code"] == 0,
            "attempt_count": old["attempt_count"] == 1,
            "rnafold_binary": old["rnafold_binary"] == config.binary,
            "rnafold_version": old["rnafold_version"] == config.expected_version,
            "rnafold_config": old["rnafold_config"] == config.as_dict(),
            "folding_input_sha256": old["folding_input_sha256"]
            == canonical_sha256(folding_input),
            "output_hash_present": bool(old["output_sha256"]),
        }
        reparsed = parse_and_validate_output(
            {
                "status": "PASS",
                "status_detail": "",
                "command": old["command"],
                "stdin": old["stdin"],
                "stdout": old["stdout"],
                "stderr": old["stderr"],
                "return_code": old["return_code"],
                "runtime_seconds": old["runtime_seconds"],
                "attempt_count": old["attempt_count"],
            },
            sequence=sequence,
            forced_pairs=pairs,
            forced_unpaired=positions,
        )
        provenance_checks.update(
            {
                "reparse_pass": reparsed["status"] == "PASS",
                "reparsed_dbn": reparsed["output_dbn"] == old["output_dbn"],
                "reparsed_pairs": reparsed["pairs_zero_based"] == old["pairs_zero_based"],
                "reparsed_output_hash": reparsed["output_sha256"] == old["output_sha256"],
            }
        )
        failed = sorted(key for key, passed in provenance_checks.items() if not passed)
        if failed:
            validation_failures.append(
                {"manifest_id": manifest_id, "reason": f"PASS provenance validation failed: {failed}"}
            )
            continue
        eligible_output_rows.append(
            {
                "protocol_version": R2_PROTOCOL_VERSION,
                "manifest_id": manifest_id,
                "manifest_payload_sha256": manifest["manifest_payload_sha256"],
                "rna_id": manifest["rna_id"],
                "channel": manifest["evidence_channel"],
                "density_percent": manifest["density_percent"],
                "evidence_seed": manifest["evidence_seed"],
                "evidence_item_count": manifest["delivered_item_count"],
                "sequence_length": len(sequence),
                "sequence_sha256": old["sequence_sha256"],
                "constraint": constraint,
                "constraint_mode": old["constraint_mode"],
                "folding_input_sha256": old["folding_input_sha256"],
                "command_config_sha256": command_config_hash,
                "output_dbn": old["output_dbn"],
                "pairs_zero_based_json": json.dumps(
                    old["pairs_zero_based"], separators=(",", ":")
                ),
                "output_sha256": old["output_sha256"],
                "status": "PASS",
                "output_valid": True,
                "constraint_satisfied": True,
                "reused_historical_pass_output": True,
                "historical_protocol_version": old["protocol_version"],
            }
        )

    eligible_expected = {
        manifest_id
        for manifest_id, row in eligibility.items()
        if row["eligibility_status"] == "R2_ELIGIBLE"
    }
    validated_ids = {row["manifest_id"] for row in eligible_output_rows}
    excluded_ids = {row["manifest_id"] for row in excluded_rows}
    if excluded_ids & eligible_expected:
        raise AssertionError("capability-excluded rows overlap eligible universe")
    completion_status = (
        "PASS"
        if not validation_failures and validated_ids == eligible_expected
        else "BLOCKED_ELIGIBLE_OUTPUT_INCOMPLETE"
    )
    structures_path = R2 / "parsed/b2_structures_v1_0_2.csv"
    excluded_path = R2 / "integrity/capability_excluded_v1_0_2.csv"
    write_csv(structures_path, eligible_output_rows)
    write_csv(excluded_path, excluded_rows)
    completion = {
        "status": completion_status,
        "protocol_version": R2_PROTOCOL_VERSION,
        "historical_raw_execution_sha256": file_sha256(RAW),
        "v1_0_2_eligible_count": len(eligible_expected),
        "validated_reused_pass_count": len(eligible_output_rows),
        "missing_eligible_output_count": len(eligible_expected - validated_ids),
        "unexpected_validated_output_count": len(validated_ids - eligible_expected),
        "eligible_validation_failure_count": len(validation_failures),
        "eligible_validation_failures": validation_failures,
        "eligible_constraint_satisfaction_count": sum(
            row["constraint_satisfied"] is True for row in eligible_output_rows
        ),
        "eligible_constraint_satisfaction_rate": (
            len(eligible_output_rows) / len(eligible_expected) if eligible_expected else None
        ),
        "capability_excluded_count": len(excluded_rows),
        "capability_excluded_entered_metric_universe_count": sum(
            row["entered_metric_universe"] is True for row in excluded_rows
        ),
        "historical_minimum_loop_failure_rows_preserved": sum(
            row["historical_execution_status"] == "CONSTRAINT_SATISFACTION_FAIL"
            for row in excluded_rows
        ),
        "historical_crossing_skip_rows_preserved": sum(
            row["historical_execution_status"] == "R2_INELIGIBLE_CROSSING_EVIDENCE"
            for row in excluded_rows
        ),
        "new_rnafold_call_count": 0,
        "reused_historical_pass_output_count": len(eligible_output_rows),
        "command_config_hashes": sorted(command_config_hashes),
        "b2_structures_v1_0_2_sha256": file_sha256(structures_path),
        "capability_excluded_v1_0_2_sha256": file_sha256(excluded_path),
        "formal_summarization_authorized": completion_status == "PASS",
        "external77_accessed": False,
        "learned_model_trained": False,
    }
    completion_path = R2 / "integrity/execution_completion_v1_0_2.json"
    completion_path.write_text(json.dumps(completion, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(completion, indent=2, sort_keys=True))
    if completion_status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
