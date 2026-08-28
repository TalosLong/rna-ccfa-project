#!/usr/bin/env python3
"""Create lightweight v2 factorial, paired, threshold, and diagnostic summaries."""
from __future__ import annotations
import csv, json
from collections import defaultdict
from pathlib import Path
import numpy as np
from rna_ccfa.cross_model import cross_model_agreement_features

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "results/selective_refiner/v2"
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")
CONDITIONS = [
 "V2A_BASE_SOURCE_AGNOSTIC_GLOBAL", "V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL",
 "V2A_BASE_SOURCE_AWARE_GLOBAL", "V2A_CROSS_SOURCE_AWARE_GLOBAL",
 "V2B_BASE_SOURCE_AGNOSTIC_SOURCE_CONDITIONAL", "V2B_CROSS_SOURCE_AGNOSTIC_SOURCE_CONDITIONAL",
 "V2B_BASE_SOURCE_AWARE_SOURCE_CONDITIONAL", "V2B_CROSS_SOURCE_AWARE_SOURCE_CONDITIONAL"]

def read(path):
    with path.open(encoding="utf-8", newline="") as h: return list(csv.DictReader(h))

def agg(rows):
    b=sum(int(x["beneficial_edit_count"]) for x in rows); h=sum(int(x["harmful_edit_count"]) for x in rows)
    tp=sum(int(x["original_tp_count"]) for x in rows); tpa=sum(int(x["tp_after_count"]) for x in rows)
    fp=sum(int(x["original_fp_count"]) for x in rows)
    return {"modification_precision": b/(b+h) if b+h else "NA", "delete_recall": b/fp if fp else 0,
            "correct_pair_preservation": tpa/tp if tp else 1, "macro_delta_f1": float(np.mean([float(x["macro_delta_f1"]) for x in rows])),
            "micro_delta_f1": float(np.mean([float(x["micro_delta_f1"]) for x in rows])), "beneficial_edit_count": b,
            "harmful_edit_count": h, "modified_pair_count": sum(int(x["modified_pair_count"]) for x in rows),
            "modified_rna_count": sum(int(x["modified_rna_count"]) for x in rows), "eligible_rna_count": sum(int(x["eligible_rna_count"]) for x in rows)}

