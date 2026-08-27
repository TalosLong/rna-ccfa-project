"""Deterministic strict-stem matching and descriptive error taxonomy."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable

from .stems import Stem, extract_strict_stems


@dataclass(frozen=True, slots=True)
class StemRelationDiagnostics:
    exact_pair_overlap: int
    pair_union_size: int
    left_arm_overlap: int
    right_arm_overlap: int
    register_gt: int
    register_pred: int
    register_displacement: int


@dataclass(frozen=True, slots=True)
class StemMatch:
    gt_index: int
    pred_index: int
    gt_stem: Stem
    predicted_stem: Stem
    diagnostics: StemRelationDiagnostics
    state: str
    boundary_subtype: str


@dataclass(frozen=True, slots=True)
class AmbiguousStemComponent:
    component_id: str
    gt_indices: tuple[int, ...]
    pred_indices: tuple[int, ...]
    candidate_edges: tuple[tuple[int, int, StemRelationDiagnostics], ...]


@dataclass(frozen=True, slots=True)
class StemErrorAnalysis:
    gt_stems: tuple[Stem, ...]
    predicted_stems: tuple[Stem, ...]
    isolated_matches: tuple[StemMatch, ...]
    ambiguous_components: tuple[AmbiguousStemComponent, ...]
    missing_gt_indices: tuple[int, ...]
    unmatched_pred_indices: tuple[int, ...]


def compute_stem_relation(gt: Stem, predicted: Stem) -> StemRelationDiagnostics:
    """Compute the frozen pair, arm, and register diagnostics."""
    gt_pairs, pred_pairs = set(gt.pairs), set(predicted.pairs)
    left_gt = set(range(gt.left_start, gt.left_end + 1))
    left_pred = set(range(predicted.left_start, predicted.left_end + 1))
    right_gt = set(range(gt.right_start, gt.right_end + 1))
    right_pred = set(range(predicted.right_start, predicted.right_end + 1))
    register_gt = sum(gt.outer_pair)
    register_pred = sum(predicted.outer_pair)
    return StemRelationDiagnostics(
        exact_pair_overlap=len(gt_pairs & pred_pairs),
        pair_union_size=len(gt_pairs | pred_pairs),
        left_arm_overlap=len(left_gt & left_pred),
        right_arm_overlap=len(right_gt & right_pred),
        register_gt=register_gt,
        register_pred=register_pred,
        register_displacement=register_pred - register_gt,
    )


def is_candidate_relation(gt: Stem, predicted: Stem, diagnostics: StemRelationDiagnostics | None = None) -> bool:
    """Return whether a stem pair is an edge under frozen taxonomy v1."""
    d = diagnostics or compute_stem_relation(gt, predicted)
    if d.exact_pair_overlap > 0:
        return True
    shorter = min(gt.n_pairs, predicted.n_pairs)
    return (
        d.register_displacement != 0
        and d.left_arm_overlap >= 2
        and d.right_arm_overlap >= 2
        and d.left_arm_overlap >= shorter - 1
        and d.right_arm_overlap >= shorter - 1
    )


def _boundary_subtype(reference: tuple[tuple[int, int], ...], subset: tuple[tuple[int, int], ...]) -> str:
    """Describe which ends of an ordered strict chain are omitted."""
    if len(subset) == len(reference):
        return "none"
    start = reference.index(subset[0])
    end = reference.index(subset[-1])
    outer = start > 0
    inner = end < len(reference) - 1
    if outer and inner:
        return "both"
    if outer:
        return "outer"
    if inner:
        return "inner"
    return "none"


def classify_isolated_stem_match(gt: Stem, predicted: Stem, diagnostics: StemRelationDiagnostics | None = None) -> tuple[str, str]:
    """Classify one eligible isolated 1:1 relation using frozen precedence."""
    d = diagnostics or compute_stem_relation(gt, predicted)
    gt_set, pred_set = set(gt.pairs), set(predicted.pairs)
    if gt_set == pred_set:
        return "exact", "none"
    if d.register_gt == d.register_pred and pred_set < gt_set:
        return "stem_truncation", _boundary_subtype(gt.pairs, predicted.pairs)
    if d.register_gt == d.register_pred and gt_set < pred_set:
        return "stem_extension", _boundary_subtype(predicted.pairs, gt.pairs)
    if is_candidate_relation(gt, predicted, d) and d.exact_pair_overlap == 0 and d.register_displacement != 0:
        return "stem_shift", "none"
    return "complex_mismatch", "none"


def build_candidate_components(gt_stems: tuple[Stem, ...], predicted_stems: tuple[Stem, ...]) -> tuple[list[tuple[int, int, StemRelationDiagnostics]], tuple[AmbiguousStemComponent, ...], set[int], set[int]]:
    """Build sorted candidate edges and ambiguous connected components."""
    edges: list[tuple[int, int, StemRelationDiagnostics]] = []
    for gi, gt in enumerate(gt_stems):
        for pi, pred in enumerate(predicted_stems):
            d = compute_stem_relation(gt, pred)
            if is_candidate_relation(gt, pred, d):
                edges.append((gi, pi, d))
    edges.sort(key=lambda e: (gt_stems[e[0]].outer_pair, predicted_stems[e[1]].outer_pair))
    gt_adj: defaultdict[int, set[int]] = defaultdict(set)
    pred_adj: defaultdict[int, set[int]] = defaultdict(set)
    for gi, pi, _ in edges:
        gt_adj[gi].add(pi); pred_adj[pi].add(gi)
    seen_g, seen_p = set(), set()
    components: list[AmbiguousStemComponent] = []
    ambiguous_g, ambiguous_p = set(), set()
    for start in sorted(gt_adj):
        if start in seen_g: continue
        gs, ps = set(), set(); q = deque([("g", start)])
        while q:
            role, idx = q.popleft()
            if role == "g":
                if idx in seen_g: continue
                seen_g.add(idx); gs.add(idx)
                q.extend(("p", p) for p in sorted(gt_adj[idx]) if p not in seen_p)
            else:
                if idx in seen_p: continue
                seen_p.add(idx); ps.add(idx)
                q.extend(("g", g) for g in sorted(pred_adj[idx]) if g not in seen_g)
        if len(gs) > 1 or len(ps) > 1:
            ambiguous_g.update(gs); ambiguous_p.update(ps)
            comp_edges = tuple((g, p, d) for g, p, d in edges if g in gs and p in ps)
            components.append(AmbiguousStemComponent(f"ambiguous_{len(components)+1:03d}", tuple(sorted(gs)), tuple(sorted(ps)), comp_edges))
    components.sort(key=lambda c: tuple(gt_stems[i].outer_pair for i in c.gt_indices) + tuple(predicted_stems[i].outer_pair for i in c.pred_indices))
    # Renumber after deterministic sorting.
    components = [AmbiguousStemComponent(f"ambiguous_{i:03d}", c.gt_indices, c.pred_indices, c.candidate_edges) for i, c in enumerate(components, 1)]
    return edges, tuple(components), ambiguous_g, ambiguous_p


def analyze_stem_errors(gt_pairs: Iterable[tuple[int, int]], predicted_pairs: Iterable[tuple[int, int]], *, sequence_length: int | None = None, sequence: str | None = None) -> StemErrorAnalysis:
    """Extract strict stems and apply frozen matching/error semantics."""
    gt_stems = extract_strict_stems(gt_pairs, sequence=sequence, sequence_length=sequence_length)
    pred_stems = extract_strict_stems(predicted_pairs, sequence=sequence, sequence_length=sequence_length)
    edges, components, ambiguous_g, ambiguous_p = build_candidate_components(gt_stems, pred_stems)
    isolated = [(g, p, d) for g, p, d in edges if len([x for x in edges if x[0] == g]) == 1 and len([x for x in edges if x[1] == p]) == 1 and g not in ambiguous_g and p not in ambiguous_p]
    matches = tuple(StemMatch(g, p, gt_stems[g], pred_stems[p], d, *classify_isolated_stem_match(gt_stems[g], pred_stems[p], d)) for g, p, d in sorted(isolated, key=lambda x: (gt_stems[x[0]].outer_pair, pred_stems[x[1]].outer_pair)))
    matched_g = {g for g, _, _ in isolated}
    matched_p = {p for _, p, _ in isolated}
    missing = tuple(i for i in range(len(gt_stems)) if i not in matched_g and i not in ambiguous_g and not any(g == i for g, _, _ in edges))
    unmatched = tuple(i for i in range(len(pred_stems)) if i not in matched_p and i not in ambiguous_p and not any(p == i for _, p, _ in edges))
    return StemErrorAnalysis(gt_stems, pred_stems, matches, components, missing, unmatched)
