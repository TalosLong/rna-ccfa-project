#!/usr/bin/env python3
"""Build descriptive strict-stem inventories from normalized Legacy121 records."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from rna_ccfa.stems import StemExtraction, extract_stems_and_singletons, summarize_stem_lengths
from rna_ccfa.structure import Pair, validate_pairs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NORMALIZED_SCHEMA = "rna-ccfa.normalized_prediction.v1"
DATASET = "legacy121_v1"
EXPECTED_RECORDS = 363
EXPECTED_RNAS = 121
EXPECTED_MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")

INVENTORY_FIELDS = (
    "record_id",
    "rna_id",
    "source_model",
    "structure_role",
    "pair_count",
    "strict_stem_count",
    "stem_pair_count",
    "singleton_pair_count",
    "mean_stem_length",
    "median_stem_length",
    "max_stem_length",
    "stem_lengths",
    "source_record_ids",
)

SUMMARY_FIELDS = (
    "structure_role",
    "source_model",
    "n_structures",
    "total_pairs",
    "total_strict_stems",
    "total_stem_pairs",
    "total_singleton_pairs",
    "fraction_pairs_in_stems",
    "mean_stem_length",
    "median_stem_length",
    "max_stem_length",
)


class StemInventoryError(RuntimeError):
    """A normalized input or strict-stem inventory invariant failed."""


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
        default=PROJECT_ROOT / "results/error_analysis",
    )
    return parser.parse_args()


def _load_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise StemInventoryError(f"normalized input does not exist: {path}")
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise StemInventoryError(f"blank line at normalized input line {line_number}")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise StemInventoryError(f"invalid JSON at line {line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise StemInventoryError(f"line {line_number} is not a JSON object")
            records.append(record)
    return records


def _canonical_structure(
    structure: Any,
    *,
    sequence: str,
    context: str,
) -> tuple[Pair, ...]:
    if not isinstance(structure, dict):
        raise StemInventoryError(f"{context} must be an object")
    pairs = structure.get("pairs")
    allow_multiple_partners = structure.get("allow_multiple_partners")
    if not isinstance(allow_multiple_partners, bool):
        raise StemInventoryError(f"{context}.allow_multiple_partners must be boolean")
    try:
        canonical = tuple(
            validate_pairs(
                pairs,
                sequence=sequence,
                allow_multiple_partners=allow_multiple_partners,
            )
        )
    except (TypeError, ValueError) as exc:
        raise StemInventoryError(f"{context}.pairs failed canonical validation: {exc}") from exc
    if pairs != [list(pair) for pair in canonical]:
        raise StemInventoryError(f"{context}.pairs are not canonical sorted pairs")
    return canonical


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _length_stats(extraction: StemExtraction) -> dict[str, float | int]:
    return summarize_stem_lengths([extraction])


def _inventory_row(
    *,
    record_id: str,
    rna_id: str,
    source_model: str,
    structure_role: str,
    extraction: StemExtraction,
    source_record_ids: list[str],
) -> dict[str, Any]:
    lengths = _length_stats(extraction)
    stem_pair_count = sum(stem.n_pairs for stem in extraction.stems)
    return {
        "record_id": record_id,
        "rna_id": rna_id,
        "source_model": source_model,
        "structure_role": structure_role,
        "pair_count": extraction.total_pair_count,
        "strict_stem_count": len(extraction.stems),
        "stem_pair_count": stem_pair_count,
        "singleton_pair_count": len(extraction.singleton_pairs),
        "mean_stem_length": lengths["mean_stem_length"],
        "median_stem_length": lengths["median_stem_length"],
        "max_stem_length": lengths["max_stem_length"],
        "stem_lengths": json.dumps(
            [stem.n_pairs for stem in extraction.stems], separators=(",", ":")
        ),
        "source_record_ids": json.dumps(source_record_ids, separators=(",", ":")),
    }


def _summary_row(
    *,
    structure_role: str,
    source_model: str,
    rows: list[dict[str, Any]],
    extractions: list[StemExtraction],
) -> dict[str, Any]:
    total_pairs = sum(int(row["pair_count"]) for row in rows)
    total_stems = sum(int(row["strict_stem_count"]) for row in rows)
    total_stem_pairs = sum(int(row["stem_pair_count"]) for row in rows)
    total_singletons = sum(int(row["singleton_pair_count"]) for row in rows)
    if total_stem_pairs + total_singletons != total_pairs:
        raise StemInventoryError(f"{source_model}: summary pair accounting failed")
    lengths = summarize_stem_lengths(extractions)
    return {
        "structure_role": structure_role,
        "source_model": source_model,
        "n_structures": len(rows),
        "total_pairs": total_pairs,
        "total_strict_stems": total_stems,
        "total_stem_pairs": total_stem_pairs,
        "total_singleton_pairs": total_singletons,
        "fraction_pairs_in_stems": total_stem_pairs / total_pairs if total_pairs else 0.0,
        **lengths,
    }


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = _parse_args()
    records = _load_records(args.input.resolve())
    if len(records) != EXPECTED_RECORDS:
        raise StemInventoryError(f"expected {EXPECTED_RECORDS} records, observed {len(records)}")

    record_ids = [record.get("record_id") for record in records]
    if any(not isinstance(record_id, str) or not record_id for record_id in record_ids):
        raise StemInventoryError("all records require a non-empty record_id")
    if len(set(record_ids)) != EXPECTED_RECORDS:
        raise StemInventoryError("normalized record_id values must be unique")

    records_by_rna: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    parsed: dict[str, dict[str, Any]] = {}
    model_counts: Counter[str] = Counter()
    for index, record in enumerate(records, start=1):
        context = f"record {index}"
        if record.get("dataset") != DATASET or record.get("schema_version") != NORMALIZED_SCHEMA:
            raise StemInventoryError(f"{context}: unexpected dataset or schema_version")
        rna_id = record.get("rna_id")
        sequence = record.get("sequence")
        if not isinstance(rna_id, str) or not rna_id or not isinstance(sequence, str) or not sequence:
            raise StemInventoryError(f"{context}: invalid rna_id or sequence")
        source_model = record.get("source_model")
        if not isinstance(source_model, dict) or source_model.get("name") not in EXPECTED_MODELS:
            raise StemInventoryError(f"{context}: unexpected source model")
        model = source_model["name"]
        metadata = record.get("metadata")
        if not isinstance(metadata, dict) or metadata.get("sequence_length") != len(sequence):
            raise StemInventoryError(f"{context}: sequence length metadata mismatch")
        gt_pairs = _canonical_structure(
            record.get("ground_truth_structure"),
            sequence=sequence,
            context=f"{context}.ground_truth_structure",
        )
        predicted_pairs = _canonical_structure(
            record.get("predicted_structure"),
            sequence=sequence,
            context=f"{context}.predicted_structure",
        )
        record_id = record["record_id"]
        parsed[record_id] = {
            "record": record,
            "rna_id": rna_id,
            "sequence": sequence,
            "source_model": model,
            "gt_pairs": gt_pairs,
            "predicted_pairs": predicted_pairs,
        }
        records_by_rna[rna_id].append(parsed[record_id])
        model_counts[model] += 1

    if len(records_by_rna) != EXPECTED_RNAS:
        raise StemInventoryError(f"expected {EXPECTED_RNAS} RNAs, observed {len(records_by_rna)}")
    if model_counts != Counter({model: EXPECTED_RNAS for model in EXPECTED_MODELS}):
        raise StemInventoryError(f"unexpected model counts: {dict(model_counts)}")

    inventory_rows: list[dict[str, Any]] = []
    grouped_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    grouped_extractions: dict[tuple[str, str], list[StemExtraction]] = defaultdict(list)
    for rna_id in sorted(records_by_rna):
        rna_records = sorted(records_by_rna[rna_id], key=lambda item: item["record"]["record_id"])
        if len(rna_records) != len(EXPECTED_MODELS):
            raise StemInventoryError(f"{rna_id}: expected three predictor records")
        sequences = {item["sequence"] for item in rna_records}
        gt_sets = {item["gt_pairs"] for item in rna_records}
        if len(sequences) != 1 or len(gt_sets) != 1:
            raise StemInventoryError(f"{rna_id}: sequence or GT differs across predictors")

        first = rna_records[0]
        gt_allow_multiple = first["record"]["ground_truth_structure"]["allow_multiple_partners"]
        gt_extraction = extract_stems_and_singletons(
            first["gt_pairs"],
            sequence=first["sequence"],
            allow_multiple_partners=gt_allow_multiple,
        )
        gt_record_id = f"{DATASET}__{_slug(rna_id)}__legacy_gt__shared_inventory_v1"
        gt_source_ids = [item["record"]["record_id"] for item in rna_records]
        gt_row = _inventory_row(
            record_id=gt_record_id,
            rna_id=rna_id,
            source_model="ground_truth",
            structure_role="ground_truth",
            extraction=gt_extraction,
            source_record_ids=gt_source_ids,
        )
        inventory_rows.append(gt_row)
        grouped_rows[("ground_truth", "ground_truth")].append(gt_row)
        grouped_extractions[("ground_truth", "ground_truth")].append(gt_extraction)

        for item in rna_records:
            record = item["record"]
            structure = record["predicted_structure"]
            extraction = extract_stems_and_singletons(
                item["predicted_pairs"],
                sequence=item["sequence"],
                allow_multiple_partners=structure["allow_multiple_partners"],
            )
            if (
                sum(stem.n_pairs for stem in extraction.stems)
                + len(extraction.singleton_pairs)
                != len(item["predicted_pairs"])
            ):
                raise StemInventoryError(f"{record['record_id']}: pair accounting failed")
            row = _inventory_row(
                record_id=record["record_id"],
                rna_id=rna_id,
                source_model=item["source_model"],
                structure_role="prediction",
                extraction=extraction,
                source_record_ids=[record["record_id"]],
            )
            inventory_rows.append(row)
            grouped_rows[("prediction", item["source_model"])].append(row)
            grouped_extractions[("prediction", item["source_model"])].append(extraction)

    if len(inventory_rows) != EXPECTED_RNAS + EXPECTED_RECORDS:
        raise StemInventoryError("unexpected stem inventory row count")

    summary_rows = [
        _summary_row(
            structure_role=role,
            source_model=model,
            rows=grouped_rows[(role, model)],
            extractions=grouped_extractions[(role, model)],
        )
        for role, model in (
            ("ground_truth", "ground_truth"),
            *(('prediction', model) for model in EXPECTED_MODELS),
        )
    ]
    if any(row["n_structures"] != EXPECTED_RNAS for row in summary_rows):
        raise StemInventoryError("each inventory summary group must contain 121 structures")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "stem_inventory_by_record.csv", INVENTORY_FIELDS, inventory_rows)
    _write_csv(output_dir / "stem_inventory_summary.csv", SUMMARY_FIELDS, summary_rows)
    print(json.dumps({"inventory_rows": len(inventory_rows), "summary_rows": summary_rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
