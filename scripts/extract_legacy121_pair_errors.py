#!/usr/bin/env python3
"""Extract frozen pair-level Legacy121 errors from baseline TP/FP/FN partitions."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from rna_ccfa.errors import (
    MissingPairAnnotation,
    WrongPartnerEvent,
    extract_pair_errors,
)
from rna_ccfa.metrics import evaluate_pairs
from rna_ccfa.structure import Pair


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_RECORDS = 363
EXPECTED_SAMPLES_PER_MODEL = 121
EXPECTED_MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")
EXPECTED_COUNTS = {
    "rnafold": {"false_positive_pair_count": 220, "missing_pair_count": 203},
    "petfold": {"false_positive_pair_count": 241, "missing_pair_count": 213},
    "trrosettarna2_native_ss": {
        "false_positive_pair_count": 432,
        "missing_pair_count": 215,
    },
}

PAIR_ERROR_FIELDS = (
    "record_id",
    "rna_id",
    "source_model",
    "error_type",
    "i",
    "j",
    "wrong_partner",
    "wrong_partner_degree",
    "linked_pair_count",
    "linked_pairs",
    "sequence_length",
)

SUMMARY_FIELDS = (
    "source_model",
    "n_samples",
    "missing_pair_count",
    "false_positive_pair_count",
    "wrong_partner_event_count",
    "wrong_partner_degree1_count",
    "wrong_partner_degree2_count",
    "pure_false_positive_count",
    "missing_pairs_linked_to_wrong_partner",
    "pure_missing_pair_count",
    "samples_with_wrong_partner",
)


class PairErrorAnalysisError(RuntimeError):
    """An authoritative baseline or derived pair-error invariant failed."""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    baseline_dir = PROJECT_ROOT / "results/baseline_legacy121_v1"
    parser.add_argument(
        "--pair-partitions",
        type=Path,
        default=baseline_dir / "pair_partitions.jsonl",
    )
    parser.add_argument(
        "--per-sample",
        type=Path,
        default=baseline_dir / "per_sample.csv",
    )
    parser.add_argument(
        "--summary-by-model",
        type=Path,
        default=baseline_dir / "summary_by_model.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "results/error_analysis",
    )
    return parser.parse_args()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise PairErrorAnalysisError(f"required baseline file does not exist: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise PairErrorAnalysisError(f"required baseline file does not exist: {path}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise PairErrorAnalysisError(f"blank JSONL line at {path}:{line_number}")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PairErrorAnalysisError(
                    f"invalid JSON at {path}:{line_number}: {exc}"
                ) from exc
            if not isinstance(row, dict):
                raise PairErrorAnalysisError(f"non-object JSON at {path}:{line_number}")
            rows.append(row)
    return rows


def _pairs(value: Any, *, context: str) -> tuple[Pair, ...]:
    if not isinstance(value, list):
        raise PairErrorAnalysisError(f"{context} must be a JSON pair list")
    pairs: list[Pair] = []
    for index, raw_pair in enumerate(value):
        if (
            not isinstance(raw_pair, list)
            or len(raw_pair) != 2
            or any(isinstance(item, bool) or not isinstance(item, int) for item in raw_pair)
        ):
            raise PairErrorAnalysisError(f"{context}[{index}] is not an integer pair")
        pairs.append((raw_pair[0], raw_pair[1]))
    if tuple(sorted(pairs)) != tuple(pairs) or len(set(pairs)) != len(pairs):
        raise PairErrorAnalysisError(f"{context} is not canonical sorted and unique")
    return tuple(pairs)


def _json_pairs(pairs: tuple[Pair, ...]) -> str:
    return json.dumps([list(pair) for pair in pairs], separators=(",", ":"))


def _validate_baseline_summary(rows: list[dict[str, str]]) -> None:
    if len(rows) != len(EXPECTED_MODELS):
        raise PairErrorAnalysisError("baseline model summary must contain exactly three rows")
    by_model = {row["source_model"]: row for row in rows}
    if set(by_model) != set(EXPECTED_MODELS):
        raise PairErrorAnalysisError("baseline model summary has unexpected models")
    for model in EXPECTED_MODELS:
        row = by_model[model]
        expected = EXPECTED_COUNTS[model]
        if int(row["n_samples"]) != EXPECTED_SAMPLES_PER_MODEL:
            raise PairErrorAnalysisError(f"{model}: frozen n_samples changed")
        if int(row["sum_fp"]) != expected["false_positive_pair_count"]:
            raise PairErrorAnalysisError(f"{model}: frozen FP count changed")
        if int(row["sum_fn"]) != expected["missing_pair_count"]:
            raise PairErrorAnalysisError(f"{model}: frozen FN count changed")


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _validate_reverse_relations(
    events: tuple[WrongPartnerEvent, ...],
    annotations: tuple[MissingPairAnnotation, ...],
) -> None:
    event_by_pair = {event.predicted_pair: event for event in events}
    annotation_by_pair = {annotation.missing_pair: annotation for annotation in annotations}
    event_edge_count = sum(event.wrong_partner_degree for event in events)
    annotation_edge_count = sum(annotation.wrong_partner_degree for annotation in annotations)
    if event_edge_count != annotation_edge_count:
        raise PairErrorAnalysisError("forward and reverse wrong-partner edge counts differ")

    for event in events:
        for missing_pair in event.linked_missing_pairs:
            annotation = annotation_by_pair[missing_pair]
            if event.predicted_pair not in annotation.linked_false_positive_pairs:
                raise PairErrorAnalysisError("wrong-partner reverse link is missing")
    for annotation in annotations:
        for predicted_pair in annotation.linked_false_positive_pairs:
            event = event_by_pair.get(predicted_pair)
            if event is None or annotation.missing_pair not in event.linked_missing_pairs:
                raise PairErrorAnalysisError("missing-pair forward link is missing")


def main() -> int:
    args = _parse_args()
    partitions = _read_jsonl(args.pair_partitions.resolve())
    per_sample_rows = _read_csv(args.per_sample.resolve())
    _validate_baseline_summary(_read_csv(args.summary_by_model.resolve()))

    if len(partitions) != EXPECTED_RECORDS or len(per_sample_rows) != EXPECTED_RECORDS:
        raise PairErrorAnalysisError("authoritative baseline must contain exactly 363 records")

    sample_by_record = {row["record_id"]: row for row in per_sample_rows}
    partition_ids = [row.get("record_id") for row in partitions]
    if len(sample_by_record) != EXPECTED_RECORDS or len(set(partition_ids)) != EXPECTED_RECORDS:
        raise PairErrorAnalysisError("baseline record_id values must be unique")
    if set(partition_ids) != set(sample_by_record):
        raise PairErrorAnalysisError("per-sample and partition record IDs differ")

    model_record_counts: Counter[str] = Counter()
    aggregate_counts: dict[str, Counter[str]] = {
        model: Counter() for model in EXPECTED_MODELS
    }
    samples_with_wrong_partner: dict[str, set[str]] = {
        model: set() for model in EXPECTED_MODELS
    }
    pair_error_rows: list[dict[str, Any]] = []
    event_rows: list[dict[str, Any]] = []

    for partition in sorted(partitions, key=lambda row: row["record_id"]):
        record_id = partition["record_id"]
        sample = sample_by_record[record_id]
        rna_id = partition.get("rna_id")
        source_model = partition.get("source_model")
        if source_model not in EXPECTED_MODELS:
            raise PairErrorAnalysisError(f"{record_id}: unexpected source model")
        if sample["rna_id"] != rna_id or sample["source_model"] != source_model:
            raise PairErrorAnalysisError(f"{record_id}: baseline identity fields disagree")
        sequence_length = int(sample["sequence_length"])
        tp = _pairs(partition.get("true_positive_pairs"), context=f"{record_id}.TP")
        fp = _pairs(partition.get("false_positive_pairs"), context=f"{record_id}.FP")
        fn = _pairs(partition.get("false_negative_pairs"), context=f"{record_id}.FN")
        if set(tp) & set(fp) or set(tp) & set(fn) or set(fp) & set(fn):
            raise PairErrorAnalysisError(f"{record_id}: TP/FP/FN partitions overlap")

        prediction = tuple(sorted((*tp, *fp)))
        ground_truth = tuple(sorted((*tp, *fn)))
        evaluation = evaluate_pairs(
            prediction,
            ground_truth,
            sequence_length=sequence_length,
        )
        if (
            evaluation.true_positive_pairs != tp
            or evaluation.false_positive_pairs != fp
            or evaluation.false_negative_pairs != fn
        ):
            raise PairErrorAnalysisError(f"{record_id}: reconstructed partitions changed")
        if (
            evaluation.tp != int(sample["tp"])
            or evaluation.fp != int(sample["fp"])
            or evaluation.fn != int(sample["fn"])
        ):
            raise PairErrorAnalysisError(f"{record_id}: per-sample counts disagree")

        extraction = extract_pair_errors(
            prediction,
            ground_truth,
            sequence_length=sequence_length,
        )
        if extraction.missing_pairs != fn or extraction.false_positive_pairs != fp:
            raise PairErrorAnalysisError(f"{record_id}: error extractor changed FP/FN")
        _validate_reverse_relations(
            extraction.wrong_partner_events,
            extraction.missing_pair_annotations,
        )

        event_by_pair = {
            event.predicted_pair: event for event in extraction.wrong_partner_events
        }
        annotation_by_pair = {
            annotation.missing_pair: annotation
            for annotation in extraction.missing_pair_annotations
        }
        if len(event_by_pair) != len(extraction.wrong_partner_events):
            raise PairErrorAnalysisError(f"{record_id}: duplicate wrong-partner event")
        if not set(event_by_pair) <= set(fp):
            raise PairErrorAnalysisError(f"{record_id}: wrong-partner event is outside FP")

        model_record_counts[source_model] += 1
        counts = aggregate_counts[source_model]
        counts["missing_pair_count"] += len(fn)
        counts["false_positive_pair_count"] += len(fp)
        counts["wrong_partner_event_count"] += len(event_by_pair)
        counts["pure_false_positive_count"] += len(fp) - len(event_by_pair)
        counts["missing_pairs_linked_to_wrong_partner"] += sum(
            annotation.wrong_partner for annotation in extraction.missing_pair_annotations
        )
        counts["pure_missing_pair_count"] += sum(
            not annotation.wrong_partner for annotation in extraction.missing_pair_annotations
        )
        for event in extraction.wrong_partner_events:
            counts[f"wrong_partner_degree{event.wrong_partner_degree}_count"] += 1
        if extraction.wrong_partner_events:
            samples_with_wrong_partner[source_model].add(record_id)

        for missing_pair in fn:
            annotation = annotation_by_pair[missing_pair]
            pair_error_rows.append(
                {
                    "record_id": record_id,
                    "rna_id": rna_id,
                    "source_model": source_model,
                    "error_type": "missing_pair",
                    "i": missing_pair[0],
                    "j": missing_pair[1],
                    "wrong_partner": str(annotation.wrong_partner).lower(),
                    "wrong_partner_degree": annotation.wrong_partner_degree,
                    "linked_pair_count": len(annotation.linked_false_positive_pairs),
                    "linked_pairs": _json_pairs(annotation.linked_false_positive_pairs),
                    "sequence_length": sequence_length,
                }
            )
        for false_positive_pair in fp:
            event = event_by_pair.get(false_positive_pair)
            linked_pairs = event.linked_missing_pairs if event else ()
            pair_error_rows.append(
                {
                    "record_id": record_id,
                    "rna_id": rna_id,
                    "source_model": source_model,
                    "error_type": "false_positive_pair",
                    "i": false_positive_pair[0],
                    "j": false_positive_pair[1],
                    "wrong_partner": str(event is not None).lower(),
                    "wrong_partner_degree": event.wrong_partner_degree if event else 0,
                    "linked_pair_count": len(linked_pairs),
                    "linked_pairs": _json_pairs(linked_pairs),
                    "sequence_length": sequence_length,
                }
            )
        for event in extraction.wrong_partner_events:
            event_rows.append(
                {
                    "record_id": record_id,
                    "rna_id": rna_id,
                    "source_model": source_model,
                    **event.as_dict(),
                }
            )

    expected_model_records = Counter(
        {model: EXPECTED_SAMPLES_PER_MODEL for model in EXPECTED_MODELS}
    )
    if model_record_counts != expected_model_records:
        raise PairErrorAnalysisError(
            f"unexpected records by model: {dict(sorted(model_record_counts.items()))}"
        )

    summary_rows: list[dict[str, Any]] = []
    for model in EXPECTED_MODELS:
        counts = aggregate_counts[model]
        for field, expected in EXPECTED_COUNTS[model].items():
            if counts[field] != expected:
                raise PairErrorAnalysisError(
                    f"{model}: expected {field}={expected}, observed {counts[field]}"
                )
        if (
            counts["wrong_partner_event_count"]
            + counts["pure_false_positive_count"]
            != counts["false_positive_pair_count"]
        ):
            raise PairErrorAnalysisError(f"{model}: wrong-partner events do not partition FP")
        if (
            counts["missing_pairs_linked_to_wrong_partner"]
            + counts["pure_missing_pair_count"]
            != counts["missing_pair_count"]
        ):
            raise PairErrorAnalysisError(f"{model}: reverse annotations do not partition FN")
        if (
            counts["wrong_partner_degree1_count"]
            + counts["wrong_partner_degree2_count"]
            != counts["wrong_partner_event_count"]
        ):
            raise PairErrorAnalysisError(f"{model}: wrong-partner degrees do not partition events")
        summary_rows.append(
            {
                "source_model": model,
                "n_samples": model_record_counts[model],
                **{field: counts[field] for field in SUMMARY_FIELDS[2:-1]},
                "samples_with_wrong_partner": len(samples_with_wrong_partner[model]),
            }
        )

    expected_error_rows = sum(
        values["missing_pair_count"] + values["false_positive_pair_count"]
        for values in EXPECTED_COUNTS.values()
    )
    if len(pair_error_rows) != expected_error_rows:
        raise PairErrorAnalysisError(
            f"expected {expected_error_rows} pair-error rows, observed {len(pair_error_rows)}"
        )
    if len(event_rows) != sum(
        row["wrong_partner_event_count"] for row in summary_rows
    ):
        raise PairErrorAnalysisError("wrong-partner JSONL row count disagrees with summary")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "pair_errors.csv", PAIR_ERROR_FIELDS, pair_error_rows)
    _write_jsonl(output_dir / "wrong_partner_events.jsonl", event_rows)
    _write_csv(
        output_dir / "pair_error_summary_by_model.csv",
        SUMMARY_FIELDS,
        summary_rows,
    )

    print(
        json.dumps(
            {
                "pair_error_rows": len(pair_error_rows),
                "wrong_partner_events": len(event_rows),
                "summary_by_model": summary_rows,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
