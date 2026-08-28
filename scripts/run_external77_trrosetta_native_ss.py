#!/usr/bin/env python3
"""Run the frozen, single-sequence trRosettaRNA2 native-SS source condition.

This is intentionally separate from normalization: it only materializes source
outputs and provenance for the 42 frozen external77 candidates.  The historical
Legacy121 audit showed that all 121 native-SS A3Ms are one-row query-only files
and that the existing standalone ensemble/0.5 decoder reproduces the stored
historical DBNs.  No GT structure is read by this script.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from rna_ccfa.normalization import sha256_file


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/external77_GT_CON_v1_nonredundant_manifest.csv"
OUT = ROOT / "results/external77_independent_test"
RAW = OUT / "source_predictions/trrosettarna2_native_ss"
INPUTS = RAW / "inputs"
MSAS = RAW / "msas"
OUTPUTS = RAW / "outputs"
LOGS = RAW / "logs"
TRRNA = Path("/root/autodl-tmp/models/trRosettaRNA2")
PYTHON = TRRNA / "env_trRNA2/bin/python"
PREDICTOR = TRRNA / "scripts/tools/ss_predictor_standalone.py"


def utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rows() -> list[dict[str, str]]:
    with MANIFEST.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))


def main() -> int:
    rs = rows()
    if len(rs) != 42:
        raise RuntimeError(f"expected frozen 42-row manifest, observed {len(rs)}")
    for d in (INPUTS, MSAS, OUTPUTS, LOGS):
        d.mkdir(parents=True, exist_ok=True)
    for row in rs:
        rid, seq = row["rna_id"], row["sequence"]
        (INPUTS / f"{rid}.fasta").write_text(f">{rid}\n{seq}\n", encoding="utf-8")
        # Historical native-SS inputs are query-only A3M files.  Keeping the
        # query as the first/only row avoids introducing a new database/MSA.
        (MSAS / f"{rid}.a3m").write_text(f">{rid}\n{seq}\n", encoding="utf-8")

    stdout = LOGS / "batch.stdout.txt"
    stderr = LOGS / "batch.stderr.txt"
    started = time.monotonic()
    command = [str(PYTHON), str(PREDICTOR), "--batch", str(INPUTS), "--msa_dir", str(MSAS),
               "-o", str(OUTPUTS), "--gpu", "-1", "--threshold", "0.5", "--resume"]
    result = subprocess.run(command, cwd=TRRNA, capture_output=True, text=True, timeout=3600)
    elapsed = time.monotonic() - started
    stdout.write_text(result.stdout, encoding="utf-8")
    stderr.write_text(result.stderr, encoding="utf-8")

    runtime_rows: list[dict[str, object]] = []
    provenance_rows: list[dict[str, object]] = []
    valid = 0
    for row in rs:
        rid = row["rna_id"]
        outdir = OUTPUTS / rid
        npz = outdir / f"{rid}_ss_prob.npz"
        dbn = outdir / f"{rid}.dbn"
        status = "valid" if result.returncode == 0 and npz.exists() and dbn.exists() else "failed"
        failure = "" if status == "valid" else f"exit={result.returncode}; missing output"
        if status == "valid":
            valid += 1
        runtime_rows.append({
            "source_model": "trrosettarna2_native_ss",
            "rna_id": rid,
            "status": status,
            "runtime_seconds": round(elapsed, 6),
            "exit_status": result.returncode,
            "command": " ".join(command),
            "version": "trRosettaRNA2 local standalone SS ensemble; checkpoint hashes in source gate",
            "environment": str(PYTHON),
            "stdout_log": str(stdout),
            "stderr_log": str(stderr),
            "failure_reason": failure,
        })
        provenance_rows.append({
            "source_model": "trrosettarna2_native_ss",
            "rna_id": rid,
            "status": status,
            "input_fasta_path": str(INPUTS / f"{rid}.fasta"),
            "input_fasta_sha256": sha256_file(INPUTS / f"{rid}.fasta"),
            "a3m_path": str(MSAS / f"{rid}.a3m"),
            "a3m_sha256": sha256_file(MSAS / f"{rid}.a3m"),
            "output_npz_path": str(npz) if status == "valid" else "",
            "output_npz_sha256": sha256_file(npz) if status == "valid" else "",
            "output_dbn_path": str(dbn) if status == "valid" else "",
            "output_dbn_sha256": sha256_file(dbn) if status == "valid" else "",
            "raw_stdout_sha256": sha256_file(stdout),
            "raw_stderr_sha256": sha256_file(stderr),
            "decoder": "mat2dotbracket threshold > 0.5; greedy strongest-pair one-partner decoder",
        })

    def write_csv(path: Path, data: list[dict[str, object]]) -> None:
        fields: list[str] = []
        for item in data:
            for key in item:
                if key not in fields:
                    fields.append(key)
        with path.open("w", encoding="utf-8", newline="") as h:
            w = csv.DictWriter(h, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            for item in data:
                w.writerow(item)

    # Preserve existing RNAfold and PETfold rows; replace only the trRNA2
    # blocked aggregate with the per-RNA execution audit.
    runtime_path = OUT / "source_runtime.csv"
    existing = list(csv.DictReader(runtime_path.open(encoding="utf-8", newline=""))) if runtime_path.exists() else []
    existing = [r for r in existing if r.get("source_model") != "trrosettarna2_native_ss"]
    write_csv(runtime_path, existing + runtime_rows)
    prov_path = OUT / "provenance_manifest.csv"
    oldprov = list(csv.DictReader(prov_path.open(encoding="utf-8", newline=""))) if prov_path.exists() else []
    oldprov = [r for r in oldprov if r.get("source_model") != "trrosettarna2_native_ss"]
    write_csv(prov_path, oldprov + provenance_rows)
    coverage_path = OUT / "source_coverage.csv"
    cov = list(csv.DictReader(coverage_path.open(encoding="utf-8", newline=""))) if coverage_path.exists() else []
    for c in cov:
        if c.get("source_model") == "trrosettarna2_native_ss":
            c.update({"valid_predictions": valid, "invalid_predictions": 42-valid,
                      "blocked": False, "complete_source_coverage": valid == 42,
                      "reason": "" if valid == 42 else "source execution failure"})
    write_csv(coverage_path, cov)
    summary_path = OUT / "validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    summary.update({"trrosettarna2_native_ss_valid": valid,
                    "trrosettarna2_native_ss_status": "valid" if valid == 42 else "failed",
                    "complete_three_source_matrix": False,
                    "normalized_records_produced": 0,
                    "last_source_update_utc": utc()})
    failures = dict(summary.get("source_failures", {}))
    failures.pop("trrosettarna2_native_ss", None)
    summary["source_failures"] = failures
    counts = dict(summary.get("source_valid_counts", {}))
    counts["trrosettarna2_native_ss"] = valid
    summary["source_valid_counts"] = counts
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"valid": valid, "exit_status": result.returncode, "runtime_seconds": round(elapsed, 3)}, indent=2))
    return 0 if valid == 42 else 1


if __name__ == "__main__":
    raise SystemExit(main())
