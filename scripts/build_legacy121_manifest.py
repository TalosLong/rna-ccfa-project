#!/usr/bin/env python3
"""Build and validate the frozen Legacy121 v1 explicit asset manifest."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from rna_ccfa import parse_dot_bracket, parse_standard_dot_bracket


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEQUENCE_ROOT = Path("/root/autodl-tmp/data/sequences")
DEFAULT_GT_ROOT = Path("/root/autodl-tmp/data/ss/gt")
DEFAULT_RNAFOLD_ROOT = Path("/root/autodl-tmp/data/ss/rnafold")
DEFAULT_PETFOLD_ROOT = Path("/root/autodl-tmp/data/ss/petfold")
DEFAULT_TRRNA2_ROOT = Path("/root/autodl-tmp/models/trRosettaRNA2/data/ss_native")

PRIMARY_FASTA_EXCLUSIONS = {
    "all.fasta",
    "rna_ligand_sequences.fasta",
    "rna_protein_sequences.fasta",
}
PETFOLD_ALIASES = {"1A9L_38_hpbulge_nmr_A": "1A9L"}
EXPECTED_GT_ONLY_FILES = {
    "8Q4O_23_g4_nmr_matrix.db",
    "8TNS_24_g4_nmr_matrix.db",
}
RNA_IUPAC_ALPHABET = set("ACGURYSWKMBDHVN")

MANIFEST_FIELDS = [
    "dataset_version",
    "rna_id",
    "sequence_path",
    "gt_path",
    "rnafold_prediction_path",
    "petfold_prediction_path",
    "trrna2_prediction_path",
    "trrna2_pair_score_path",
    "gt_mapping_key",
    "petfold_source_id",
    "petfold_alias_applied",
    "validation_status",
]

AUDIT_FIELDS = [
    "rna_id",
    "status",
    "sequence_length",
    "sequence_exists",
    "gt_exists",
    "rnafold_prediction_exists",
    "petfold_prediction_exists",
    "trrna2_prediction_exists",
    "trrna2_pair_score_exists",
    "gt_pair_count",
    "rnafold_pair_count",
    "petfold_pair_count",
    "trrna2_pair_count",
    "warnings",
    "failure_reason",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence-root", type=Path, default=DEFAULT_SEQUENCE_ROOT)
    parser.add_argument("--gt-root", type=Path, default=DEFAULT_GT_ROOT)
    parser.add_argument("--rnafold-root", type=Path, default=DEFAULT_RNAFOLD_ROOT)
    parser.add_argument("--petfold-root", type=Path, default=DEFAULT_PETFOLD_ROOT)
    parser.add_argument("--trrna2-root", type=Path, default=DEFAULT_TRRNA2_ROOT)
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=PROJECT_ROOT / "manifests/legacy121_v1.csv",
    )
    parser.add_argument(
        "--audit-output",
        type=Path,
        default=PROJECT_ROOT / "results/manifest_audit/legacy121_v1_audit.csv",
    )
    return parser.parse_args()


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _read_primary_sequence(path: Path, rna_id: str) -> tuple[str, list[str]]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2 or not lines[0].startswith(">"):
        raise ValueError("expected one FASTA header followed by sequence data")
    if any(line.startswith(">") for line in lines[1:]):
        raise ValueError("expected exactly one FASTA record")

    header_id = lines[0][1:].split()[0]
    if header_id != rna_id:
        raise ValueError(f"FASTA header ID {header_id!r} does not match rna_id {rna_id!r}")

    raw_sequence = "".join(lines[1:])
    if not raw_sequence:
        raise ValueError("sequence is empty")
    sequence = raw_sequence.upper()
    illegal = sorted(set(sequence) - RNA_IUPAC_ALPHABET)
    if illegal:
        raise ValueError(f"sequence contains illegal symbols: {''.join(illegal)}")

    warnings: list[str] = []
    if raw_sequence != sequence:
        warnings.append("raw_sequence_lowercase")
    return sequence, warnings


def _read_one_line_structure(path: Path) -> str:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError(f"expected one non-empty structure line, observed {len(lines)}")
    return lines[0]


def _read_trrna2_structure(path: Path, rna_id: str) -> str:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 2 or not lines[0].startswith(">"):
        raise ValueError("expected trRosettaRNA2 DBN header and one structure line")
    header_id = lines[0][1:].split()[0]
    if header_id != rna_id:
        raise ValueError(f"DBN header ID {header_id!r} does not match rna_id {rna_id!r}")
    return lines[1]


def _append_failure(failures: list[str], label: str, error: Exception) -> None:
    failures.append(f"{label}: {type(error).__name__}: {error}")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build(args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]], list[str]]:
    primary_paths = sorted(
        path
        for path in args.sequence_root.glob("*.fasta")
        if path.name not in PRIMARY_FASTA_EXCLUSIONS
    )
    global_failures: list[str] = []
    if len(primary_paths) != 121:
        global_failures.append(f"expected 121 primary FASTA files, observed {len(primary_paths)}")

    rna_ids = [path.stem for path in primary_paths]
    if len(set(rna_ids)) != len(rna_ids):
        global_failures.append("duplicate rna_id derived from primary FASTA filenames")

    manifest_rows: list[dict[str, object]] = []
    audit_rows: list[dict[str, object]] = []
    included_gt_names: set[str] = set()

    for sequence_path in primary_paths:
        rna_id = sequence_path.stem
        failures: list[str] = []
        warnings: list[str] = []

        if not rna_id.endswith("_A"):
            failures.append("rna_id does not end with the frozen chain suffix '_A'")
            gt_mapping_key = rna_id
        else:
            gt_mapping_key = rna_id[:-2]

        petfold_source_id = PETFOLD_ALIASES.get(rna_id, gt_mapping_key)
        alias_applied = rna_id in PETFOLD_ALIASES
        if alias_applied:
            warnings.append("petfold_filename_alias_applied")

        gt_path = args.gt_root / f"{gt_mapping_key}_matrix.db"
        rnafold_path = args.rnafold_root / f"{rna_id}.db"
        petfold_path = args.petfold_root / f"{petfold_source_id}.db"
        trrna2_dir = args.trrna2_root / rna_id
        trrna2_path = trrna2_dir / f"{rna_id}.dbn"
        trrna2_score_path = trrna2_dir / f"{rna_id}_ss_prob.npz"
        included_gt_names.add(gt_path.name)

        assets = {
            "sequence": sequence_path,
            "gt": gt_path,
            "rnafold_prediction": rnafold_path,
            "petfold_prediction": petfold_path,
            "trrna2_prediction": trrna2_path,
            "trrna2_pair_score": trrna2_score_path,
        }
        exists = {label: path.is_file() for label, path in assets.items()}
        for label, is_present in exists.items():
            if not is_present:
                failures.append(f"missing {label}: {assets[label]}")

        sequence: str | None = None
        if exists["sequence"]:
            try:
                sequence, sequence_warnings = _read_primary_sequence(sequence_path, rna_id)
                warnings.extend(sequence_warnings)
            except (OSError, UnicodeError, ValueError) as error:
                _append_failure(failures, "sequence", error)

        pair_counts: dict[str, int | str] = {
            "gt": "",
            "rnafold": "",
            "petfold": "",
            "trrna2": "",
        }
        if sequence is not None:
            parsers = [
                ("gt", gt_path, _read_one_line_structure, parse_dot_bracket),
                ("rnafold", rnafold_path, _read_one_line_structure, parse_standard_dot_bracket),
                ("petfold", petfold_path, _read_one_line_structure, parse_standard_dot_bracket),
            ]
            for label, path, reader, parser in parsers:
                if not exists[f"{label}_prediction" if label != "gt" else "gt"]:
                    continue
                try:
                    structure = reader(path)
                    pair_counts[label] = len(parser(structure, sequence_length=len(sequence)))
                except (OSError, UnicodeError, ValueError) as error:
                    _append_failure(failures, label, error)

            if exists["trrna2_prediction"]:
                try:
                    structure = _read_trrna2_structure(trrna2_path, rna_id)
                    pair_counts["trrna2"] = len(
                        parse_standard_dot_bracket(structure, sequence_length=len(sequence))
                    )
                except (OSError, UnicodeError, ValueError) as error:
                    _append_failure(failures, "trrna2", error)

        if exists["trrna2_pair_score"] and trrna2_score_path.stat().st_size == 0:
            failures.append(f"empty trrna2_pair_score: {trrna2_score_path}")

        status = "valid" if not failures else "invalid"
        manifest_rows.append(
            {
                "dataset_version": "Legacy121_v1",
                "rna_id": rna_id,
                "sequence_path": str(sequence_path.resolve()),
                "gt_path": str(gt_path.resolve()),
                "rnafold_prediction_path": str(rnafold_path.resolve()),
                "petfold_prediction_path": str(petfold_path.resolve()),
                "trrna2_prediction_path": str(trrna2_path.resolve()),
                "trrna2_pair_score_path": str(trrna2_score_path.resolve()),
                "gt_mapping_key": gt_mapping_key,
                "petfold_source_id": petfold_source_id,
                "petfold_alias_applied": _bool_text(alias_applied),
                "validation_status": status,
            }
        )
        audit_rows.append(
            {
                "rna_id": rna_id,
                "status": status,
                "sequence_length": len(sequence) if sequence is not None else "",
                "sequence_exists": _bool_text(exists["sequence"]),
                "gt_exists": _bool_text(exists["gt"]),
                "rnafold_prediction_exists": _bool_text(exists["rnafold_prediction"]),
                "petfold_prediction_exists": _bool_text(exists["petfold_prediction"]),
                "trrna2_prediction_exists": _bool_text(exists["trrna2_prediction"]),
                "trrna2_pair_score_exists": _bool_text(exists["trrna2_pair_score"]),
                "gt_pair_count": pair_counts["gt"],
                "rnafold_pair_count": pair_counts["rnafold"],
                "petfold_pair_count": pair_counts["petfold"],
                "trrna2_pair_count": pair_counts["trrna2"],
                "warnings": ";".join(sorted(set(warnings))),
                "failure_reason": " | ".join(failures),
            }
        )

    observed_gt_names = {path.name for path in args.gt_root.glob("*.db")}
    extra_gt_names = observed_gt_names - included_gt_names
    if extra_gt_names != EXPECTED_GT_ONLY_FILES:
        global_failures.append(
            "GT-only file set differs from the frozen exclusion set: "
            f"observed={sorted(extra_gt_names)!r}, expected={sorted(EXPECTED_GT_ONLY_FILES)!r}"
        )
    missing_excluded = [
        name for name in EXPECTED_GT_ONLY_FILES if not (args.gt_root / name).is_file()
    ]
    if missing_excluded:
        global_failures.append(f"expected preserved GT-only files are missing: {missing_excluded!r}")

    if any(row["status"] != "valid" for row in audit_rows):
        global_failures.append("one or more primary RNA rows failed validation")
    return manifest_rows, audit_rows, global_failures


def main() -> int:
    args = _parse_args()
    manifest_rows, audit_rows, global_failures = build(args)
    _write_csv(args.manifest_output, MANIFEST_FIELDS, manifest_rows)
    _write_csv(args.audit_output, AUDIT_FIELDS, audit_rows)

    valid_rows = sum(row["status"] == "valid" for row in audit_rows)
    print(f"manifest_rows={len(manifest_rows)}")
    print(f"valid_rows={valid_rows}")
    print(f"invalid_rows={len(audit_rows) - valid_rows}")
    print(f"excluded_gt_only={','.join(sorted(EXPECTED_GT_ONLY_FILES))}")
    if global_failures:
        for failure in global_failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    print("legacy121_v1_status=frozen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
