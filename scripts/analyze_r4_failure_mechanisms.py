#!/usr/bin/env python3
"""Post-hoc diagnostics of the frozen R4 held-out outputs.

This script never trains, calibrates, selects a threshold, or changes a held-out
decision.  It reads the sealed combined Track E score files and immutable R4
candidate table, verifies their hashes, and writes descriptive diagnostics to a
separate postmortem directory.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
from typing import Iterable

import numpy as np
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rna_ccfa.evidence_reconciliation import sha256_file, write_json  # noqa: E402


R4 = ROOT / "results/clean_learned_evidence_reconciliation_r4"
OUT = R4 / "postmortem"
SEEDS = (17, 29, 41, 53, 67)
CHANNELS = ("positive_pair", "unpaired")
SCOPES = ("DIRECT", "LOCAL_CONFLICT", "NON_EVIDENCED")

FROZEN_HASHES = {
    "docs/clean_learned_evidence_reconciliation_r4_protocol.md":
        "81ce3923c19a99094418dc5fb568c7081192ac84c542b33dbb4bafa888c739e4",
    "docs/clean_learned_evidence_reconciliation_r4_results.md":
        "728e931d4e1329935fe990154940cb0b35900f56d14298d88ef59a7ad8e3fc8c",
    "results/clean_learned_evidence_reconciliation_r4/features/candidate_rows.parquet":
        "4f0204611333f8783aced1eddd874dedf71c837debc68515abda54cf35834a7c",
    "results/clean_learned_evidence_reconciliation_r4/features/feature_contract.json":
        "154d9e2a59c2d571369edc516c0932b41adb8bea62943a3de6920431e9c7ad28",
    "results/clean_learned_evidence_reconciliation_r4/summaries/gate_b.json":
        "91e5cce227a7928b29536e49908af55fe195d72d1761a36be31d29fe97dd3bc6",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/ern_combined_seed_17.parquet":
        "dc8b12ed34e5b55a6a4fd0b93079dc48fe147c781ec5d05ff7bcd096b3451c70",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/ern_combined_seed_29.parquet":
        "8a112ea13c13b4d1f4209f1a44fd0bcba47aec0734d8d49c9b726051155500bf",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/ern_combined_seed_41.parquet":
        "b9b78f48ef04d4c43be35e47477b5b892d642359588de21088d402addc9c7d30",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/ern_combined_seed_53.parquet":
        "21dd488d7324cbde91c7c67803b5ed4eb2f27f06eb344c9ca2ebf29a2efe3771",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/ern_combined_seed_67.parquet":
        "5498879eadd96801dc557403ecfe02ae4a89ae84f35720a59b58630f9e39cb17",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/b4_evidence_masked_combined_seed_17.parquet":
        "e1eafb1ad907adabd11072afb84e6b238769916de25999785961ed083a331c0b",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/b4_evidence_masked_combined_seed_29.parquet":
        "e6bcb90f33f26e396babf6a3758f7ca22ad80bca670ab90aea9c246c74810996",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/b4_evidence_masked_combined_seed_41.parquet":
        "9e883edc4ceb55877515a293f173288c4a828591b977de1ca3329d13a2d0e36d",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/b4_evidence_masked_combined_seed_53.parquet":
        "4e87ab134abb40827cd4c3f6549f43dc1324ce2efb26407aaa3d7bf961a2e37a",
    "results/clean_learned_evidence_reconciliation_r4/pair_scores/b4_evidence_masked_combined_seed_67.parquet":
        "542e02663e14c9cbb8d1ec6e6e228e1752ce644b680e79289be7a657069e438c",
}

PAIR_TYPES = (
    "AA", "AC", "AG", "AU", "CA", "CC", "CG", "CU", "GA", "GC",
    "GG", "GU", "UA", "UC", "UG", "UU", "OTHER", "UNKNOWN",
)


def sequence_separation_bin(value: int) -> str:
    if value <= 9:
        return "04-09"
    if value <= 19:
        return "10-19"
    if value <= 49:
        return "20-49"
    if value <= 99:
        return "50-99"
    return "100+"


def stem_position_bin(singleton: float, normalized: float) -> str:
    if singleton >= 0.5:
        return "SINGLETON"
    if normalized < 0.25:
        return "[0.00,0.25)"
    if normalized < 0.50:
        return "[0.25,0.50)"
    if normalized < 0.75:
        return "[0.50,0.75)"
    return "[0.75,1.00]"


def boundary_status(singleton: float, outer: float, inner: float) -> str:
    if singleton >= 0.5:
        return "SINGLETON"
    if outer >= 0.5 and inner >= 0.5:
        return "BOTH_BOUNDARIES"
    if outer >= 0.5:
        return "OUTER_BOUNDARY"
    if inner >= 0.5:
        return "INNER_BOUNDARY"
    return "STEM_INTERIOR"


def p2_agreement_bin(value: float) -> str:
    support = int(round(2.0 * value))
    if support not in (0, 1, 2) or not math.isclose(value, support / 2.0, abs_tol=1e-8):
        raise AssertionError(f"unexpected P2 support value: {value}")
    return f"{support}_of_2_other_sources"


def p4_risk_bin(bpp: float) -> str:
    risk = 1.0 - bpp
    if risk < 0.10:
        return "[0.00,0.10)"
    if risk < 0.25:
        return "[0.10,0.25)"
    if risk < 0.50:
        return "[0.25,0.50)"
    if risk < 0.75:
        return "[0.50,0.75)"
    return "[0.75,1.00]"


def calibrated_risk_bin(probability: float) -> str:
    index = min(int(probability * 10.0), 9)
    lower = index / 10.0
    upper = (index + 1) / 10.0
    closing = "]" if index == 9 else ")"
    return f"[{lower:.1f},{upper:.1f}{closing}"


def risk_difference_bin(value: float) -> str:
    if value < -0.25:
        return "[-1.00,-0.25)"
    if value < -0.10:
        return "[-0.25,-0.10)"
    if value < -0.02:
        return "[-0.10,-0.02)"
    if value < 0.02:
        return "[-0.02,0.02)"
    if value < 0.10:
        return "[0.02,0.10)"
    if value < 0.25:
        return "[0.10,0.25)"
    return "[0.25,1.00]"


def pair_type_from_one_hot(values: np.ndarray) -> np.ndarray:
    if values.shape[1] != len(PAIR_TYPES):
        raise AssertionError("pair-type block has the wrong width")
    if not np.allclose(values.sum(axis=1), 1.0):
        raise AssertionError("pair-type block is not one-hot")
    return np.asarray([PAIR_TYPES[index] for index in values.argmax(axis=1)], dtype=object)


def verify_frozen_inputs() -> dict[str, str]:
    observed = {relative: sha256_file(ROOT / relative) for relative in FROZEN_HASHES}
    mismatches = {
        relative: {"expected": FROZEN_HASHES[relative], "observed": digest}
        for relative, digest in observed.items() if digest != FROZEN_HASHES[relative]
    }
    if mismatches:
        raise AssertionError(f"frozen R4 input hash mismatch: {mismatches}")
    return observed


def write_csv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    materialized = list(rows)
    if not materialized:
        raise ValueError(f"refusing empty output: {path}")
    fields: list[str] = []
    for row in materialized:
        for field in row:
            if field not in fields:
                fields.append(field)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(materialized)


def empty_counts() -> dict[str, int]:
    return {
        "events": 0, "tp": 0, "fp": 0,
        "ern_removed_fp": 0, "b4_removed_fp": 0,
        "ern_lost_tp": 0, "b4_lost_tp": 0,
        "ern_only_removed_fp": 0, "b4_only_removed_fp": 0,
        "ern_only_lost_tp": 0, "b4_only_lost_tp": 0,
    }


def add_counts(target: dict[str, int], label: int, ern_delete: bool, b4_delete: bool) -> None:
    target["events"] += 1
    if label == 1:
        target["fp"] += 1
        target["ern_removed_fp"] += int(ern_delete)
        target["b4_removed_fp"] += int(b4_delete)
        target["ern_only_removed_fp"] += int(ern_delete and not b4_delete)
        target["b4_only_removed_fp"] += int(b4_delete and not ern_delete)
    else:
        target["tp"] += 1
        target["ern_lost_tp"] += int(ern_delete)
        target["b4_lost_tp"] += int(b4_delete)
        target["ern_only_lost_tp"] += int(ern_delete and not b4_delete)
        target["b4_only_lost_tp"] += int(b4_delete and not ern_delete)


def safe_rate(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def format_breakdown(dimension: str, stratum: str, counts: dict[str, int]) -> dict[str, object]:
    ern_deleted = counts["ern_removed_fp"] + counts["ern_lost_tp"]
    b4_deleted = counts["b4_removed_fp"] + counts["b4_lost_tp"]
    return {
        "dimension": dimension,
        "stratum": stratum,
        "scope_filter": "ALL" if dimension in {
            "scope", "source_all_scopes", "channel_all_scopes", "source_channel_all_scopes"
        } else "NON_EVIDENCED_ONLY",
        "event_count_total_across_5_seeds": counts["events"],
        "mean_event_count_per_seed": counts["events"] / len(SEEDS),
        "mean_tp_opportunities_per_seed": counts["tp"] / len(SEEDS),
        "mean_fp_opportunities_per_seed": counts["fp"] / len(SEEDS),
        "mean_ern_removed_fp_per_seed": counts["ern_removed_fp"] / len(SEEDS),
        "mean_b4_removed_fp_per_seed": counts["b4_removed_fp"] / len(SEEDS),
        "mean_delta_removed_fp_per_seed":
            (counts["ern_removed_fp"] - counts["b4_removed_fp"]) / len(SEEDS),
        "mean_ern_lost_tp_per_seed": counts["ern_lost_tp"] / len(SEEDS),
        "mean_b4_lost_tp_per_seed": counts["b4_lost_tp"] / len(SEEDS),
        "mean_delta_lost_tp_per_seed":
            (counts["ern_lost_tp"] - counts["b4_lost_tp"]) / len(SEEDS),
        "mean_ern_only_removed_fp_per_seed": counts["ern_only_removed_fp"] / len(SEEDS),
        "mean_b4_only_removed_fp_per_seed": counts["b4_only_removed_fp"] / len(SEEDS),
        "mean_ern_only_lost_tp_per_seed": counts["ern_only_lost_tp"] / len(SEEDS),
        "mean_b4_only_lost_tp_per_seed": counts["b4_only_lost_tp"] / len(SEEDS),
        "ern_tp_preservation": 1.0 - safe_rate(counts["ern_lost_tp"], counts["tp"])
            if counts["tp"] else None,
        "b4_tp_preservation": 1.0 - safe_rate(counts["b4_lost_tp"], counts["tp"])
            if counts["tp"] else None,
        "ern_fp_removal": safe_rate(counts["ern_removed_fp"], counts["fp"]),
        "b4_fp_removal": safe_rate(counts["b4_removed_fp"], counts["fp"]),
        "ern_modification_precision": safe_rate(counts["ern_removed_fp"], ern_deleted),
        "b4_modification_precision": safe_rate(counts["b4_removed_fp"], b4_deleted),
    }


def load_candidate_categories() -> dict[str, np.ndarray]:
    columns = [
        "candidate_row_id", "pair_i", "pair_j", "candidate_03",
        "candidate_06", "candidate_07", "candidate_08", "candidate_78", "candidate_79",
    ] + [f"candidate_{index:02d}" for index in range(23, 41)]
    table = pq.read_table(R4 / "features/candidate_rows.parquet", columns=columns)
    data = table.to_pydict()
    ids = np.asarray(data["candidate_row_id"], dtype=np.int64)
    if not np.array_equal(ids, np.arange(310838, dtype=np.int64)):
        raise AssertionError("candidate_row_id must be contiguous and canonical")
    pair_block = np.column_stack([
        np.asarray(data[f"candidate_{index:02d}"], dtype=float) for index in range(23, 41)
    ])
    singleton = np.asarray(data["candidate_03"], dtype=float)
    normalized = np.asarray(data["candidate_06"], dtype=float)
    outer = np.asarray(data["candidate_07"], dtype=float)
    inner = np.asarray(data["candidate_08"], dtype=float)
    return {
        "sequence_separation": np.asarray([
            sequence_separation_bin(j - i) for i, j in zip(data["pair_i"], data["pair_j"])
        ], dtype=object),
        "stem_position": np.asarray([
            stem_position_bin(s, p) for s, p in zip(singleton, normalized)
        ], dtype=object),
        "boundary_status": np.asarray([
            boundary_status(s, o, i) for s, o, i in zip(singleton, outer, inner)
        ], dtype=object),
        "pair_type": pair_type_from_one_hot(pair_block),
        "p2_agreement": np.asarray([
            p2_agreement_bin(value) for value in data["candidate_78"]
        ], dtype=object),
        "p4_bpp_risk": np.asarray([
            p4_risk_bin(value) for value in data["candidate_79"]
        ], dtype=object),
    }


def score_path(condition: str, seed: int) -> Path:
    prefix = "ern" if condition == "ERN" else "b4_evidence_masked"
    return R4 / f"pair_scores/{prefix}_combined_seed_{seed}.parquet"


def main() -> None:
    input_hashes = verify_frozen_inputs()
    categories = load_candidate_categories()
    fixed_dimensions = (
        "source", "channel", "evidence_density", "sequence_separation",
        "stem_position", "boundary_status", "pair_type", "p2_agreement", "p4_bpp_risk",
    )
    breakdown: dict[tuple[str, str], dict[str, int]] = defaultdict(empty_counts)
    channel_rows: list[dict[str, object]] = []

    score_columns = [
        "candidate_row_id", "source", "channel", "density_percent", "label_delete",
        "scope", "test_fold", "calibrated_probability", "decision",
    ]
    for seed in SEEDS:
        ern = pq.read_table(score_path("ERN", seed), columns=score_columns).to_pydict()
        b4 = pq.read_table(
            score_path("B4_EVIDENCE_MASKED", seed),
            columns=["candidate_row_id", "calibrated_probability", "decision"],
        ).to_pydict()
        ern_ids = np.asarray(ern["candidate_row_id"], dtype=np.int64)
        b4_ids = np.asarray(b4["candidate_row_id"], dtype=np.int64)
        if (not np.array_equal(ern_ids, b4_ids) or len(np.unique(ern_ids)) != 310838
                or int(ern_ids.min()) != 0 or int(ern_ids.max()) != 310837):
            raise AssertionError(f"ERN/B4 row mismatch for seed {seed}")
        labels = np.asarray(ern["label_delete"], dtype=np.int8)
        scopes = np.asarray(ern["scope"], dtype=object)
        ern_delete = np.asarray(ern["decision"], dtype=object) == "DELETE"
        b4_delete = np.asarray(b4["decision"], dtype=object) == "DELETE"
        ern_probability = np.asarray(ern["calibrated_probability"], dtype=float)
        b4_probability = np.asarray(b4["calibrated_probability"], dtype=float)
        source = np.asarray(ern["source"], dtype=object)
        channel = np.asarray(ern["channel"], dtype=object)
        density = np.asarray([f"{value}%" for value in ern["density_percent"]], dtype=object)
        fold = np.asarray(ern["test_fold"], dtype=int)
        dynamic = {
            "source": source,
            "channel": channel,
            "evidence_density": density,
            **{name: values[ern_ids] for name, values in categories.items()},
            "calibrated_ern_risk": np.asarray([
                calibrated_risk_bin(value) for value in ern_probability
            ], dtype=object),
            "ern_minus_b4_risk": np.asarray([
                risk_difference_bin(value) for value in ern_probability - b4_probability
            ], dtype=object),
        }

        for index in range(len(labels)):
            scope = str(scopes[index])
            if scope not in SCOPES:
                raise AssertionError(f"unexpected scope: {scope}")
            add_counts(breakdown[("scope", scope)], int(labels[index]),
                       bool(ern_delete[index]), bool(b4_delete[index]))
            add_counts(breakdown[("source_all_scopes", str(source[index]))],
                       int(labels[index]), bool(ern_delete[index]), bool(b4_delete[index]))
            add_counts(breakdown[("channel_all_scopes", str(channel[index]))],
                       int(labels[index]), bool(ern_delete[index]), bool(b4_delete[index]))
            add_counts(breakdown[("source_channel_all_scopes",
                                  f"{source[index]}|{channel[index]}")],
                       int(labels[index]), bool(ern_delete[index]), bool(b4_delete[index]))
            if scope == "NON_EVIDENCED":
                for dimension in fixed_dimensions + ("calibrated_ern_risk", "ern_minus_b4_risk"):
                    add_counts(breakdown[(dimension, str(dynamic[dimension][index]))],
                               int(labels[index]), bool(ern_delete[index]), bool(b4_delete[index]))

        for aggregation, seed_values, fold_values in (
            ("SEED_ALL_FOLDS", (seed,), (None,)),
            ("SEED_FOLD", (seed,), tuple(range(5))),
        ):
            for seed_value in seed_values:
                for fold_value in fold_values:
                    for channel_value in CHANNELS:
                        mask = channel == channel_value
                        if fold_value is not None:
                            mask &= fold == fold_value
                        tp = int(np.sum(mask & (labels == 0)))
                        lost = int(np.sum(mask & (labels == 0) & ern_delete))
                        channel_rows.append({
                            "aggregation": aggregation, "seed": seed_value,
                            "test_fold": "ALL" if fold_value is None else fold_value,
                            "channel": channel_value, "tp_opportunities": tp,
                            "lost_tp": lost, "tp_preservation": 1.0 - lost / tp,
                        })

    # Fold summaries pool the five fixed model seeds; they are descriptive, not biological replicates.
    for fold_value in range(5):
        for channel_value in CHANNELS:
            selected = [row for row in channel_rows if row["aggregation"] == "SEED_FOLD"
                        and row["test_fold"] == fold_value and row["channel"] == channel_value]
            tp = sum(int(row["tp_opportunities"]) for row in selected)
            lost = sum(int(row["lost_tp"]) for row in selected)
            channel_rows.append({
                "aggregation": "FOLD_ALL_SEEDS", "seed": "ALL", "test_fold": fold_value,
                "channel": channel_value, "tp_opportunities": tp, "lost_tp": lost,
                "tp_preservation": 1.0 - lost / tp,
            })

    breakdown_rows = [
        format_breakdown(dimension, stratum, counts)
        for (dimension, stratum), counts in sorted(breakdown.items())
    ]
    write_csv(OUT / "diagnostic_breakdowns.csv", breakdown_rows)
    write_csv(OUT / "channel_preservation_stability.csv", channel_rows)

    scope_rows = {row["stratum"]: row for row in breakdown_rows if row["dimension"] == "scope"}
    total_delta_fp = sum(float(scope_rows[scope]["mean_delta_removed_fp_per_seed"])
                         for scope in SCOPES)
    total_delta_lost_tp = sum(float(scope_rows[scope]["mean_delta_lost_tp_per_seed"])
                              for scope in SCOPES)
    seed_signs = []
    for seed in SEEDS:
        records = {row["channel"]: row for row in channel_rows
                   if row["aggregation"] == "SEED_ALL_FOLDS" and row["seed"] == seed}
        seed_signs.append(records["positive_pair"]["tp_preservation"] >
                          records["unpaired"]["tp_preservation"])
    fold_signs = []
    for fold_value in range(5):
        records = {row["channel"]: row for row in channel_rows
                   if row["aggregation"] == "FOLD_ALL_SEEDS" and row["test_fold"] == fold_value}
        fold_signs.append(records["positive_pair"]["tp_preservation"] >
                          records["unpaired"]["tp_preservation"])
    fold_seed_rows = [row for row in channel_rows if row["aggregation"] == "SEED_FOLD"]
    fold_seed_positive_wins = 0
    for seed in SEEDS:
        for fold_value in range(5):
            records = {row["channel"]: row for row in fold_seed_rows
                       if row["seed"] == seed and row["test_fold"] == fold_value}
            fold_seed_positive_wins += int(records["positive_pair"]["tp_preservation"] >
                                            records["unpaired"]["tp_preservation"])

    total_tp_events = 260623
    observed_preservation = 0.9896824148290827
    requirement = 0.99
    summary = {
        "schema_version": "r4_postmortem_diagnostic_v1",
        "status": "POSTHOC_DIAGNOSTIC_COMPLETE",
        "frozen_gate_b_decision_unchanged": "R4_GATE_B_FAIL",
        "analysis_role": "DESCRIPTIVE_HYPOTHESIS_GENERATION_ONLY",
        "frozen_input_hashes": input_hashes,
        "gate_b_miss": {
            "observed_event_tp_preservation": observed_preservation,
            "frozen_requirement": requirement,
            "preservation_gap": requirement - observed_preservation,
            "total_tp_opportunity_events_per_seed": total_tp_events,
            "observed_mean_lost_tp_events_per_seed": 2689.0,
            "maximum_integer_lost_tp_events_for_0_99": math.floor(total_tp_events * 0.01),
            "excess_mean_lost_tp_event_scale":
                (requirement - observed_preservation) * total_tp_events,
            "threshold_rescue_permitted": False,
        },
        "ern_vs_b4_attribution_mean_per_seed": {
            "net_additional_removed_fp": total_delta_fp,
            "net_additional_lost_tp": total_delta_lost_tp,
            "local_conflict_additional_removed_fp":
                scope_rows["LOCAL_CONFLICT"]["mean_delta_removed_fp_per_seed"],
            "non_evidenced_additional_removed_fp":
                scope_rows["NON_EVIDENCED"]["mean_delta_removed_fp_per_seed"],
            "non_evidenced_additional_lost_tp":
                scope_rows["NON_EVIDENCED"]["mean_delta_lost_tp_per_seed"],
            "direct_change_in_lost_tp": scope_rows["DIRECT"]["mean_delta_lost_tp_per_seed"],
            "fraction_of_net_additional_fp_removal_from_local_conflict":
                scope_rows["LOCAL_CONFLICT"]["mean_delta_removed_fp_per_seed"] / total_delta_fp,
            "fraction_of_net_additional_fp_removal_from_non_evidenced":
                scope_rows["NON_EVIDENCED"]["mean_delta_removed_fp_per_seed"] / total_delta_fp,
        },
        "channel_stability": {
            "positive_pair_higher_preservation_seed_summaries": sum(seed_signs),
            "seed_summary_comparisons": len(seed_signs),
            "positive_pair_higher_preservation_fold_summaries": sum(fold_signs),
            "fold_summary_comparisons": len(fold_signs),
            "positive_pair_higher_preservation_fold_seed_cells": fold_seed_positive_wins,
            "fold_seed_comparisons": 25,
        },
        "scientific_firewall": {
            "new_model_trained": False,
            "ern_or_b4_retrained": False,
            "threshold_changed": False,
            "seed_or_channel_selected": False,
            "model_feature_added": False,
            "external77_accessed": False,
            "r5_started": False,
            "noisy_or_real_evidence_accessed": False,
            "historical_e2_executed": False,
        },
        "outputs": {
            "diagnostic_breakdowns": "results/clean_learned_evidence_reconciliation_r4/postmortem/diagnostic_breakdowns.csv",
            "channel_stability": "results/clean_learned_evidence_reconciliation_r4/postmortem/channel_preservation_stability.csv",
        },
    }
    write_json(OUT / "diagnostic_summary.json", summary)
    print(json.dumps({
        "status": summary["status"],
        "gate_b": summary["frozen_gate_b_decision_unchanged"],
        "gate_gap": summary["gate_b_miss"]["preservation_gap"],
        "net_additional_removed_fp": total_delta_fp,
        "net_additional_lost_tp": total_delta_lost_tp,
        "local_fraction": summary["ern_vs_b4_attribution_mean_per_seed"]
            ["fraction_of_net_additional_fp_removal_from_local_conflict"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
