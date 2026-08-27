#!/usr/bin/env python3
"""Normalize frozen Legacy121 v1 historical predictions into schema-v1 JSONL."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np

from rna_ccfa.normalization import (
    SCHEMA_VERSION,
    SCORE_SYMMETRY_ATOL,
    NormalizationError,
    ScoreNormalizationStats,
    make_record_id,
    normalize_probability_matrix_diagonal,
    sha256_file,
    validate_normalized_probability_matrix,
    validate_normalized_sequence,
)
from rna_ccfa.structure import (
    parse_extended_dot_bracket,
    parse_standard_dot_bracket,
    validate_pairs,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = "legacy121_v1"
GROUND_TRUTH_LABEL = "legacy_gt"
RUN_ID = "historical_legacy121_v1"
EXPECTED_RNAS = 121
EXPECTED_RECORDS = 363
SOURCE_SCORE_KEY = "ss"
NORMALIZED_SCORE_KEY = "pair_scores"


@dataclass(frozen=True, slots=True)
class SourceSpec:
    name: str
    label: str
    manifest_path_field: str
    trrna2_scores: bool = False


SOURCE_SPECS = (
    SourceSpec("rnafold", "rnafold_historical", "rnafold_prediction_path"),
    SourceSpec("petfold", "petfold_historical", "petfold_prediction_path"),
    SourceSpec(
        "trrosettarna2_native_ss",
        "trrna2_native_ss_historical",
        "trrna2_prediction_path",
        trrna2_scores=True,
    ),
)

AUDIT_FIELDS = [
    "record_id",
    "rna_id",
    "source_model",
    "status",
    "sequence_length",
    "gt_pair_count",
    "predicted_pair_count",
    "pair_scores_available",
    "raw_pair_score_path",
    "raw_pair_score_sha256",
    "raw_pair_score_sha256_after",
    "raw_pair_score_unchanged",
    "normalized_pair_score_path",
    "normalized_pair_score_sha256",
    "normalized_pair_score_size_bytes",
    "score_shape",
    "score_dtype",
    "diagonal_nonzero_count_before",
    "diagonal_min_before",
    "diagonal_max_before",
    "max_asymmetry_before",
    "min_score_before",
    "max_score_before",
    "diagonal_nonzero_count_after",
    "max_asymmetry_after",
    "min_score_after",
    "max_score_after",
    "max_off_diagonal_absolute_change",
    "warnings",
    "failure_reason",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "manifests/legacy121_v1.csv",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "normalized/legacy121_v1",
    )
    parser.add_argument(
        "--audit-output",
        type=Path,
        default=PROJECT_ROOT
        / "results/normalization/legacy121_v1_normalization_audit.csv",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=PROJECT_ROOT / "results/normalization/legacy121_v1_summary.json",
    )
    return parser.parse_args()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_RNAS:
        raise NormalizationError(
            f"frozen manifest must contain {EXPECTED_RNAS} rows, observed {len(rows)}"
        )
    rna_ids = [row["rna_id"] for row in rows]
    if len(set(rna_ids)) != EXPECTED_RNAS:
        raise NormalizationError("frozen manifest contains duplicate rna_id values")
    if any(row.get("validation_status") != "valid" for row in rows):
        raise NormalizationError("frozen manifest contains a non-valid row")
    return rows


def _read_fasta(path: Path, expected_id: str) -> tuple[str, str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2 or not lines[0].startswith(">"):
        raise NormalizationError(f"invalid one-record FASTA: {path}")
    if any(line.startswith(">") for line in lines[1:]):
        raise NormalizationError(f"multiple FASTA records are not allowed: {path}")
    header_id = lines[0][1:].split()[0]
    if header_id != expected_id:
        raise NormalizationError(
            f"FASTA header {header_id!r} does not match manifest rna_id {expected_id!r}"
        )
    raw_sequence = "".join(lines[1:])
    normalized_sequence = raw_sequence.upper()
    validate_normalized_sequence(normalized_sequence)
    return raw_sequence, normalized_sequence


def _read_single_line_structure(path: Path) -> str:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise NormalizationError(
            f"expected one structure line in {path}, observed {len(lines)}"
        )
    return lines[0]


def _read_trrna2_structure(path: Path, expected_id: str) -> str:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 2 or not lines[0].startswith(">"):
        raise NormalizationError(f"invalid historical trRosettaRNA2 DBN layout: {path}")
    header_id = lines[0][1:].split()[0]
    if header_id != expected_id:
        raise NormalizationError(
            f"DBN header {header_id!r} does not match manifest rna_id {expected_id!r}"
        )
    return lines[1]


def _raw_file(role: str, path: Path, hash_cache: dict[Path, str]) -> dict[str, str]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise NormalizationError(f"missing raw {role} file: {resolved}")
    if resolved not in hash_cache:
        hash_cache[resolved] = sha256_file(resolved)
    return {"role": role, "path": str(resolved), "sha256": hash_cache[resolved]}


def _pairs_json(pairs: list[tuple[int, int]]) -> list[list[int]]:
    return [[i, j] for i, j in pairs]


def _source_model(spec: SourceSpec) -> dict[str, Any]:
    parameters: dict[str, Any] = {"historical_run_parameters": "UNKNOWN"}
    if spec.name == "petfold":
        parameters["historical_alignment_input"] = "UNKNOWN"
    if spec.trrna2_scores:
        parameters.update(
            {
                "historical_checkpoint_identity": "UNKNOWN",
                "historical_score_array_key": SOURCE_SCORE_KEY,
            }
        )
    decoder_parameters: dict[str, Any] = {"settings": "UNKNOWN"}
    if spec.trrna2_scores:
        decoder_parameters.update(
            {
                "structure_source": "historical_dbn",
                "score_matrix_redecoded": False,
            }
        )
    return {
        "name": spec.name,
        "version": None,
        "checkpoint_id": None,
        "checkpoint_sha256": None,
        "run_id": RUN_ID,
        "input_mode": "unknown",
        "parameters": parameters,
        "decoder": {
            "name": "historical_output",
            "version": None,
            "parameters": decoder_parameters,
        },
    }


def _base_transformations(raw_sequence: str) -> list[dict[str, Any]]:
    return [
        {
            "name": "normalize_sequence_case",
            "version": "1",
            "parameters": {
                "from": "lowercase",
                "to": "uppercase",
                "changed": raw_sequence != raw_sequence.upper(),
            },
            "input_roles": ["sequence"],
        },
        {
            "name": "parse_extended_dot_bracket_to_canonical_pairs",
            "version": "1",
            "parameters": {"coordinate_system": "zero_based", "preserve_crossings": True},
            "input_roles": ["ground_truth"],
        },
        {
            "name": "parse_standard_dot_bracket_to_canonical_pairs",
            "version": "1",
            "parameters": {"coordinate_system": "zero_based"},
            "input_roles": ["prediction"],
        },
    ]


def _score_transformation(stats: ScoreNormalizationStats) -> dict[str, Any]:
    return {
        "name": "set_diagonal_to_zero",
        "version": "1",
        "parameters": {
            "reason": "self-pair scores are invalid under normalized schema v1",
            "diagonal_nonzero_count_before": stats.diagonal_nonzero_count_before,
            "diagonal_min_before": stats.diagonal_min_before,
            "diagonal_max_before": stats.diagonal_max_before,
            "max_asymmetry_before": stats.max_asymmetry_before,
            "min_score_before": stats.min_score_before,
            "max_score_before": stats.max_score_before,
            "symmetry_atol": SCORE_SYMMETRY_ATOL,
            "max_off_diagonal_absolute_change": stats.max_off_diagonal_absolute_change,
        },
        "input_roles": ["pair_scores"],
    }


def _record_warnings(
    *, raw_sequence: str, spec: SourceSpec, petfold_alias_applied: bool
) -> list[str]:
    warnings = [
        "historical_model_version_unknown",
        "historical_output_unknown_decoder_settings",
        "family_split_metadata_unavailable",
    ]
    if raw_sequence != raw_sequence.upper():
        warnings.append("raw_sequence_lowercase")
    if spec.name == "petfold":
        warnings.append("petfold_historical_alignment_input_unknown")
        if petfold_alias_applied:
            warnings.append("petfold_alias_applied")
    if spec.trrna2_scores:
        warnings.append("trrna2_historical_checkpoint_identity_unknown")
    return sorted(warnings)


def _empty_audit_row(record_id: str, rna_id: str, source_model: str) -> dict[str, Any]:
    row: dict[str, Any] = {field: "" for field in AUDIT_FIELDS}
    row.update(
        {
            "record_id": record_id,
            "rna_id": rna_id,
            "source_model": source_model,
            "status": "invalid",
            "pair_scores_available": "false",
        }
    )
    return row


def _validate_record_contract(record: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "record_id",
        "dataset",
        "rna_id",
        "sequence",
        "ground_truth_structure",
        "source_model",
        "predicted_structure",
        "pair_scores",
        "provenance",
        "metadata",
    }
    missing = sorted(required - record.keys())
    if missing:
        raise NormalizationError(f"normalized record is missing required fields: {missing}")
    if record["schema_version"] != SCHEMA_VERSION:
        raise NormalizationError(f"unexpected schema version {record['schema_version']!r}")
    if record["dataset"] != DATASET:
        raise NormalizationError(f"unexpected dataset {record['dataset']!r}")

    sequence = record["sequence"]
    validate_normalized_sequence(sequence)
    length = len(sequence)
    if record["metadata"].get("sequence_length") != length:
        raise NormalizationError("metadata.sequence_length does not match normalized sequence")
    for field in ("ground_truth_structure", "predicted_structure"):
        structure = record[field]
        if not isinstance(structure.get("source_value"), str):
            raise NormalizationError(f"{field}.source_value must be a string")
        if len(structure["source_value"]) != length:
            raise NormalizationError(f"{field}.source_value length does not match sequence")
        canonical = validate_pairs(
            structure.get("pairs", []),
            sequence_length=length,
            allow_multiple_partners=bool(structure.get("allow_multiple_partners", False)),
        )
        if _pairs_json(canonical) != structure.get("pairs"):
            raise NormalizationError(f"{field}.pairs is not canonical")

    provenance = record["provenance"]
    if not provenance.get("raw_files"):
        raise NormalizationError("provenance.raw_files is empty")
    for raw_file in provenance["raw_files"]:
        if not all(raw_file.get(field) for field in ("role", "path", "sha256")):
            raise NormalizationError("provenance contains an incomplete raw-file descriptor")


def _write_normalized_sidecar(
    *,
    raw_path: Path,
    output_root: Path,
    record_id: str,
    expected_length: int,
    hash_cache: dict[Path, str],
) -> tuple[dict[str, Any], ScoreNormalizationStats, dict[str, Any]]:
    resolved_raw = raw_path.resolve()
    raw_hash_before = hash_cache.get(resolved_raw) or sha256_file(resolved_raw)
    hash_cache[resolved_raw] = raw_hash_before

    with np.load(resolved_raw, allow_pickle=False) as archive:
        if SOURCE_SCORE_KEY not in archive.files:
            raise NormalizationError(
                f"raw score NPZ {resolved_raw} lacks array key {SOURCE_SCORE_KEY!r}"
            )
        raw_matrix = np.array(archive[SOURCE_SCORE_KEY], copy=True)

    normalized, stats = normalize_probability_matrix_diagonal(
        raw_matrix,
        expected_length=expected_length,
    )
    if stats.max_off_diagonal_absolute_change != 0.0:
        raise NormalizationError("mandatory off-diagonal zero-change acceptance failed")

    relative_path = PurePosixPath("pair_scores") / f"{record_id}.npz"
    sidecar_path = output_root / Path(relative_path)
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(sidecar_path, **{NORMALIZED_SCORE_KEY: normalized})

    normalized_hash = sha256_file(sidecar_path)
    with np.load(sidecar_path, allow_pickle=False) as archive:
        if archive.files != [NORMALIZED_SCORE_KEY]:
            raise NormalizationError(
                f"normalized sidecar has unexpected keys {archive.files!r}"
            )
        reloaded = np.array(archive[NORMALIZED_SCORE_KEY], copy=True)
    validate_normalized_probability_matrix(reloaded, expected_length=expected_length)
    if reloaded.dtype != raw_matrix.dtype:
        raise NormalizationError(
            f"sidecar dtype changed from {raw_matrix.dtype} to {reloaded.dtype}"
        )
    off_diagonal = ~np.eye(expected_length, dtype=bool)
    if not np.array_equal(reloaded[off_diagonal], raw_matrix[off_diagonal]):
        raise NormalizationError("sidecar off-diagonal values differ from raw matrix")

    raw_hash_after = sha256_file(resolved_raw)
    if raw_hash_after != raw_hash_before:
        raise NormalizationError(f"raw historical NPZ changed during normalization: {resolved_raw}")

    descriptor = {
        "representation": "dense_matrix",
        "path": relative_path.as_posix(),
        "array_key": NORMALIZED_SCORE_KEY,
        "shape": [expected_length, expected_length],
        "dtype": str(reloaded.dtype),
        "semantics": "probability",
        "symmetric": True,
        "diagonal": "zero",
        "sha256": normalized_hash,
        "source_path": str(resolved_raw),
        "source_array_key": SOURCE_SCORE_KEY,
    }
    audit = {
        "raw_pair_score_path": str(resolved_raw),
        "raw_pair_score_sha256": raw_hash_before,
        "raw_pair_score_sha256_after": raw_hash_after,
        "raw_pair_score_unchanged": "true",
        "normalized_pair_score_path": relative_path.as_posix(),
        "normalized_pair_score_sha256": normalized_hash,
        "normalized_pair_score_size_bytes": sidecar_path.stat().st_size,
        "score_shape": f"{expected_length}x{expected_length}",
        "score_dtype": str(reloaded.dtype),
        **asdict(stats),
    }
    return descriptor, stats, audit


def _build_record(
    *,
    manifest_row: dict[str, str],
    manifest_path: Path,
    spec: SourceSpec,
    output_root: Path,
    hash_cache: dict[Path, str],
    created_at_utc: str,
) -> tuple[dict[str, Any], dict[str, Any], ScoreNormalizationStats | None]:
    rna_id = manifest_row["rna_id"]
    record_id = make_record_id(DATASET, rna_id, GROUND_TRUTH_LABEL, spec.name, RUN_ID)
    sequence_path = Path(manifest_row["sequence_path"])
    ground_truth_path = Path(manifest_row["gt_path"])
    prediction_path = Path(manifest_row[spec.manifest_path_field])

    raw_sequence, sequence = _read_fasta(sequence_path, rna_id)
    length = len(sequence)
    ground_truth = _read_single_line_structure(ground_truth_path)
    if spec.trrna2_scores:
        prediction = _read_trrna2_structure(prediction_path, rna_id)
    else:
        prediction = _read_single_line_structure(prediction_path)

    ground_truth_pairs = parse_extended_dot_bracket(
        ground_truth, sequence_length=length
    )
    predicted_pairs = parse_standard_dot_bracket(prediction, sequence_length=length)
    transformations = _base_transformations(raw_sequence)
    petfold_alias_applied = manifest_row.get("petfold_alias_applied", "false") == "true"
    if spec.name == "petfold" and petfold_alias_applied:
        transformations.append(
            {
                "name": "apply_explicit_manifest_id_alias",
                "version": "1",
                "parameters": {
                    "source_id": manifest_row["petfold_source_id"],
                    "rna_id": rna_id,
                },
                "input_roles": ["dataset_manifest", "prediction"],
            }
        )

    raw_files = [
        _raw_file("dataset_manifest", manifest_path, hash_cache),
        _raw_file("sequence", sequence_path, hash_cache),
        _raw_file("ground_truth", ground_truth_path, hash_cache),
        _raw_file("prediction", prediction_path, hash_cache),
    ]
    pair_scores: dict[str, Any] | None = None
    score_stats: ScoreNormalizationStats | None = None
    score_audit: dict[str, Any] = {}
    if spec.trrna2_scores:
        raw_score_path = Path(manifest_row["trrna2_pair_score_path"])
        raw_files.append(_raw_file("pair_scores", raw_score_path, hash_cache))
        pair_scores, score_stats, score_audit = _write_normalized_sidecar(
            raw_path=raw_score_path,
            output_root=output_root,
            record_id=record_id,
            expected_length=length,
            hash_cache=hash_cache,
        )
        transformations.append(_score_transformation(score_stats))

    warnings = _record_warnings(
        raw_sequence=raw_sequence,
        spec=spec,
        petfold_alias_applied=petfold_alias_applied,
    )
    record = {
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "dataset": DATASET,
        "rna_id": rna_id,
        "sequence": sequence,
        "ground_truth_structure": {
            "label": GROUND_TRUTH_LABEL,
            "source_format": "extended_dot_bracket",
            "source_value": ground_truth,
            "pairs": _pairs_json(ground_truth_pairs),
            "allow_multiple_partners": False,
        },
        "source_model": _source_model(spec),
        "predicted_structure": {
            "label": spec.label,
            "source_format": "dot_bracket",
            "source_value": prediction,
            "pairs": _pairs_json(predicted_pairs),
            "allow_multiple_partners": False,
        },
        "pair_scores": pair_scores,
        "provenance": {
            "raw_files": raw_files,
            "normalizer": {
                "name": "normalize_legacy121",
                "version": "1",
                "command": "PYTHONPATH=src python scripts/normalize_legacy121.py",
                "config": {
                    "dataset": DATASET,
                    "score_transformation": (
                        "set_diagonal_to_zero" if spec.trrna2_scores else None
                    ),
                    "score_symmetry_atol": (
                        SCORE_SYMMETRY_ATOL if spec.trrna2_scores else None
                    ),
                },
            },
            "transformations": transformations,
            "created_at_utc": created_at_utc,
        },
        "metadata": {
            "sequence_length": length,
            "contains_ambiguous_bases": bool(set(sequence) - set("ACGU")),
            "pseudoknot_encoded": any(
                character not in ".()" for character in ground_truth
            ),
            "warnings": warnings,
        },
    }
    _validate_record_contract(record)

    audit_row = _empty_audit_row(record_id, rna_id, spec.name)
    audit_row.update(
        {
            "status": "valid",
            "sequence_length": length,
            "gt_pair_count": len(ground_truth_pairs),
            "predicted_pair_count": len(predicted_pairs),
            "pair_scores_available": str(pair_scores is not None).lower(),
            "warnings": ";".join(warnings),
            **score_audit,
        }
    )
    return record, audit_row, score_stats


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def _write_audit(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _build_summary(
    *,
    records: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    score_stats: list[ScoreNormalizationStats],
    output_root: Path,
    predictions_path: Path,
    audit_path: Path,
    created_at_utc: str,
) -> dict[str, Any]:
    records_by_predictor: dict[str, dict[str, int]] = {}
    for spec in SOURCE_SPECS:
        rows = [row for row in audit_rows if row["source_model"] == spec.name]
        records_by_predictor[spec.name] = {
            "produced": sum(row["status"] == "valid" for row in rows),
            "valid": sum(row["status"] == "valid" for row in rows),
            "invalid": sum(row["status"] != "valid" for row in rows),
            "with_pair_scores": sum(row["pair_scores_available"] == "true" for row in rows),
        }

    warning_counts = Counter(
        warning
        for record in records
        for warning in record["metadata"].get("warnings", [])
    )
    sidecar_paths = [
        output_root / Path(record["pair_scores"]["path"])
        for record in records
        if record["pair_scores"] is not None
    ]
    pair_score_summary = {
        "records": len(score_stats),
        "matrices_with_nonzero_diagonal_before": sum(
            stats.diagonal_nonzero_count_before > 0 for stats in score_stats
        ),
        "diagonal_nonzero_count_before_total": sum(
            stats.diagonal_nonzero_count_before for stats in score_stats
        ),
        "diagonal_min_before": min(
            (stats.diagonal_min_before for stats in score_stats), default=None
        ),
        "diagonal_max_before": max(
            (stats.diagonal_max_before for stats in score_stats), default=None
        ),
        "max_asymmetry_before": max(
            (stats.max_asymmetry_before for stats in score_stats), default=None
        ),
        "min_score_before": min(
            (stats.min_score_before for stats in score_stats), default=None
        ),
        "max_score_before": max(
            (stats.max_score_before for stats in score_stats), default=None
        ),
        "diagonal_nonzero_count_after_total": sum(
            stats.diagonal_nonzero_count_after for stats in score_stats
        ),
        "all_normalized_diagonals_zero": all(
            stats.diagonal_nonzero_count_after == 0 for stats in score_stats
        ),
        "max_off_diagonal_absolute_change": max(
            (stats.max_off_diagonal_absolute_change for stats in score_stats),
            default=None,
        ),
        "raw_historical_npz_unchanged": all(
            row.get("raw_pair_score_unchanged") == "true"
            for row in audit_rows
            if row.get("pair_scores_available") == "true"
        ),
        "normalized_sidecar_count": len(sidecar_paths),
        "normalized_sidecar_total_size_bytes": sum(
            path.stat().st_size for path in sidecar_paths
        ),
    }
    valid = sum(row["status"] == "valid" for row in audit_rows)
    invalid = len(audit_rows) - valid
    with_pair_scores = sum(
        row["pair_scores_available"] == "true" for row in audit_rows
    )
    acceptance_passed = (
        len(audit_rows) == EXPECTED_RECORDS
        and len(records) == EXPECTED_RECORDS
        and valid == EXPECTED_RECORDS
        and invalid == 0
        and all(
            values["valid"] == EXPECTED_RNAS
            for values in records_by_predictor.values()
        )
        and with_pair_scores == EXPECTED_RNAS
        and len(score_stats) == EXPECTED_RNAS
        and pair_score_summary["all_normalized_diagonals_zero"]
        and pair_score_summary["max_off_diagonal_absolute_change"] == 0.0
        and pair_score_summary["raw_historical_npz_unchanged"]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset": DATASET,
        "generated_at_utc": created_at_utc,
        "expected_rnas": EXPECTED_RNAS,
        "expected_records": EXPECTED_RECORDS,
        "attempted_records": len(audit_rows),
        "produced_records": len(records),
        "valid_records": valid,
        "invalid_records": invalid,
        "records_by_predictor": records_by_predictor,
        "records_with_pair_scores": with_pair_scores,
        "pair_score_normalization": pair_score_summary,
        "warnings": {
            "total_occurrences": sum(warning_counts.values()),
            "by_code": dict(sorted(warning_counts.items())),
        },
        "outputs": {
            "predictions_jsonl": str(predictions_path.resolve()),
            "audit_csv": str(audit_path.resolve()),
        },
        "baseline_evaluation_performed": False,
        "acceptance_passed": acceptance_passed,
    }


def main() -> int:
    args = _parse_args()
    manifest_path = args.manifest.resolve()
    output_root = args.output_root.resolve()
    predictions_path = output_root / "predictions.jsonl"
    audit_path = args.audit_output.resolve()
    summary_path = args.summary_output.resolve()
    created_at_utc = _utc_now()

    manifest_rows = _read_manifest(manifest_path)
    records: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    score_stats: list[ScoreNormalizationStats] = []
    hash_cache: dict[Path, str] = {}
    record_ids: set[str] = set()

    for manifest_row in manifest_rows:
        for spec in SOURCE_SPECS:
            record_id = make_record_id(
                DATASET,
                manifest_row["rna_id"],
                GROUND_TRUTH_LABEL,
                spec.name,
                RUN_ID,
            )
            try:
                if record_id in record_ids:
                    raise NormalizationError(f"duplicate record_id {record_id}")
                record, audit_row, stats = _build_record(
                    manifest_row=manifest_row,
                    manifest_path=manifest_path,
                    spec=spec,
                    output_root=output_root,
                    hash_cache=hash_cache,
                    created_at_utc=created_at_utc,
                )
                record_ids.add(record_id)
                records.append(record)
                audit_rows.append(audit_row)
                if stats is not None:
                    score_stats.append(stats)
            except Exception as error:
                audit_row = _empty_audit_row(
                    record_id, manifest_row["rna_id"], spec.name
                )
                audit_row["failure_reason"] = f"{type(error).__name__}: {error}"
                audit_rows.append(audit_row)

    _write_jsonl(predictions_path, records)
    _write_audit(audit_path, audit_rows)
    summary = _build_summary(
        records=records,
        audit_rows=audit_rows,
        score_stats=score_stats,
        output_root=output_root,
        predictions_path=predictions_path,
        audit_path=audit_path,
        created_at_utc=created_at_utc,
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["acceptance_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
