"""Deterministic simulated structural-evidence generation and validation.

The generator deliberately accepts only an RNA identifier, sequence, and exact
ground-truth pair set. Predictor outputs and prediction-error annotations are
not inputs to any sampling or corruption function.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .rule_refinement import WATSON_CRICK_WOBBLE_TYPES
from .structure import Pair, validate_pairs

PROTOCOL_VERSION = "simulated_evidence_v1"
POSITIVE_PAIR_EVIDENCE = "POSITIVE_PAIR_EVIDENCE"
UNPAIRED_NUCLEOTIDE_EVIDENCE = "UNPAIRED_NUCLEOTIDE_EVIDENCE"
EVIDENCE_CHANNELS = (POSITIVE_PAIR_EVIDENCE, UNPAIRED_NUCLEOTIDE_EVIDENCE)
DENSITY_GRID_PERCENT = (0, 1, 5, 10, 20, 50)
NOISE_GRID_PERCENT = (0, 5, 10, 20, 30)
EVIDENCE_SEEDS = (101, 103, 107, 109, 113)
ALLOWED_GENERATOR_INPUT_FIELDS = frozenset(
    {"rna_id", "sequence", "ground_truth_pairs"}
)
FORBIDDEN_GENERATOR_INPUT_FIELDS = frozenset(
    {
        "predicted_pairs",
        "predicted_structure",
        "source_model",
        "pair_scores",
        "tp_pairs",
        "fp_pairs",
        "fn_pairs",
        "wrong_partner",
        "error_labels",
    }
)


class EvidenceValidationError(ValueError):
    """A simulated-evidence manifest violates the frozen schema."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_canonical(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _stable_rng(*parts: object) -> random.Random:
    payload = "\x1f".join(str(part) for part in parts)
    seed = int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:16], "big")
    return random.Random(seed)


def _validated_gt(sequence: str, ground_truth_pairs: Iterable[Sequence[int]]) -> tuple[Pair, ...]:
    if not isinstance(sequence, str) or not sequence:
        raise EvidenceValidationError("sequence must be a non-empty string")
    if any(base not in "ACGU" for base in sequence):
        raise EvidenceValidationError("simulated_evidence_v1 requires an ACGU-only sequence")
    return tuple(validate_pairs(ground_truth_pairs, sequence=sequence))


def validate_generator_input_fields(fields: Iterable[str]) -> None:
    """Fail if a caller attempts to provide anything beyond the GT-only contract."""

    supplied = set(fields)
    if supplied != set(ALLOWED_GENERATOR_INPUT_FIELDS):
        forbidden = sorted(supplied & FORBIDDEN_GENERATOR_INPUT_FIELDS)
        unexpected = sorted(supplied - ALLOWED_GENERATOR_INPUT_FIELDS)
        missing = sorted(ALLOWED_GENERATOR_INPUT_FIELDS - supplied)
        raise EvidenceValidationError(
            "generator inputs must be exactly rna_id, sequence, and "
            f"ground_truth_pairs; forbidden={forbidden}, unexpected={unexpected}, "
            f"missing={missing}"
        )


def pair_evidence_universe(
    sequence: str, ground_truth_pairs: Iterable[Sequence[int]]
) -> tuple[Pair, ...]:
    """Return the sorted exact-GT pair evidence universe."""

    return _validated_gt(sequence, ground_truth_pairs)


def unpaired_evidence_universe(
    sequence: str, ground_truth_pairs: Iterable[Sequence[int]]
) -> tuple[int, ...]:
    """Return sorted positions unpaired in the exact GT structure."""

    pairs = _validated_gt(sequence, ground_truth_pairs)
    paired = {endpoint for pair in pairs for endpoint in pair}
    return tuple(position for position in range(len(sequence)) if position not in paired)


