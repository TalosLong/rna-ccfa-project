#!/usr/bin/env python3
"""Run the frozen Phase 2 rule-baseline v1 Legacy121 pilot evaluation."""

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
from rna_ccfa.rule_refinement import PREREGISTERED_CONDITIONS, refine_prediction
from rna_ccfa.structure import Pair, validate_pairs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = "legacy121_v1"
SCHEMA_VERSION = "rna-ccfa.normalized_prediction.v1"
EXPECTED_RECORDS = 363
EXPECTED_RNAS = 121
EXPECTED_MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")
EXPECTED_CONDITIONS = ("ORIGINAL", "R1", "R2", "R3", "R1_R2", "R1_R3")
EXPECTED_ORIGINAL_COUNTS = {
    "rnafold": (1473, 220, 203),
    "petfold": (1463, 241, 213),
    "trrosettarna2_native_ss": (1461, 432, 215),
}
EXPECTED_TRIGGER_COUNTS = {
    "rnafold": {"R1": 13, "R2": 72, "R3": 0, "R1_R2": 85, "R1_R3": 13},
    "petfold": {"R1": 10, "R2": 68, "R3": 0, "R1_R2": 78, "R1_R3": 10},
    "trrosettarna2_native_ss": {
        "R1": 63,
        "R2": 44,
        "R3": 20,
        "R1_R2": 107,
        "R1_R3": 83,
    },
}

PER_SAMPLE_FIELDS = (
    "record_id",
    "rna_id",
    "source_model",
    "condition",
    "sequence_length",
    "gt_pair_count",
    "original_predicted_pair_count",
    "refined_predicted_pair_count",
    "tp_before",
    "fp_before",
    "fn_before",
    "tp",
    "fp",
    "fn",
    "precision",
    "recall",
    "f1",
    "delta_precision",
    "delta_recall",
    "delta_f1",
    "modified_pair_count",
    "beneficial_edit_count",
    "harmful_edit_count",
    "beneficial_edit_fraction",
    "harmful_edit_fraction",
    "correct_pair_preservation_rate",
)

MODEL_SUMMARY_FIELDS = (
    "source_model",
    "condition",
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
    "macro_delta_precision",
    "macro_delta_recall",
    "macro_delta_f1",
    "micro_delta_precision",
    "micro_delta_recall",
    "micro_delta_f1",
    "total_modified_pairs",
    "total_beneficial_edits",
    "total_harmful_edits",
    "pooled_beneficial_edit_fraction",
    "pooled_harmful_edit_fraction",
    "pooled_correct_pair_preservation_rate",
    "n_rnas_modified",
    "fraction_rnas_modified",
    "pilot_outcome",
)


class RuleBaselineEvaluationError(RuntimeError):
    """A frozen input, rule output, or accounting invariant failed."""


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
        default=PROJECT_ROOT / "results/rule_baseline",
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
        raise RuleBaselineEvaluationError(f"normalized input does not exist: {path}")
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise RuleBaselineEvaluationError(f"blank JSONL line {line_number}")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuleBaselineEvaluationError(
                    f"invalid JSON at line {line_number}: {exc}"
                ) from exc
            if not isinstance(record, dict):
                raise RuleBaselineEvaluationError(f"line {line_number} is not an object")
            records.append(record)
    return records


def _require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuleBaselineEvaluationError(f"{context} must be an object")
    return value


def _validated_stored_pairs(
    structure: Any,
    *,
    sequence: str,
    context: str,
) -> tuple[Pair, ...]:
    structure = _require_mapping(structure, context)
    allow_multiple = structure.get("allow_multiple_partners")
    if not isinstance(allow_multiple, bool):
        raise RuleBaselineEvaluationError(f"{context}.allow_multiple_partners must be boolean")
    pairs = structure.get("pairs")
    try:
        canonical = validate_pairs(
            pairs,
            sequence=sequence,
            allow_multiple_partners=allow_multiple,
        )
    except (TypeError, ValueError) as exc:
        raise RuleBaselineEvaluationError(f"{context}.pairs are invalid: {exc}") from exc
    if pairs != [[i, j] for i, j in canonical]:
        raise RuleBaselineEvaluationError(f"{context}.pairs are not stored canonically")
    return tuple(canonical)


