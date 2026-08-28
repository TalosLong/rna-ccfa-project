#!/usr/bin/env python3
"""Validate generated external77 source outputs without normalization/evaluation."""
from __future__ import annotations
import csv, json
from pathlib import Path
import numpy as np
from rna_ccfa.normalization import sha256_file
from rna_ccfa.structure import parse_extended_dot_bracket, validate_pairs

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/external77_independent_test"
MANIFEST = ROOT / "manifests/external77_GT_CON_v1_nonredundant_manifest.csv"

def main() -> int:
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8", newline="")))
    result = {"rnafold": {"valid": 0, "invalid": 0}, "trrosettarna2_native_ss": {"valid": 0, "invalid": 0}}
    failures = []
    for row in rows:
        rid, seq = row["rna_id"], row["sequence"]
        for model, suffix in (("rnafold", ".dbn"), ("trrosettarna2_native_ss", ".dbn")):
            if model == "rnafold":
                p = OUT / "source_predictions/rnafold/outputs" / f"{rid}.dbn"
            else:
                p = OUT / "source_predictions/trrosettarna2_native_ss/outputs" / rid / f"{rid}.dbn"
            try:
                lines = [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
                if model == "rnafold":
                    if len(lines) != 3 or lines[1] != seq:
                        raise ValueError("header/sequence mismatch")
                    structure = lines[2]
                else:
                    # The historical standalone writer stores header + DBN;
                    # the query sequence is validated from the frozen A3M.
                    if len(lines) != 2 or lines[0] != f">{rid}":
                        raise ValueError("DBN header/length mismatch")
                    a3m_lines = (p.parents[2] / "msas" / f"{rid}.a3m").read_text(encoding="utf-8").splitlines()
                    if len(a3m_lines) < 2 or a3m_lines[1] != seq:
                        raise ValueError("A3M sequence mismatch")
                    structure = lines[1]
                pairs = validate_pairs(parse_extended_dot_bracket(structure, sequence=seq), sequence=seq)
                if model.startswith("tr"):
                    npz = p.parent / f"{rid}_ss_prob.npz"
                    arr = np.load(npz)["ss"]
                    if arr.shape != (len(seq), len(seq)) or not np.isfinite(arr).all():
                        raise ValueError("invalid score matrix shape/finite check")
                result[model]["valid"] += 1
            except Exception as exc:  # noqa: BLE001
                result[model]["invalid"] += 1
                failures.append({"rna_id": rid, "source_model": model, "reason": str(exc)})
    summary_path = OUT / "validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["source_valid_counts"]["rnafold"] = result["rnafold"]["valid"]
    summary["source_valid_counts"]["trrosettarna2_native_ss"] = result["trrosettarna2_native_ss"]["valid"]
    summary["source_invalid_counts"] = {k: v["invalid"] for k, v in result.items()}
    summary["trrosettarna2_native_ss_status"] = "valid" if result["trrosettarna2_native_ss"]["valid"] == 42 else "failed"
    summary["source_failures"] = {"petfold": "historical alignment/projection unavailable"} if result["trrosettarna2_native_ss"]["invalid"] == 0 else {"petfold": "historical alignment/projection unavailable", "trrosettarna2_native_ss": failures}
    summary["source_matrix_validation"] = {"rnafold": result["rnafold"], "trrosettarna2_native_ss": result["trrosettarna2_native_ss"], "failures": failures}
    summary["complete_three_source_matrix"] = False
    summary["normalized_records_produced"] = 0
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary["source_matrix_validation"], indent=2, sort_keys=True))
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
