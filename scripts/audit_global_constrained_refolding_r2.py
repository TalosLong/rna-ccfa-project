#!/usr/bin/env python3
"""Audit the installed ViennaRNA hard-constraint interface for R2.

This is an environment/toy audit only.  It deliberately does not run a
Legacy121 refolding benchmark and never reads external77.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from rna_ccfa.structure import parse_standard_dot_bracket, validate_pairs


ROOT = Path(__file__).resolve().parents[1]
RNAFOLD = Path("/usr/bin/RNAfold")
MANIFESTS = ROOT / "results/evidence_guidance/e0/clean_manifests.jsonl"
OUT = ROOT / "results/global_constrained_refolding_r2/integrity"


def project_to_vienna(position: int) -> int:
    """Convert one project 0-based coordinate to ViennaRNA's 1-based coordinate."""

    if isinstance(position, bool) or not isinstance(position, int) or position < 0:
        raise ValueError(f"invalid project coordinate: {position!r}")
    return position + 1


def _crossing(first: tuple[int, int], second: tuple[int, int]) -> bool:
    i, j = first
    a, b = second
    return (i < a < j < b) or (a < i < b < j)


def build_constraint_string(
    sequence_length: int,
    forced_pairs: list[tuple[int, int]],
    forced_unpaired: list[int],
) -> str:
    """Build a ViennaRNA stdin constraint string, refusing non-PK conflicts."""

    if sequence_length < 0:
        raise ValueError("sequence length must be non-negative")
    pairs = validate_pairs(forced_pairs, sequence_length=sequence_length)
    unpaired = set(forced_unpaired)
    if any(isinstance(k, bool) or not isinstance(k, int) or not 0 <= k < sequence_length for k in unpaired):
        raise ValueError("forced-unpaired coordinate is outside the sequence")
    partners: dict[int, int] = {}
    for i, j in pairs:
        for endpoint, partner in ((i, j), (j, i)):
            if endpoint in partners and partners[endpoint] != partner:
                raise ValueError("incompatible forced pair partners")
            partners[endpoint] = partner
        if i in unpaired or j in unpaired:
            raise ValueError("a nucleotide cannot be forced paired and unpaired")
    for left, pair in enumerate(pairs):
        if any(_crossing(pair, other) for other in pairs[left + 1 :]):
            raise ValueError("crossing forced pairs are unsupported by standard DBN constraints")

    chars = ["."] * sequence_length
    for i, j in pairs:
        chars[project_to_vienna(i) - 1] = "("
        chars[project_to_vienna(j) - 1] = ")"
    for k in unpaired:
        if chars[k] != ".":
            raise ValueError("constraint conflict at forced-unpaired position")
        chars[project_to_vienna(k) - 1] = "x"
    return "".join(chars)


def _run(sequence: str, constraint: str | None) -> dict[str, object]:
    command = [str(RNAFOLD), "--noPS"]
    if constraint is not None:
        command.extend(["-C", "--enforceConstraint"])
        stdin = f">r2_toy\n{sequence}\n{constraint}\n"
    else:
        stdin = f">r2_toy\n{sequence}\n"
    completed = subprocess.run(command, input=stdin, text=True, capture_output=True, check=False, timeout=30)
    if completed.returncode != 0:
        raise RuntimeError(f"RNAfold failed ({completed.returncode}): {completed.stderr}")
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    structure_line = next((line.split()[0] for line in lines if len(line.split()[0]) == len(sequence) and set(line.split()[0]) <= set(".()")), None)
    if structure_line is None:
        raise RuntimeError(f"could not parse RNAfold output: {completed.stdout!r}")
    pairs = parse_standard_dot_bracket(structure_line, sequence=sequence)
    return {
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "dbn": structure_line,
        "pairs_zero_based": [list(pair) for pair in pairs],
    }


def _satisfies(result: dict[str, object], pairs: list[tuple[int, int]], unpaired: list[int]) -> bool:
    observed = {tuple(pair) for pair in result["pairs_zero_based"]}  # type: ignore[arg-type]
    return all(pair in observed for pair in pairs) and all(all(k not in pair for pair in observed) for k in unpaired)


