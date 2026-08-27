"""Reusable normalization helpers for schema-v1 prediction records."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np


SCHEMA_VERSION = "rna-ccfa.normalized_prediction.v1"
SCORE_SYMMETRY_ATOL = 1e-7
RNA_IUPAC_ALPHABET = frozenset("ACGURYSWKMBDHVN")


class NormalizationError(ValueError):
    """An input cannot be normalized without violating schema v1."""


@dataclass(frozen=True, slots=True)
class ScoreNormalizationStats:
    """Pre/post audit values for diagonal-only probability normalization."""

    diagonal_nonzero_count_before: int
    diagonal_min_before: float
    diagonal_max_before: float
    max_asymmetry_before: float
    min_score_before: float
    max_score_before: float
    diagonal_nonzero_count_after: int
    max_asymmetry_after: float
    min_score_after: float
    max_score_after: float
    max_off_diagonal_absolute_change: float


def sha256_file(path: Path) -> str:
    """Return the lowercase SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def filesystem_slug(value: str) -> str:
    """Convert a record-ID component to a lowercase filesystem-safe slug."""

    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if not slug:
        raise NormalizationError(f"cannot create a non-empty slug from {value!r}")
    return slug


def make_record_id(
    dataset: str,
    rna_id: str,
    ground_truth_label: str,
    source_model: str,
    run_id: str,
) -> str:
    """Build a schema-v1 record ID from its five identity components."""

    return "__".join(
        filesystem_slug(component)
        for component in (dataset, rna_id, ground_truth_label, source_model, run_id)
    )


def validate_normalized_sequence(sequence: str) -> None:
    """Validate the schema-v1 normalized sequence representation."""

    if not sequence:
        raise NormalizationError("normalized sequence is empty")
    if sequence != sequence.upper() or any(character.isspace() for character in sequence):
        raise NormalizationError("normalized sequence must be uppercase and whitespace-free")
    illegal = sorted(set(sequence) - RNA_IUPAC_ALPHABET)
    if illegal:
        raise NormalizationError(f"normalized sequence contains illegal symbols: {illegal!r}")


def _matrix_audit(matrix: np.ndarray) -> tuple[float, float, float, np.ndarray]:
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise NormalizationError(f"score matrix must be square, observed shape {matrix.shape!r}")
    if not np.issubdtype(matrix.dtype, np.floating):
        raise NormalizationError(f"score matrix must use a floating dtype, observed {matrix.dtype}")
    if not np.isfinite(matrix).all():
        raise NormalizationError("score matrix contains non-finite values")

    minimum = float(np.min(matrix))
    maximum = float(np.max(matrix))
    if minimum < 0.0 or maximum > 1.0:
        raise NormalizationError(
            f"probability score matrix range [{minimum}, {maximum}] is outside [0, 1]"
        )
    max_asymmetry = float(np.max(np.abs(matrix - matrix.T)))
    diagonal = np.diag(matrix)
    return minimum, maximum, max_asymmetry, diagonal


def normalize_probability_matrix_diagonal(
    matrix: np.ndarray,
    *,
    expected_length: int,
    symmetry_atol: float = SCORE_SYMMETRY_ATOL,
) -> tuple[np.ndarray, ScoreNormalizationStats]:
    """Copy a probability matrix and set only its diagonal to exact zero.

    Off-diagonal values and dtype are preserved. Input validation happens
    before copying; output validation proves the approved transformation is the
    only numerical change.
    """

    if matrix.shape != (expected_length, expected_length):
        raise NormalizationError(
            f"score shape {matrix.shape!r} does not match sequence length {expected_length}"
        )
    min_before, max_before, asym_before, diagonal_before = _matrix_audit(matrix)
    if asym_before > symmetry_atol:
        raise NormalizationError(
            f"raw score matrix asymmetry {asym_before} exceeds tolerance {symmetry_atol}"
        )

    normalized = np.array(matrix, copy=True)
    np.fill_diagonal(normalized, 0.0)

    min_after, max_after, asym_after, diagonal_after = _matrix_audit(normalized)
    diagonal_nonzero_after = int(np.count_nonzero(diagonal_after))
    if diagonal_nonzero_after != 0:
        raise NormalizationError("normalized score matrix diagonal is not exactly zero")
    if asym_after > symmetry_atol:
        raise NormalizationError(
            f"normalized score matrix asymmetry {asym_after} exceeds tolerance {symmetry_atol}"
        )
    if normalized.dtype != matrix.dtype:
        raise NormalizationError(
            f"score dtype changed from {matrix.dtype} to {normalized.dtype}"
        )

    off_diagonal = ~np.eye(expected_length, dtype=bool)
    if expected_length > 1:
        max_off_diagonal_change = float(
            np.max(np.abs(normalized[off_diagonal] - matrix[off_diagonal]))
        )
    else:
        max_off_diagonal_change = 0.0
    if max_off_diagonal_change != 0.0 or not np.array_equal(
        normalized[off_diagonal], matrix[off_diagonal]
    ):
        raise NormalizationError("off-diagonal score values changed during normalization")

    return normalized, ScoreNormalizationStats(
        diagonal_nonzero_count_before=int(np.count_nonzero(diagonal_before)),
        diagonal_min_before=float(np.min(diagonal_before)),
        diagonal_max_before=float(np.max(diagonal_before)),
        max_asymmetry_before=asym_before,
        min_score_before=min_before,
        max_score_before=max_before,
        diagonal_nonzero_count_after=diagonal_nonzero_after,
        max_asymmetry_after=asym_after,
        min_score_after=min_after,
        max_score_after=max_after,
        max_off_diagonal_absolute_change=max_off_diagonal_change,
    )


def validate_normalized_probability_matrix(
    matrix: np.ndarray,
    *,
    expected_length: int,
    symmetry_atol: float = SCORE_SYMMETRY_ATOL,
) -> None:
    """Validate a normalized dense probability matrix against schema v1."""

    if matrix.shape != (expected_length, expected_length):
        raise NormalizationError(
            f"score shape {matrix.shape!r} does not match sequence length {expected_length}"
        )
    _, _, max_asymmetry, diagonal = _matrix_audit(matrix)
    if max_asymmetry > symmetry_atol:
        raise NormalizationError(
            f"score matrix asymmetry {max_asymmetry} exceeds tolerance {symmetry_atol}"
        )
    if np.count_nonzero(diagonal) != 0:
        raise NormalizationError("normalized score matrix diagonal must be exactly zero")
