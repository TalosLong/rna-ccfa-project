#!/usr/bin/env python3
"""Run the frozen historical single-sequence PETfold protocol on external77."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from rna_ccfa.normalization import sha256_file
from rna_ccfa.structure import parse_dot_bracket, validate_pairs
try:
    from scripts.reproduce_petfold import petfold_pairs, structure_from_stdout
except ModuleNotFoundError:  # direct execution places scripts/ on sys.path
    from reproduce_petfold import petfold_pairs, structure_from_stdout


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/external77_GT_CON_v1_nonredundant_manifest.csv"
OUT = ROOT / "results/external77_independent_test/petfold"
INPUTS = OUT / "inputs"
RAW = OUT / "raw"
LOGS = OUT / "logs"
PARSED = OUT / "parsed"
RUNTIME = OUT / "runtime.csv"
PETFOLD = Path(os.environ.get("PETFOLD_BIN", "/root/autodl-tmp/PETfold/bin/PETfold"))
PETFOLDBIN = PETFOLD.parent


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 42 or len({row["rna_id"] for row in rows}) != 42:
        raise RuntimeError("frozen external77 manifest must contain 42 unique RNAs")
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if not PETFOLD.is_file() or not os.access(PETFOLD, os.X_OK):
        raise SystemExit(f"PETfold executable is unavailable or not executable: {PETFOLD}")
    for directory in (INPUTS, RAW, LOGS, PARSED):
        directory.mkdir(parents=True, exist_ok=True)

    runtime_rows: list[dict[str, object]] = []
    valid = 0
    for row in read_manifest():
        rid, sequence = row["rna_id"], row["sequence"].upper()
        fasta = INPUTS / f"{rid}.fasta"
        fasta.write_text(f">{rid}\n{sequence}\n", encoding="utf-8")
        stdout_path = RAW / f"{rid}.stdout.txt"
        stderr_path = LOGS / f"{rid}.stderr.txt"
        pp_path = RAW / f"{rid}.petfoldrr"
        parsed_path = PARSED / f"{rid}.json"
        command = [str(PETFOLD), "-f", str(fasta), "-r", str(pp_path)]
        environment = dict(os.environ)
        environment["PETFOLDBIN"] = str(PETFOLDBIN)
        started = time.monotonic()
        result = subprocess.run(
            command, cwd=PETFOLDBIN.parent, env=environment,
            capture_output=True, text=True, timeout=300, check=False,
        )
        runtime = time.monotonic() - started
        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")
        status, failure, structure, pairs = "valid", "", "", []
        try:
            if result.returncode != 0:
                raise RuntimeError(f"PETfold exit code {result.returncode}")
            structure = structure_from_stdout(result.stdout)
            pairs = petfold_pairs(structure, sequence)
            if len(structure) != len(sequence):
                raise RuntimeError("structure/query length mismatch")
            if not pp_path.is_file():
                raise RuntimeError("PET reliability sidecar missing")
        except Exception as exc:  # noqa: BLE001
            status, failure = "invalid", str(exc)
        parsed = {
            "rna_id": rid, "sequence": sequence, "sequence_length": len(sequence),
            "structure": structure, "pairs": [[i, j] for i, j in pairs],
            "status": status, "failure_reason": failure,
            "input_fasta_path": str(fasta), "input_fasta_sha256": sha256_file(fasta),
            "raw_stdout_path": str(stdout_path), "raw_stdout_sha256": sha256_file(stdout_path),
            "stderr_path": str(stderr_path), "stderr_sha256": sha256_file(stderr_path),
            "petfoldrr_path": str(pp_path) if pp_path.exists() else "",
            "petfoldrr_sha256": sha256_file(pp_path) if pp_path.exists() else "",
            "command": "PETFOLDBIN=" + str(PETFOLDBIN) + " " + " ".join(command),
            "runtime_seconds": round(runtime, 6), "exit_code": result.returncode,
            "created_at_utc": utc(),
        }
        parsed_path.write_text(json.dumps(parsed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if status == "valid":
            valid += 1
        runtime_rows.append({
            "source_model": "petfold", "rna_id": rid, "status": status,
            "runtime_seconds": round(runtime, 6), "exit_code": result.returncode,
            "command": parsed["command"], "version": "PETfold v2.0",
            "executable": str(PETFOLD), "petfold_binary_sha256": sha256_file(PETFOLD),
            "article_grm_sha256": sha256_file(PETFOLDBIN / "article.grm"),
            "scfg_rate_sha256": sha256_file(PETFOLDBIN / "scfg.rate"),
            "input_fasta_path": str(fasta), "input_fasta_sha256": parsed["input_fasta_sha256"],
            "raw_stdout_path": str(stdout_path), "raw_stdout_sha256": parsed["raw_stdout_sha256"],
            "stderr_path": str(stderr_path), "stderr_sha256": parsed["stderr_sha256"],
            "petfoldrr_path": parsed["petfoldrr_path"], "petfoldrr_sha256": parsed["petfoldrr_sha256"],
            "failure_reason": failure,
        })
    write_csv(RUNTIME, runtime_rows)
    print(json.dumps({"valid": valid, "invalid": 42 - valid, "runtime_csv": str(RUNTIME)}, indent=2))
    return 0 if valid == 42 else 1


if __name__ == "__main__":
    raise SystemExit(main())