def toy_audit() -> list[dict[str, object]]:
    cases = [
        {
            "name": "first_last_pair",
            "sequence": "GGGAAACCC",
            "pairs": [(0, 8)],
            "unpaired": [],
        },
        {
            "name": "last_position_unpaired",
            "sequence": "GGGAAACCC",
            "pairs": [],
            "unpaired": [8],
        },
        {
            "name": "internal_pair",
            "sequence": "GGGAAACCCGGG",
            "pairs": [(1, 10)],
            "unpaired": [],
        },
        {
            "name": "multiple_nested_pairs",
            "sequence": "GCGCGCGCGCGC",
            "pairs": [(0, 11), (1, 10)],
            "unpaired": [],
        },
        {
            "name": "internal_unpaired",
            "sequence": "GGGAAACCC",
            "pairs": [],
            "unpaired": [6],
        },
    ]
    results: list[dict[str, object]] = []
    for case in cases:
        sequence = str(case["sequence"])
        pairs = [tuple(pair) for pair in case["pairs"]]  # type: ignore[arg-type]
        unpaired = [int(k) for k in case["unpaired"]]  # type: ignore[arg-type]
        constraint = build_constraint_string(len(sequence), pairs, unpaired)
        result = _run(sequence, constraint)
        results.append({
            **case,
            "constraint": constraint,
            "vienna_positions": {
                "pairs": [[project_to_vienna(i), project_to_vienna(j)] for i, j in pairs],
                "unpaired": [project_to_vienna(k) for k in unpaired],
            },
            "rnafold": result,
            "constraint_satisfied": _satisfies(result, pairs, unpaired),
        })
        if not results[-1]["constraint_satisfied"]:
            raise AssertionError(f"toy constraint failed: {case['name']}")

    conflict_cases = [
        {"name": "crossing_pairs", "pairs": [(0, 5), (2, 7)], "unpaired": []},
        {"name": "pair_unpaired_conflict", "pairs": [(0, 8)], "unpaired": [0]},
    ]
    for case in conflict_cases:
        try:
            build_constraint_string(9, case["pairs"], case["unpaired"])  # type: ignore[arg-type]
        except ValueError as exc:
            results.append({"name": case["name"], "expected_rejection": str(exc), "constraint_satisfied": True})
        else:
            raise AssertionError(f"unsatisfiable toy case was not rejected: {case['name']}")
    return results


def crossing_manifest_audit() -> dict[str, object]:
    total = 0
    pair_manifests = 0
    crossing_manifests: list[dict[str, object]] = []
    if not MANIFESTS.exists():
        raise FileNotFoundError(MANIFESTS)
    for line in MANIFESTS.open(encoding="utf-8"):
        if not line.strip():
            continue
        manifest = json.loads(line)
        if manifest["noise_level_percent"] != 0:
            continue
        total += 1
        if manifest["evidence_channel"] != "POSITIVE_PAIR_EVIDENCE":
            continue
        pair_manifests += 1
        pairs = [(int(item["delivered_evidence_item"]["i"]), int(item["delivered_evidence_item"]["j"])) for item in manifest["items"]]
        if any(_crossing(pair, other) for left, pair in enumerate(pairs) for other in pairs[left + 1 :]):
            crossing_manifests.append({
                "rna_id": manifest["rna_id"],
                "density_percent": manifest["density_percent"],
                "evidence_seed": manifest["evidence_seed"],
            })
    return {
        "clean_manifest_count": total,
        "pair_channel_manifest_count": pair_manifests,
        "crossing_pair_manifest_count": len(crossing_manifests),
        "crossing_pair_manifest_fraction": len(crossing_manifests) / pair_manifests if pair_manifests else None,
        "crossing_rna_count": len({row["rna_id"] for row in crossing_manifests}),
        "crossing_examples": crossing_manifests[:10],
        "standard_non_pseudoknot_dbn_can_represent_all_pair_constraints": False,
    }


