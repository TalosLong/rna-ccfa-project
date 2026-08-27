#!/usr/bin/env python3
"""Evaluate normalized Legacy121 v1 historical structures with the shared evaluator."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rna_ccfa.aggregation import aggregate_pair_evaluations
from rna_ccfa.metrics import PairEvaluation, evaluate_pairs
from rna_ccfa.structure import Pair, validate_pairs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = "legacy121_v1"
SCHEMA_VERSION = "rna-ccfa.normalized_prediction.v1"
EXPECTED_RECORDS = 363
EXPECTED_RNAS = 121
EXPECTED_MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")

PER_SAMPLE_FIELDS = (
    "record_id",
    "rna_id",
    "source_model",
    "sequence_length",
    "gt_pair_count",
    "predicted_pair_count",
    "tp",
    "fp",
    "fn",
    "precision",
    "recall",
    "f1",
)

MODEL_SUMMARY_FIELDS = (
    "source_model",
    "n_samples",
    "sum_tp",
    "sum_fp",
    "sum_fn",
    "macro_precision",
    "macro_recall",
    "macro_f1",
    "micro_precision",
    "micro_recall",
    "micro_f1",
    "median_f1",
    "std_f1",
    "min_f1",
    "max_f1",
)


class BaselineEvaluationError(RuntimeError):
    """The normalized input or a derived baseline result failed acceptance."""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "normalized/legacy121_v1/predictions.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "results/baseline_legacy121_v1",
    )
    return parser.parse_args()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise BaselineEvaluationError(f"normalized input does not exist: {path}")

    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise BaselineEvaluationError(f"blank JSONL line at input line {line_number}")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise BaselineEvaluationError(
                    f"invalid JSON at input line {line_number}: {exc}"
                ) from exc
            if not isinstance(record, dict):
                raise BaselineEvaluationError(
                    f"input line {line_number} must contain a JSON object"
                )
            records.append(record)
    return records


def _require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BaselineEvaluationError(f"{context} must be an object")
    return value


def _validate_structure(
    structure: Any,
    *,
    sequence: str,
    context: str,
) -> tuple[Pair, ...]:
    structure = _require_mapping(structure, context)
    pairs = structure.get("pairs")
    allow_multiple_partners = structure.get("allow_multiple_partners")
    if not isinstance(allow_multiple_partners, bool):
        raise BaselineEvaluationError(f"{context}.allow_multiple_partners must be boolean")
    try:
        canonical = validate_pairs(
            pairs,
            sequence=sequence,
            allow_multiple_partners=allow_multiple_partners,
        )
    except (TypeError, ValueError) as exc:
        raise BaselineEvaluationError(f"{context}.pairs failed canonical validation: {exc}") from exc

    canonical_json = [[i, j] for i, j in canonical]
    if pairs != canonical_json:
        raise BaselineEvaluationError(
            f"{context}.pairs are valid coordinates but not stored in canonical sorted form"
        )
    return tuple(canonical)


def _validate_dataset(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) != EXPECTED_RECORDS:
        raise BaselineEvaluationError(
            f"expected {EXPECTED_RECORDS} normalized records, observed {len(records)}"
        )

    record_ids: list[str] = []
    model_counts: Counter[str] = Counter()
    records_by_rna: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    canonical_pairs: dict[str, tuple[tuple[Pair, ...], tuple[Pair, ...]]] = {}

    for index, record in enumerate(records):
        context = f"record {index + 1}"
        if record.get("dataset") != DATASET:
            raise BaselineEvaluationError(f"{context} has unexpected dataset")
        if record.get("schema_version") != SCHEMA_VERSION:
            raise BaselineEvaluationError(f"{context} has unexpected schema_version")

        record_id = record.get("record_id")
        rna_id = record.get("rna_id")
        sequence = record.get("sequence")
        if not isinstance(record_id, str) or not record_id:
            raise BaselineEvaluationError(f"{context}.record_id must be a non-empty string")
        if not isinstance(rna_id, str) or not rna_id:
            raise BaselineEvaluationError(f"{context}.rna_id must be a non-empty string")
        if not isinstance(sequence, str) or not sequence:
            raise BaselineEvaluationError(f"{context}.sequence must be a non-empty string")

        source_model = _require_mapping(record.get("source_model"), f"{context}.source_model")
        model_name = source_model.get("name")
        if model_name not in EXPECTED_MODELS:
            raise BaselineEvaluationError(f"{context} has unexpected source model {model_name!r}")

        metadata = _require_mapping(record.get("metadata"), f"{context}.metadata")
        if metadata.get("sequence_length") != len(sequence):
            raise BaselineEvaluationError(f"{context} sequence_length does not match sequence")

        gt_pairs = _validate_structure(
            record.get("ground_truth_structure"),
            sequence=sequence,
            context=f"{context}.ground_truth_structure",
        )
        predicted_pairs = _validate_structure(
            record.get("predicted_structure"),
            sequence=sequence,
            context=f"{context}.predicted_structure",
        )

        record_ids.append(record_id)
        model_counts[model_name] += 1
        records_by_rna[rna_id].append(record)
        canonical_pairs[record_id] = (predicted_pairs, gt_pairs)

    duplicates = sorted(record_id for record_id, count in Counter(record_ids).items() if count > 1)
    if duplicates:
        raise BaselineEvaluationError(f"duplicate record_id values: {duplicates[:3]}")
    if len(records_by_rna) != EXPECTED_RNAS:
        raise BaselineEvaluationError(
            f"expected {EXPECTED_RNAS} unique rna_id values, observed {len(records_by_rna)}"
        )
    expected_model_counts = Counter({model: EXPECTED_RNAS for model in EXPECTED_MODELS})
    if model_counts != expected_model_counts:
        raise BaselineEvaluationError(
            f"unexpected records per model: {dict(sorted(model_counts.items()))}"
        )

    expected_model_set = set(EXPECTED_MODELS)
    for rna_id, rna_records in records_by_rna.items():
        if len(rna_records) != len(EXPECTED_MODELS):
            raise BaselineEvaluationError(
                f"RNA {rna_id!r} has {len(rna_records)} records instead of 3"
            )
        rna_models = [record["source_model"]["name"] for record in rna_records]
        if set(rna_models) != expected_model_set or len(set(rna_models)) != len(EXPECTED_MODELS):
            raise BaselineEvaluationError(
                f"RNA {rna_id!r} does not have exactly one record per expected model"
            )
        sequences = {record["sequence"] for record in rna_records}
        if len(sequences) != 1:
            raise BaselineEvaluationError(f"RNA {rna_id!r} has inconsistent sequences")
        gt_pair_sets = {
            canonical_pairs[record["record_id"]][1]
            for record in rna_records
        }
        if len(gt_pair_sets) != 1:
            raise BaselineEvaluationError(
                f"RNA {rna_id!r} has inconsistent ground-truth pairs"
            )

    return {
        "record_count_exact": True,
        "unique_rna_count_exact": True,
        "records_per_model_exact": True,
        "three_predictors_per_rna": True,
        "record_ids_unique": True,
        "sequences_consistent_per_rna": True,
        "ground_truth_pairs_consistent_per_rna": True,
        "all_pairs_canonical_and_valid": True,
        "canonical_pairs": canonical_pairs,
    }


def _evaluate_record(
    record: dict[str, Any],
    canonical_pairs: dict[str, tuple[tuple[Pair, ...], tuple[Pair, ...]]],
) -> PairEvaluation:
    record_id = record["record_id"]
    predicted_pairs, gt_pairs = canonical_pairs[record_id]
    predicted_structure = record["predicted_structure"]
    gt_structure = record["ground_truth_structure"]

    evaluation = evaluate_pairs(
        predicted_pairs,
        gt_pairs,
        sequence=record["sequence"],
        prediction_allow_multiple_partners=predicted_structure["allow_multiple_partners"],
        ground_truth_allow_multiple_partners=gt_structure["allow_multiple_partners"],
    )
    if evaluation.tp + evaluation.fn != len(gt_pairs):
        raise BaselineEvaluationError(f"{record_id}: tp + fn != gt_pair_count")
    if evaluation.tp + evaluation.fp != len(predicted_pairs):
        raise BaselineEvaluationError(f"{record_id}: tp + fp != predicted_pair_count")

    tp_set = set(evaluation.true_positive_pairs)
    fp_set = set(evaluation.false_positive_pairs)
    fn_set = set(evaluation.false_negative_pairs)
    if tp_set & fp_set or tp_set & fn_set or fp_set & fn_set:
        raise BaselineEvaluationError(f"{record_id}: TP, FP, and FN partitions overlap")
    if tp_set | fp_set != set(predicted_pairs):
        raise BaselineEvaluationError(f"{record_id}: TP and FP do not partition prediction")
    if tp_set | fn_set != set(gt_pairs):
        raise BaselineEvaluationError(f"{record_id}: TP and FN do not partition ground truth")

    metric_values = (evaluation.precision, evaluation.recall, evaluation.f1)
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in metric_values):
        raise BaselineEvaluationError(f"{record_id}: metric is non-finite or outside [0, 1]")
    return evaluation


def _warning_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_warning_counts: Counter[str] = Counter()
    for record in records:
        warnings = record["metadata"].get("warnings", [])
        if not isinstance(warnings, list) or any(not isinstance(item, str) for item in warnings):
            raise BaselineEvaluationError("metadata.warnings must be a list of strings")
        normalized_warning_counts.update(warnings)
    return {
        "normalized_input_warning_counts": dict(sorted(normalized_warning_counts.items())),
        "pair_score_records_ignored": sum(record.get("pair_scores") is not None for record in records),
        "notes": [
            "Historical model versions and decoder settings remain unknown where flagged by normalization.",
            "Pair-score sidecars were not opened or used; historical predicted_structure.pairs were evaluated.",
            "MCC and pseudoknot-specific metrics remain deferred by protocol.",
        ],
    }


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    args = _parse_args()
    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    input_sha256 = _sha256_file(input_path)
    records = _load_records(input_path)

    invariant_checks = _validate_dataset(records)
    canonical_pairs = invariant_checks.pop("canonical_pairs")

    per_sample_rows: list[dict[str, Any]] = []
    partition_rows: list[dict[str, Any]] = []
    evaluations_by_model: defaultdict[str, list[PairEvaluation]] = defaultdict(list)

    for record in records:
        evaluation = _evaluate_record(record, canonical_pairs)
        record_id = record["record_id"]
        source_model = record["source_model"]["name"]
        predicted_pairs, gt_pairs = canonical_pairs[record_id]
        evaluations_by_model[source_model].append(evaluation)
        per_sample_rows.append(
            {
                "record_id": record_id,
                "rna_id": record["rna_id"],
                "source_model": source_model,
                "sequence_length": len(record["sequence"]),
                "gt_pair_count": len(gt_pairs),
                "predicted_pair_count": len(predicted_pairs),
                **evaluation.as_dict(),
            }
        )
        partition_rows.append(
            {
                "record_id": record_id,
                "rna_id": record["rna_id"],
                "source_model": source_model,
                "true_positive_pairs": [list(pair) for pair in evaluation.true_positive_pairs],
                "false_positive_pairs": [list(pair) for pair in evaluation.false_positive_pairs],
                "false_negative_pairs": [list(pair) for pair in evaluation.false_negative_pairs],
            }
        )

    if len(per_sample_rows) != EXPECTED_RECORDS or len(partition_rows) != EXPECTED_RECORDS:
        raise BaselineEvaluationError("derived output row count does not match expected records")

    summaries_by_model: dict[str, dict[str, int | float]] = {}
    model_summary_rows: list[dict[str, Any]] = []
    for model in EXPECTED_MODELS:
        summary = aggregate_pair_evaluations(evaluations_by_model[model])
        if summary.n_samples != EXPECTED_RNAS:
            raise BaselineEvaluationError(f"{model}: expected 121 evaluated samples")
        summary_dict = summary.as_dict()
        if any(
            not math.isfinite(value) or not 0.0 <= value <= 1.0
            for key, value in summary_dict.items()
            if key.startswith(("macro_", "micro_"))
            or key in {"median_f1", "std_f1", "min_f1", "max_f1"}
        ):
            raise BaselineEvaluationError(f"{model}: invalid aggregate metric")
        summaries_by_model[model] = summary_dict
        model_summary_rows.append({"source_model": model, **summary_dict})

    if _sha256_file(input_path) != input_sha256:
        raise BaselineEvaluationError("normalized input changed during evaluation")

    invariant_checks.update(
        {
            "per_record_count_identities": True,
            "pair_partitions_disjoint_and_complete": True,
            "all_metrics_finite_and_bounded": True,
            "normalized_input_unchanged": True,
        }
    )
    records_by_model = {model: len(evaluations_by_model[model]) for model in EXPECTED_MODELS}
    summary_json = {
        "dataset": DATASET,
        "schema_version": SCHEMA_VERSION,
        "normalized_input_path": str(input_path),
        "normalized_input_sha256": input_sha256,
        "expected_records": EXPECTED_RECORDS,
        "evaluated_records": len(per_sample_rows),
        "unique_rna_ids": len({record["rna_id"] for record in records}),
        "records_by_model": records_by_model,
        "evaluator_definition": {
            "implementation": "rna_ccfa.metrics.evaluate_pairs",
            "pair_representation": "canonical 0-based [i,j] with i < j",
            "pair_equality": "exact",
            "true_positives": "prediction intersection ground_truth",
            "false_positives": "prediction minus ground_truth",
            "false_negatives": "ground_truth minus prediction",
            "macro_metrics": "arithmetic mean of 121 per-sample metric values",
            "micro_metrics": "sum TP/FP/FN over 121 samples before computing metrics",
            "empty_set_convention": (
                "empty prediction and GT yields precision=recall=F1=1; otherwise a zero "
                "precision, recall, or F1 denominator yields 0"
            ),
            "std_f1": "population standard deviation across 121 per-sample F1 values (ddof=0)",
            "pair_scores_used": False,
            "mcc_computed": False,
            "pseudoknot_specific_metrics_computed": False,
        },
        "summaries_by_model": summaries_by_model,
        "invariant_checks": invariant_checks,
        "evaluation_warnings": _warning_summary(records),
        "generated_at_utc": _utc_now(),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "per_sample.csv", PER_SAMPLE_FIELDS, per_sample_rows)
    _write_jsonl(output_dir / "pair_partitions.jsonl", partition_rows)
    _write_csv(output_dir / "summary_by_model.csv", MODEL_SUMMARY_FIELDS, model_summary_rows)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary_json, handle, indent=2, sort_keys=True)
        handle.write("\n")

    if _sha256_file(input_path) != input_sha256:
        raise BaselineEvaluationError("normalized input changed while writing derived outputs")

    print(json.dumps(summary_json, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
