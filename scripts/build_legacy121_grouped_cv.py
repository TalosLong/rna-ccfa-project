#!/usr/bin/env python3
"""Build deterministic Legacy121 grouped five-fold assignments.

The assignment unit is an 80%-global-identity connected component. All three
source-model records for an RNA inherit its RNA-level fold.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from Bio import Align


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/legacy121_v1.csv"
OUTPUT = ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv"
THRESHOLD = 0.80
N_FOLDS = 5


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
    return counts.identities / (counts.identities + counts.mismatches + counts.gaps)


def _sequence(path: str) -> str:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return "".join(line.strip() for line in lines if line.strip() and not line.startswith(">"))


def _components(sequences: dict[str, str]) -> list[list[str]]:
    ids = sorted(sequences)
    parent = {rna_id: rna_id for rna_id in ids}

    def find(value: str) -> str:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(first: str, second: str) -> None:
        first_root, second_root = find(first), find(second)
        if first_root != second_root:
            parent[second_root] = first_root

    aligner = _aligner()
    for offset, first in enumerate(ids):
        for second in ids[offset + 1 :]:
            if _identity(aligner, sequences[first], sequences[second]) >= THRESHOLD:
                union(first, second)
    grouped: dict[str, list[str]] = defaultdict(list)
    for rna_id in ids:
        grouped[find(rna_id)].append(rna_id)
    return sorted((sorted(members) for members in grouped.values()), key=lambda members: (len(members), members), reverse=True)


def main() -> int:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 121 or len({row["rna_id"] for row in rows}) != 121:
        raise RuntimeError("Legacy121 manifest must contain 121 unique RNAs")
    sequences = {row["rna_id"]: _sequence(row["sequence_path"]) for row in rows}
    components = _components(sequences)
    fold_components: list[list[list[str]]] = [[] for _ in range(N_FOLDS)]
    fold_sizes = [0] * N_FOLDS
    for component in components:
        target = min(range(N_FOLDS), key=lambda fold: (fold_sizes[fold], fold))
        fold_components[target].append(component)
        fold_sizes[target] += len(component)
    fold_by_rna = {
        rna_id: fold
        for fold, groups in enumerate(fold_components)
        for group in groups
        for rna_id in group
    }
    if len(fold_by_rna) != 121:
        raise RuntimeError("fold assignment does not cover all Legacy121 RNAs")
    for group in components:
        assigned = {fold_by_rna[rna_id] for rna_id in group}
        if len(assigned) != 1:
            raise RuntimeError("identity-connected component crosses folds")
    output_rows = []
    component_by_rna = {
        rna_id: (component_index, group)
        for component_index, group in enumerate(sorted(components, key=lambda values: values[0]))
        for rna_id in group
    }
    for rna_id in sorted(sequences):
        component_id, group = component_by_rna[rna_id]
        output_rows.append(
            {
                "rna_id": rna_id,
                "fold": fold_by_rna[rna_id],
                "component_id": f"identity_component_{component_id:03d}",
                "component_size": len(group),
                "sequence_length": len(sequences[rna_id]),
                "source_records_per_rna": 3,
                "source_models": "rnafold|petfold|trrosettarna2_native_ss",
                "identity_threshold": THRESHOLD,
                "split_unit": "rna_and_identity_component",
            }
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(output_rows[0])
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)
    fold_counts = {str(fold): sum(row["fold"] == fold for row in output_rows) for fold in range(N_FOLDS)}
    print({"n_rnas": len(output_rows), "n_components": len(components), "fold_counts": fold_counts})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