def round_half_up_count(universe_size: int, percentage: int, *, minimum_one: bool) -> int:
    """Round ``percentage * universe_size`` to nearest integer, with .5 upward."""

    if isinstance(universe_size, bool) or universe_size < 0:
        raise EvidenceValidationError("universe_size must be a non-negative integer")
    if isinstance(percentage, bool) or percentage < 0 or percentage > 100:
        raise EvidenceValidationError("percentage must be an integer in [0, 100]")
    count = (universe_size * percentage + 50) // 100
    if minimum_one and percentage > 0 and universe_size > 0 and count == 0:
        count = 1
    return min(universe_size, count)


def _item_payload(channel: str, item: Pair | int) -> dict[str, int]:
    if channel == POSITIVE_PAIR_EVIDENCE:
        i, j = item  # type: ignore[misc]
        return {"i": int(i), "j": int(j)}
    if channel == UNPAIRED_NUCLEOTIDE_EVIDENCE:
        return {"i": int(item)}
    raise EvidenceValidationError(f"unknown evidence channel: {channel}")


def _source_gt_hash(rna_id: str, sequence: str, pairs: Sequence[Pair]) -> str:
    return sha256_canonical(
        {"rna_id": rna_id, "sequence": sequence, "ground_truth_pairs": pairs}
    )


