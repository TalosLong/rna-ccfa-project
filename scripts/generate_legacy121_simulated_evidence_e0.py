#!/usr/bin/env python3
"""Generate and audit frozen Legacy121 simulated-evidence v1 manifests.

This Stage E0 script creates evidence manifests only. It does not inspect a
source prediction, apply a refinement condition, or compute structure metrics.
"""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

from rna_ccfa.simulated_evidence import (
    DENSITY_GRID_PERCENT,
    EVIDENCE_CHANNELS,
    EVIDENCE_SEEDS,
    NOISE_GRID_PERCENT,
    POSITIVE_PAIR_EVIDENCE,
    PROTOCOL_VERSION,
    UNPAIRED_NUCLEOTIDE_EVIDENCE,
    build_clean_evidence_manifest,
    corrupt_evidence_manifest,
    evidence_jsonl_bytes,
    pair_evidence_universe,
    unpaired_evidence_universe,
    validate_evidence_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
FOLDS = ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv"
GENERATOR = ROOT / "src/rna_ccfa/simulated_evidence.py"
OUT = ROOT / "results/evidence_guidance/e0"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_gt_only_inputs() -> dict[str, dict]:
    """Deduplicate the 363 records into 121 GT-only generator inputs."""

    gt_only: dict[str, dict] = {}
    source_copies: defaultdict[str, int] = defaultdict(int)
    with NORMALIZED.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            # Deliberately extract only the three fields permitted by the
            # generator contract. Prediction and error fields are never read.
            value = {
                "rna_id": record["rna_id"],
                "sequence": record["sequence"],
                "ground_truth_pairs": record["ground_truth_structure"]["pairs"],
            }
            rna_id = value["rna_id"]
            normalized_value = {
                **value,
                "ground_truth_pairs": [list(pair) for pair in value["ground_truth_pairs"]],
            }
            if rna_id in gt_only and gt_only[rna_id] != normalized_value:
                raise AssertionError(f"inconsistent Legacy121 GT copies for {rna_id}")
            gt_only[rna_id] = normalized_value
            source_copies[rna_id] += 1
    if len(gt_only) != 121 or any(source_copies[rna_id] != 3 for rna_id in gt_only):
        raise AssertionError("expected 121 RNAs with exactly three identical GT copies")

    with FOLDS.open(encoding="utf-8") as handle:
        fold_rows = list(csv.DictReader(handle))
    if len(fold_rows) != 121 or {row["rna_id"] for row in fold_rows} != set(gt_only):
        raise AssertionError("frozen Legacy121 folds do not match the GT-only inputs")
    return gt_only


def generate_clean_manifests(gt_only: dict[str, dict]) -> list[dict]:
    manifests = []
    for rna_id in sorted(gt_only):
        row = gt_only[rna_id]
        for channel in EVIDENCE_CHANNELS:
            for density in DENSITY_GRID_PERCENT:
                for seed in EVIDENCE_SEEDS:
                    manifest = build_clean_evidence_manifest(
                        rna_id=rna_id,
                        sequence=row["sequence"],
                        ground_truth_pairs=row["ground_truth_pairs"],
                        evidence_channel=channel,
                        density_percent=density,
                        evidence_seed=seed,
                    )
                    validate_evidence_manifest(
                        manifest,
                        sequence=row["sequence"],
                        ground_truth_pairs=row["ground_truth_pairs"],
                    )
                    manifests.append(manifest)
    if len(manifests) != 2 * 6 * 5 * 121:
        raise AssertionError("clean manifest count mismatch")
    return manifests


def universe_rows(gt_only: dict[str, dict]) -> list[dict]:
    rows = []
    for rna_id in sorted(gt_only):
        value = gt_only[rna_id]
        pairs = pair_evidence_universe(value["sequence"], value["ground_truth_pairs"])
        unpaired = unpaired_evidence_universe(value["sequence"], pairs)
        rows.append(
            {
                "rna_id": rna_id,
                "sequence_length": len(value["sequence"]),
                "gt_pair_count": len(pairs),
                "unpaired_nucleotide_count": len(unpaired),
                "pair_universe_usable": int(bool(pairs)),
                "unpaired_universe_usable": int(bool(unpaired)),
            }
        )
    return rows


def clean_index(manifests: list[dict]) -> list[dict]:
    return [
        {
            "manifest_id": row["manifest_id"],
            "rna_id": row["rna_id"],
            "sequence_length": row["sequence_length"],
            "evidence_channel": row["evidence_channel"],
            "density_percent": row["density_percent"],
            "evidence_seed": row["evidence_seed"],
            "noise_level_percent": row["noise_level_percent"],
            "eligible_universe_size": row["eligible_universe_size"],
            "selected_item_count": row["selected_item_count"],
            "minimum_one_applied": int(row["minimum_one_applied"]),
            "source_gt_sha256": row["source_gt_sha256"],
            "manifest_payload_sha256": row["manifest_payload_sha256"],
        }
        for row in sorted(manifests, key=lambda item: item["manifest_id"])
    ]


def selected_count_summary(manifests: list[dict]) -> list[dict]:
    groups: defaultdict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in manifests:
        groups[(row["evidence_channel"], row["density_percent"])].append(row)
    summary = []
    for (channel, density), rows in sorted(groups.items()):
        total = sum(row["selected_item_count"] for row in rows)
        summary.append(
            {
                "evidence_channel": channel,
                "density_percent": density,
                "manifest_count": len(rows),
                "rna_count": len({row["rna_id"] for row in rows}),
                "evidence_seed_count": len({row["evidence_seed"] for row in rows}),
                "selected_items_all_seeds": total,
                "selected_items_per_seed": total // len(EVIDENCE_SEEDS),
                "minimum_one_manifest_count": sum(row["minimum_one_applied"] for row in rows),
                "minimum_one_rna_count_per_seed": sum(
                    row["minimum_one_applied"]
                    for row in rows
                    if row["evidence_seed"] == EVIDENCE_SEEDS[0]
                ),
                "zero_universe_manifest_count": sum(
                    row["eligible_universe_size"] == 0 for row in rows
                ),
            }
        )
    return summary


def noise_validation_sample(gt_only: dict[str, dict]) -> tuple[list[dict], list[dict], dict]:
    manifests: list[dict] = []
    summary: list[dict] = []
    selected_rnas: dict[str, str] = {}
    for channel in EVIDENCE_CHANNELS:
        ranked = []
        for rna_id, value in gt_only.items():
            if channel == POSITIVE_PAIR_EVIDENCE:
                size = len(pair_evidence_universe(value["sequence"], value["ground_truth_pairs"]))
            else:
                size = len(unpaired_evidence_universe(value["sequence"], value["ground_truth_pairs"]))
            ranked.append((-size, rna_id))
        _, rna_id = min(ranked)
        selected_rnas[channel] = rna_id
        value = gt_only[rna_id]
        clean = build_clean_evidence_manifest(
            rna_id=rna_id,
            sequence=value["sequence"],
            ground_truth_pairs=value["ground_truth_pairs"],
            evidence_channel=channel,
            density_percent=50,
            evidence_seed=101,
        )
        for noise in NOISE_GRID_PERCENT:
            if noise == 0:
                noisy = clean
            else:
                noisy = corrupt_evidence_manifest(
                    clean,
                    sequence=value["sequence"],
                    ground_truth_pairs=value["ground_truth_pairs"],
                    noise_level_percent=noise,
                )
            validate_evidence_manifest(
                noisy,
                sequence=value["sequence"],
                ground_truth_pairs=value["ground_truth_pairs"],
            )
            manifests.append(noisy)
            summary.append(
                {
                    "evidence_channel": channel,
                    "rna_id": rna_id,
                    "density_percent": 50,
                    "evidence_seed": 101,
                    "noise_level_percent": noise,
                    "eligible_universe_size": noisy["eligible_universe_size"],
                    "selected_item_count": noisy["selected_item_count"],
                    "requested_corruption_count": noisy["requested_corruption_count"],
                    "successful_corruption_count": noisy["successful_corruption_count"],
                    "unavailable_corruption_count": noisy["unavailable_corruption_count"],
                    "delivered_item_count": noisy["delivered_item_count"],
                    "manifest_payload_sha256": noisy["manifest_payload_sha256"],
                }
            )
    return manifests, summary, selected_rnas


def main() -> None:
    gt_only = load_gt_only_inputs()
    manifests = generate_clean_manifests(gt_only)
    serialized = evidence_jsonl_bytes(manifests)
    # Independent deterministic regeneration is a hard E0 audit.
    rerun = evidence_jsonl_bytes(generate_clean_manifests(gt_only))
    if serialized != rerun:
        raise AssertionError("deterministic clean-manifest rerun mismatch")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "clean_manifests.jsonl").write_bytes(serialized)
    write_csv(OUT / "clean_manifest_index.csv", clean_index(manifests))
    universes = universe_rows(gt_only)
    write_csv(OUT / "evidence_universe_by_rna.csv", universes)
    selected_summary = selected_count_summary(manifests)
    write_csv(OUT / "selected_counts_by_density.csv", selected_summary)

    noise_manifests, noise_summary, selected_rnas = noise_validation_sample(gt_only)
    noise_bytes = evidence_jsonl_bytes(noise_manifests)
    (OUT / "noise_mechanism_validation.jsonl").write_bytes(noise_bytes)
    write_csv(OUT / "noise_mechanism_validation_summary.csv", noise_summary)

    write_json(
        OUT / "protocol_config.json",
        {
            "protocol_version": PROTOCOL_VERSION,
            "status": "FROZEN_BEFORE_EVIDENCE_GUIDED_EVALUATION",
            "evidence_channels": list(EVIDENCE_CHANNELS),
            "density_grid_percent": list(DENSITY_GRID_PERCENT),
            "evidence_seeds": list(EVIDENCE_SEEDS),
            "noise_grid_percent": list(NOISE_GRID_PERCENT),
            "selection_count_rule": "round_half_up_then_minimum_one_for_positive_density",
            "noise_count_rule": "round_half_up_without_minimum_one",
            "pair_corruption_policy": "preserve_one_endpoint_and_sample_unique_canonical_non_gt_partner",
            "unpaired_corruption_policy": "replace_with_unique_gt_paired_position_claimed_unpaired",
            "corruption_failure_policy": "CORRUPTION_UNAVAILABLE",
            "generator_inputs": ["rna_id", "sequence", "ground_truth_pairs"],
            "future_e1_conditions": [
                "ORIGINAL",
                "V3_VETO2_FIXED",
                "PAIR_PROTECT_ONLY",
                "PAIR_HARD_ENFORCE",
                "UNPAIRED_HARD_DELETE",
            ],
            "future_evaluation_scopes": [
                "DIRECT_EVIDENCE_EFFECT",
                "LOCAL_CONFLICT_EFFECT",
                "NON_EVIDENCED_EFFECT",
            ],
            "stage_e1_evaluated": False,
            "external77_accessed": False,
        },
    )

    pair_sizes = [row["gt_pair_count"] for row in universes]
    unpaired_sizes = [row["unpaired_nucleotide_count"] for row in universes]
    generator_sha = sha256_file(GENERATOR)
    clean_sha = hashlib.sha256(serialized).hexdigest()
    summary = {
        "protocol_version": PROTOCOL_VERSION,
        "status": "EVIDENCE_GUIDANCE_STAGE_E0_COMPLETE",
        "normalized_legacy121_sha256": sha256_file(NORMALIZED),
        "frozen_fold_assignment_sha256": sha256_file(FOLDS),
        "generator_source_sha256": generator_sha,
        "generator_inputs": ["rna_id", "sequence", "ground_truth_pairs"],
        "prediction_fields_used": [],
        "rna_count": len(gt_only),
        "clean_manifest_count": len(manifests),
        "clean_selected_item_count": sum(row["selected_item_count"] for row in manifests),
        "clean_manifest_jsonl_sha256": clean_sha,
        "deterministic_rerun_sha256": hashlib.sha256(rerun).hexdigest(),
        "deterministic_rerun_match": serialized == rerun,
        "evidence_channels": list(EVIDENCE_CHANNELS),
        "density_grid_percent": list(DENSITY_GRID_PERCENT),
        "evidence_seeds": list(EVIDENCE_SEEDS),
        "noise_grid_percent": list(NOISE_GRID_PERCENT),
        "pair_channel_usable_rnas": sum(size > 0 for size in pair_sizes),
        "unpaired_channel_usable_rnas": sum(size > 0 for size in unpaired_sizes),
        "pair_universe_total": sum(pair_sizes),
        "unpaired_universe_total": sum(unpaired_sizes),
        "pair_universe_median": statistics.median(pair_sizes),
        "unpaired_universe_median": statistics.median(unpaired_sizes),
        "noise_validation_manifest_count": len(noise_manifests),
        "noise_validation_rnas": selected_rnas,
        "noise_requested_corruptions": sum(row["requested_corruption_count"] for row in noise_summary),
        "noise_successful_corruptions": sum(row["successful_corruption_count"] for row in noise_summary),
        "noise_unavailable_corruptions": sum(row["unavailable_corruption_count"] for row in noise_summary),
        "invalid_coordinate_failures": 0,
        "duplicate_failures": 0,
        "canonical_corrupted_pair_failures": 0,
        "manifest_validation_failures": 0,
        "stage_e1_structure_evaluation_performed": False,
        "new_neural_training_runs": 0,
        "external77_accessed": False,
    }
    write_json(OUT / "generation_summary.json", summary)
    write_json(
        OUT / "suite_hashes.json",
        {
            "protocol_version": PROTOCOL_VERSION,
            "clean_manifests_jsonl": clean_sha,
            "clean_manifest_index_csv": sha256_file(OUT / "clean_manifest_index.csv"),
            "evidence_universe_by_rna_csv": sha256_file(OUT / "evidence_universe_by_rna.csv"),
            "selected_counts_by_density_csv": sha256_file(OUT / "selected_counts_by_density.csv"),
            "noise_mechanism_validation_jsonl": hashlib.sha256(noise_bytes).hexdigest(),
            "noise_mechanism_validation_summary_csv": sha256_file(OUT / "noise_mechanism_validation_summary.csv"),
            "protocol_config_json": sha256_file(OUT / "protocol_config.json"),
        },
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
