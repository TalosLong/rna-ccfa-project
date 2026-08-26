"""Canonical RNA secondary-structure parsing and validation.

The public parsers return zero-based ``(i, j)`` tuples with ``i < j``, sorted
lexicographically. Invalid input is rejected rather than silently repaired.
Crossing pairs are retained.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from numbers import Integral, Real
from string import ascii_lowercase, ascii_uppercase
from typing import TypeAlias

Pair: TypeAlias = tuple[int, int]


class StructureValidationError(ValueError):
    """A structure representation violates the normalized schema contract."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


_SYMBOL_PAIRS = dict(zip("([{<" + ascii_uppercase, ")]}>" + ascii_lowercase))
_CLOSING_TO_OPENING = {closing: opening for opening, closing in _SYMBOL_PAIRS.items()}


def _raise(code: str, message: str) -> None:
    raise StructureValidationError(message, code=code)


def _resolve_sequence_length(
    *,
    sequence: str | None,
    sequence_length: int | None,
    required: bool,
) -> int | None:
    if sequence is not None and not isinstance(sequence, str):
        _raise("invalid_sequence", "sequence must be a string")

    if sequence_length is not None:
        if isinstance(sequence_length, bool) or not isinstance(sequence_length, Integral):
            _raise("invalid_sequence_length", "sequence_length must be an integer")
        sequence_length = int(sequence_length)
        if sequence_length < 0:
            _raise("invalid_sequence_length", "sequence_length must be non-negative")

    if sequence is not None:
        observed = len(sequence)
        if sequence_length is not None and sequence_length != observed:
            _raise(
                "length_mismatch",
                f"sequence length {observed} does not match sequence_length {sequence_length}",
            )
        return observed

    if required and sequence_length is None:
        _raise(
            "missing_sequence_length",
            "sequence or sequence_length is required for coordinate validation",
        )
    return sequence_length


def _check_representation_length(
    observed_length: int,
    expected_length: int | None,
    representation: str,
) -> None:
    if expected_length is not None and observed_length != expected_length:
        _raise(
            "length_mismatch",
            f"{representation} length {observed_length} does not match sequence length "
            f"{expected_length}",
        )


def validate_pairs(
    pairs: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    allow_multiple_partners: bool = False,
) -> list[Pair]:
    """Validate zero-based pairs and return them in canonical sorted order.

    Pair endpoints are never reordered or deduplicated silently. Reversed,
    duplicate, self, and out-of-range pairs are fatal validation errors.
    """

    length = _resolve_sequence_length(
        sequence=sequence,
        sequence_length=sequence_length,
        required=True,
    )
    assert length is not None

    if isinstance(pairs, (str, bytes)):
        _raise("invalid_pair", "pairs must be an iterable of two-item sequences")

    canonical: list[Pair] = []
    seen: set[Pair] = set()
    partners: dict[int, int] = {}

    try:
        iterator = iter(pairs)
    except TypeError:
        _raise("invalid_pair", "pairs must be iterable")

    for pair_number, raw_pair in enumerate(iterator):
        if isinstance(raw_pair, (str, bytes)):
            _raise("invalid_pair", f"pair {pair_number} must contain exactly two indices")
        try:
            endpoints = tuple(raw_pair)
        except TypeError:
            _raise("invalid_pair", f"pair {pair_number} must be iterable")
        if len(endpoints) != 2:
            _raise("invalid_pair", f"pair {pair_number} must contain exactly two indices")

        raw_i, raw_j = endpoints
        if (
            isinstance(raw_i, bool)
            or isinstance(raw_j, bool)
            or not isinstance(raw_i, Integral)
            or not isinstance(raw_j, Integral)
        ):
            _raise("invalid_pair", f"pair {pair_number} endpoints must be integers")

        i, j = int(raw_i), int(raw_j)
        pair = (i, j)
        if i == j:
            _raise("self_pair", f"self pair {pair} is not allowed")
        if i > j:
            _raise("reversed_pair", f"pair {pair} must satisfy i < j")
        if i < 0 or j >= length:
            _raise(
                "out_of_range_pair",
                f"pair {pair} is outside valid coordinates [0, {length})",
            )
        if pair in seen:
            _raise("duplicate_pair", f"duplicate pair {pair}")

        if not allow_multiple_partners:
            for nucleotide, partner in ((i, j), (j, i)):
                previous = partners.get(nucleotide)
                if previous is not None and previous != partner:
                    _raise(
                        "multiple_partners",
                        f"nucleotide {nucleotide} is paired with both {previous} and {partner}",
                    )
                partners[nucleotide] = partner

        seen.add(pair)
        canonical.append(pair)

    return sorted(canonical)


