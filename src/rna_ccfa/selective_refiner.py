"""Frozen observable-feature and label pipeline for selective refinement v1."""
from __future__ import annotations
from dataclasses import dataclass
from .stems import extract_stems_and_singletons
from .structure import Pair, validate_pairs

CATEGORIES = {
    "base_i": ("A","C","G","U","N/OTHER"), "base_j": ("A","C","G","U","N/OTHER"),
    "pair_type": ("AA","AC","AG","AU","CA","CC","CG","CU","GA","GC","GG","GU","UA","UC","UG","UU","OTHER"),
    "outward_pair_type": ("NONE", "AA","AC","AG","AU","CA","CC","CG","CU","GA","GC","GG","GU","UA","UC","UG","UU","OTHER"),
    "inward_pair_type": ("NONE", "AA","AC","AG","AU","CA","CC","CG","CU","GA","GC","GU","UA","UC","UG","UU","OTHER"),
    "source_model": ("rnafold","petfold","trrosettarna2_native_ss"),
}
NUMERIC = ("sequence_length","raw_separation","relative_separation","singleton_flag","strict_stem_length","stem_pair_position","normalized_stem_position","outer_boundary_flag","inner_boundary_flag","outward_neighbor_exists","inward_neighbor_exists")
FORBIDDEN = ("gt","truth","tp","fp","fn","wrong_partner","missing","family","dataset")

@dataclass(frozen=True)
class FeatureRow:
    rna_id: str; source_model: str; pair: Pair; features: dict[str, object]; label: int

def _base(x: str) -> str: return x if x in "ACGU" else "N/OTHER"
def _ptype(seq: str, pair: Pair) -> str:
    s = _base(seq[pair[0]]) + _base(seq[pair[1]])
    return s if s in CATEGORIES["pair_type"] else "OTHER"

def extract_feature_rows(rna_id: str, sequence: str, pairs, gt_pairs, source_model: str, include_source: bool) -> list[FeatureRow]:
    canonical = tuple(validate_pairs(pairs, sequence=sequence)); gt = set(validate_pairs(gt_pairs, sequence=sequence))
    if source_model not in CATEGORIES["source_model"]: raise ValueError(source_model)
    ex = extract_stems_and_singletons(canonical, sequence=sequence)
    info: dict[Pair, tuple[int,int,float,bool,bool]] = {}
    for stem in ex.stems:
        for pos, pair in enumerate(stem.pairs):
            info[pair] = (stem.n_pairs, pos, pos/(stem.n_pairs-1), pos == 0, pos == stem.n_pairs-1)
    singleton = set(ex.singleton_pairs)
    pair_set = set(canonical); rows = []
    for i,j in canonical:
        pair=(i,j); out=(i-1,j+1); inn=(i+1,j-1)
        if pair in singleton: sl, pos, norm, outer, inner = 0,0,0.,False,False
        else: sl,pos,norm,outer,inner=info[pair]
        f={"base_i":_base(sequence[i]),"base_j":_base(sequence[j]),"pair_type":_ptype(sequence,pair),
           "sequence_length":len(sequence),"raw_separation":j-i,"relative_separation":(j-i)/(len(sequence)-1) if len(sequence)>1 else 0.,
           "singleton_flag":int(pair in singleton),"strict_stem_length":sl,"stem_pair_position":pos,"normalized_stem_position":norm,
           "outer_boundary_flag":int(outer),"inner_boundary_flag":int(inner),"outward_neighbor_exists":int(out in pair_set),
           "outward_pair_type":_ptype(sequence,out) if out in pair_set else "NONE","inward_neighbor_exists":int(inn in pair_set),
           "inward_pair_type":_ptype(sequence,inn) if inn in pair_set else "NONE"}
        if include_source: f["source_model"]=source_model
        bad=[k for k in f if k.lower() in FORBIDDEN]
        if bad: raise AssertionError(f"forbidden feature columns: {bad}")
        rows.append(FeatureRow(rna_id,source_model,pair,f,int(pair not in gt)))
    return rows
