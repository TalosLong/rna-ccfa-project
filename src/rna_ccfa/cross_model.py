"""GT-free cross-model agreement features for selective refinement."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .stems import extract_stems_and_singletons
from .structure import Pair, validate_pairs

SOURCE_MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")


def cross_model_agreement_features(
    source_model: str,
    pair: Sequence[int],
    predictions: Mapping[str, Sequence[Sequence[int]]],
    *,
    sequence_length: int,
) -> dict[str, int | float]:
    """Return prediction-only agreement features for one source-predicted pair.

    A complete, one-partner-constrained three-source matrix is required. The
    source pair itself is immutable and is never inferred from another model.
    """

    if source_model not in SOURCE_MODELS:
        raise ValueError(f"unknown source model: {source_model}")
    if set(predictions) != set(SOURCE_MODELS):
        raise ValueError("cross-model features require the complete frozen three-source matrix")

    canonical = {
        source: set(validate_pairs(source_pairs, sequence_length=sequence_length))
        for source, source_pairs in predictions.items()
    }
    p = tuple(pair)
    if p not in canonical[source_model]:
        raise ValueError("feature unit must belong to the immutable source prediction")

    other_sources = [source for source in SOURCE_MODELS if source != source_model]
    support = {source: int(p in canonical[source]) for source in SOURCE_MODELS}
    support[source_model] = 0  # structural zero; named flags are source-aware only
    exact_support = sum(support[source] for source in other_sources)

    def partner_map(pairs: set[Pair]) -> dict[int, int]:
        result: dict[int, int] = {}
        for i, j in pairs:
            result[i] = j
            result[j] = i
        return result

    partners = {source: partner_map(canonical[source]) for source in SOURCE_MODELS}
    i, j = p
    endpoint_i_exact = sum(partners[source].get(i) == j for source in other_sources)
    endpoint_j_exact = sum(partners[source].get(j) == i for source in other_sources)
    endpoint_i_conflict = sum(
        i in partners[source] and partners[source][i] != j for source in other_sources
    )
    endpoint_j_conflict = sum(
        j in partners[source] and partners[source][j] != i for source in other_sources
    )

    extraction = extract_stems_and_singletons(
        canonical[source_model], sequence_length=sequence_length
    )
    stem_pairs: tuple[Pair, ...] = ()
    for stem in extraction.stems:
        if p in stem.pairs:
            stem_pairs = stem.pairs
            break
    if stem_pairs:
        supported_pairs = sum(
            any(stem_pair in canonical[source] for source in other_sources)
            for stem_pair in stem_pairs
        )
        full_stem_support = int(
            any(all(stem_pair in canonical[source] for stem_pair in stem_pairs) for source in other_sources)
        )
        stem_fraction = supported_pairs / len(stem_pairs)
    else:
        full_stem_support = 0
        stem_fraction = 0.0

    outward = (i - 1, j + 1)
    inward = (i + 1, j - 1)
    return {
        "exact_support_other_count": exact_support,
        "support_by_rnafold": support["rnafold"],
        "support_by_petfold": support["petfold"],
        "support_by_trrosettarna2": support["trrosettarna2_native_ss"],
        "any_other_exact_support": int(exact_support > 0),
        "all_three_exact_agreement": int(exact_support == 2),
        "endpoint_i_partner_agreement_count": endpoint_i_exact,
        "endpoint_j_partner_agreement_count": endpoint_j_exact,
        "endpoint_i_conflict_count": endpoint_i_conflict,
        "endpoint_j_conflict_count": endpoint_j_conflict,
        "any_partner_conflict": int(endpoint_i_conflict + endpoint_j_conflict > 0),
        "local_inward_pair_support_count": sum(inward in canonical[source] for source in other_sources),
        "local_outward_pair_support_count": sum(outward in canonical[source] for source in other_sources),
        "strict_stem_supported_by_other_model": full_stem_support,
        "fraction_source_stem_pairs_supported": stem_fraction,
    }