def _parse_dot_bracket(
    structure: str,
    *,
    extended: bool,
    sequence: str | None,
    sequence_length: int | None,
    allow_multiple_partners: bool,
) -> list[Pair]:
    if not isinstance(structure, str):
        _raise("invalid_structure", "dot-bracket structure must be a string")

    expected_length = _resolve_sequence_length(
        sequence=sequence,
        sequence_length=sequence_length,
        required=False,
    )
    _check_representation_length(len(structure), expected_length, "structure")

    symbol_pairs = _SYMBOL_PAIRS if extended else {"(": ")"}
    closing_to_opening = (
        _CLOSING_TO_OPENING if extended else {")": "("}
    )
    stacks: dict[str, list[int]] = {opening: [] for opening in symbol_pairs}
    pairs: list[Pair] = []

    for position, symbol in enumerate(structure):
        if symbol == ".":
            continue
        if symbol in symbol_pairs:
            stacks[symbol].append(position)
            continue
        if symbol in closing_to_opening:
            opening = closing_to_opening[symbol]
            if not stacks[opening]:
                _raise(
                    "unmatched_bracket",
                    f"unmatched closing symbol {symbol!r} at position {position}",
                )
            pairs.append((stacks[opening].pop(), position))
            continue
        _raise(
            "illegal_structure_character",
            f"illegal structure character {symbol!r} at position {position}",
        )

    unmatched = sorted(
        (position, opening)
        for opening, positions in stacks.items()
        for position in positions
    )
    if unmatched:
        position, opening = unmatched[0]
        _raise(
            "unmatched_bracket",
            f"unmatched opening symbol {opening!r} at position {position}",
        )

    return validate_pairs(
        pairs,
        sequence_length=len(structure),
        allow_multiple_partners=allow_multiple_partners,
    )


def parse_dot_bracket(
    structure: str,
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    allow_multiple_partners: bool = False,
) -> list[Pair]:
    """Parse extended dot-bracket, including all schema-v1 symbol families."""

    return _parse_dot_bracket(
        structure,
        extended=True,
        sequence=sequence,
        sequence_length=sequence_length,
        allow_multiple_partners=allow_multiple_partners,
    )


def parse_extended_dot_bracket(
    structure: str,
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    allow_multiple_partners: bool = False,
) -> list[Pair]:
    """Parse schema-v1 extended dot-bracket notation.

    This explicit name is an alias-style entry point; ``parse_dot_bracket``
    accepts the same extended symbol set for convenient direct use.
    """

    return parse_dot_bracket(
        structure,
        sequence=sequence,
        sequence_length=sequence_length,
        allow_multiple_partners=allow_multiple_partners,
    )


def parse_standard_dot_bracket(
    structure: str,
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    allow_multiple_partners: bool = False,
) -> list[Pair]:
    """Parse standard dot-bracket containing only ``.``, ``(``, and ``)``."""

    return _parse_dot_bracket(
        structure,
        extended=False,
        sequence=sequence,
        sequence_length=sequence_length,
        allow_multiple_partners=allow_multiple_partners,
    )


