#!/usr/bin/env python3
"""Reproduce historical PETfold records using the migrated single-sequence install."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from rna_ccfa.normalization import sha256_file
from rna_ccfa.structure import parse_dot_bracket, validate_pairs


ROOT = Path(__file__).resolve().parents[1]
LEGACY_MANIFEST = ROOT / "manifests/legacy121_v1.csv"
LEGACY_NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
PETFOLD = Path(os.environ.get("PETFOLD_BIN", "/root/autodl-tmp/PETfold/bin/PETfold"))
PETFOLDBIN = PETFOLD.parent
OUT = ROOT / "results/petfold_reproduction"
RAW = OUT / "legacy121_raw"
LOGS = OUT / "legacy121_logs"

AUDIT_IDS = [
    "1XWU_16_hp_nmr_A",
    "1TBK_17_hp_nmr_A",
    "2M21_21_hp_nmr_A",
    "5A17_32_hp_nmr_A",
    "9FO9_33_hp_nmr_A",
    "1A60_44_pseudknot_nmr_A",
    "2MQT_68_hpbulge_nmr_A",
    "7LYG_142_4wj_xray_A",
    "2N1Q_155_4wj_nmr_A",
    "9G7C_224_4wj_cryoEM_A",
]


def file_hash(path: Path) -> str:
    return sha256_file(path)


def structure_from_stdout(stdout: str) -> str:
    """Extract PETfold's final structure without changing its coordinates."""
    candidates = []
    for line in stdout.splitlines():
        if line.startswith("PETfold RNA structure:"):
            candidates.append(line.split("\t", 1)[-1].strip())
    if not candidates:
        raise ValueError("PETfold RNA structure line is absent")
    return candidates[-1]


def petfold_pairs(structure: str, sequence: str) -> list[tuple[int, int]]:
    """Convert PETfold's 0-based output positions to canonical project pairs.

    PETfold emits one structure character per input FASTA residue. The project
    parser enumerates those characters from zero, so no alignment projection or
    one-based adjustment is applied here.
    """
    return validate_pairs(parse_dot_bracket(structure, sequence=sequence), sequence=sequence)


def load_manifest() -> dict[str, dict[str, str]]:
    with LEGACY_MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 121:
        raise RuntimeError(f"expected 121 Legacy121 rows, observed {len(rows)}")
    return {row["rna_id"]: row for row in rows}


def load_expected() -> dict[str, dict[str, object]]:
    expected: dict[str, dict[str, object]] = {}
    for line in LEGACY_NORMALIZED.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["source_model"]["name"] == "petfold":
            expected[record["rna_id"]] = record
    if len(expected) != 121:
        raise RuntimeError(f"expected 121 historical PETfold records, observed {len(expected)}")
    return expected


def run_record(row: dict[str, str], expected: dict[str, object]) -> dict[str, object]:
    rid = row["rna_id"]
    sequence_path = Path(row["sequence_path"])
    sequence = "".join(
        line.strip() for line in sequence_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith(">")
    ).upper()
    raw_path = RAW / f"{rid}.stdout.txt"
    stderr_path = LOGS / f"{rid}.stderr.txt"
    pp_path = RAW / f"{rid}.petfoldrr"
    command = [str(PETFOLD), "-f", str(sequence_path), "-r", str(pp_path)]
    env = dict(os.environ)
    env["PETFOLDBIN"] = str(PETFOLDBIN)
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=PETFOLDBIN.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    runtime = time.monotonic() - started
    raw_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")

    status = "valid"
    error = ""
    rerun_pairs: list[tuple[int, int]] = []
    structure = ""
    try:
        if completed.returncode != 0:
            raise RuntimeError(f"PETfold exit code {completed.returncode}")
        structure = structure_from_stdout(completed.stdout)
        rerun_pairs = petfold_pairs(structure, sequence)
        if not pp_path.exists():
            raise RuntimeError("PET reliability sidecar was not produced")
    except Exception as exc:  # noqa: BLE001
        status = "invalid"
        error = str(exc)

    historical_pairs = [tuple(pair) for pair in expected["predicted_structure"]["pairs"]]
    historical_set = set(historical_pairs)
    rerun_set = set(rerun_pairs)
    exact = status == "valid" and historical_set == rerun_set
    if status == "valid" and not exact:
        error = "canonical pair-set mismatch"
    return {
        "rna_id": rid,
        "sequence_length": len(sequence),
        "historical_pair_count": len(historical_set),
        "reproduced_pair_count": len(rerun_set),
        "exact_pair_set_match": exact,
        "historical_only_pair_count": len(historical_set - rerun_set),
        "rerun_only_pair_count": len(rerun_set - historical_set),
        "status": "exact" if exact else status,
        "failure_reason": error,
        "command": "PETFOLDBIN=" + str(PETFOLDBIN) + " " + " ".join(command),
        "input_fasta_path": str(sequence_path),
        "input_fasta_sha256": file_hash(sequence_path),
        "raw_stdout_path": str(raw_path),
        "raw_stdout_sha256": file_hash(raw_path),
        "stderr_path": str(stderr_path),
        "stderr_sha256": file_hash(stderr_path),
        "petfoldrr_path": str(pp_path) if pp_path.exists() else "",
        "petfoldrr_sha256": file_hash(pp_path) if pp_path.exists() else "",
        "runtime_seconds": round(runtime, 6),
        "exit_code": completed.returncode,
        "output_structure": structure,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="run all 121 after the 10-RNA gate")
    args = parser.parse_args()
    if not PETFOLD.is_file():
        raise SystemExit(f"missing PETfold executable: {PETFOLD}")
    RAW.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    expected = load_expected()
    audit_rows = [run_record(manifest[rid], expected[rid]) for rid in AUDIT_IDS]
    write_csv(OUT / "legacy121_reproduction_10.csv", audit_rows)
    exact10 = sum(row["status"] == "exact" for row in audit_rows)
    print(json.dumps({"subset_exact": f"{exact10}/10"}, indent=2))
    if exact10 != 10:
        return 1
    if not args.all:
        return 0
    all_rows = [run_record(manifest[rid], expected[rid]) for rid in sorted(manifest)]
    write_csv(OUT / "legacy121_reproduction_121.csv", all_rows)
    exact121 = sum(row["status"] == "exact" for row in all_rows)
    print(json.dumps({"all_exact": f"{exact121}/121"}, indent=2))
    return 0 if exact121 == 121 else 1


if __name__ == "__main__":
    raise SystemExit(main())
