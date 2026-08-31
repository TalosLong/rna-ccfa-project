"""Frozen RNAfold adapter and accounting helpers for R2/B2.

The folding adapter accepts only a sequence and delivered hard constraints.
Source-predictor identity and source-predicted structures are deliberately not
part of its interface.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .structure import Pair, parse_structure, validate_pairs


PAIR_CHANNEL = "POSITIVE_PAIR_EVIDENCE"
UNPAIRED_CHANNEL = "UNPAIRED_NUCLEOTIDE_EVIDENCE"
R2_PROTOCOL_VERSION = "global_constrained_refolding_r2_protocol_v1.0.2"
MINIMUM_LOOP_ENCLOSED_NUCLEOTIDES = 3
ALLOWED_PAIR_TYPES = frozenset({"AU", "UA", "GC", "CG", "GU", "UG"})


class ConstraintBuildError(ValueError):
    """A delivered constraint cannot be represented by the frozen solver."""

    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True, slots=True)
class ViennaRNAConfig:
    binary: str = "/usr/bin/RNAfold"
    expected_version: str = "RNAfold 2.4.17"
    timeout_seconds: float = 30.0
    retry_count: int = 0
    temperature_celsius: float = 37.0
    dangles: int = 2
    parameter_set: str = "ViennaRNA default"
    mode: str = "linear MFE standard non-pseudoknot DP"

    def command(self, *, constrained: bool) -> list[str]:
        command = [self.binary, "--noPS"]
        if constrained:
            command.extend(["-C", "--enforceConstraint"])
        return command

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value.update(
            {
                "noLP": False,
                "noGU": False,
                "noClosingGU": False,
                "gquad": False,
                "circular": False,
                "soft_constraints": False,
            }
        )
        return value


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def project_to_vienna(position: int) -> int:
    """Convert a project zero-based coordinate to ViennaRNA one-based form."""

    if isinstance(position, bool) or not isinstance(position, int) or position < 0:
        raise ValueError(f"invalid project coordinate: {position!r}")
    return position + 1


def pairs_cross(first: Pair, second: Pair) -> bool:
    i, j = first
    k, l = second
    return (i < k < j < l) or (k < i < l < j)


def contains_crossing_pairs(pairs: Iterable[Sequence[int]], sequence_length: int) -> bool:
    canonical = validate_pairs(pairs, sequence_length=sequence_length)
    return any(
        pairs_cross(pair, other)
        for index, pair in enumerate(canonical)
        for other in canonical[index + 1 :]
    )


def minimum_loop_compatible(pair: Sequence[int]) -> bool:
    """Return whether one canonical pair meets frozen ViennaRNA TURN semantics."""

    if len(pair) != 2:
        raise ValueError("pair must contain exactly two coordinates")
    i, j = pair
    if isinstance(i, bool) or isinstance(j, bool) or not isinstance(i, int) or not isinstance(j, int):
        raise ValueError("pair coordinates must be integers")
    if i < 0 or i >= j:
        raise ValueError("pair must be canonical with 0 <= i < j")
    return j - i - 1 >= MINIMUM_LOOP_ENCLOSED_NUCLEOTIDES


def pair_capability_flags(
    pairs: Iterable[Sequence[int]], sequence_length: int
) -> dict[str, bool | int | None]:
    """Classify crossing and minimum-loop solver capability independently."""

    canonical = validate_pairs(pairs, sequence_length=sequence_length)
    separations = [j - i for i, j in canonical]
    return {
        "crossing_flag": any(
            pairs_cross(pair, other)
            for index, pair in enumerate(canonical)
            for other in canonical[index + 1 :]
        ),
        "minimum_loop_flag": any(not minimum_loop_compatible(pair) for pair in canonical),
        "minimum_pair_separation": min(separations) if separations else None,
    }


def build_constraint_string(
    sequence_length: int,
    pair_items: Iterable[Sequence[int]] = (),
    unpaired_items: Iterable[int] = (),
) -> str:
    """Build the exact frozen ViennaRNA hard-constraint string."""

    if isinstance(sequence_length, bool) or not isinstance(sequence_length, int) or sequence_length <= 0:
        raise ConstraintBuildError("UNSATISFIABLE_CONSTRAINT", "sequence length must be a positive integer")
    try:
        pairs = validate_pairs(pair_items, sequence_length=sequence_length)
    except ValueError as exc:
        raise ConstraintBuildError("UNSATISFIABLE_CONSTRAINT", str(exc)) from exc

    raw_unpaired = list(unpaired_items)
    if len(set(raw_unpaired)) != len(raw_unpaired):
        raise ConstraintBuildError("UNSATISFIABLE_CONSTRAINT", "duplicate forced-unpaired coordinate")
    unpaired: set[int] = set()
    for position in raw_unpaired:
        if isinstance(position, bool) or not isinstance(position, int) or not 0 <= position < sequence_length:
            raise ConstraintBuildError(
                "UNSATISFIABLE_CONSTRAINT", "forced-unpaired coordinate is outside the sequence"
            )
        unpaired.add(position)

    endpoints = {endpoint for pair in pairs for endpoint in pair}
    if endpoints & unpaired:
        raise ConstraintBuildError(
            "UNSATISFIABLE_CONSTRAINT", "a nucleotide cannot be forced paired and unpaired"
        )
    if any(
        pairs_cross(pair, other)
        for index, pair in enumerate(pairs)
        for other in pairs[index + 1 :]
    ):
        raise ConstraintBuildError(
            "UNSUPPORTED_CROSSING_CONSTRAINT",
            "crossing forced pairs are unsupported by standard DBN constraints",
        )
    short_pairs = [pair for pair in pairs if not minimum_loop_compatible(pair)]
    if short_pairs:
        raise ConstraintBuildError(
            "UNSUPPORTED_MINIMUM_LOOP_CONSTRAINT",
            "forced pairs violate frozen ViennaRNA minimum loop size: "
            f"{short_pairs}",
        )

    symbols = ["."] * sequence_length
    for i, j in pairs:
        symbols[project_to_vienna(i) - 1] = "("
        symbols[project_to_vienna(j) - 1] = ")"
    for position in sorted(unpaired):
        symbols[project_to_vienna(position) - 1] = "x"
    return "".join(symbols)


def query_rnafold_version(config: ViennaRNAConfig) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [config.binary, "--version"],
            text=True,
            capture_output=True,
            check=False,
            timeout=config.timeout_seconds,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"could not query frozen RNAfold binary: {exc}") from exc
    runtime = time.perf_counter() - started
    observed = completed.stdout.strip()
    if completed.returncode != 0 or observed != config.expected_version:
        raise RuntimeError(
            f"frozen RNAfold mismatch: returncode={completed.returncode}, version={observed!r}"
        )
    return {
        "command": [config.binary, "--version"],
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "return_code": completed.returncode,
        "runtime_seconds": runtime,
        "version": observed,
    }


def run_constrained_rnafold(
    sequence: str,
    constraint: str | None,
    *,
    record_id: str,
    config: ViennaRNAConfig,
) -> dict[str, Any]:
    """Run one frozen RNAfold command without a shell or adaptive retry."""

    if not sequence or any(base not in "ACGU" for base in sequence):
        return {
            "status": "INVALID_SEQUENCE",
            "status_detail": "R2 requires a non-empty ACGU sequence",
            "command": [],
            "stdin": "",
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "runtime_seconds": 0.0,
            "attempt_count": 0,
        }
    constrained = constraint is not None
    if constrained and len(constraint) != len(sequence):
        return {
            "status": "CONSTRAINT_LENGTH_MISMATCH",
            "status_detail": "constraint and sequence lengths differ",
            "command": config.command(constrained=True),
            "stdin": "",
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "runtime_seconds": 0.0,
            "attempt_count": 0,
        }
    command = config.command(constrained=constrained)
    stdin = f">{record_id}\n{sequence}\n"
    if constrained:
        stdin += f"{constraint}\n"
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            input=stdin,
            text=True,
            capture_output=True,
            check=False,
            timeout=config.timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "RNAFOLD_TIMEOUT",
            "status_detail": f"timeout after {config.timeout_seconds} seconds",
            "command": command,
            "stdin": stdin,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "return_code": None,
            "runtime_seconds": time.perf_counter() - started,
            "attempt_count": 1,
        }
    except OSError as exc:
        return {
            "status": "RNAFOLD_PROCESS_ERROR",
            "status_detail": str(exc),
            "command": command,
            "stdin": stdin,
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "runtime_seconds": time.perf_counter() - started,
            "attempt_count": 1,
        }
    status = "PASS" if completed.returncode == 0 else "RNAFOLD_NONZERO_EXIT"
    return {
        "status": status,
        "status_detail": "" if status == "PASS" else f"RNAfold exited with {completed.returncode}",
        "command": command,
        "stdin": stdin,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "return_code": completed.returncode,
        "runtime_seconds": time.perf_counter() - started,
        "attempt_count": 1,
    }


_DBN_TOKEN = re.compile(r"^[.()]+$")


def parse_and_validate_output(
    run_result: dict[str, Any],
    *,
    sequence: str,
    forced_pairs: Iterable[Sequence[int]] = (),
    forced_unpaired: Iterable[int] = (),
) -> dict[str, Any]:
    """Parse a successful CLI result and fail closed on any invalid output."""

    result = dict(run_result)
    result.update(
        {
            "output_dbn": None,
            "pairs_zero_based": None,
            "output_sha256": None,
            "output_valid": False,
            "constraint_satisfied": False,
        }
    )
    if result.get("status") != "PASS":
        return result
    candidates = []
    for line in str(result.get("stdout", "")).splitlines():
        fields = line.strip().split()
        if fields and len(fields[0]) == len(sequence) and _DBN_TOKEN.fullmatch(fields[0]):
            candidates.append(fields[0])
    if len(candidates) != 1:
        result["status"] = "OUTPUT_PARSE_ERROR"
        result["status_detail"] = f"expected exactly one length-matched DBN token, found {len(candidates)}"
        return result
    dbn = candidates[0]
    try:
        pairs = parse_structure(dbn, "dot_bracket", sequence=sequence)
        pairs = validate_pairs(pairs, sequence=sequence)
    except ValueError as exc:
        result["status"] = "OUTPUT_PARSE_ERROR"
        result["status_detail"] = str(exc)
        return result
    illegal = [pair for pair in pairs if sequence[pair[0]] + sequence[pair[1]] not in ALLOWED_PAIR_TYPES]
    if illegal:
        result["status"] = "ILLEGAL_PAIR"
        result["status_detail"] = f"noncanonical RNAfold output pairs: {illegal[:5]}"
        return result
    if contains_crossing_pairs(pairs, len(sequence)):
        result["status"] = "UNEXPECTED_CROSSING_OUTPUT"
        result["status_detail"] = "standard RNAfold output contains crossing pairs"
        return result
    observed = set(pairs)
    required = set(validate_pairs(forced_pairs, sequence_length=len(sequence)))
    unpaired = set(forced_unpaired)
    missing = sorted(required - observed)
    paired_unpaired = sorted(position for position in unpaired if any(position in pair for pair in observed))
    if missing or paired_unpaired:
        result["status"] = "CONSTRAINT_SATISFACTION_FAIL"
        result["status_detail"] = f"missing_forced_pairs={missing}; paired_forced_unpaired={paired_unpaired}"
        return result
    result.update(
        {
            "output_dbn": dbn,
            "pairs_zero_based": [list(pair) for pair in pairs],
            "output_sha256": canonical_sha256(
                {"sequence": sequence, "output_dbn": dbn, "pairs_zero_based": pairs}
            ),
            "output_valid": True,
            "constraint_satisfied": True,
        }
    )
    return result


def full_refold_edit_decomposition(
    original: Iterable[Sequence[int]],
    ground_truth: Iterable[Sequence[int]],
    refolded: Iterable[Sequence[int]],
    *,
    sequence_length: int,
) -> dict[str, set[Pair]]:
    """Return the frozen mutually auditable full-refold pair partitions."""

    source = set(validate_pairs(original, sequence_length=sequence_length))
    truth = set(validate_pairs(ground_truth, sequence_length=sequence_length))
    result = set(validate_pairs(refolded, sequence_length=sequence_length))
    parts = {
        "preserved_tp": source & truth & result,
        "lost_tp": (source & truth) - result,
        "removed_fp": (source - truth) - result,
        "preserved_original_fp": (source - truth) & result,
        "new_tp": (result - source) & truth,
        "new_fp": (result - source) - truth,
        "unchanged_pairs": source & result,
        "deleted_pairs": source - result,
        "added_pairs": result - source,
    }
    if parts["preserved_tp"] & parts["lost_tp"]:
        raise AssertionError("preserved and lost TP overlap")
    if len(parts["preserved_tp"]) + len(parts["lost_tp"]) != len(source & truth):
        raise AssertionError("original TP accounting identity failed")
    if len(parts["removed_fp"]) + len(parts["preserved_original_fp"]) != len(source - truth):
        raise AssertionError("original FP accounting identity failed")
    if len(parts["new_tp"]) + len(parts["new_fp"]) != len(parts["added_pairs"]):
        raise AssertionError("added-pair accounting identity failed")
    if parts["unchanged_pairs"] | parts["deleted_pairs"] != source:
        raise AssertionError("source pair partition failed")
    if parts["unchanged_pairs"] | parts["added_pairs"] != result:
        raise AssertionError("refolded pair partition failed")
    return parts


def pair_scope_partition(
    ground_truth: set[Pair],
    original: set[Pair],
    refolded: set[Pair],
    evidence_pairs: set[Pair],
) -> dict[str, set[Pair]]:
    universe = ground_truth | original | refolded
    endpoints = {endpoint for pair in evidence_pairs for endpoint in pair}
    direct = set(evidence_pairs)
    local = {pair for pair in universe - direct if set(pair) & endpoints}
    non_evidenced = universe - direct - local
    if direct & local or direct & non_evidenced or local & non_evidenced:
        raise AssertionError("pair evidence scopes overlap")
    if direct | local | non_evidenced != universe:
        raise AssertionError("pair evidence scopes are not exhaustive")
    return {
        "DIRECT_EVIDENCE_EFFECT": direct,
        "LOCAL_CONFLICT_EFFECT": local,
        "NON_EVIDENCED_EFFECT": non_evidenced,
    }


def unpaired_scope_partition(
    ground_truth: set[Pair],
    original: set[Pair],
    refolded: set[Pair],
    evidence_positions: set[int],
) -> dict[str, set[Pair]]:
    universe = ground_truth | original | refolded
    local = {pair for pair in universe if set(pair) & evidence_positions}
    non_evidenced = universe - local
    if local & non_evidenced or local | non_evidenced != universe:
        raise AssertionError("unpaired evidence pair scopes are not disjoint/exhaustive")
    return {
        "DIRECT_EVIDENCE_EFFECT": set(),
        "LOCAL_CONFLICT_EFFECT": local,
        "NON_EVIDENCED_EFFECT": non_evidenced,
    }


def safe_ratio(numerator: int | float, denominator: int | float) -> float | None:
    """Return the frozen NA-on-zero-denominator ratio."""

    return numerator / denominator if denominator else None