def _with_manifest_hash(manifest: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(manifest)
    result.pop("manifest_payload_sha256", None)
    result["manifest_payload_sha256"] = sha256_canonical(result)
    return result


def build_clean_evidence_manifest(
    *,
    rna_id: str,
    sequence: str,
    ground_truth_pairs: Iterable[Sequence[int]],
    evidence_channel: str,
    density_percent: int,
    evidence_seed: int,
    protocol_version: str = PROTOCOL_VERSION,
) -> dict[str, Any]:
    """Build one clean manifest using only the selected GT evidence universe."""

    validate_generator_input_fields(("rna_id", "sequence", "ground_truth_pairs"))
    if not isinstance(rna_id, str) or not rna_id:
        raise EvidenceValidationError("rna_id must be a non-empty string")
    if protocol_version != PROTOCOL_VERSION:
        raise EvidenceValidationError("protocol_version is not the frozen version")
    if evidence_channel not in EVIDENCE_CHANNELS:
        raise EvidenceValidationError(f"unknown evidence channel: {evidence_channel}")
    if isinstance(density_percent, bool) or density_percent not in DENSITY_GRID_PERCENT:
        raise EvidenceValidationError("density is outside the frozen grid")
    if isinstance(evidence_seed, bool) or evidence_seed not in EVIDENCE_SEEDS:
        raise EvidenceValidationError("evidence seed is outside the frozen seed set")
    pairs = _validated_gt(sequence, ground_truth_pairs)
    universe: tuple[Pair | int, ...]
    if evidence_channel == POSITIVE_PAIR_EVIDENCE:
        universe = pairs
    else:
        universe = unpaired_evidence_universe(sequence, pairs)
    selected_count = round_half_up_count(
        len(universe), density_percent, minimum_one=True
    )
    rng = _stable_rng(
        protocol_version, rna_id, evidence_channel, density_percent, evidence_seed, "selection"
    )
    selected = sorted(rng.sample(list(universe), selected_count)) if selected_count else []
    items = [
        {
            "item_index": index,
            "status": "CLEAN",
            "corruption_requested": False,
            "original_clean_evidence_item": _item_payload(evidence_channel, item),
            "delivered_evidence_item": _item_payload(evidence_channel, item),
        }
        for index, item in enumerate(selected)
    ]
    manifest_id = (
        f"{protocol_version}__{rna_id}__{evidence_channel.lower()}__"
        f"density_{density_percent:02d}__seed_{evidence_seed}__noise_00"
    )
    manifest = {
        "schema_version": PROTOCOL_VERSION,
        "protocol_version": protocol_version,
        "manifest_id": manifest_id,
        "rna_id": rna_id,
        "sequence_length": len(sequence),
        "evidence_channel": evidence_channel,
        "density_percent": density_percent,
        "evidence_seed": evidence_seed,
        "noise_level_percent": 0,
        "eligible_universe_size": len(universe),
        "selected_item_count": selected_count,
        "minimum_one_applied": bool(
            density_percent > 0
            and len(universe) > 0
            and (len(universe) * density_percent + 50) // 100 == 0
        ),
        "requested_corruption_count": 0,
        "successful_corruption_count": 0,
        "unavailable_corruption_count": 0,
        "delivered_item_count": selected_count,
        "realized_corruption_fraction": 0.0,
        "source_gt_sha256": _source_gt_hash(rna_id, sequence, pairs),
        "generator_inputs": ["rna_id", "sequence", "ground_truth_pairs"],
        "items": items,
    }
    result = _with_manifest_hash(manifest)
    validate_evidence_manifest(result, sequence=sequence, ground_truth_pairs=pairs)
    return result


def _pair_from_item(item: Mapping[str, Any]) -> Pair:
    return int(item["i"]), int(item["j"])


def _corruption_indices(manifest: Mapping[str, Any], noise_percent: int) -> set[int]:
    count = round_half_up_count(
        int(manifest["selected_item_count"]), noise_percent, minimum_one=False
    )
    if not count:
        return set()
    rng = _stable_rng(
        manifest["protocol_version"],
        manifest["rna_id"],
        manifest["evidence_channel"],
        manifest["density_percent"],
        manifest["evidence_seed"],
        noise_percent,
        "corruption_selection",
    )
    return set(rng.sample(range(int(manifest["selected_item_count"])), count))


def corrupt_evidence_manifest(
    clean_manifest: Mapping[str, Any],
    *,
    sequence: str,
    ground_truth_pairs: Iterable[Sequence[int]],
    noise_level_percent: int,
) -> dict[str, Any]:
    """Deterministically corrupt selected observations under the frozen policy."""

    if noise_level_percent not in NOISE_GRID_PERCENT or noise_level_percent == 0:
        raise EvidenceValidationError("corruption requires one of the frozen nonzero noise levels")
    pairs = _validated_gt(sequence, ground_truth_pairs)
    validate_evidence_manifest(clean_manifest, sequence=sequence, ground_truth_pairs=pairs)
    if int(clean_manifest["noise_level_percent"]) != 0:
        raise EvidenceValidationError("corruption input must be a clean manifest")

    manifest = json.loads(json.dumps(clean_manifest))
    manifest.pop("manifest_payload_sha256", None)
    manifest["noise_level_percent"] = noise_level_percent
    manifest["manifest_id"] = str(manifest["manifest_id"]).rsplit("noise_", 1)[0] + f"noise_{noise_level_percent:02d}"
    chosen = _corruption_indices(clean_manifest, noise_level_percent)
    manifest["requested_corruption_count"] = len(chosen)
    gt_set = set(pairs)

    if manifest["evidence_channel"] == POSITIVE_PAIR_EVIDENCE:
        preserved_endpoint: dict[int, int] = {}
        for index in sorted(chosen):
            clean_pair = _pair_from_item(manifest["items"][index]["original_clean_evidence_item"])
            rng = _stable_rng(manifest["manifest_id"], index, "preserved_endpoint")
            preserved_endpoint[index] = clean_pair[rng.randrange(2)]
        reserved = {
            endpoint
            for item in manifest["items"]
            if int(item["item_index"]) not in chosen
            for endpoint in _pair_from_item(item["original_clean_evidence_item"])
        }
        reserved.update(preserved_endpoint.values())
        delivered_pairs: set[Pair] = {
            _pair_from_item(item["delivered_evidence_item"])
            for item in manifest["items"]
            if int(item["item_index"]) not in chosen
        }
        for index in sorted(chosen):
            item = manifest["items"][index]
            item["corruption_requested"] = True
            endpoint = preserved_endpoint[index]
            candidates: list[Pair] = []
            for alternative in range(len(sequence)):
                if alternative == endpoint or alternative in reserved:
                    continue
                candidate = tuple(sorted((endpoint, alternative)))
                if candidate in gt_set or candidate in delivered_pairs:
                    continue
                if sequence[candidate[0]] + sequence[candidate[1]] not in WATSON_CRICK_WOBBLE_TYPES:
                    continue
                candidates.append(candidate)
            if not candidates:
                item["status"] = "CORRUPTION_UNAVAILABLE"
                item["delivered_evidence_item"] = None
                continue
            rng = _stable_rng(manifest["manifest_id"], index, "alternative_partner")
            delivered = candidates[rng.randrange(len(candidates))]
            item["status"] = "CORRUPTED"
            item["delivered_evidence_item"] = _item_payload(POSITIVE_PAIR_EVIDENCE, delivered)
            delivered_pairs.add(delivered)
            reserved.update(delivered)
    else:
        paired_positions = sorted({endpoint for pair in pairs for endpoint in pair})
        used: set[int] = {
            int(item["delivered_evidence_item"]["i"])
            for item in manifest["items"]
            if int(item["item_index"]) not in chosen
        }
        for index in sorted(chosen):
            item = manifest["items"][index]
            item["corruption_requested"] = True
            candidates = [position for position in paired_positions if position not in used]
            if not candidates:
                item["status"] = "CORRUPTION_UNAVAILABLE"
                item["delivered_evidence_item"] = None
                continue
            rng = _stable_rng(manifest["manifest_id"], index, "paired_position")
            delivered = candidates[rng.randrange(len(candidates))]
            item["status"] = "CORRUPTED"
            item["delivered_evidence_item"] = _item_payload(
                UNPAIRED_NUCLEOTIDE_EVIDENCE, delivered
            )
            used.add(delivered)

    successful = sum(item["status"] == "CORRUPTED" for item in manifest["items"])
    unavailable = sum(item["status"] == "CORRUPTION_UNAVAILABLE" for item in manifest["items"])
    manifest["successful_corruption_count"] = successful
    manifest["unavailable_corruption_count"] = unavailable
    manifest["delivered_item_count"] = int(manifest["selected_item_count"]) - unavailable
    manifest["realized_corruption_fraction"] = (
        successful / int(manifest["selected_item_count"])
        if int(manifest["selected_item_count"])
        else 0.0
    )
    result = _with_manifest_hash(manifest)
    validate_evidence_manifest(result, sequence=sequence, ground_truth_pairs=pairs)
    return result


def validate_evidence_manifest(
    manifest: Mapping[str, Any],
    *,
    sequence: str,
    ground_truth_pairs: Iterable[Sequence[int]],
) -> None:
    """Validate schema, evidence semantics, coordinates, uniqueness, and hash."""

    pairs = _validated_gt(sequence, ground_truth_pairs)
    if manifest.get("schema_version") != PROTOCOL_VERSION:
        raise EvidenceValidationError("unexpected evidence schema version")
    if manifest.get("protocol_version") != PROTOCOL_VERSION:
        raise EvidenceValidationError("unexpected evidence protocol version")
    if not isinstance(manifest.get("rna_id"), str) or not manifest["rna_id"]:
        raise EvidenceValidationError("invalid RNA ID")
    if set(manifest.get("generator_inputs", ())) != set(ALLOWED_GENERATOR_INPUT_FIELDS):
        raise EvidenceValidationError("manifest violates the GT-only generator input contract")
    if manifest.get("source_gt_sha256") != _source_gt_hash(
        str(manifest["rna_id"]), sequence, pairs
    ):
        raise EvidenceValidationError("source GT hash mismatch")
    if manifest.get("evidence_channel") not in EVIDENCE_CHANNELS:
        raise EvidenceValidationError("unknown evidence channel")
    if int(manifest.get("sequence_length", -1)) != len(sequence):
        raise EvidenceValidationError("sequence length mismatch")
    expected_hash = sha256_canonical(
        {key: value for key, value in manifest.items() if key != "manifest_payload_sha256"}
    )
    if manifest.get("manifest_payload_sha256") != expected_hash:
        raise EvidenceValidationError("manifest payload hash mismatch")
    channel = str(manifest["evidence_channel"])
    universe: set[Pair] | set[int]
    if channel == POSITIVE_PAIR_EVIDENCE:
        universe = set(pairs)
    else:
        universe = set(unpaired_evidence_universe(sequence, pairs))
    if int(manifest["eligible_universe_size"]) != len(universe):
        raise EvidenceValidationError("eligible universe size mismatch")
    density = manifest.get("density_percent")
    seed = manifest.get("evidence_seed")
    noise = manifest.get("noise_level_percent")
    if isinstance(density, bool) or density not in DENSITY_GRID_PERCENT:
        raise EvidenceValidationError("manifest density is outside the frozen grid")
    if isinstance(seed, bool) or seed not in EVIDENCE_SEEDS:
        raise EvidenceValidationError("manifest seed is outside the frozen set")
    if isinstance(noise, bool) or noise not in NOISE_GRID_PERCENT:
        raise EvidenceValidationError("manifest noise is outside the frozen grid")
    items = list(manifest["items"])
    if int(manifest["selected_item_count"]) != len(items):
        raise EvidenceValidationError("selected item count mismatch")
    expected_selected = round_half_up_count(
        len(universe), int(density), minimum_one=True
    )
    if len(items) != expected_selected:
        raise EvidenceValidationError("selected item count violates frozen rounding")
    expected_minimum_one = bool(
        int(density) > 0
        and len(universe) > 0
        and (len(universe) * int(density) + 50) // 100 == 0
    )
    if bool(manifest.get("minimum_one_applied")) != expected_minimum_one:
        raise EvidenceValidationError("minimum-one flag mismatch")
    delivered: list[Pair | int] = []
    gt_set = set(pairs)
    paired_positions = {endpoint for pair in pairs for endpoint in pair}
    successful = unavailable = 0
    for expected_index, item in enumerate(items):
        if int(item["item_index"]) != expected_index:
            raise EvidenceValidationError("item indices must be contiguous")
        original_payload = item["original_clean_evidence_item"]
        original: Pair | int
        if channel == POSITIVE_PAIR_EVIDENCE:
            original = _pair_from_item(original_payload)
        else:
            original = int(original_payload["i"])
        if original not in universe:
            raise EvidenceValidationError("clean evidence item is outside its GT universe")
        status = item["status"]
        payload = item["delivered_evidence_item"]
        if status == "CLEAN":
            if item.get("corruption_requested"):
                raise EvidenceValidationError("clean item cannot request corruption")
            if payload != original_payload:
                raise EvidenceValidationError("clean item was modified")
        elif status == "CORRUPTED":
            if not item.get("corruption_requested"):
                raise EvidenceValidationError("corrupted item lacks request flag")
            successful += 1
            if payload is None:
                raise EvidenceValidationError("corrupted item has no delivered value")
            if channel == POSITIVE_PAIR_EVIDENCE:
                value = _pair_from_item(payload)
                validate_pairs([value], sequence=sequence)
                if value in gt_set or len(set(value) & set(original)) != 1:  # type: ignore[arg-type]
                    raise EvidenceValidationError("pair corruption is not a one-endpoint non-GT pair")
                if sequence[value[0]] + sequence[value[1]] not in WATSON_CRICK_WOBBLE_TYPES:
                    raise EvidenceValidationError("corrupted pair type is not allowed")
            else:
                value = int(payload["i"])
                if value < 0 or value >= len(sequence) or value not in paired_positions:
                    raise EvidenceValidationError("unpaired corruption is not a GT-paired position")
        elif status == "CORRUPTION_UNAVAILABLE":
            if not item.get("corruption_requested"):
                raise EvidenceValidationError("unavailable item lacks request flag")
            unavailable += 1
            if payload is not None:
                raise EvidenceValidationError("unavailable corruption must not deliver an item")
            continue
        else:
            raise EvidenceValidationError(f"unknown item status: {status}")
        if channel == POSITIVE_PAIR_EVIDENCE:
            delivered.append(_pair_from_item(payload))
        else:
            delivered.append(int(payload["i"]))
    if len(delivered) != len(set(delivered)):
        raise EvidenceValidationError("duplicate delivered evidence items")
    if channel == POSITIVE_PAIR_EVIDENCE:
        validate_pairs(delivered, sequence=sequence)
    if successful != int(manifest["successful_corruption_count"]):
        raise EvidenceValidationError("successful corruption count mismatch")
    if unavailable != int(manifest["unavailable_corruption_count"]):
        raise EvidenceValidationError("unavailable corruption count mismatch")
    if len(delivered) != int(manifest["delivered_item_count"]):
        raise EvidenceValidationError("delivered item count mismatch")
    if successful + unavailable != int(manifest["requested_corruption_count"]):
        raise EvidenceValidationError("requested corruption accounting mismatch")
    expected_requested = round_half_up_count(
        len(items), int(noise), minimum_one=False
    )
    if int(manifest["requested_corruption_count"]) != expected_requested:
        raise EvidenceValidationError("requested corruption count violates frozen rounding")
    expected_fraction = successful / len(items) if items else 0.0
    if abs(float(manifest["realized_corruption_fraction"]) - expected_fraction) > 1e-15:
        raise EvidenceValidationError("realized corruption fraction mismatch")


def evidence_jsonl_bytes(manifests: Iterable[Mapping[str, Any]]) -> bytes:
    """Serialize manifests in deterministic identifier order."""

    ordered = sorted(manifests, key=lambda row: str(row["manifest_id"]))
    return ("".join(_canonical_json(row) + "\n" for row in ordered)).encode("utf-8")


def apply_pair_protect_only(
    predicted_pairs: Iterable[Sequence[int]],
    evidence_pairs: Iterable[Sequence[int]],
    *,
    sequence_length: int,
) -> list[Pair]:
    """Apply the frozen PAIR_PROTECT_ONLY transformation."""

    prediction = set(validate_pairs(predicted_pairs, sequence_length=sequence_length))
    evidence = set(validate_pairs(evidence_pairs, sequence_length=sequence_length))
    evidence_endpoints = {endpoint for pair in evidence for endpoint in pair}
    result = {
        pair
        for pair in prediction
        if pair in evidence or not (set(pair) & evidence_endpoints)
    }
    return validate_pairs(result, sequence_length=sequence_length)


def apply_pair_hard_enforce(
    predicted_pairs: Iterable[Sequence[int]],
    evidence_pairs: Iterable[Sequence[int]],
    *,
    sequence_length: int,
) -> list[Pair]:
    """Apply the frozen PAIR_HARD_ENFORCE transformation."""

    protected = apply_pair_protect_only(
        predicted_pairs, evidence_pairs, sequence_length=sequence_length
    )
    evidence = validate_pairs(evidence_pairs, sequence_length=sequence_length)
    return validate_pairs([*protected, *[pair for pair in evidence if pair not in protected]], sequence_length=sequence_length)


def apply_unpaired_hard_delete(
    predicted_pairs: Iterable[Sequence[int]],
    unpaired_evidence: Iterable[int],
    *,
    sequence_length: int,
) -> list[Pair]:
    """Apply the frozen UNPAIRED_HARD_DELETE transformation."""

    prediction = validate_pairs(predicted_pairs, sequence_length=sequence_length)
    positions = list(unpaired_evidence)
    if len(positions) != len(set(positions)):
        raise EvidenceValidationError("duplicate unpaired evidence positions")
    if any(isinstance(position, bool) or not isinstance(position, int) or position < 0 or position >= sequence_length for position in positions):
        raise EvidenceValidationError("unpaired evidence coordinate is invalid")
    selected = set(positions)
    return validate_pairs(
        [pair for pair in prediction if not (set(pair) & selected)],
        sequence_length=sequence_length,
    )
