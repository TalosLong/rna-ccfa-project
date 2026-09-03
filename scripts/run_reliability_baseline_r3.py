#!/usr/bin/env python3
"""Materialize the frozen R3 Pair-Reliability Baseline Suite score tables.

This runner performs no training or parameter updates. It reads only the
frozen Legacy121, historical comparator, clean-evidence, and R2 v1.0.2 assets.
All joins are validated before any R3 artifact directory is created.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from rna_ccfa.metrics import evaluate_pairs
from rna_ccfa.structure import Pair, validate_pairs


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "normalized/legacy121_v1/predictions.jsonl"
FOLDS = ROOT / "results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv"
MANIFESTS = ROOT / "results/evidence_guidance/e0/clean_manifests.jsonl"
MANIFEST_INDEX = ROOT / "results/evidence_guidance/e0/clean_manifest_index.csv"
V1 = ROOT / "results/selective_refiner/v1/POOLED_SOURCE_AGNOSTIC"
V1_RECON = ROOT / "results/selective_refiner/v2/base_reconstructed/POOLED_SOURCE_AGNOSTIC"
V3 = ROOT / "results/selective_refiner/v3/veto2_fixed"
V3_CONDITIONS = ROOT / "results/selective_refiner/v3_protocol_audit/v3_conditions.json"
R2 = ROOT / "results/global_constrained_refolding_r2"
ELIGIBILITY = R2 / "integrity/r2_manifest_eligibility_v1_0_2.csv"
B2_STRUCTURES = R2 / "parsed/b2_structures_v1_0_2.csv"
MATCHED_B0 = R2 / "integrity/r2_matched_b0_view_v1_0_2.csv"
MATCHED_B1 = R2 / "integrity/r2_matched_b1_view_v1_0_2.csv"
OUT = ROOT / "results/reliability_baseline_r3"

SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")
SEEDS = (17, 29, 41, 53, 67)
PAIR_CHANNEL = "POSITIVE_PAIR_EVIDENCE"
UNPAIRED_CHANNEL = "UNPAIRED_NUCLEOTIDE_EVIDENCE"
RNAFOLD = Path("/usr/bin/RNAfold")
RNAFOLD_ARGV = (
    str(RNAFOLD), "--noPS", "--partfunc=1", "--bppmThreshold=0",
    "--temp=37", "--dangles=2",
)
EXPECTED_COUNTS = {
    "rnafold": {"pairs": 1693, "keep": 1473, "delete": 220},
    "petfold": {"pairs": 1704, "keep": 1463, "delete": 241},
    "trrosettarna2_native_ss": {"pairs": 1893, "keep": 1461, "delete": 432},
}


def support_other_count_risk(
    pair: Pair, source: str, predictions: dict[str, set[Pair]]
) -> tuple[int, int]:
    support = sum(pair in predictions[other] for other in SOURCES if other != source)
    if support not in (0, 1, 2):
        raise AssertionError("support_other_count must be 0, 1, or 2")
    return support, 2 - support


def local_evidence_conflict_risk(
    pair: Pair, channel: str, delivered_pairs: set[Pair], delivered_unpaired: set[int]
) -> int:
    if channel == PAIR_CHANNEL:
        endpoints = {position for evidence_pair in delivered_pairs for position in evidence_pair}
        return int(pair not in delivered_pairs and bool(set(pair) & endpoints))
    if channel == UNPAIRED_CHANNEL:
        return int(bool(set(pair) & delivered_unpaired))
    raise AssertionError(f"unexpected evidence channel: {channel}")


def b2_disagreement_risk(pair: Pair, b2_pairs: set[Pair]) -> int:
    return int(pair not in b2_pairs)


def v3_fixed_delete(p_delete: float, threshold: float | None, support_other_count: int) -> int:
    return int(threshold is not None and p_delete >= threshold and support_other_count < 2)


def validate_r2_eligibility_counts(rows: Sequence[Mapping[str, str]]) -> Counter:
    counts = Counter(
        row["channel"] for row in rows if row["eligibility_status"] == "R2_ELIGIBLE"
    )
    if counts != Counter({PAIR_CHANNEL: 3523, UNPAIRED_CHANNEL: 3630}):
        raise AssertionError(f"R2 eligible channel counts mismatch: {counts}")
    return counts


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv_gz(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty score table: {path}")
    fields = list(dict.fromkeys(key for row in rows for key in row))
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as zipped:
        with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as text:
            writer = csv.DictWriter(text, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    path.write_bytes(buffer.getvalue())


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fail_on_forbidden_path(paths: Iterable[Path]) -> None:
    for path in paths:
        resolved = str(path.resolve()).lower()
        if "external77" in resolved:
            raise AssertionError(f"locked external77 path rejected: {path}")


def load_legacy() -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, int]]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    with NORMALIZED.open(encoding="utf-8") as handle:
        for line in handle:
            raw = json.loads(line)
            source = raw["source_model"]["name"]
            if source not in SOURCES:
                raise AssertionError(f"unexpected source: {source}")
            rna_id = raw["rna_id"]
            sequence = raw["sequence"]
            gt = set(validate_pairs(raw["ground_truth_structure"]["pairs"], sequence=sequence))
            original = set(validate_pairs(raw["predicted_structure"]["pairs"], sequence=sequence))
            key = (rna_id, source)
            if key in records:
                raise AssertionError(f"duplicate normalized record: {key}")
            shared = evaluate_pairs(original, gt, sequence_length=len(sequence))
            labels = {pair: int(pair not in gt) for pair in original}
            if shared.tp != sum(label == 0 for label in labels.values()):
                raise AssertionError(f"TP label mismatch for {key}")
            if shared.fp != sum(label == 1 for label in labels.values()):
                raise AssertionError(f"FP label mismatch for {key}")
            records[key] = {
                "rna_id": rna_id,
                "source": source,
                "sequence": sequence,
                "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(),
                "gt": gt,
                "original": original,
                "labels": labels,
                "gt_pair_count": len(gt),
            }
    rnas = {key[0] for key in records}
    if len(records) != 363 or len(rnas) != 121:
        raise AssertionError(f"Legacy121 matrix mismatch: {len(records)} records, {len(rnas)} RNAs")
    for rna_id in rnas:
        if {source for candidate, source in records if candidate == rna_id} != set(SOURCES):
            raise AssertionError(f"incomplete source matrix for {rna_id}")
        copies = [records[(rna_id, source)] for source in SOURCES]
        if len({row["sequence"] for row in copies}) != 1 or len({frozenset(row["gt"]) for row in copies}) != 1:
            raise AssertionError(f"source copies disagree for {rna_id}")
    for source, expected in EXPECTED_COUNTS.items():
        subset = [row for (rna, candidate), row in records.items() if candidate == source]
        observed = {
            "pairs": sum(len(row["original"]) for row in subset),
            "keep": sum(sum(label == 0 for label in row["labels"].values()) for row in subset),
            "delete": sum(sum(label == 1 for label in row["labels"].values()) for row in subset),
        }
        if observed != expected:
            raise AssertionError(f"frozen pair inventory mismatch for {source}: {observed}")

    fold_rows = csv_rows(FOLDS)
    folds = {row["rna_id"]: int(row["fold"]) for row in fold_rows}
    if len(folds) != 121 or set(folds) != rnas or set(folds.values()) != set(range(5)):
        raise AssertionError("frozen grouped folds mismatch")
    return records, folds


def base_pair_row(
    record: dict[str, Any], fold: int, partition: str, pair: Pair,
    baseline_id: str, score_type: str, risk: float | int,
) -> dict[str, Any]:
    return {
        "rna_id": record["rna_id"], "source": record["source"],
        "fold": fold, "partition": partition, "pair_i": pair[0], "pair_j": pair[1],
        "label_delete": record["labels"][pair], "risk": risk,
        "baseline_id": baseline_id, "score_type": score_type,
        "gt_pair_count": record["gt_pair_count"],
    }


def expected_partition_keys(
    records: dict[tuple[str, str], dict[str, Any]], folds: dict[str, int],
    rotation: int, partition: str,
) -> set[tuple[str, str, int, int]]:
    target = rotation if partition == "test" else (rotation + 1) % 5
    return {
        (rna_id, source, pair[0], pair[1])
        for (rna_id, source), record in records.items() if folds[rna_id] == target
        for pair in record["original"]
    }


def audit_score_rows(
    rows: list[dict[str, str]], expected: set[tuple[str, str, int, int]],
    records: dict[tuple[str, str], dict[str, Any]], partition: str,
) -> dict[tuple[str, str, int, int], dict[str, str]]:
    mapped: dict[tuple[str, str, int, int], dict[str, str]] = {}
    for row in rows:
        key = (row["rna_id"], row["source_model"], int(row["i"]), int(row["j"]))
        if key in mapped:
            raise AssertionError(f"duplicate historical score key: {key}")
        if row["partition"] != partition:
            raise AssertionError(f"historical partition mismatch: {row}")
        record = records[(key[0], key[1])]
        pair = (key[2], key[3])
        if pair not in record["original"] or int(row["label_delete"]) != record["labels"][pair]:
            raise AssertionError(f"historical pair/label mismatch: {key}")
        score = float(row["p_delete"])
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise AssertionError(f"invalid historical p_delete: {score}")
        mapped[key] = row
    if set(mapped) != expected:
        raise AssertionError(
            f"historical score join mismatch: expected {len(expected)}, observed {len(mapped)}"
        )
    return mapped


def materialize_track_p(
    records: dict[tuple[str, str], dict[str, Any]], folds: dict[str, int]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    outputs: dict[str, list[dict[str, Any]]] = {
        "track_p_p0": [], "track_p_p2": [], "track_p_p4": [],
    }
    for seed in SEEDS:
        outputs[f"track_p_p1_seed{seed}"] = []
        outputs[f"track_p_p3_seed{seed}"] = []
    p1_audit = []
    p3_audit = []

    predictions = {
        rna_id: {source: records[(rna_id, source)]["original"] for source in SOURCES}
        for rna_id in folds
    }
    for rotation in range(5):
        train_rnas = {rna for rna, fold in folds.items() if fold not in (rotation, (rotation + 1) % 5)}
        test_rnas = {rna for rna, fold in folds.items() if fold == rotation}
        train_labels = [
            label for (rna, _), record in records.items() if rna in train_rnas
            for label in record["labels"].values()
        ]
        pooled_prevalence = sum(train_labels) / len(train_labels)
        source_prevalence = {}
        for source in SOURCES:
            labels = [
                label for (rna, candidate), record in records.items()
                if rna in train_rnas and candidate == source for label in record["labels"].values()
            ]
            source_prevalence[source] = sum(labels) / len(labels)
        for rna_id in sorted(test_rnas):
            for source in SOURCES:
                record = records[(rna_id, source)]
                for pair in sorted(record["original"]):
                    pooled = base_pair_row(
                        record, rotation, "test", pair, "R3-P0", "PROBABILITY_LIKE_CONSTANT",
                        pooled_prevalence,
                    )
                    pooled["reference_scope"] = "POOLED_TRAINING_PREVALENCE"
                    outputs["track_p_p0"].append(pooled)
                    source_row = base_pair_row(
                        record, rotation, "test", pair, "R3-P0", "PROBABILITY_LIKE_CONSTANT",
                        source_prevalence[source],
                    )
                    source_row["reference_scope"] = "SOURCE_WISE_TRAINING_PREVALENCE"
                    outputs["track_p_p0"].append(source_row)

        for partition in ("validation", "test"):
            target_fold = (rotation + 1) % 5 if partition == "validation" else rotation
            for rna_id in sorted(rna for rna, fold in folds.items() if fold == target_fold):
                for source in SOURCES:
                    record = records[(rna_id, source)]
                    for pair in sorted(record["original"]):
                        support, agreement_risk = support_other_count_risk(pair, source, predictions[rna_id])
                        p2 = base_pair_row(
                            record, rotation, partition, pair, "R3-P2", "ORDINAL_RISK", agreement_risk,
                        )
                        p2["support_other_count"] = support
                        outputs["track_p_p2"].append(p2)

        expected_val = expected_partition_keys(records, folds, rotation, "validation")
        expected_test = expected_partition_keys(records, folds, rotation, "test")
        for seed in SEEDS:
            recon = V1_RECON / f"fold_{rotation}" / f"seed_{seed}"
            v1 = V1 / f"fold_{rotation}" / f"seed_{seed}"
            config = json.loads((recon / "config.json").read_text(encoding="utf-8"))
            if config.get("retrained") is not False or config.get("source_v1_variant") != "POOLED_SOURCE_AGNOSTIC":
                raise AssertionError(f"invalid historical reconstruction config: {recon}")
            if config.get("v1_checkpoint_sha256") != file_sha256(v1 / "checkpoint.pt"):
                raise AssertionError(f"checkpoint provenance mismatch: {recon}")
            val = audit_score_rows(
                csv_rows(recon / "validation_pair_scores.csv"), expected_val, records, "validation"
            )
            test = audit_score_rows(
                csv_rows(recon / "test_pair_scores.csv"), expected_test, records, "test"
            )
            authoritative = audit_score_rows(
                csv_rows(v1 / "per_pair_scores.csv"), expected_test, records, "test"
            )
            max_abs = max(abs(float(test[key]["p_delete"]) - float(authoritative[key]["p_delete"])) for key in expected_test)
            # Existing validation materialization is used directly. Held-out R3
            # scores remain the authoritative v1 files, not their later CPU
            # reconstruction copy.
            for partition, mapping in (("validation", val), ("test", authoritative)):
                for key in sorted(mapping):
                    record = records[(key[0], key[1])]
                    row = base_pair_row(
                        record, rotation, partition, (key[2], key[3]),
                        "R3-P1", "RAW_UNCALIBRATED_PROBABILITY_LIKE", float(mapping[key]["p_delete"]),
                    )
                    row["historical_seed"] = seed
                    outputs[f"track_p_p1_seed{seed}"].append(row)
            p1_audit.append({
                "fold": rotation, "seed": seed, "validation_rows": len(val), "test_rows": len(test),
                "historical_cpu_reconstruction_vs_authoritative_test_max_abs_error": max_abs,
                "validation_scores_source": "historical_v2.0.1_checkpoint_reconstruction",
                "test_scores_source": "authoritative_v1_per_pair_scores",
                "checkpoint_inference_during_r3": False, "training_during_r3": False,
            })

            v3_path = V3 / f"fold_{rotation}" / f"seed_{seed}" / "per_pair_decisions.csv"
            v3_rows = csv_rows(v3_path)
            v3_map: dict[tuple[str, str, int, int], dict[str, str]] = {}
            threshold = json.loads((v1 / "selected_threshold.json").read_text(encoding="utf-8"))["threshold"]
            for historical in v3_rows:
                key = (historical["rna_id"], historical["source_model"], int(historical["i"]), int(historical["j"]))
                if key in v3_map or key not in expected_test:
                    raise AssertionError(f"V3 key mismatch: {key}")
                record = records[(key[0], key[1])]
                pair = (key[2], key[3])
                support, _ = support_other_count_risk(pair, key[1], predictions[key[0]])
                expected_delete = v3_fixed_delete(float(historical["p_delete"]), threshold, support)
                if (
                    int(historical["label_delete"]) != record["labels"][pair]
                    or int(historical["support_other_count"]) != support
                    or int(historical["delete"]) != expected_delete
                    or historical["decision"] != ("DELETE" if expected_delete else "KEEP")
                ):
                    raise AssertionError(f"V3 frozen policy mismatch: {key}")
                if float(historical["p_delete"]) != float(test[key]["p_delete"]):
                    raise AssertionError(f"V3 score provenance mismatch: {key}")
                out = base_pair_row(
                    record, rotation, "test", pair, "R3-P3", "BINARY_DECISION", expected_delete,
                )
                out.update({
                    "historical_seed": seed, "support_other_count": support,
                    "historical_p_delete": float(historical["p_delete"]),
                    "historical_threshold": threshold if threshold is not None else "",
                    "decision": historical["decision"],
                })
                outputs[f"track_p_p3_seed{seed}"].append(out)
                v3_map[key] = historical
            if set(v3_map) != expected_test:
                raise AssertionError(f"V3 join incomplete for fold {rotation}, seed {seed}")
            p3_audit.append({
                "fold": rotation, "seed": seed, "test_rows": len(v3_rows),
                "threshold_semantics": "IMMUTABLE_V3_VETO2_FIXED", "policy_join": "PASS",
            })
    return outputs, {"p1_runs": p1_audit, "p3_runs": p3_audit}


UBOX_RE = re.compile(r"^\s*(\d+)\s+(\d+)\s+([^\s]+)\s+ubox\s*$")


def parse_bpp_dotplot(text: str, sequence_length: int) -> list[tuple[int, int, float]]:
    pairs: dict[tuple[int, int], float] = {}
    for line in text.splitlines():
        match = UBOX_RE.match(line)
        if not match:
            continue
        one_i, one_j = int(match.group(1)), int(match.group(2))
        try:
            root_probability = float(match.group(3))
        except ValueError as error:
            raise ValueError(f"invalid ubox probability: {line}") from error
        i, j = one_i - 1, one_j - 1
        probability = root_probability ** 2
        if (
            not (0 <= i < j < sequence_length) or not math.isfinite(probability)
            or probability < 0.0 or probability > 1.0
        ):
            raise ValueError(f"invalid ubox record: {line}")
        if (i, j) in pairs:
            raise ValueError(f"duplicate ubox record: {(one_i, one_j)}")
        pairs[(i, j)] = probability
    expected = sequence_length * (sequence_length - 1) // 2
    expected_keys = {(i, j) for i in range(sequence_length) for j in range(i + 1, sequence_length)}
    if len(pairs) != expected or set(pairs) != expected_keys:
        missing = len(expected_keys - set(pairs))
        raise ValueError(f"incomplete BPP upper triangle: {len(pairs)}/{expected}, missing={missing}")
    return [(i, j, pairs[(i, j)]) for i, j in sorted(pairs)]


def matrix_bytes(rows: list[tuple[int, int, float]]) -> bytes:
    return "".join(f"{i},{j},{probability:.17g}\n" for i, j, probability in rows).encode("ascii")


def run_bpp(sequence: str) -> tuple[list[tuple[int, int, float]], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="r3_bpp_") as directory:
        work = Path(directory)
        env = os.environ.copy()
        env["LC_ALL"] = "C"
        completed = subprocess.run(
            RNAFOLD_ARGV, input=f">r3bpp\n{sequence}\n", text=True,
            cwd=work, env=env, capture_output=True, check=False,
        )
        dotplot = work / "r3bpp_dp.ps"
        if completed.returncode != 0 or not dotplot.is_file():
            raise RuntimeError(
                f"RNAfold BPP failure rc={completed.returncode}: {completed.stderr.strip()}"
            )
        raw = dotplot.read_text(encoding="utf-8")
        rows = parse_bpp_dotplot(raw, len(sequence))
        compact_hash = hashlib.sha256(matrix_bytes(rows)).hexdigest()
        return rows, {
            "return_code": completed.returncode,
            "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            "stderr": completed.stderr.strip(),
            "raw_dotplot_sha256": hashlib.sha256(dotplot.read_bytes()).hexdigest(),
            "matrix_sha256": compact_hash,
            "record_count": len(rows), "parse_status": "PASS",
        }


def materialize_bpp(
    records: dict[tuple[str, str], dict[str, Any]], folds: dict[str, int],
    track_p: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    version = subprocess.run([str(RNAFOLD), "--version"], text=True, capture_output=True, check=True).stdout.strip()
    if version != "RNAfold 2.4.17":
        raise AssertionError(f"frozen RNAfold version mismatch: {version}")
    toy_a, toy_audit = run_bpp("GGGAAACCC")
    toy_b, _ = run_bpp("GGGAAACCC")
    if toy_a != toy_b or len(toy_a) != 36:
        raise AssertionError("BPP deterministic toy audit failed")
    toy_value = {(i, j): p for i, j, p in toy_a}[(2, 6)]
    if abs(toy_value - 0.518753349792) > 1e-12:
        raise AssertionError(f"BPP toy semantic mismatch: {toy_value}")

    unique = {rna_id: records[(rna_id, SOURCES[0])] for rna_id in folds}
    matrices: dict[str, dict[Pair, float]] = {}
    compact_rows: list[dict[str, Any]] = []
    provenance = []
    audited_reruns = set(sorted(unique)[:2] + sorted(unique)[-1:])
    for rna_id in sorted(unique):
        record = unique[rna_id]
        matrix, audit = run_bpp(record["sequence"])
        if rna_id in audited_reruns:
            rerun, _ = run_bpp(record["sequence"])
            if matrix != rerun:
                raise AssertionError(f"BPP deterministic rerun mismatch for {rna_id}")
        matrices[rna_id] = {(i, j): probability for i, j, probability in matrix}
        for i, j, probability in matrix:
            compact_rows.append({"rna_id": rna_id, "pair_i": i, "pair_j": j, "bpp": probability})
        provenance.append({
            "rna_id": rna_id, "sequence_sha256": record["sequence_sha256"],
            "rnafold_version": version, "command": "LC_ALL=C " + " ".join(RNAFOLD_ARGV),
            "matrix_sha256": audit["matrix_sha256"], "record_count": audit["record_count"],
            "parse_status": audit["parse_status"], "deterministic_rerun_audited": rna_id in audited_reruns,
        })

    for rotation in range(5):
        for partition, target in (("validation", (rotation + 1) % 5), ("test", rotation)):
            for rna_id in sorted(rna for rna, fold in folds.items() if fold == target):
                for source in SOURCES:
                    record = records[(rna_id, source)]
                    for pair in sorted(record["original"]):
                        if pair not in matrices[rna_id]:
                            raise AssertionError(f"BPP join failure: {(rna_id, source, pair)}")
                        probability = matrices[rna_id][pair]
                        row = base_pair_row(
                            record, rotation, partition, pair, "R3-P4",
                            "THERMODYNAMIC_PROBABILITY_DERIVED_RISK", 1.0 - probability,
                        )
                        row["rnafold_bpp"] = probability
                        track_p["track_p_p4"].append(row)
    expected_pair_rows = 2 * sum(expected["pairs"] for expected in EXPECTED_COUNTS.values())
    if len(track_p["track_p_p4"]) != expected_pair_rows:
        raise AssertionError("P4 all-source join count mismatch")
    return compact_rows, provenance, {
        "status": "R3_BPP_BASELINE_AVAILABLE", "rnafold_version": version,
        "command": "LC_ALL=C " + " ".join(RNAFOLD_ARGV),
        "unique_rnas": len(unique), "compact_matrix_records": len(compact_rows),
        "all_three_sources_joined": True, "joined_pair_rows_validation_plus_test": expected_pair_rows,
        "toy": {**toy_audit, "one_based_3_7_zero_based_2_6_probability": toy_value},
        "deterministic_rerun_rnas": sorted(audited_reruns),
    }


def load_manifests() -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    with MANIFESTS.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["manifest_id"] in manifests:
                raise AssertionError(f"duplicate manifest: {row['manifest_id']}")
            manifests[row["manifest_id"]] = row
    if len(manifests) != 7260:
        raise AssertionError(f"clean manifest universe mismatch: {len(manifests)}")
    index = {row["manifest_id"]: row["manifest_payload_sha256"] for row in csv_rows(MANIFEST_INDEX)}
    if len(index) != 7260 or index != {key: row["manifest_payload_sha256"] for key, row in manifests.items()}:
        raise AssertionError("manifest index/payload mismatch")
    return manifests


def materialize_track_e(
    records: dict[tuple[str, str], dict[str, Any]], folds: dict[str, int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    manifests = load_manifests()
    eligibility_rows = csv_rows(ELIGIBILITY)
    if len(eligibility_rows) != 7260:
        raise AssertionError("R2 eligibility inventory mismatch")
    eligible = {row["manifest_id"]: row for row in eligibility_rows if row["eligibility_status"] == "R2_ELIGIBLE"}
    channel_counts = validate_r2_eligibility_counts(eligibility_rows)
    ineligible = set(manifests) - set(eligible)
    if len(eligible) != 7153 or len(ineligible) != 107:
        raise AssertionError("R2 eligibility total mismatch")

    b2_rows = csv_rows(B2_STRUCTURES)
    b2: dict[str, set[Pair]] = {}
    for row in b2_rows:
        if row["manifest_id"] in b2 or row["manifest_id"] not in eligible:
            raise AssertionError(f"unexpected/duplicate B2 manifest: {row['manifest_id']}")
        if row["status"] != "PASS" or row["output_valid"] != "True" or row["constraint_satisfied"] != "True":
            raise AssertionError(f"invalid B2 structure: {row['manifest_id']}")
        b2[row["manifest_id"]] = {
            tuple(pair) for pair in json.loads(row["pairs_zero_based_json"])
        }
    if set(b2) != set(eligible):
        raise AssertionError("B2 eligible manifest join is not 100%")

    b0_rows = csv_rows(MATCHED_B0)
    b0 = {(row["manifest_id"], row["source_model"]): row for row in b0_rows}
    if len(b0) != 7153 * 3:
        raise AssertionError("matched B0 key count mismatch")
    b1_rows = csv_rows(MATCHED_B1)
    b1 = {}
    for row in b1_rows:
        primary = "PAIR_HARD_ENFORCE" if row["evidence_channel"] == PAIR_CHANNEL else "UNPAIRED_HARD_DELETE"
        if row["condition"] == primary:
            b1[(row["manifest_id"], row["source_model"])] = row
    expected_contexts = {(manifest_id, source) for manifest_id in eligible for source in SOURCES}
    if set(b0) != expected_contexts or set(b1) != expected_contexts:
        raise AssertionError("matched B0/B1 context universe mismatch")

    e1_rows: list[dict[str, Any]] = []
    e2_rows: list[dict[str, Any]] = []
    context_count = Counter()
    for manifest_id in sorted(eligible):
        manifest = manifests[manifest_id]
        eligibility = eligible[manifest_id]
        if (
            manifest["rna_id"] != eligibility["rna_id"]
            or manifest["manifest_payload_sha256"] != eligibility["manifest_payload_sha256"]
            or manifest["evidence_channel"] != eligibility["channel"]
        ):
            raise AssertionError(f"eligible manifest provenance mismatch: {manifest_id}")
        if manifest["noise_level_percent"] != 0:
            raise AssertionError(f"non-clean evidence in R3: {manifest_id}")
        rna_id = manifest["rna_id"]
        channel = manifest["evidence_channel"]
        delivered_pairs = {
            (int(item["delivered_evidence_item"]["i"]), int(item["delivered_evidence_item"]["j"]))
            for item in manifest["items"]
        } if channel == PAIR_CHANNEL else set()
        delivered_unpaired = {
            int(item["delivered_evidence_item"]["i"]) for item in manifest["items"]
        } if channel == UNPAIRED_CHANNEL else set()
        for source in SOURCES:
            record = records[(rna_id, source)]
            key = (manifest_id, source)
            if b0[key]["manifest_payload_sha256"] != manifest["manifest_payload_sha256"] or b1[key]["manifest_payload_sha256"] != manifest["manifest_payload_sha256"]:
                raise AssertionError(f"B0/B1 payload join mismatch: {key}")
            flagged_local = 0
            for pair in sorted(record["original"]):
                risk_e1 = local_evidence_conflict_risk(
                    pair, channel, delivered_pairs, delivered_unpaired
                )
                risk_e2 = b2_disagreement_risk(pair, b2[manifest_id])
                common = {
                    "manifest_id": manifest_id, "manifest_payload_sha256": manifest["manifest_payload_sha256"],
                    "rna_id": rna_id, "source": source, "fold": folds[rna_id], "partition": "test",
                    "channel": channel, "density": int(manifest["density_percent"]),
                    "evidence_seed": int(manifest["evidence_seed"]),
                    "pair_i": pair[0], "pair_j": pair[1], "gt_pair_count": record["gt_pair_count"],
                }
                # Risks are frozen before the GT-derived label is attached.
                row_e1 = {**common, "risk": risk_e1, "baseline_id": "R3-E1", "score_type": "BINARY_INDICATOR"}
                row_e2 = {**common, "risk": risk_e2, "baseline_id": "R3-E2", "score_type": "BINARY_INDICATOR"}
                row_e1["label_delete"] = record["labels"][pair]
                row_e2["label_delete"] = record["labels"][pair]
                e1_rows.append(row_e1)
                e2_rows.append(row_e2)
                flagged_local += risk_e1
            if flagged_local != int(b1[key]["local_conflicting_pairs_removed"]):
                raise AssertionError(f"E1/B1 local-conflict join mismatch: {key}")
            context_count[channel] += 1
    if len(e1_rows) != len(e2_rows):
        raise AssertionError("Track E baseline row mismatch")
    if context_count != Counter({PAIR_CHANNEL: 3523 * 3, UNPAIRED_CHANNEL: 3630 * 3}):
        raise AssertionError("Track E context count mismatch")
    return e1_rows, e2_rows, {
        "eligible_manifests": len(eligible), "pair_eligible_manifests": channel_counts[PAIR_CHANNEL],
        "unpaired_eligible_manifests": channel_counts[UNPAIRED_CHANNEL],
        "capability_ineligible_manifests": len(ineligible), "matched_source_contexts": len(expected_contexts),
        "pair_realization_rows_per_baseline": len(e1_rows), "b2_join_fraction": 1.0,
        "e1_b1_scope_join_fraction": 1.0, "b0_b1_b2_context_join": "PASS",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUT)
    args = parser.parse_args()
    input_paths = [
        NORMALIZED, FOLDS, MANIFESTS, MANIFEST_INDEX, V3_CONDITIONS,
        ELIGIBILITY, B2_STRUCTURES, MATCHED_B0, MATCHED_B1,
    ]
    input_paths += sorted(V1.glob("fold_*/seed_*/per_pair_scores.csv"))
    input_paths += sorted(V1.glob("fold_*/seed_*/checkpoint.pt"))
    input_paths += sorted(V1_RECON.glob("fold_*/seed_*/validation_pair_scores.csv"))
    input_paths += sorted(V1_RECON.glob("fold_*/seed_*/test_pair_scores.csv"))
    input_paths += sorted(V3.glob("fold_*/seed_*/per_pair_decisions.csv"))
    fail_on_forbidden_path(input_paths + [args.output_root])
    if any(not path.is_file() for path in input_paths):
        missing = [str(path) for path in input_paths if not path.is_file()]
        raise FileNotFoundError(missing)
    if (
        len(list(V1.glob("fold_*/seed_*/per_pair_scores.csv"))) != 25
        or len(list(V1_RECON.glob("fold_*/seed_*/validation_pair_scores.csv"))) != 25
        or len(list(V1_RECON.glob("fold_*/seed_*/test_pair_scores.csv"))) != 25
        or len(list(V3.glob("fold_*/seed_*/per_pair_decisions.csv"))) != 25
    ):
        raise AssertionError("historical fold/seed asset inventory mismatch")

    records, folds = load_legacy()
    track_p, historical_audit = materialize_track_p(records, folds)
    bpp_rows, bpp_provenance, bpp_audit = materialize_bpp(records, folds, track_p)
    track_e_e1, track_e_e2, track_e_audit = materialize_track_e(records, folds)

    expected_twice = 2 * 5290
    if len(track_p["track_p_p2"]) != expected_twice:
        raise AssertionError("P2 validation/test row count mismatch")
    p2_support_counts = Counter(
        int(row["support_other_count"]) for row in track_p["track_p_p2"]
        if row["partition"] == "test"
    )
    if p2_support_counts != Counter({0: 504, 1: 586, 2: 4200}):
        raise AssertionError(f"P2 frozen support inventory mismatch: {p2_support_counts}")
    if any(len(track_p[f"track_p_p1_seed{seed}"]) != expected_twice for seed in SEEDS):
        raise AssertionError("P1 validation/test row count mismatch")
    if any(len(track_p[f"track_p_p3_seed{seed}"]) != 5290 for seed in SEEDS):
        raise AssertionError("P3 held-out row count mismatch")

    # Only now, after all formal joins have passed, create R3 artifacts.
    out = args.output_root
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"R3 output already exists and is non-empty: {out}")
    for name, rows in track_p.items():
        write_csv_gz(out / "pair_scores" / f"{name}.csv.gz", rows)
    write_csv_gz(out / "pair_scores" / "track_e_e1.csv.gz", track_e_e1)
    write_csv_gz(out / "pair_scores" / "track_e_e2.csv.gz", track_e_e2)
    write_csv_gz(out / "pair_scores" / "rnafold_bpp" / "bpp_matrices.csv.gz", bpp_rows)
    write_csv_gz(out / "pair_scores" / "rnafold_bpp" / "provenance.csv.gz", bpp_provenance)

    hashes = {str(path.relative_to(ROOT)): file_sha256(path) for path in input_paths}
    write_json(out / "integrity" / "input_hashes.json", {
        "files": hashes, "input_file_count": len(hashes),
        "external77_accessed": False, "hash_algorithm": "sha256",
    })
    write_json(out / "integrity" / "universe_audit.json", {
        "status": "PASS", "track_p_unique_rnas": 121, "track_p_source_records": 363,
        "track_p_original_pairs": 5290, "track_p_keep_pairs": 4397,
        "track_p_delete_pairs": 893, "source_counts": EXPECTED_COUNTS,
        "frozen_grouped_folds": Counter(folds.values()), **track_e_audit,
    })
    write_json(out / "integrity" / "historical_score_audit.json", {
        "status": "PASS", "authoritative_v1_variant": "POOLED_SOURCE_AGNOSTIC",
        "historical_seeds": SEEDS, "p1": historical_audit["p1_runs"],
        "p3": historical_audit["p3_runs"], "retraining": False, "retuning": False,
    })
    write_json(out / "integrity" / "bpp_generation_audit.json", {
        **bpp_audit, "per_rna": bpp_provenance,
    })
    write_json(out / "integrity" / "track_p_join_audit.json", {
        "status": "PASS", "p0_rows": len(track_p["track_p_p0"]),
        "p1_rows_per_seed": expected_twice, "p2_rows": len(track_p["track_p_p2"]),
        "p2_heldout_support_counts": dict(sorted(p2_support_counts.items())),
        "p3_rows_per_seed": 5290, "p4_rows": len(track_p["track_p_p4"]),
        "all_original_pair_labels_match_shared_evaluator": True,
    })
    write_json(out / "integrity" / "track_e_join_audit.json", {"status": "PASS", **track_e_audit})
    write_json(out / "integrity" / "leakage_audit.json", {
        "status": "PASS", "gt_use": "LABELS_AND_OUTCOME_METRICS_ONLY",
        "score_construction_uses_gt": False, "missing_gt_pairs_are_candidates": False,
        "external77_accessed": False, "new_training_runs": 0, "historical_retuning": False,
        "combined_scores": False, "noise_or_real_evidence": False, "r4_started": False,
        "pseudoknot_branch": False, "two_d_to_three_d": False,
    })
    write_json(out / "integrity" / "runner_completion.json", {
        "status": "R3_SCORE_MATERIALIZATION_COMPLETE", "all_join_gates_passed": True,
        "summarization_started": False, "output_hashes_pending_final_summary": True,
    })
    print(json.dumps({
        "status": "R3_SCORE_MATERIALIZATION_COMPLETE", "track_p_pairs": 5290,
        "track_e_pair_realizations_per_baseline": len(track_e_e1),
        "bpp_matrix_records": len(bpp_rows),
    }, indent=2))


if __name__ == "__main__":
    main()
