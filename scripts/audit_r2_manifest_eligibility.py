#!/usr/bin/env python3
"""Deterministically classify clean R2 manifests before any R2 execution.

This audit only inspects delivered evidence coordinates and manifest metadata.
It never reads predictions, labels, performance, or external77.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "results/evidence_guidance/e0/clean_manifests.jsonl"
OUT = ROOT / "results/global_constrained_refolding_r2/integrity"
B1 = ROOT / "results/evidence_guidance/stage_e1/per_rna_evidence_results.csv"

PAIR = "POSITIVE_PAIR_EVIDENCE"
UNPAIRED = "UNPAIRED_NUCLEOTIDE_EVIDENCE"
DENSITIES = (0, 1, 5, 10, 20, 50)
SEEDS = (101, 103, 107, 109, 113)


def crossing(a: tuple[int, int], b: tuple[int, int]) -> bool:
    i, j = a
    k, l = b
    return (i < k < j < l) or (k < i < l < j)


def canonical_pairs(items: list[dict]) -> list[tuple[int, int]]:
    pairs = []
    for item in items:
        evidence = item["delivered_evidence_item"]
        i, j = int(evidence["i"]), int(evidence["j"])
        pairs.append((min(i, j), max(i, j)))
    return sorted(set(pairs))


def crossing_count(pairs: list[tuple[int, int]]) -> int:
    return sum(crossing(a, b) for n, a in enumerate(pairs) for b in pairs[n + 1 :])


def classify(manifest: dict) -> dict:
    channel = manifest["evidence_channel"]
    pairs = canonical_pairs(manifest["items"]) if channel == PAIR else []
    n_cross = crossing_count(pairs)
    if channel == PAIR and n_cross:
        status, reason = "R2_INELIGIBLE_CROSSING_EVIDENCE", "delivered exact pair set contains crossing relation"
    elif channel in (PAIR, UNPAIRED):
        status, reason = "R2_ELIGIBLE", "noncrossing pair set" if channel == PAIR else "unpaired channel has no independent blocker"
    else:
        raise ValueError(f"unexpected evidence channel: {channel}")
    return {
        "rna_id": manifest["rna_id"],
        "channel": channel,
        "density_percent": int(manifest["density_percent"]),
        "evidence_seed": int(manifest["evidence_seed"]),
        "manifest_id": manifest["manifest_id"],
        "manifest_payload_sha256": manifest["manifest_payload_sha256"],
        "evidence_item_count": int(manifest["delivered_item_count"]),
        "crossing_pair_count": n_cross,
        "eligibility_status": status,
        "reason": reason,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def audit() -> tuple[list[dict], dict]:
    rows = []
    with MANIFESTS.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            manifest = json.loads(line)
            if manifest["noise_level_percent"] != 0:
                continue
            rows.append(classify(manifest))
    rows.sort(key=lambda r: r["manifest_id"])
    if len(rows) != 7260:
        raise AssertionError(f"expected 7260 clean manifests, found {len(rows)}")
    pair = [r for r in rows if r["channel"] == PAIR]
    crossing_rows = [r for r in pair if r["eligibility_status"] != "R2_ELIGIBLE"]
    if len(pair) != 3630 or len(crossing_rows) != 87:
        raise AssertionError(f"unexpected pair eligibility counts: {len(pair)}, {len(crossing_rows)}")

    def group_count(keys, predicate=lambda r: True):
        grouped = defaultdict(lambda: {"total": 0, "eligible": 0, "ineligible": 0, "rna_count": 0})
        rnas = defaultdict(set)
        eligible_rnas = defaultdict(set)
        for row in rows:
            if not predicate(row):
                continue
            key = tuple(row[k] for k in keys)
            grouped[key]["total"] += 1
            grouped[key]["eligible"] += row["eligibility_status"] == "R2_ELIGIBLE"
            grouped[key]["ineligible"] += row["eligibility_status"] != "R2_ELIGIBLE"
            rnas[key].add(row["rna_id"])
            if row["eligibility_status"] == "R2_ELIGIBLE":
                eligible_rnas[key].add(row["rna_id"])
        return [{**dict(zip(keys, key)), **value, "rna_count": len(rnas[key]), "eligible_rna_count": len(eligible_rnas[key])} for key, value in sorted(grouped.items())]

    summary = {
        "protocol_version": "global_constrained_refolding_r2_protocol_v1.0.1",
        "manifest_source": str(MANIFESTS.relative_to(ROOT)),
        "manifest_source_sha256": hashlib.sha256(MANIFESTS.read_bytes()).hexdigest(),
        "clean_manifest_count": len(rows),
        "pair_manifest_count": len(pair),
        "pair_eligible_count": sum(r["eligibility_status"] == "R2_ELIGIBLE" for r in pair),
        "pair_ineligible_crossing_count": len(crossing_rows),
        "unpaired_manifest_count": sum(r["channel"] == UNPAIRED for r in rows),
        "affected_rna_ids": sorted({r["rna_id"] for r in crossing_rows}),
        "coverage_by_density": group_count(["channel", "density_percent"]),
        "coverage_by_evidence_seed": group_count(["channel", "evidence_seed"]),
        "coverage_by_density_seed": group_count(["channel", "density_percent", "evidence_seed"]),
        "coverage_by_rna": group_count(["channel", "rna_id"]),
        "coverage_by_rna_density": group_count(["channel", "rna_id", "density_percent"]),
        "policy": "exclude entire crossing pair manifest; never drop or rewrite evidence",
        "formal_r2_execution_started": False,
        "external77_accessed": False,
    }
    return rows, summary


def make_matched_b1(rows: list[dict]) -> int:
    """Create a manifest-ID-filtered B1 view; do not recompute any metric."""
    if not B1.exists():
        return 0
    eligible = {r["manifest_id"] for r in rows if r["eligibility_status"] == "R2_ELIGIBLE"}
    with B1.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        selected = [row for row in reader if row.get("manifest_id") in eligible]
        fields = reader.fieldnames or []
    out = OUT / "r2_matched_b1_view.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(selected)
    return len(selected)


def main() -> None:
    rows, summary = audit()
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "r2_manifest_eligibility.csv", rows)
    matched_rows = make_matched_b1(rows)
    summary["matched_b1_view_rows"] = matched_rows
    (OUT / "r2_eligibility_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("clean_manifest_count", "pair_manifest_count", "pair_eligible_count", "pair_ineligible_crossing_count", "affected_rna_ids", "matched_b1_view_rows")}, sort_keys=True))


if __name__ == "__main__":
    main()
