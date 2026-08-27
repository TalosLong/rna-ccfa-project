#!/usr/bin/env python3
"""Generate deterministic Legacy121 strict-stem error descriptions."""
from __future__ import annotations

import csv, json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from rna_ccfa.stem_errors import analyze_stem_errors

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "normalized/legacy121_v1/predictions.jsonl"
OUT = ROOT / "results/error_analysis"
MODELS = ("rnafold", "petfold", "trrosettarna2_native_ss")

def _stem_dict(stem): return stem.as_dict()
def _pair_list(pairs): return [list(p) for p in pairs]
def _fmt(value): return "" if value is None else json.dumps(value, separators=(",", ":"))

def main() -> None:
    records = [json.loads(line) for line in INPUT.read_text().splitlines() if line.strip()]
    if len(records) != 363: raise RuntimeError(f"expected 363 records, got {len(records)}")
    OUT.mkdir(parents=True, exist_ok=True)
    events_path = OUT / "stem_error_events.jsonl"
    csv_path = OUT / "stem_errors.csv"
    analyses = []
    with events_path.open("w", encoding="utf-8") as ef:
        for r in sorted(records, key=lambda x: x["record_id"]):
            length = r["metadata"]["sequence_length"]
            a = analyze_stem_errors(r["ground_truth_structure"]["pairs"], r["predicted_structure"]["pairs"], sequence_length=length)
            isolated_g = {m.gt_index for m in a.isolated_matches}; isolated_p = {m.pred_index for m in a.isolated_matches}
            ambiguous_g = {i for c in a.ambiguous_components for i in c.gt_indices}; ambiguous_p = {i for c in a.ambiguous_components for i in c.pred_indices}
            if len(isolated_g) + len(ambiguous_g) + len(a.missing_gt_indices) != len(a.gt_stems): raise RuntimeError(f"GT accounting failed for {r['record_id']}")
            if len(isolated_p) + len(ambiguous_p) + len(a.unmatched_pred_indices) != len(a.predicted_stems): raise RuntimeError(f"prediction accounting failed for {r['record_id']}")
            if len(a.isolated_matches) != len({(m.gt_index, m.pred_index) for m in a.isolated_matches}): raise RuntimeError("duplicate isolated relation")
            analyses.append((r, a))
            model = r["source_model"]["name"] if isinstance(r["source_model"], dict) else r["source_model"]
            comp_rows=[]
            for c in a.ambiguous_components:
                comp_rows.append({"component_id":c.component_id,"state":"complex_mismatch","gt_stems":[_stem_dict(a.gt_stems[i]) for i in c.gt_indices],"predicted_stems":[_stem_dict(a.predicted_stems[i]) for i in c.pred_indices],"candidate_edges":[{"gt_index":g,"pred_index":p,"exact_pair_overlap":d.exact_pair_overlap,"pair_union_size":d.pair_union_size,"left_arm_overlap":d.left_arm_overlap,"right_arm_overlap":d.right_arm_overlap,"register_gt":d.register_gt,"register_pred":d.register_pred,"register_displacement":d.register_displacement} for g,p,d in c.candidate_edges]})
            obj={"record_id":r["record_id"],"rna_id":r["rna_id"],"source_model":model,"gt_stem_count":len(a.gt_stems),"predicted_stem_count":len(a.predicted_stems),"isolated_matches":[],"ambiguous_components":comp_rows,"missing_gt_stems":[_stem_dict(a.gt_stems[i]) for i in a.missing_gt_indices],"unmatched_predicted_stems":[_stem_dict(a.predicted_stems[i]) for i in a.unmatched_pred_indices]}
            for m in a.isolated_matches:
                d=m.diagnostics; obj["isolated_matches"].append({"gt_stem":_stem_dict(m.gt_stem),"predicted_stem":_stem_dict(m.predicted_stem),"state":m.state,"exact_pair_overlap":d.exact_pair_overlap,"pair_union_size":d.pair_union_size,"left_arm_overlap":d.left_arm_overlap,"right_arm_overlap":d.right_arm_overlap,"register_gt":d.register_gt,"register_pred":d.register_pred,"register_displacement":d.register_displacement,"boundary_subtype":m.boundary_subtype})
            ef.write(json.dumps(obj, separators=(",", ":"), sort_keys=True)+"\n")
    rows=[]
    for r,a in analyses:
        model = r["source_model"]["name"] if isinstance(r["source_model"], dict) else r["source_model"]
        base={"record_id":r["record_id"],"rna_id":r["rna_id"],"source_model":model}
        for m in a.isolated_matches:
            d=m.diagnostics; rows.append({**base,"event_type":m.state,"gt_outer_pair":_fmt(list(m.gt_stem.outer_pair)),"pred_outer_pair":_fmt(list(m.predicted_stem.outer_pair)),"gt_n_pairs":m.gt_stem.n_pairs,"pred_n_pairs":m.predicted_stem.n_pairs,"exact_pair_overlap":d.exact_pair_overlap,"left_arm_overlap":d.left_arm_overlap,"right_arm_overlap":d.right_arm_overlap,"register_displacement":d.register_displacement,"boundary_subtype":m.boundary_subtype,"ambiguous_component_id":""})
        for c in a.ambiguous_components:
            for i in c.gt_indices: rows.append({**base,"event_type":"complex_mismatch","gt_outer_pair":_fmt(list(a.gt_stems[i].outer_pair)),"pred_outer_pair":"","gt_n_pairs":a.gt_stems[i].n_pairs,"pred_n_pairs":"","exact_pair_overlap":"","left_arm_overlap":"","right_arm_overlap":"","register_displacement":"","boundary_subtype":"none","ambiguous_component_id":c.component_id})
            for i in c.pred_indices: rows.append({**base,"event_type":"complex_mismatch","gt_outer_pair":"","pred_outer_pair":_fmt(list(a.predicted_stems[i].outer_pair)),"gt_n_pairs":"","pred_n_pairs":a.predicted_stems[i].n_pairs,"exact_pair_overlap":"","left_arm_overlap":"","right_arm_overlap":"","register_displacement":"","boundary_subtype":"none","ambiguous_component_id":c.component_id})
        for i in a.missing_gt_indices: rows.append({**base,"event_type":"stem_missing","gt_outer_pair":_fmt(list(a.gt_stems[i].outer_pair)),"pred_outer_pair":"","gt_n_pairs":a.gt_stems[i].n_pairs,"pred_n_pairs":"","exact_pair_overlap":"","left_arm_overlap":"","right_arm_overlap":"","register_displacement":"","boundary_subtype":"none","ambiguous_component_id":""})
        for i in a.unmatched_pred_indices: rows.append({**base,"event_type":"unmatched_predicted_stem","gt_outer_pair":"","pred_outer_pair":_fmt(list(a.predicted_stems[i].outer_pair)),"gt_n_pairs":"","pred_n_pairs":a.predicted_stems[i].n_pairs,"exact_pair_overlap":"","left_arm_overlap":"","right_arm_overlap":"","register_displacement":"","boundary_subtype":"none","ambiguous_component_id":""})
    fields=["record_id","rna_id","source_model","event_type","gt_outer_pair","pred_outer_pair","gt_n_pairs","pred_n_pairs","exact_pair_overlap","left_arm_overlap","right_arm_overlap","register_displacement","boundary_subtype","ambiguous_component_id"]
    with csv_path.open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)
    summary=[]
    for model in MODELS:
        aset=[a for r,a in analyses if (r["source_model"]["name"] if isinstance(r["source_model"], dict) else r["source_model"])==model]; c=Counter(); gt=pred=0
        for a in aset:
            gt+=len(a.gt_stems); pred+=len(a.predicted_stems); c.update(m.state for m in a.isolated_matches); c["ambiguous_component_count"]+=len(a.ambiguous_components); c["ambiguous_gt_stem_count"]+=sum(len(x.gt_indices) for x in a.ambiguous_components); c["ambiguous_predicted_stem_count"]+=sum(len(x.pred_indices) for x in a.ambiguous_components); c["stem_missing_count"]+=len(a.missing_gt_indices); c["unmatched_predicted_stem_count"]+=len(a.unmatched_pred_indices)
        row={"source_model":model,"n_samples":len(aset),"gt_stem_instances":gt,"predicted_stem_instances":pred,"exact_count":c["exact"],"stem_truncation_count":c["stem_truncation"],"stem_extension_count":c["stem_extension"],"stem_shift_count":c["stem_shift"],"isolated_complex_mismatch_count":c["complex_mismatch"],"ambiguous_component_count":c["ambiguous_component_count"],"ambiguous_gt_stem_count":c["ambiguous_gt_stem_count"],"ambiguous_predicted_stem_count":c["ambiguous_predicted_stem_count"],"stem_missing_count":c["stem_missing_count"],"unmatched_predicted_stem_count":c["unmatched_predicted_stem_count"]}
        row["fraction_gt_stems_exact"]=row["exact_count"]/gt if gt else 0; row["fraction_gt_stems_missing"]=row["stem_missing_count"]/gt if gt else 0; row["fraction_predicted_stems_unmatched"]=row["unmatched_predicted_stem_count"]/pred if pred else 0; summary.append(row)
    sf=OUT/"stem_error_summary_by_model.csv"; fields=list(summary[0]);
    with sf.open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(summary)
    totals={k:sum(int(x[k]) for x in summary) for k in ("gt_stem_instances","predicted_stem_instances","ambiguous_component_count","ambiguous_gt_stem_count","ambiguous_predicted_stem_count")}
    if totals != {"gt_stem_instances":1005,"predicted_stem_instances":933,"ambiguous_component_count":53,"ambiguous_gt_stem_count":113,"ambiguous_predicted_stem_count":53}: raise RuntimeError(f"audit regression failed: {totals}")
    isolated=sum(int(x["exact_count"])+int(x["stem_truncation_count"])+int(x["stem_extension_count"])+int(x["stem_shift_count"])+int(x["isolated_complex_mismatch_count"]) for x in summary)
    if isolated != 758: raise RuntimeError(f"isolated regression failed: {isolated}")
    if sum(int(x["stem_missing_count"]) for x in summary)+totals["ambiguous_gt_stem_count"]+isolated != 1005: raise RuntimeError("GT accounting failed")
    if sum(int(x["unmatched_predicted_stem_count"]) for x in summary)+totals["ambiguous_predicted_stem_count"]+isolated != 933: raise RuntimeError("prediction accounting failed")
    print(json.dumps({"records":len(records),"summary":summary,"generated_at_utc":datetime.now(timezone.utc).isoformat()}))

if __name__ == "__main__": main()
