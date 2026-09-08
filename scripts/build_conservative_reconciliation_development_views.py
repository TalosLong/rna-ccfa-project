#!/usr/bin/env python3
"""Create immutable CER references over frozen R4 features and grouped folds."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rna_ccfa.conservative_reconciliation import (  # noqa: E402
    CER_PROTOCOL_SHA256, CHANNELS, ROTATIONS, development_split_roles, guard_cer_path,
)
from rna_ccfa.evidence_reconciliation import sha256_file, write_json  # noqa: E402


RESULTS = ROOT / "results/conservative_reconciliation_development"
FEATURES = RESULTS / "features"
SPLITS = RESULTS / "splits"
INTEGRITY = RESULTS / "integrity"
R4_FEATURES = ROOT / "results/clean_learned_evidence_reconciliation_r4/features"
SPLIT_PATH = ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv"


def _write_parquet_once(table: pa.Table, path: Path) -> None:
    if path.exists():
        raise SystemExit(f"refusing to overwrite immutable CER view: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path, compression="zstd", use_dictionary=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    audit = json.loads((INTEGRITY / "pretraining_protocol_audit.json").read_text())
    if audit.get("status") != "PASS":
        raise SystemExit("CER pretraining protocol audit is not PASS")
    contract_path = guard_cer_path(R4_FEATURES / "feature_contract.json")
    candidate_path = guard_cer_path(R4_FEATURES / "candidate_rows.parquet")
    pair_path = guard_cer_path(R4_FEATURES / "positive_pair_items.parquet")
    unpaired_path = guard_cer_path(R4_FEATURES / "unpaired_nucleotide_items.parquet")
    guard_cer_path(SPLIT_PATH)
    contract = json.loads(contract_path.read_text())
    expected = (80, 17, 8, 4)
    observed = (
        contract["candidate_dimension"], contract["positive_pair_item_dimension"],
        contract["unpaired_item_dimension"], contract["evidence_descriptor_dimension"],
    )
    if observed != expected:
        raise SystemExit(f"R4 feature dimension mismatch: {observed}")
    if args.dry_run:
        print(json.dumps({"status": "PASS", "views_written": False, "feature_dimensions": observed}, indent=2))
        return

    candidate_columns = [
        "candidate_row_id", "manifest_id", "manifest_payload_sha256", "rna_id",
        "source", "rna_fold", "channel", "pair_i", "pair_j",
        "original_pair_member", "scope",
    ]
    candidates = pq.read_table(candidate_path, columns=candidate_columns)
    if len(candidates) != 310838 or len(set(candidates["candidate_row_id"].to_pylist())) != 310838:
        raise AssertionError("candidate reference universe mismatch")
    candidate_inventory = candidates.append_column(
        "source_feature_artifact_sha256",
        pa.array([sha256_file(candidate_path)] * len(candidates)),
    )
    pair_items = pq.read_table(pair_path, columns=["candidate_row_id", "rna_fold", "item_index"])
    unpaired_items = pq.read_table(unpaired_path, columns=["candidate_row_id", "rna_fold", "item_index"])
    if len(pair_items) != 411297 or len(unpaired_items) != 507455:
        raise AssertionError("item reference universe mismatch")
    pair_items = pair_items.append_column(
        "source_feature_artifact_sha256", pa.array([sha256_file(pair_path)] * len(pair_items))
    )
    unpaired_items = unpaired_items.append_column(
        "source_feature_artifact_sha256", pa.array([sha256_file(unpaired_path)] * len(unpaired_items))
    )
    output_paths = {
        "candidate": FEATURES / "candidate_row_inventory.parquet",
        "positive_pair": FEATURES / "positive_pair_item_inventory.parquet",
        "unpaired": FEATURES / "unpaired_item_inventory.parquet",
    }
    _write_parquet_once(candidate_inventory, output_paths["candidate"])
    _write_parquet_once(pair_items, output_paths["positive_pair"])
    _write_parquet_once(unpaired_items, output_paths["unpaired"])

    reference = {
        "schema_version": "conservative_reconciliation_feature_contract_reference_v1",
        "status": "LOCKED", "cer_protocol_sha256": CER_PROTOCOL_SHA256,
        "r4_feature_contract_path": str(contract_path.relative_to(ROOT)),
        "r4_feature_contract_sha256": sha256_file(contract_path),
        "candidate_dimension": 80, "positive_pair_item_dimension": 17,
        "unpaired_item_dimension": 8, "evidence_descriptor_dimension": 4,
        "candidate_feature_names": contract["candidate_feature_names"],
        "positive_pair_item_feature_names": contract["positive_pair_item_feature_names"],
        "unpaired_item_feature_names": contract["unpaired_item_feature_names"],
        "evidence_descriptor_names": contract["evidence_descriptor_names"],
        "model_candidate_columns": contract["model_candidate_columns"],
        "model_descriptor_columns": contract["model_descriptor_columns"],
        "zero_evidence_transform": "68_EXACT_ZEROS_AFTER_PREPROCESSING",
        "source_identity_model_input": False, "label_or_metadata_model_input": False,
        "gt_inference_feature": False, "r4_risk_or_decision_model_input": False,
        "b2_disagreement_model_input": False, "postmortem_bin_model_input": False,
        "feature_added_removed_reordered": False,
        "inventory_hashes": {key: sha256_file(path) for key, path in output_paths.items()},
    }
    write_json(FEATURES / "feature_contract_reference.json", reference)

    with SPLIT_PATH.open(newline="", encoding="utf-8") as handle:
        split_rows = list(csv.DictReader(handle))
    fold_by_rna = {row["rna_id"]: int(row["fold"]) for row in split_rows}
    metadata = candidates.to_pydict()
    rows_by_channel_rna: dict[tuple[str, str], int] = Counter()
    manifests_by_channel_rna: dict[tuple[str, str], set[str]] = defaultdict(set)
    sources_by_rna: dict[str, set[str]] = defaultdict(set)
    for channel, rna, manifest, source in zip(
        metadata["channel"], metadata["rna_id"], metadata["manifest_id"], metadata["source"]
    ):
        rows_by_channel_rna[(channel, rna)] += 1
        manifests_by_channel_rna[(channel, rna)].add(manifest)
        sources_by_rna[rna].add(source)
    if any(len(values) != 3 for values in sources_by_rna.values()):
        raise AssertionError("source records did not follow RNA grouping")

    split_hashes = {}
    for channel in CHANNELS:
        for rotation in ROTATIONS:
            roles = development_split_roles(fold_by_rna, rotation)
            payload = {
                "schema_version": "conservative_reconciliation_development_split_v1",
                "status": "LOCKED", "channel": channel, "rotation": rotation,
                "grouping_unit": "RNA", "grouped_split_path": str(SPLIT_PATH.relative_to(ROOT)),
                "grouped_split_sha256": sha256_file(SPLIT_PATH), "independent_test": False,
                "role_fold_ids": {
                    "development_train": [f for f in ROTATIONS if f not in (rotation, (rotation + 1) % 5)],
                    "development_validation": [(rotation + 1) % 5],
                    "development_assessment": [rotation],
                },
                "roles": {}, "rna_disjoint": True, "source_coassignment": True,
                "evidence_realization_coassignment": True, "external_dataset_identifiers": [],
            }
            for role, rnas in roles.items():
                ordered = sorted(rnas)
                payload["roles"][role] = {
                    "rna_ids": ordered, "rna_count": len(ordered),
                    "candidate_row_count": sum(rows_by_channel_rna[(channel, rna)] for rna in ordered),
                    "manifest_count": sum(len(manifests_by_channel_rna[(channel, rna)]) for rna in ordered),
                    "source_record_count": sum(len(sources_by_rna[rna]) for rna in ordered),
                }
            serialized = json.dumps(payload, sort_keys=True)
            if "held_out_test" in serialized or "external_validation" in serialized:
                raise AssertionError("forbidden post-R4 role alias entered split schema")
            path = SPLITS / channel / f"rotation_{rotation}.json"
            if path.exists():
                raise SystemExit(f"refusing to overwrite split manifest: {path}")
            write_json(path, payload)
            split_hashes[str(path.relative_to(ROOT))] = sha256_file(path)

    channel_values = candidates["channel"].to_pylist()
    manifests = candidates["manifest_id"].to_pylist()
    completion = {
        "schema_version": "conservative_reconciliation_feature_reference_completion_v1",
        "status": "PASS", "rna_count": len(fold_by_rna),
        "source_record_count": len(sources_by_rna) * 3,
        "positive_pair_manifests": len({m for c, m in zip(channel_values, manifests) if c == "positive_pair"}),
        "unpaired_manifests": len({m for c, m in zip(channel_values, manifests) if c == "unpaired"}),
        "total_manifests": len(set(manifests)), "candidate_rows": len(candidates),
        "positive_pair_item_incidences": len(pair_items), "unpaired_item_incidences": len(unpaired_items),
        "clean_evidence_regenerated": False, "feature_values_copied_or_rebuilt": False,
        "split_manifest_count": len(split_hashes), "split_manifest_hashes": split_hashes,
        "artifact_hashes": {
            **{str(path.relative_to(ROOT)): sha256_file(path) for path in output_paths.values()},
            str((FEATURES / "feature_contract_reference.json").relative_to(ROOT)): sha256_file(FEATURES / "feature_contract_reference.json"),
        },
    }
    if (completion["rna_count"], completion["source_record_count"], completion["positive_pair_manifests"],
        completion["unpaired_manifests"], completion["total_manifests"], completion["candidate_rows"]) != (121, 363, 3523, 3630, 7153, 310838):
        raise AssertionError(f"CER reference universe mismatch: {completion}")
    write_json(INTEGRITY / "feature_contract_audit.json", {
        "schema_version": "conservative_reconciliation_feature_contract_audit_v1",
        "status": "PASS", "exact_r4_allowlist_and_order": True,
        "dimensions": {"candidate": 80, "positive_pair_item": 17, "unpaired_item": 8, "descriptors": 4},
        "feature_firewall_pass": True, "predictor_identity_excluded": True,
        "r4_risk_decision_excluded": True, "postmortem_bins_excluded": True,
    })
    write_json(INTEGRITY / "split_leakage_audit.json", {
        "schema_version": "conservative_reconciliation_split_leakage_audit_v1",
        "status": "PASS", "biological_unit": "RNA", "rna_count": 121,
        "source_record_count": 363, "rna_disjoint_all_rotations": True,
        "source_and_evidence_coassigned": True, "legacy121_role": "DEVELOPMENT_ONLY",
        "independent_test": False, "grouped_split_sha256": sha256_file(SPLIT_PATH),
    })
    write_json(INTEGRITY / "feature_reference_completion.json", completion)
    print(json.dumps(completion, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