def main() -> None:
    if not RNAFOLD.exists() or shutil.which(str(RNAFOLD)) is None:
        raise FileNotFoundError(RNAFOLD)
    version = subprocess.run([str(RNAFOLD), "--version"], text=True, capture_output=True, check=True, timeout=30)
    basic_help_result = subprocess.run([str(RNAFOLD), "--help"], text=True, capture_output=True, check=True, timeout=30)
    full_help_result = subprocess.run([str(RNAFOLD), "--full-help"], text=True, capture_output=True, check=True, timeout=30)
    help_text = full_help_result.stdout
    binding_interpreters = ["python", "/root/miniconda3/bin/python", "/root/miniconda3/envs/nufold_P/bin/python"]
    binding_probe: list[dict[str, object]] = []
    for interpreter in binding_interpreters:
        probe = subprocess.run([interpreter, "-c", "import RNA; print(RNA.__version__)"], text=True, capture_output=True, check=False, timeout=30)
        binding_probe.append({"interpreter": interpreter, "returncode": probe.returncode, "stdout": probe.stdout, "stderr": probe.stderr})
    alternate_binaries: list[dict[str, object]] = []
    for candidate in (
        Path("/root/autodl-tmp/models/trRosettaRNA2/scripts/bin/RNAfold"),
        Path("/root/autodl-tmp/models/DRfold_repo/third_party/ViennaRNA-2.0.7/Progs/RNAfold"),
    ):
        if candidate.exists():
            result = subprocess.run([str(candidate), "--version"], text=True, capture_output=True, check=False, timeout=30)
            alternate_binaries.append({"path": str(candidate), "returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    payload = {
        "status": "R2_PROTOCOL_BLOCKED",
        "binary_path": str(RNAFOLD),
        "version_command": [str(RNAFOLD), "--version"],
        "version_stdout": version.stdout.strip(),
        "help_sha256": hashlib.sha256(basic_help_result.stdout.encode()).hexdigest(),
        "full_help_sha256": hashlib.sha256(help_text.encode()).hexdigest(),
        "constraint_help": {
            "supports_constraint_option": "--constraint" in help_text,
            "supports_enforce_constraint": "--enforceConstraint" in help_text,
            "supports_shape_soft_constraints": "--shape" in help_text,
            "supports_noLP": "--noLP" in help_text,
            "supports_dangles": "--dangles" in help_text,
            "supports_temperature": "--temp" in help_text,
        },
        "python_binding": {"installed": False, "probed_interpreters": binding_interpreters, "probe_results": binding_probe},
        "alternate_binary_versions": alternate_binaries,
        "hard_constraint_semantics": {
            "forced_pair_specific_partner": True,
            "forced_unpaired": True,
            "constraint_input": "stdin constraint line after sequence with -C --enforceConstraint",
            "constraint_file_support": "-C optional filename is a ViennaRNA command-file interface, not a plain DBN constraint line; R2 uses stdin",
            "commands_file_support": "--commands is advertised but not used",
            "coordinate_conversion": "project 0-based position + 1 = ViennaRNA 1-based position",
            "crossing_pair_sets": False,
        },
        "toy_tests": toy_audit(),
        "clean_manifest_crossing_audit": crossing_manifest_audit(),
        "blocker": "87 clean POSITIVE_PAIR_EVIDENCE manifests contain crossing delivered pairs; standard ViennaRNA non-pseudoknot DBN constraints cannot express all of them simultaneously without dropping or changing evidence semantics.",
        "external77_accessed": False,
        "legacy121_benchmark_started": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rnafold_version.txt").write_text(version.stdout, encoding="utf-8")
    (OUT / "rnafold_help.txt").write_text(basic_help_result.stdout, encoding="utf-8")
    (OUT / "rnafold_full_help.txt").write_text(help_text, encoding="utf-8")
    (OUT / "python_binding_probe.json").write_text(json.dumps(binding_probe, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "environment_audit.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "toy_sanity_results.json").write_text(json.dumps(payload["toy_tests"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "binary": payload["version_stdout"], "toy_tests": len(payload["toy_tests"]), "crossing_pair_manifests": payload["clean_manifest_crossing_audit"]["crossing_pair_manifest_count"]}, indent=2))


if __name__ == "__main__":
    main()
