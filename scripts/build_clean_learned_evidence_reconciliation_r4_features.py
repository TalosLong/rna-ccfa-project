#!/usr/bin/env python3
"""Build the frozen R4 feature artifacts without regenerating evidence."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rna_ccfa.evidence_reconciliation import (  # noqa: E402
    CANDIDATE_78_NAMES,
    CANDIDATE_FEATURE_NAMES,
    CHANNEL_TO_MANIFEST,
    DESCRIPTOR_NAMES,
    FROZEN_CLEAN_MANIFEST_SHA256,
    FROZEN_SPLIT_SHA256,
    ITEM_DIM,
    MANIFEST_TO_CHANNEL,
    MODEL_INPUT_COLUMNS,
    PAIR_ITEM_FEATURE_NAMES,
    R4_PROTOCOL_SHA256,
    SOURCES,
    UNPAIRED_ITEM_FEATURE_NAMES,
    append_frozen_reliability_signals,
    candidate_features_from_prediction,
    canonical_json_sha256,
    evidence_features_for_candidate,
    guard_r4_path,
    sha256_file,
    write_json,
)


RESULTS = ROOT / "results/clean_learned_evidence_reconciliation_r4"
FEATURES = RESULTS / "features"
INTEGRITY = RESULTS / "integrity"
INPUTS = {
    "protocol": ROOT / "docs/clean_learned_evidence_reconciliation_r4_protocol.md",
    "split": ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv",
    "normalized": ROOT / "normalized/legacy121_v1/predictions.jsonl",
    "clean_manifests": ROOT / "results/evidence_guidance/e0/clean_manifests.jsonl",
    "eligibility": ROOT / "results/global_constrained_refolding_r2/integrity/r2_manifest_eligibility_v1_0_2.csv",
    "p2": ROOT / "results/reliability_baseline_r3/pair_scores/track_p_p2.csv.gz",
    "p4": ROOT / "results/reliability_baseline_r3/pair_scores/track_p_p4.csv.gz",
    "e1": ROOT / "results/reliability_baseline_r3/pair_scores/track_e_e1.csv.gz",
}


class StreamingParquet:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.writer: pq.ParquetWriter | None = None
        self.rows = 0

    def append(self, rows: list[dict[str, object]]) -> None:
        if not rows:
            return
        table = pa.Table.from_pylist(rows)
        if self.writer is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.writer = pq.ParquetWriter(
                self.path, table.schema, compression="zstd", use_dictionary=True
            )
        self.writer.write_table(table)
        self.rows += len(rows)
        rows.clear()

    def close(self) -> None:
        if self.writer is None:
            raise AssertionError(f"no rows written: {self.path}")
        self.writer.close()


def load_signal(path: Path, value_field: str) -> dict[tuple[str, str, int, int], tuple[float, int]]:
    output: dict[tuple[str, str, int, int], tuple[float, int]] = {}
    guard_r4_path(path)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["rna_id"], row["source"], int(row["pair_i"]), int(row["pair_j"]))
            value = (float(row[value_field]), int(row["label_delete"]))
            if key in output and output[key] != value:
                raise AssertionError(f"inconsistent duplicate frozen signal: {key}")
            output[key] = value
    if len(output) != 5290:
        raise AssertionError(f"frozen signal must cover 5,290 pairs: {len(output)}")
    return output


def load_e1() -> dict[tuple[str, str, int, int], tuple[int, int, int, str]]:
    output: dict[tuple[str, str, int, int], tuple[int, int, int, str]] = {}
    path = INPUTS["e1"]
    guard_r4_path(path)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["manifest_id"], row["source"], int(row["pair_i"]), int(row["pair_j"]))
            if key in output:
                raise AssertionError(f"duplicate E1 row: {key}")
            output[key] = (
                int(float(row["risk"])), int(row["label_delete"]),
                int(row["gt_pair_count"]), row["manifest_payload_sha256"],
            )
    if len(output) != 310838:
        raise AssertionError(f"E1 universe mismatch: {len(output)}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    preflight = json.loads((INTEGRITY / "preflight.json").read_text())
    if preflight["status"] != "PASS" or not preflight["scientific_execution_authorized"]:
        raise SystemExit("R4 preflight is not PASS")
    for path in INPUTS.values():
        guard_r4_path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
    if sha256_file(INPUTS["protocol"]) != R4_PROTOCOL_SHA256:
        raise SystemExit("frozen R4 protocol hash mismatch")
    if sha256_file(INPUTS["split"]) != FROZEN_SPLIT_SHA256:
        raise SystemExit("frozen grouped split hash mismatch")
    if sha256_file(INPUTS["clean_manifests"]) != FROZEN_CLEAN_MANIFEST_SHA256:
        raise SystemExit("clean evidence manifest hash mismatch")

    with INPUTS["split"].open(newline="", encoding="utf-8") as handle:
        fold_rows = list(csv.DictReader(handle))
    fold_by_rna = {row["rna_id"]: int(row["fold"]) for row in fold_rows}
    if len(fold_rows) != 121 or len(fold_by_rna) != 121:
        raise AssertionError("grouped split must contain 121 unique RNAs")
    if Counter(fold_by_rna.values()) != Counter({0: 25, 1: 24, 2: 24, 3: 24, 4: 24}):
        raise AssertionError("grouped split fold counts mismatch")
    if any(int(row["source_records_per_rna"]) != 3 for row in fold_rows):
        raise AssertionError("source records were not grouped by RNA")

    guard_r4_path(INPUTS["normalized"])
    records = [json.loads(line) for line in INPUTS["normalized"].read_text().splitlines() if line.strip()]
    if len(records) != 363:
        raise AssertionError("Legacy121 source-record count mismatch")
    records_by_key = {(row["rna_id"], row["source_model"]["name"]): row for row in records}
    if len(records_by_key) != 363 or {key[0] for key in records_by_key} != set(fold_by_rna):
        raise AssertionError("Legacy121 record identity mismatch")
    for rna_id in fold_by_rna:
        if {source for candidate, source in records_by_key if candidate == rna_id} != set(SOURCES):
            raise AssertionError(f"source record matrix incomplete: {rna_id}")

    with INPUTS["eligibility"].open(newline="", encoding="utf-8") as handle:
        eligibility_rows = list(csv.DictReader(handle))
    eligible_rows = [row for row in eligibility_rows if row["eligibility_status"] == "R2_ELIGIBLE"]
    eligible_counts = Counter(row["channel"] for row in eligible_rows)
    if eligible_counts != Counter({"POSITIVE_PAIR_EVIDENCE": 3523, "UNPAIRED_NUCLEOTIDE_EVIDENCE": 3630}):
        raise AssertionError(f"R2 v1.0.2 universe mismatch: {eligible_counts}")

    eligible_ids = {row["manifest_id"] for row in eligible_rows}
    manifests: dict[str, dict[str, object]] = {}
    guard_r4_path(INPUTS["clean_manifests"])
    with INPUTS["clean_manifests"].open(encoding="utf-8") as handle:
        for line in handle:
            manifest = json.loads(line)
            if manifest["manifest_id"] not in eligible_ids:
                continue
            if int(manifest["noise_level_percent"]) != 0:
                raise AssertionError("R4 accepts clean evidence only")
            if manifest["manifest_id"] in manifests:
                raise AssertionError("duplicate clean manifest")
            manifests[manifest["manifest_id"]] = manifest
    if set(manifests) != eligible_ids:
        raise AssertionError("eligible clean manifests are incomplete")

    p2 = load_signal(INPUTS["p2"], "support_other_count")
    p4 = load_signal(INPUTS["p4"], "rnafold_bpp")
    e1 = load_e1()
    if args.dry_run:
        print(json.dumps({
            "status": "PASS", "eligible_manifests": len(eligible_rows),
            "source_records": len(records), "p2_pairs": len(p2), "p4_pairs": len(p4),
            "e1_rows": len(e1), "feature_artifacts_written": False,
        }, indent=2, sort_keys=True))
        return

    FEATURES.mkdir(parents=True, exist_ok=True)
    candidate_path = FEATURES / "candidate_rows.parquet"
    pair_item_path = FEATURES / "positive_pair_items.parquet"
    unpaired_item_path = FEATURES / "unpaired_nucleotide_items.parquet"
    for path in (candidate_path, pair_item_path, unpaired_item_path):
        if path.exists():
            raise SystemExit(f"refusing to overwrite feature artifact: {path}")

    candidate_writer = StreamingParquet(candidate_path)
    item_writers = {
        "positive_pair": StreamingParquet(pair_item_path),
        "unpaired": StreamingParquet(unpaired_item_path),
    }
    candidate_buffer: list[dict[str, object]] = []
    item_buffers: dict[str, list[dict[str, object]]] = {channel: [] for channel in CHANNEL_TO_MANIFEST}
    candidate_cache: dict[tuple[str, str], dict[tuple[int, int], np.ndarray]] = {}
    sequence_hashes: dict[str, str] = {}
    prediction_hashes: dict[tuple[str, str], str] = {}
    channel_candidate_counts: Counter[str] = Counter()
    channel_item_counts: Counter[str] = Counter()
    source_record_keys: set[tuple[str, str]] = set()
    seen_e1: set[tuple[str, str, int, int]] = set()
    scope_counts: Counter[tuple[str, str]] = Counter()
    row_id = 0

    for eligibility in eligible_rows:
        manifest_id = eligibility["manifest_id"]
        manifest = manifests[manifest_id]
        if manifest["manifest_payload_sha256"] != eligibility["manifest_payload_sha256"]:
            raise AssertionError(f"manifest payload hash join mismatch: {manifest_id}")
        rna_id = str(manifest["rna_id"])
        channel = MANIFEST_TO_CHANNEL[str(manifest["evidence_channel"])]
        sequence_length = int(manifest["sequence_length"])
        delivered_items = [dict(item["delivered_evidence_item"]) for item in manifest["items"]]
        if len(delivered_items) != int(manifest["delivered_item_count"]):
            raise AssertionError("delivered item count mismatch")
        for source in SOURCES:
            record = records_by_key[(rna_id, source)]
            sequence = str(record["sequence"])
            if len(sequence) != sequence_length:
                raise AssertionError("sequence length mismatch")
            source_record_keys.add((rna_id, source))
            cache_key = (rna_id, source)
            if cache_key not in candidate_cache:
                candidate_cache[cache_key] = candidate_features_from_prediction(
                    rna_id, sequence, record["predicted_structure"]["pairs"], source
                )
                sequence_hashes[rna_id] = hashlib.sha256(sequence.encode()).hexdigest()
                prediction_hashes[cache_key] = canonical_json_sha256(
                    sorted(tuple(map(int, pair)) for pair in record["predicted_structure"]["pairs"])
                )
            gt_pairs = {tuple(map(int, pair)) for pair in record["ground_truth_structure"]["pairs"]}
            gt_pair_count = len(gt_pairs)
            for pair in sorted(candidate_cache[cache_key]):
                signal_key = (rna_id, source, pair[0], pair[1])
                p2_value, p2_label = p2[signal_key]
                p4_value, p4_label = p4[signal_key]
                label = int(pair not in gt_pairs)
                if p2_label != label or p4_label != label:
                    raise AssertionError(f"R3 label join mismatch: {signal_key}")
                candidate = append_frozen_reliability_signals(
                    candidate_cache[cache_key][pair], int(p2_value), float(p4_value)
                )
                item_matrix, descriptors, scope = evidence_features_for_candidate(
                    channel, pair, delivered_items, sequence_length
                )
                e1_key = (manifest_id, source, pair[0], pair[1])
                e1_risk, e1_label, e1_gt_count, e1_payload = e1[e1_key]
                if e1_label != label or e1_gt_count != gt_pair_count or e1_payload != manifest["manifest_payload_sha256"]:
                    raise AssertionError(f"E1 metadata join mismatch: {e1_key}")
                if e1_risk != int(descriptors[2]):
                    raise AssertionError(f"E1 LOCAL_CONFLICT mismatch: {e1_key}")
                seen_e1.add(e1_key)

                output: dict[str, object] = {
                    "candidate_row_id": row_id,
                    "manifest_id": manifest_id,
                    "manifest_payload_sha256": manifest["manifest_payload_sha256"],
                    "rna_id": rna_id,
                    "source": source,
                    "rna_fold": int(fold_by_rna[rna_id]),
                    "channel": channel,
                    "density_percent": int(manifest["density_percent"]),
                    "evidence_seed": int(manifest["evidence_seed"]),
                    "pair_i": pair[0],
                    "pair_j": pair[1],
                    "sequence_length": sequence_length,
                    "sequence_sha256": sequence_hashes[rna_id],
                    "original_prediction_sha256": prediction_hashes[cache_key],
                    "original_pair_member": True,
                    "gt_pair_count": gt_pair_count,
                    "label_delete": label,
                    "original_pair_status": "FP" if label else "TP",
                    "scope": scope,
                    "item_count": len(delivered_items),
                }
                output.update({name: float(candidate[index]) for index, name in enumerate(MODEL_INPUT_COLUMNS)})
                output.update({f"evidence_descriptor_{index:02d}": float(descriptors[index]) for index in range(4)})
                candidate_buffer.append(output)
                channel_candidate_counts[channel] += 1
                scope_counts[(channel, scope)] += 1

                feature_names = PAIR_ITEM_FEATURE_NAMES if channel == "positive_pair" else UNPAIRED_ITEM_FEATURE_NAMES
                for item_index, item_features in enumerate(item_matrix):
                    item_output: dict[str, object] = {
                        "candidate_row_id": row_id,
                        "rna_fold": int(fold_by_rna[rna_id]),
                        "item_index": item_index,
                    }
                    item_output.update({name: float(item_features[index]) for index, name in enumerate(feature_names)})
                    item_buffers[channel].append(item_output)
                    channel_item_counts[channel] += 1
                row_id += 1

                if len(candidate_buffer) >= 5000:
                    candidate_writer.append(candidate_buffer)
                if len(item_buffers[channel]) >= 10000:
                    item_writers[channel].append(item_buffers[channel])

    candidate_writer.append(candidate_buffer)
    for channel in item_writers:
        item_writers[channel].append(item_buffers[channel])
    candidate_writer.close()
    for writer in item_writers.values():
        writer.close()

    if row_id != 310838 or candidate_writer.rows != 310838:
        raise AssertionError(f"R4 candidate universe mismatch: {row_id}")
    if seen_e1 != set(e1):
        raise AssertionError("R4 did not consume the exact frozen E1 row universe")
    if len(source_record_keys) != 363 or len({rna for rna, _ in source_record_keys}) != 121:
        raise AssertionError("R4 source-record universe mismatch")

    artifact_hashes = {
        str(path.relative_to(ROOT)): sha256_file(path)
        for path in (candidate_path, pair_item_path, unpaired_item_path)
    }
    feature_contract = {
        "schema_version": "clean_learned_evidence_reconciliation_r4_features_v1",
        "status": "FROZEN_FEATURES_BUILT",
        "protocol_sha256": R4_PROTOCOL_SHA256,
        "source_agnostic": True,
        "candidate_feature_names": list(CANDIDATE_FEATURE_NAMES),
        "candidate_dimension": 80,
        "historical_candidate_dimension": len(CANDIDATE_78_NAMES),
        "positive_pair_item_feature_names": list(PAIR_ITEM_FEATURE_NAMES),
        "positive_pair_item_dimension": ITEM_DIM["positive_pair"],
        "unpaired_item_feature_names": list(UNPAIRED_ITEM_FEATURE_NAMES),
        "unpaired_item_dimension": ITEM_DIM["unpaired"],
        "evidence_descriptor_names": list(DESCRIPTOR_NAMES),
        "evidence_descriptor_dimension": 4,
        "model_candidate_columns": list(MODEL_INPUT_COLUMNS),
        "model_descriptor_columns": [f"evidence_descriptor_{index:02d}" for index in range(4)],
        "label_and_evaluation_metadata_separate_from_model_tensor": True,
        "predictor_identity_model_input": False,
        "gt_derived_inference_feature": False,
        "b2_disagreement_model_input": False,
        "nominal_density_model_input": False,
        "evidence_seed_model_input": False,
        "original_clean_item_model_input": False,
        "empty_evidence_block": "68_EXACT_ZEROS_AFTER_PREPROCESSING",
        "artifact_hashes": artifact_hashes,
    }
    feature_contract["feature_contract_sha256"] = canonical_json_sha256(feature_contract)
    write_json(FEATURES / "feature_contract.json", feature_contract)

    write_json(INTEGRITY / "split_leakage_audit.json", {
        "schema_version": "r4_split_leakage_audit_v1", "status": "PASS",
        "biological_unit": "RNA", "rna_count": 121, "source_record_count": 363,
        "fold_counts": dict(sorted(Counter(fold_by_rna.values()).items())),
        "source_records_grouped_with_rna": True, "identity_components_crossing_folds": 0,
        "grouped_split_sha256": sha256_file(INPUTS["split"]),
    })
    write_json(INTEGRITY / "feature_firewall_audit.json", {
        "schema_version": "r4_feature_firewall_audit_v1", "status": "PASS",
        "candidate_model_columns": list(MODEL_INPUT_COLUMNS),
        "descriptor_model_columns": [f"evidence_descriptor_{index:02d}" for index in range(4)],
        "candidate_dimension": 80, "descriptor_dimension": 4,
        "source_identity_excluded": True, "labels_excluded_from_model_tensor": True,
        "gt_inference_features_excluded": True, "b2_disagreement_excluded": True,
        "manifest_metadata_excluded": True, "feature_allowlist_exact": True,
    })
    completion = {
        "schema_version": "r4_feature_build_completion_v1", "status": "PASS",
        "rna_count": 121, "source_record_count": 363,
        "positive_pair_manifests": 3523, "unpaired_manifests": 3630,
        "eligible_manifests": 7153, "candidate_rows": row_id,
        "candidate_rows_by_channel": dict(channel_candidate_counts),
        "item_incidences_by_channel": dict(channel_item_counts),
        "scope_counts": {f"{channel}:{scope}": count for (channel, scope), count in sorted(scope_counts.items())},
        "evidence_regenerated": False, "external77_data_accessed": False,
        "noisy_or_real_evidence_accessed": False, "historical_e2_runner_executed": False,
        "artifact_hashes": {**artifact_hashes, str((FEATURES / "feature_contract.json").relative_to(ROOT)): sha256_file(FEATURES / "feature_contract.json")},
    }
    write_json(INTEGRITY / "feature_build_completion.json", completion)
    print(json.dumps(completion, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