def parse_pair_list(
    pairs: Iterable[Sequence[int]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    index_base: int = 0,
    allow_multiple_partners: bool = False,
) -> list[Pair]:
    """Parse an explicit zero- or one-based pair list.

    ``index_base=1`` performs the explicit provenance-relevant conversion to
    zero-based coordinates before validation.
    """

    if index_base not in (0, 1) or isinstance(index_base, bool):
        _raise("invalid_index_base", "index_base must be 0 or 1")

    converted: list[tuple[object, ...]] = []
    if isinstance(pairs, (str, bytes)):
        _raise("invalid_pair", "pairs must be an iterable of two-item sequences")
    try:
        iterator = iter(pairs)
    except TypeError:
        _raise("invalid_pair", "pairs must be iterable")

    for pair_number, raw_pair in enumerate(iterator):
        if isinstance(raw_pair, (str, bytes)):
            _raise("invalid_pair", f"pair {pair_number} must contain exactly two indices")
        try:
            endpoints = tuple(raw_pair)
        except TypeError:
            _raise("invalid_pair", f"pair {pair_number} must be iterable")
        if len(endpoints) != 2:
            _raise("invalid_pair", f"pair {pair_number} must contain exactly two indices")
        if all(
            isinstance(endpoint, Integral) and not isinstance(endpoint, bool)
            for endpoint in endpoints
        ):
            converted.append(tuple(int(endpoint) - index_base for endpoint in endpoints))
        else:
            converted.append(endpoints)

    return validate_pairs(
        converted,
        sequence=sequence,
        sequence_length=sequence_length,
        allow_multiple_partners=allow_multiple_partners,
    )


def _binary_matrix_value(value: object, row: int, column: int) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, Real) and value in (0, 1):
        return int(value)
    _raise(
        "invalid_matrix_value",
        f"matrix[{row}][{column}] must be binary 0 or 1, got {value!r}",
    )


def parse_dense_matrix(
    matrix: Iterable[Iterable[Real]],
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    allow_multiple_partners: bool = False,
) -> list[Pair]:
    """Convert a symmetric binary dense pair matrix to canonical pairs."""

    if isinstance(matrix, (str, bytes)):
        _raise("invalid_matrix_shape", "dense matrix must be a square two-dimensional array")
    try:
        raw_rows = list(matrix)
    except TypeError:
        _raise("invalid_matrix_shape", "dense matrix must be iterable")

    rows: list[list[object]] = []
    for row_number, raw_row in enumerate(raw_rows):
        if isinstance(raw_row, (str, bytes)):
            _raise("invalid_matrix_shape", f"matrix row {row_number} must be iterable")
        try:
            rows.append(list(raw_row))
        except TypeError:
            _raise("invalid_matrix_shape", f"matrix row {row_number} must be iterable")

    size = len(rows)
    if any(len(row) != size for row in rows):
        _raise(
            "invalid_matrix_shape",
            f"dense matrix must be square; observed {size} rows with unequal row lengths",
        )

    expected_length = _resolve_sequence_length(
        sequence=sequence,
        sequence_length=sequence_length,
        required=False,
    )
    _check_representation_length(size, expected_length, "matrix dimension")

    binary = [
        [_binary_matrix_value(value, row, column) for column, value in enumerate(values)]
        for row, values in enumerate(rows)
    ]
    for i in range(size):
        if binary[i][i] != 0:
            _raise("self_pair", f"matrix diagonal at ({i}, {i}) encodes a self pair")
        for j in range(i + 1, size):
            if binary[i][j] != binary[j][i]:
                _raise(
                    "asymmetric_matrix",
                    f"matrix entries ({i}, {j}) and ({j}, {i}) differ",
                )

    pairs = [
        (i, j)
        for i in range(size)
        for j in range(i + 1, size)
        if binary[i][j] == 1
    ]
    return validate_pairs(
        pairs,
        sequence_length=size,
        allow_multiple_partners=allow_multiple_partners,
    )


def parse_structure(
    value: object,
    source_format: str,
    *,
    sequence: str | None = None,
    sequence_length: int | None = None,
    index_base: int = 0,
    allow_multiple_partners: bool = False,
) -> list[Pair]:
    """Dispatch a normalized-schema structure representation to its parser."""

    common = {
        "sequence": sequence,
        "sequence_length": sequence_length,
        "allow_multiple_partners": allow_multiple_partners,
    }
    if source_format == "dot_bracket":
        return parse_standard_dot_bracket(value, **common)  # type: ignore[arg-type]
    if source_format == "extended_dot_bracket":
        return parse_extended_dot_bracket(value, **common)  # type: ignore[arg-type]
    if source_format == "pair_list":
        return parse_pair_list(value, index_base=index_base, **common)  # type: ignore[arg-type]
    if source_format == "dense_matrix":
        return parse_dense_matrix(value, **common)  # type: ignore[arg-type]
    _raise("unsupported_format", f"unsupported structure source_format {source_format!r}")
