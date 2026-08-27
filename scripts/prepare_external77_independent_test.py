#!/usr/bin/env python3
"""Freeze external77 GT_CON candidates and run only reproducible RNAfold.

This script intentionally does not create normalized prediction records unless
all three source-model matrices are available. PETfold and trRosettaRNA2 are
audited and recorded as blocked when their required input protocols are not
frozen for this external set.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Bio import Align

from rna_ccfa.normalization import sha256_file, validate_normalized_sequence
from rna_ccfa.structure import parse_extended_dot_bracket, validate_pairs


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_ROOT = Path("/root/autodl-tmp/data/NMRFOLD-BENCHMARK-STANDARD-v1")
EXTERNAL_MANIFEST = (
    EXTERNAL_ROOT
    / "data/NMRFOLD_external77_fullatom_3SS_v3/NMRFOLD_external77_fullatom_3SS_manifest.csv"
)
EXTERNAL_DBN_ROOT = EXTERNAL_ROOT / "data/ss_dotbracket"
CANDIDATE_AUDIT = ROOT / "results/selective_refiner_protocol/external77_gt_con_candidate_ids.csv"
LEGACY_MANIFEST = ROOT / "manifests/legacy121_v1.csv"
OUTPUT = ROOT / "results/external77_independent_test"
RAW_ROOT = OUTPUT / "source_predictions"
NORMALIZED_ROOT = ROOT / "normalized/external77_GT_CON_v1_nonredundant"
IDENTITY_THRESHOLD = 0.80


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _aligner() -> Align.PairwiseAligner:
    aligner = Align.PairwiseAligner()
    aligner.mode = "global"
    aligner.match_score = 1.0
    aligner.mismatch_score = 0.0
    aligner.open_gap_score = -1.0
    aligner.extend_gap_score = -1.0
    return aligner


def _identity(aligner: Align.PairwiseAligner, first: str, second: str) -> float:
    counts = aligner.align(first, second)[0].counts()
    denominator = counts.identities + counts.mismatches + counts.gaps
    return counts.identities / denominator


def _canonical_hash(pairs: list[tuple[int, int]]) -> str:
    payload = json.dumps([[i, j] for i, j in pairs], separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _freeze_manifest() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    external = _read_rows(EXTERNAL_MANIFEST)
    candidates = _read_rows(CANDIDATE_AUDIT)
    candidate_from_audit = {
        row["sequence_id"]
        for row in candidates
        if row["eligible_external77_gt_con_v1_candidate"] == "True"
    }
    legacy_rows = _read_rows(LEGACY_MANIFEST)
    legacy_sequences: dict[str, str] = {}
    for row in legacy_rows:
        sequence = Path(row["sequence_path"]).read_text().splitlines()
        sequence = "".join(line.strip() for line in sequence if line.strip() and not line.startswith(">"))
        legacy_sequences[row["rna_id"]] = sequence.upper()
    aligner = _aligner()
    dbn_by_sequence: dict[str, list[Path]] = {}
    for candidate_path in sorted(EXTERNAL_DBN_ROOT.glob("*_GT_CON.dbn")):
        candidate_lines = [line.strip() for line in candidate_path.read_text().splitlines() if line.strip()]
        if len(candidate_lines) != 3:
            raise RuntimeError(f"unexpected GT_CON DBN layout: {candidate_path}")
        dbn_by_sequence.setdefault(candidate_lines[1].upper(), []).append(candidate_path)
    selected: list[dict[str, Any]] = []
    recomputed_ids: set[str] = set()
    for row in sorted(external, key=lambda item: item["sequence_id"]):
        sequence_id = row["sequence_id"]
        sequence = row["sequence"].upper()
        identities = {
            rna_id: _identity(aligner, sequence, legacy_sequence)
            for rna_id, legacy_sequence in sorted(legacy_sequences.items())
        }
        max_identity = max(identities.values())
        nearest = min(
            rna_id for rna_id, value in identities.items() if value == max_identity
        )
        eligible = set(sequence) <= set("ACGU") and max_identity < IDENTITY_THRESHOLD
        if eligible:
            recomputed_ids.add(sequence_id)
        if eligible != (sequence_id in candidate_from_audit):
            raise RuntimeError(
                f"candidate mismatch for {sequence_id}: recomputed={eligible}, "
                f"frozen_csv={sequence_id in candidate_from_audit}"
            )
        if not eligible:
            continue
        matching_dbn_paths = dbn_by_sequence.get(sequence, [])
        if len(matching_dbn_paths) != 1:
            raise RuntimeError(
                f"GT_CON DBN sequence index for {sequence_id} has "
                f"{len(matching_dbn_paths)} matches: {matching_dbn_paths}"
            )
        dbn_path = matching_dbn_paths[0]
        lines = [line.strip() for line in dbn_path.read_text().splitlines() if line.strip()]
        if len(lines) != 3:
            raise RuntimeError(f"unexpected GT_CON DBN layout: {dbn_path}")
        if lines[1].upper() != sequence:
            raise RuntimeError(f"GT_CON sequence mismatch for {sequence_id}: {dbn_path}")
        pairs = validate_pairs(parse_extended_dot_bracket(lines[2], sequence=sequence), sequence=sequence)
        selected.append(
            {
                "rna_id": sequence_id,
                "sequence_id": sequence_id,
                "sequence": sequence,
                "sequence_length": len(sequence),
                "gt_con_structure": lines[2],
                "gt_con_pair_count": len(pairs),
                "gt_con_structure_sha256": _canonical_hash(pairs),
                "gt_con_source_path": str(dbn_path.resolve()),
                "gt_con_source_file_sha256": sha256_file(dbn_path),
                "original_source_path": str((EXTERNAL_ROOT / row["source_cif"]).resolve())
                if not Path(row["source_cif"]).is_absolute()
                else row["source_cif"],
                "selected_cif_path": str((EXTERNAL_MANIFEST.parent / row["selected_cif"]).resolve()),
                "max_identity_to_legacy121": max_identity,
                "nearest_legacy121_rna_id": nearest,
                "eligibility_status": "eligible",
                "exclusion_reason": "",
            }
        )
    if recomputed_ids != candidate_from_audit:
        raise RuntimeError("recomputed candidate set differs from frozen CSV")
    if len(selected) != 42:
        raise RuntimeError(f"expected 42 eligible candidates, observed {len(selected)}")
    return selected, {
        "external_rows": len(external),
        "frozen_csv_eligible_rows": len(candidate_from_audit),
        "recomputed_eligible_rows": len(recomputed_ids),
        "candidate_set_matches_frozen_csv": True,
        "identity_threshold": IDENTITY_THRESHOLD,
        "gt_semantics": "GT_CON",
    }


def _write_manifest(rows: list[dict[str, Any]]) -> Path:
    path = ROOT / "manifests/external77_GT_CON_v1_nonredundant_manifest.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _run_rnafold(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    input_root = RAW_ROOT / "rnafold" / "inputs"
    output_root = RAW_ROOT / "rnafold" / "outputs"
    log_root = RAW_ROOT / "rnafold" / "logs"
    for path in (input_root, output_root, log_root):
        path.mkdir(parents=True, exist_ok=True)
    version = subprocess.run(["/usr/bin/RNAfold", "--version"], capture_output=True, text=True, check=True)
    version_text = (version.stdout + version.stderr).strip()
    runtime_rows: list[dict[str, Any]] = []
    provenance_rows: list[dict[str, Any]] = []
    for row in rows:
        rid = row["rna_id"]
        fasta = input_root / f"{rid}.fasta"
        stdout_path = log_root / f"{rid}.stdout.txt"
        stderr_path = log_root / f"{rid}.stderr.txt"
        dbn_path = output_root / f"{rid}.dbn"
        fasta.write_text(f">{rid}\n{row['sequence']}\n", encoding="utf-8")
        started = time.monotonic()
        result = subprocess.run(
            ["/usr/bin/RNAfold", "--noPS", str(fasta)],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        elapsed = time.monotonic() - started
        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")
        status = "valid"
        failure = ""
        try:
            lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            if result.returncode != 0 or len(lines) < 3:
                raise ValueError(f"exit={result.returncode}, output_lines={len(lines)}")
            if lines[0].lstrip(">") != rid or lines[1] != row["sequence"]:
                raise ValueError("RNAfold header/sequence mismatch")
            structure = lines[2].split()[0]
            pairs = validate_pairs(parse_extended_dot_bracket(structure, sequence=row["sequence"]), sequence=row["sequence"])
            dbn_path.write_text(f">{rid}\n{row['sequence']}\n{structure}\n", encoding="utf-8")
            pair_hash = _canonical_hash(pairs)
        except Exception as exc:  # noqa: BLE001 - per-source failure is recorded
            status = "invalid"
            failure = str(exc)
            pair_hash = ""
        runtime_rows.append(
            {
                "source_model": "rnafold",
                "rna_id": rid,
                "status": status,
                "runtime_seconds": round(elapsed, 6),
                "exit_status": result.returncode,
                "command": f"/usr/bin/RNAfold --noPS {fasta}",
                "version": version_text,
                "environment": "system /usr/bin/RNAfold; no project-specific Python environment",
                "stdout_log": str(stdout_path),
                "stderr_log": str(stderr_path),
                "failure_reason": failure,
            }
        )
        provenance_rows.append(
            {
                "source_model": "rnafold",
                "rna_id": rid,
                "status": status,
                "output_path": str(dbn_path) if status == "valid" else "",
                "output_sha256": sha256_file(dbn_path) if status == "valid" else "",
                "output_size_bytes": dbn_path.stat().st_size if status == "valid" else "",
                "canonical_pair_sha256": pair_hash,
                "raw_stdout_sha256": sha256_file(stdout_path),
                "raw_stderr_sha256": sha256_file(stderr_path),
            }
        )
    return runtime_rows, provenance_rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    rows, candidate_audit = _freeze_manifest()
    manifest_path = _write_manifest(rows)
    runtime_rnafold, provenance_rnafold = _run_rnafold(rows)
    runtime_rows = runtime_rnafold + [
        {
            "source_model": model,
            "rna_id": "ALL_42",
            "status": "BLOCKED",
            "runtime_seconds": "",
            "exit_status": "NOT_RUN",
            "command": "NOT_RUN",
            "version": "UNKNOWN",
            "environment": "NOT_RUN",
            "stdout_log": "",
            "stderr_log": "",
            "failure_reason": reason,
        }
        for model, reason in (
            ("petfold", "alignment input/projection protocol is not frozen for external77"),
            ("trrosettarna2_native_ss", "A3M/MSA input and lossless native-SS decoder are not frozen for external77"),
        )
    ]
    provenance_rows = provenance_rnafold
    _write_csv(OUTPUT / "source_runtime.csv", runtime_rows)
    _write_csv(OUTPUT / "provenance_manifest.csv", provenance_rows)
    _write_csv(
        OUTPUT / "source_coverage.csv",
        [
            {
                "source_model": model,
                "expected_rnas": 42,
                "valid_predictions": sum(1 for row in runtime_rnafold if row["status"] == "valid")
                if model == "rnafold"
                else 0,
                "invalid_predictions": sum(1 for row in runtime_rnafold if row["status"] == "invalid")
                if model == "rnafold"
                else 0,
                "blocked": model != "rnafold",
                "complete_source_coverage": model == "rnafold"
                and all(row["status"] == "valid" for row in runtime_rnafold),
                "reason": "" if model == "rnafold" else "source protocol not frozen/executable for this external set",
            }
            for model in ("rnafold", "petfold", "trrosettarna2_native_ss")
        ],
    )
    NORMALIZED_ROOT.mkdir(parents=True, exist_ok=True)
    (NORMALIZED_ROOT / "README.md").write_text(
        "# external77 GT_CON v1 nonredundant normalization\n\n"
        "STATUS: NOT_READY_FOR_NORMALIZED_RECORDS\n\n"
        "The 42-row GT_CON manifest is frozen, but PETfold and trRosettaRNA2 "
        "source protocols are blocked. No normalized JSONL records are emitted "
        "until the complete three-source matrix is available.\n",
        encoding="utf-8",
    )
    valid_rnafold = sum(row["status"] == "valid" for row in runtime_rnafold)
    validation = {
        "dataset": "external77_GT_CON_v1_nonredundant",
        "generated_at_utc": _utc(),
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "gt_semantics": "GT_CON",
        "candidate_audit": candidate_audit,
        "eligible_rna_count": len(rows),
        "expected_complete_records": 126,
        "normalized_records_produced": 0,
        "complete_three_source_matrix": False,
        "source_valid_counts": {"rnafold": valid_rnafold, "petfold": 0, "trrosettarna2_native_ss": 0},
        "source_failures": {
            "petfold": "alignment input/projection protocol is not frozen for external77",
            "trrosettarna2_native_ss": "A3M/MSA input and lossless native-SS decoder are not frozen for external77",
        },
        "all_eligible_sequences_acgu_only": True,
        "all_identity_below_0_80": True,
        "gt_con_parseability": True,
        "normalization_status": "blocked_until_complete_three_source_matrix",
    }
    (OUTPUT / "validation_summary.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