def _validate_dataset(
    records: list[dict[str, Any]],
) -> dict[str, tuple[tuple[Pair, ...], tuple[Pair, ...]]]:
    if len(records) != EXPECTED_RECORDS:
        raise RuleBaselineEvaluationError(
            f"expected {EXPECTED_RECORDS} records, observed {len(records)}"
        )
    if tuple(PREREGISTERED_CONDITIONS) != EXPECTED_CONDITIONS:
        raise RuleBaselineEvaluationError(
            f"deployable conditions changed: {PREREGISTERED_CONDITIONS}"
        )

    record_ids: list[str] = []
    model_counts: Counter[str] = Counter()
    records_by_rna: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    pair_map: dict[str, tuple[tuple[Pair, ...], tuple[Pair, ...]]] = {}
    for index, record in enumerate(records, start=1):
        context = f"record {index}"
        if record.get("dataset") != DATASET:
            raise RuleBaselineEvaluationError(f"{context}: unexpected dataset")
        if record.get("schema_version") != SCHEMA_VERSION:
            raise RuleBaselineEvaluationError(f"{context}: unexpected schema version")
        record_id = record.get("record_id")
        rna_id = record.get("rna_id")
        sequence = record.get("sequence")
        if not isinstance(record_id, str) or not record_id:
            raise RuleBaselineEvaluationError(f"{context}: invalid record_id")
        if not isinstance(rna_id, str) or not rna_id:
            raise RuleBaselineEvaluationError(f"{context}: invalid rna_id")
        if not isinstance(sequence, str) or not sequence:
            raise RuleBaselineEvaluationError(f"{context}: invalid sequence")
        metadata = _require_mapping(record.get("metadata"), f"{context}.metadata")
        if metadata.get("sequence_length") != len(sequence):
            raise RuleBaselineEvaluationError(f"{record_id}: sequence length mismatch")
        source_model = _require_mapping(record.get("source_model"), f"{context}.source_model")
        model = source_model.get("name")
        if model not in EXPECTED_MODELS:
            raise RuleBaselineEvaluationError(f"{record_id}: unexpected model {model!r}")

        predicted = _validated_stored_pairs(
            record.get("predicted_structure"),
            sequence=sequence,
            context=f"{record_id}.predicted_structure",
        )
        ground_truth = _validated_stored_pairs(
            record.get("ground_truth_structure"),
            sequence=sequence,
            context=f"{record_id}.ground_truth_structure",
        )
        if record["predicted_structure"]["allow_multiple_partners"]:
            raise RuleBaselineEvaluationError(
                f"{record_id}: deployable prediction cannot allow multiple partners"
            )

        record_ids.append(record_id)
        model_counts[model] += 1
        records_by_rna[rna_id].append(record)
        pair_map[record_id] = (predicted, ground_truth)

    duplicates = sorted(key for key, count in Counter(record_ids).items() if count != 1)
    if duplicates:
        raise RuleBaselineEvaluationError(f"duplicate record IDs: {duplicates[:3]}")
    if model_counts != Counter({model: EXPECTED_RNAS for model in EXPECTED_MODELS}):
        raise RuleBaselineEvaluationError(f"unexpected model counts: {dict(model_counts)}")
    if len(records_by_rna) != EXPECTED_RNAS:
        raise RuleBaselineEvaluationError(
            f"expected {EXPECTED_RNAS} RNA IDs, observed {len(records_by_rna)}"
        )
    for rna_id, group in records_by_rna.items():
        if len(group) != len(EXPECTED_MODELS):
            raise RuleBaselineEvaluationError(f"{rna_id}: expected three model records")
        if {record["source_model"]["name"] for record in group} != set(EXPECTED_MODELS):
            raise RuleBaselineEvaluationError(f"{rna_id}: model coverage mismatch")
        if len({record["sequence"] for record in group}) != 1:
            raise RuleBaselineEvaluationError(f"{rna_id}: sequence mismatch")
        if len({pair_map[record["record_id"]][1] for record in group}) != 1:
            raise RuleBaselineEvaluationError(f"{rna_id}: GT pair mismatch")
    return pair_map