def main():
    summary=V2/"summary"; summary.mkdir(parents=True, exist_ok=True)
    pooled=read(summary/"factorial_metrics.csv"); source=read(summary/"metrics_by_source.csv")
    factorial=[]
    for condition in CONDITIONS:
        rows=[x for x in pooled if x["condition"]==condition]
        factorial.append({"condition":condition,"scope":"pooled",**agg(rows)})
        for s in SOURCES:
            factorial.append({"condition":condition,"scope":"source","source_model":s,**agg([x for x in source if x["condition"]==condition and x["source_model"]==s])})
    fields=list(dict.fromkeys(k for x in factorial for k in x));
    with (summary/"factorial_metrics_aggregate.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(factorial)
    secondary=[x for x in factorial if x["scope"]=="pooled"]
    with (summary/"secondary_factorial_summary.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(secondary[0])); w.writeheader(); w.writerows(secondary)

    pairs=[]
    for scope, rows in (("pooled",pooled),("source",source)):
        for s in (("ALL",) if scope=="pooled" else SOURCES):
            for fold in range(5):
                for seed in (17,29,41,53,67):
                    ss=s if scope=="source" else "ALL"; c=[x for x in rows if x["condition"]=="V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL" and x["fold"]==str(fold) and x["seed"]==str(seed) and (scope=="pooled" or x["source_model"]==ss)][0]
                    b=[x for x in rows if x["condition"]=="V2A_BASE_SOURCE_AGNOSTIC_GLOBAL" and x["fold"]==str(fold) and x["seed"]==str(seed) and (scope=="pooled" or x["source_model"]==ss)][0]
                    pairs.append({"scope":scope,"source_model":ss,"fold":fold,"seed":seed,"cross_deployable":c["deployable"],"base_deployable":b["deployable"],"precision_cross":c["modification_precision"],"precision_base":b["modification_precision"],"precision_gain":"NA" if c["modification_precision"]=="" or b["modification_precision"]=="" else "NA","recall_gain":float(c["delete_recall"])-float(b["delete_recall"]),"preservation_gain":float(c["correct_pair_preservation"])-float(b["correct_pair_preservation"]),"macro_delta_gain":float(c["macro_delta_f1"])-float(b["macro_delta_f1"]),"micro_delta_gain":float(c["micro_delta_f1"])-float(b["micro_delta_f1"])})
    with (summary/"base_vs_cross_paired.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(pairs[0])); w.writeheader(); w.writerows(pairs)

    threshold=[]
    roots={"BASE_SOURCE_AGNOSTIC":V2/"base_reconstructed/POOLED_SOURCE_AGNOSTIC","BASE_SOURCE_AWARE":V2/"base_reconstructed/POOLED_SOURCE_AWARE","CROSS_SOURCE_AGNOSTIC":V2/"cross_source_agnostic","CROSS_SOURCE_AWARE":V2/"cross_source_aware"}
    for name,root in roots.items():
        for fold in range(5):
            for seed in (17,29,41,53,67):
                d=root/f"fold_{fold}"/f"seed_{seed}"
                g=json.loads((d/"global_threshold.json").read_text())
                sc=json.loads((d/"source_conditional_thresholds.json").read_text())
                threshold.append({"backbone":name,"fold":fold,"seed":seed,"global_status":g["status"],"global_threshold":g["threshold"],"source_status":sc["status"],"source_thresholds":json.dumps(sc["thresholds"],sort_keys=True)})
    with (summary/"threshold_deployability.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(threshold[0])); w.writeheader(); w.writerows(threshold)

    # Prediction-only diagnostic: support category and selected deletions for primary CROSS.
    records={}; preds=defaultdict(dict)
    for line in (ROOT/"normalized/legacy121_v1/predictions.jsonl").read_text().splitlines():
        r=json.loads(line); key=(r["rna_id"],r["source_model"]["name"]); records[key]=r; preds[r["rna_id"]][r["source_model"]["name"]]=r["predicted_structure"]["pairs"]
    diag=defaultdict(lambda:[0,0,0,0,0])
    crossroot=V2/"cross_source_agnostic"
    for fold in range(5):
        for seed in (17,29,41,53,67):
            d=crossroot/f"fold_{fold}"/f"seed_{seed}"; g=json.loads((d/"global_threshold.json").read_text()); threshold_value=g["threshold"]
            if threshold_value is None: continue
            for row in read(d/"test_pair_scores.csv"):
                key=(row["rna_id"],row["source_model"]); pair=(int(row["i"]),int(row["j"]))
                cf=cross_model_agreement_features(row["source_model"],pair,preds[row["rna_id"]],sequence_length=len(records[key]["sequence"]))
                k=(row["source_model"],int(cf["exact_support_other_count"])); a=diag[k]; label=int(row["label_delete"]); a[0]+=1; a[1]+=int(label==1)
                if float(row["p_delete"])>=threshold_value:
                    a[2]+=1; a[3]+=int(label==1); a[4]+=int(label==0)
    diag_rows=[]
    for (s,k),(n,fp,deleted,b,harmful) in sorted(diag.items()):
        diag_rows.append({"condition":"V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL","source_model":s,"support_other_count":k,"examples":n,"fp_count":fp,"fp_prevalence":fp/n,"predicted_delete_count":deleted,"predicted_delete_rate":deleted/n,"beneficial_edits":b,"harmful_edits":harmful,"deletion_precision":b/(b+harmful) if b+harmful else "NA","deletion_recall":b/fp if fp else 0})
    with (summary/"cross_feature_diagnostics.csv").open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=list(diag_rows[0])); w.writeheader(); w.writerows(diag_rows)
    # Materialize the requested per-run structure metrics for the new CROSS runs.
    for condition, rootname in (("V2A_CROSS_SOURCE_AGNOSTIC_GLOBAL","cross_source_agnostic"),("V2A_CROSS_SOURCE_AWARE_GLOBAL","cross_source_aware")):
        for row in [x for x in pooled if x["condition"]==condition]:
            d=V2/rootname/f"fold_{row['fold']}"/f"seed_{row['seed']}"
            (d/"structure_metrics.csv").write_text("metric,value\n"+"\n".join(f"{k},{row[k]}" for k in ("macro_delta_f1","micro_delta_f1","modification_precision","delete_recall","correct_pair_preservation","modified_pair_count","modified_rna_count"))+"\n")
    print(json.dumps({"aggregate_rows":sum(1 for _ in factorial),"paired_rows":sum(1 for _ in pairs),"threshold_rows":sum(1 for _ in threshold),"diagnostic_rows":sum(1 for _ in diag_rows)}))
if __name__=="__main__": main()