def _evaluate(
    predicted: tuple[Pair, ...],
    ground_truth: tuple[Pair, ...],
    *,
    record: dict[str, Any],
) -> PairEvaluation:
    evaluation = evaluate_pairs(
        predicted,
        ground_truth,
        sequence=record["sequence"],
        prediction_allow_multiple_partners=False,
        ground_truth_allow_multiple_partners=record["ground_truth_structure"][
            "allow_multiple_partners"
        ],
    )
    if evaluation.tp + evaluation.fp != len(predicted):
        raise RuleBaselineEvaluationError(f"{record['record_id']}: TP+FP accounting failed")
    if evaluation.tp + evaluation.fn != len(ground_truth):
        raise RuleBaselineEvaluationError(f"{record['record_id']}: TP+FN accounting failed")
    if any(
        not math.isfinite(value) or not 0.0 <= value <= 1.0
        for value in (evaluation.precision, evaluation.recall, evaluation.f1)
    ):
        raise RuleBaselineEvaluationError(f"{record['record_id']}: invalid metric")
    return evaluation


def _outcome(
    *,
    condition: str,
    modified: int,
    beneficial: int,
    harmful: int,
    macro_delta_f1: float,
    micro_delta_f1: float,
) -> str:
    if condition == "ORIGINAL":
        return "REFERENCE"
    if modified == 0 or beneficial <= harmful:
        return "NO USEFUL SIGNAL"
    if macro_delta_f1 > 0.0 and micro_delta_f1 > 0.0:
        return "USEFUL SIGNAL"
    return "TRADE-OFF"


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
    pair_map = _validate_dataset(records)

    per_sample_rows: list[dict[str, Any]] = []
    edit_rows: list[dict[str, Any]] = []
    evaluations: defaultdict[tuple[str, str], list[PairEvaluation]] = defaultdict(list)
    rows_by_key: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for record in sorted(records, key=lambda item: item["record_id"]):
        record_id = record["record_id"]
        model = record["source_model"]["name"]
        original_pairs, ground_truth = pair_map[record_id]
        before = _evaluate(original_pairs, ground_truth, record=record)
        tp_before = set(before.true_positive_pairs)
        fp_before = set(before.false_positive_pairs)

        for condition in EXPECTED_CONDITIONS:
            refinement = refine_prediction(
                original_pairs,
                sequence=record["sequence"],
                condition=condition,
            )
            if refinement.original_pairs != original_pairs:
                raise RuleBaselineEvaluationError(
                    f"{record_id}/{condition}: original snapshot changed"
                )
            after = _evaluate(refinement.refined_pairs, ground_truth, record=record)
            deleted = {edit.deleted_pair for edit in refinement.edits}
            beneficial = len(deleted & fp_before)
            harmful = len(deleted & tp_before)
            modified = len(deleted)

            identity_checks = (
                beneficial + harmful == modified,
                after.tp == before.tp - harmful,
                after.fp == before.fp - beneficial,
                after.fn == before.fn + harmful,
            )
            if not all(identity_checks):
                raise RuleBaselineEvaluationError(
                    f"{record_id}/{condition}: deletion-only accounting failed: "
                    f"before={(before.tp, before.fp, before.fn)}, "
                    f"after={(after.tp, after.fp, after.fn)}, "
                    f"edits={(modified, beneficial, harmful)}"
                )

            row = {
                "record_id": record_id,
                "rna_id": record["rna_id"],
                "source_model": model,
                "condition": condition,
                "sequence_length": len(record["sequence"]),
                "gt_pair_count": len(ground_truth),
                "original_predicted_pair_count": len(original_pairs),
                "refined_predicted_pair_count": len(refinement.refined_pairs),
                "tp_before": before.tp,
                "fp_before": before.fp,
                "fn_before": before.fn,
                "tp": after.tp,
                "fp": after.fp,
                "fn": after.fn,
                "precision": after.precision,
                "recall": after.recall,
                "f1": after.f1,
                "delta_precision": after.precision - before.precision,
                "delta_recall": after.recall - before.recall,
                "delta_f1": after.f1 - before.f1,
                "modified_pair_count": modified,
                "beneficial_edit_count": beneficial,
                "harmful_edit_count": harmful,
                "beneficial_edit_fraction": beneficial / modified if modified else None,
                "harmful_edit_fraction": harmful / modified if modified else None,
                "correct_pair_preservation_rate": after.tp / before.tp if before.tp else None,
            }
            per_sample_rows.append(row)
            evaluations[(model, condition)].append(after)
            rows_by_key[(model, condition)].append(row)

            for edit in refinement.edits:
                trigger_stem_ids = sorted(
                    {trigger.stem_id for trigger in edit.triggers if trigger.stem_id is not None}
                )
                edit_rows.append(
                    {
                        "record_id": record_id,
                        "rna_id": record["rna_id"],
                        "source_model": model,
                        "condition_id": condition,
                        "rule_id": (
                            edit.triggering_rule_ids[0]
                            if len(edit.triggering_rule_ids) == 1
                            else None
                        ),
                        "triggering_rule_ids": list(edit.triggering_rule_ids),
                        "deleted_pair": list(edit.deleted_pair),
                        "original_pair_state": "present",
                        "new_pair_state": "deleted",
                        "observable_trigger_features": [
                            {
                                "rule_id": trigger.rule_id,
                                "features": trigger.observable_trigger_features,
                            }
                            for trigger in edit.triggers
                        ],
                        "stem_id": trigger_stem_ids[0] if len(trigger_stem_ids) == 1 else None,
                        "pair_confidence": None,
                        "was_tp_before": edit.deleted_pair in tp_before,
                        "was_fp_before": edit.deleted_pair in fp_before,
                        "beneficial_or_harmful": (
                            "beneficial" if edit.deleted_pair in fp_before else "harmful"
                        ),
                    }
                )

    expected_metric_rows = EXPECTED_RECORDS * len(EXPECTED_CONDITIONS)
    if len(per_sample_rows) != expected_metric_rows:
        raise RuleBaselineEvaluationError(
            f"expected {expected_metric_rows} per-sample rows, observed {len(per_sample_rows)}"
        )
    edit_keys = [
        (row["record_id"], row["condition_id"], tuple(row["deleted_pair"]))
        for row in edit_rows
    ]
    duplicate_edit_keys = sorted(
        key for key, count in Counter(edit_keys).items() if count != 1
    )
    if duplicate_edit_keys:
        raise RuleBaselineEvaluationError(
            f"duplicate edit-log keys: {duplicate_edit_keys[:3]}"
        )
    edit_counts_by_record_condition = Counter(
        (row["record_id"], row["condition_id"]) for row in edit_rows
    )
    beneficial_counts_by_record_condition = Counter(
        (row["record_id"], row["condition_id"])
        for row in edit_rows
        if row["beneficial_or_harmful"] == "beneficial"
    )
    harmful_counts_by_record_condition = Counter(
        (row["record_id"], row["condition_id"])
        for row in edit_rows
        if row["beneficial_or_harmful"] == "harmful"
    )
    for row in per_sample_rows:
        key = (row["record_id"], row["condition"])
        if edit_counts_by_record_condition[key] != row["modified_pair_count"]:
            raise RuleBaselineEvaluationError(f"{key}: edit-log count mismatch")
        if beneficial_counts_by_record_condition[key] != row["beneficial_edit_count"]:
            raise RuleBaselineEvaluationError(f"{key}: beneficial edit-log mismatch")
        if harmful_counts_by_record_condition[key] != row["harmful_edit_count"]:
            raise RuleBaselineEvaluationError(f"{key}: harmful edit-log mismatch")

    original_summaries = {
        model: aggregate_pair_evaluations(evaluations[(model, "ORIGINAL")])
        for model in EXPECTED_MODELS
    }
    for model, expected in EXPECTED_ORIGINAL_COUNTS.items():
        observed = original_summaries[model]
        if (observed.sum_tp, observed.sum_fp, observed.sum_fn) != expected:
            raise RuleBaselineEvaluationError(
                f"{model}: frozen Original counts changed from {expected} to "
                f"{(observed.sum_tp, observed.sum_fp, observed.sum_fn)}"
            )

    summary_rows: list[dict[str, Any]] = []
    observed_trigger_counts: dict[str, dict[str, int]] = defaultdict(dict)
    for model in EXPECTED_MODELS:
        original = original_summaries[model]
        for condition in EXPECTED_CONDITIONS:
            group = rows_by_key[(model, condition)]
            summary = aggregate_pair_evaluations(evaluations[(model, condition)])
            if len(group) != EXPECTED_RNAS or summary.n_samples != EXPECTED_RNAS:
                raise RuleBaselineEvaluationError(f"{model}/{condition}: expected 121 rows")
            modified = sum(int(row["modified_pair_count"]) for row in group)
            beneficial = sum(int(row["beneficial_edit_count"]) for row in group)
            harmful = sum(int(row["harmful_edit_count"]) for row in group)
            n_modified = sum(int(row["modified_pair_count"] > 0) for row in group)
            observed_trigger_counts[model][condition] = modified
            macro_delta_precision = summary.macro_precision - original.macro_precision
            macro_delta_recall = summary.macro_recall - original.macro_recall
            macro_delta_f1 = summary.macro_f1 - original.macro_f1
            micro_delta_precision = summary.micro_precision - original.micro_precision
            micro_delta_recall = summary.micro_recall - original.micro_recall
            micro_delta_f1 = summary.micro_f1 - original.micro_f1
            summary_rows.append(
                {
                    "source_model": model,
                    "condition": condition,
                    "n_samples": summary.n_samples,
                    "sum_tp": summary.sum_tp,
                    "sum_fp": summary.sum_fp,
                    "sum_fn": summary.sum_fn,
                    "macro_precision": summary.macro_precision,
                    "macro_recall": summary.macro_recall,
                    "macro_f1": summary.macro_f1,
                    "micro_precision": summary.micro_precision,
                    "micro_recall": summary.micro_recall,
                    "micro_f1": summary.micro_f1,
                    "macro_delta_precision": macro_delta_precision,
                    "macro_delta_recall": macro_delta_recall,
                    "macro_delta_f1": macro_delta_f1,
                    "micro_delta_precision": micro_delta_precision,
                    "micro_delta_recall": micro_delta_recall,
                    "micro_delta_f1": micro_delta_f1,
                    "total_modified_pairs": modified,
                    "total_beneficial_edits": beneficial,
                    "total_harmful_edits": harmful,
                    "pooled_beneficial_edit_fraction": beneficial / modified if modified else None,
                    "pooled_harmful_edit_fraction": harmful / modified if modified else None,
                    "pooled_correct_pair_preservation_rate": (
                        summary.sum_tp / original.sum_tp if original.sum_tp else None
                    ),
                    "n_rnas_modified": n_modified,
                    "fraction_rnas_modified": n_modified / EXPECTED_RNAS,
                    "pilot_outcome": _outcome(
                        condition=condition,
                        modified=modified,
                        beneficial=beneficial,
                        harmful=harmful,
                        macro_delta_f1=macro_delta_f1,
                        micro_delta_f1=micro_delta_f1,
                    ),
                }
            )

    for model, expected_by_condition in EXPECTED_TRIGGER_COUNTS.items():
        observed = {
            condition: observed_trigger_counts[model][condition]
            for condition in expected_by_condition
        }
        if observed != expected_by_condition:
            raise RuleBaselineEvaluationError(
                f"{model}: frozen observable trigger regression failed: "
                f"expected {expected_by_condition}, observed {observed}"
            )
    if observed_trigger_counts["rnafold"]["ORIGINAL"] != 0 or observed_trigger_counts[
        "petfold"
    ]["ORIGINAL"] != 0 or observed_trigger_counts["trrosettarna2_native_ss"][
        "ORIGINAL"
    ] != 0:
        raise RuleBaselineEvaluationError("ORIGINAL condition unexpectedly modified pairs")

    if _sha256_file(input_path) != input_sha256:
        raise RuleBaselineEvaluationError("normalized input changed during evaluation")

    validation_summary = {
        "dataset": DATASET,
        "schema_version": SCHEMA_VERSION,
        "normalized_input_path": str(input_path),
        "normalized_input_sha256": input_sha256,
        "expected_records": EXPECTED_RECORDS,
        "validated_records": len(records),
        "unique_rna_ids": len({record["rna_id"] for record in records}),
        "records_by_model": {
            model: sum(record["source_model"]["name"] == model for record in records)
            for model in EXPECTED_MODELS
        },
        "preregistered_conditions": list(EXPECTED_CONDITIONS),
        "per_sample_metric_rows": len(per_sample_rows),
        "model_condition_summary_rows": len(summary_rows),
        "edit_log_rows": len(edit_rows),
        "observable_trigger_counts_by_model_condition": {
            model: dict(observed_trigger_counts[model]) for model in EXPECTED_MODELS
        },
        "original_counts_by_model": {
            model: {
                "tp": original_summaries[model].sum_tp,
                "fp": original_summaries[model].sum_fp,
                "fn": original_summaries[model].sum_fn,
            }
            for model in EXPECTED_MODELS
        },
        "invariant_checks": {
            "normalized_dataset_invariants_passed": True,
            "only_preregistered_conditions_evaluated": True,
            "all_original_predictions_valid": True,
            "all_post_edit_predictions_valid": True,
            "all_deletions_from_immutable_original_snapshot": True,
            "all_deletions_unique_per_record_condition": True,
            "all_deletion_accounting_identities_passed": True,
            "all_metrics_finite_and_bounded": True,
            "frozen_original_counts_reproduced": True,
            "frozen_observable_trigger_counts_reproduced": True,
            "normalized_input_unchanged": True,
        },
        "null_encoding": {
            "csv": "empty field",
            "json": "null",
            "undefined_when": [
                "edit fractions when modified_pair_count == 0",
                "correct_pair_preservation_rate when TP_before == 0",
            ],
        },
        "evaluation_definition": {
            "implementation": "rna_ccfa.metrics.evaluate_pairs",
            "pair_equality": "exact canonical pair equality",
            "rule_implementation": "rna_ccfa.rule_refinement.refine_prediction",
            "pair_scores_used": False,
            "predictor_inference_run": False,
            "refined_structures_persisted": False,
            "statistical_tests_run": False,
            "pseudoknot_specific_logic_used": False,
        },
        "warnings": [
            "Legacy121 was used for Phase 1 characterization; this is a pilot/feasibility evaluation.",
            "R3 trigger coverage is source-skewed and must not be described as model-agnostic evidence.",
            "Undefined per-sample fractions are not replaced with zero in aggregation.",
        ],
        "generated_at_utc": _utc_now(),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "per_sample_metrics.csv", PER_SAMPLE_FIELDS, per_sample_rows)
    _write_csv(
        output_dir / "model_condition_summary.csv",
        MODEL_SUMMARY_FIELDS,
        summary_rows,
    )
    _write_jsonl(output_dir / "edit_log.jsonl", edit_rows)
    with (output_dir / "validation_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(validation_summary, handle, indent=2, sort_keys=True)
        handle.write("\n")

    if _sha256_file(input_path) != input_sha256:
        raise RuleBaselineEvaluationError("normalized input changed while writing outputs")

    print(json.dumps(validation_summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
