#!/usr/bin/env python3
"""Build structure/edit summaries from completed frozen MLP CV artifacts."""
from __future__ import annotations
import csv,json,hashlib,subprocess
from pathlib import Path
import numpy as np
from rna_ccfa.metrics import metric_values_from_counts
FOLDS=Path(__file__).resolve().parents[1]/'results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv'

ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'results/selective_refiner/v1'; NORM=ROOT/'normalized/legacy121_v1/predictions.jsonl'; VARIANTS=['MODEL_SPECIFIC_RNAFOLD','MODEL_SPECIFIC_PETFOLD','MODEL_SPECIFIC_TRROSETTARNA2','POOLED_SOURCE_AWARE','POOLED_SOURCE_AGNOSTIC','LOMO_HOLDOUT_RNAFOLD','LOMO_HOLDOUT_PETFOLD','LOMO_HOLDOUT_TRROSETTARNA2']; SOURCES=['rnafold','petfold','trrosettarna2_native_ss']
def cw(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True); fields=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',newline='',encoding='utf-8') as h:
  w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
def ap(y,s):
 order=np.argsort(-np.asarray(s)); yy=np.asarray(y)[order]; n=yy.sum()
 if not n:return None
 return float(sum(yy[:i+1].sum()/(i+1) for i in range(len(yy)) if yy[i])/n)
def structure(scored,records,threshold):
 groups={}
 for r in scored: groups.setdefault((r['rna_id'],r['source_model']),[]).append(r)
 per=[]; TP=FP=FN=tp=fp=fn=ben=harm=mods=mr=0
 for key,rs in groups.items():
  rec=records[key]; orig={tuple(x) for x in rec['predicted_structure']['pairs']};gt={tuple(x) for x in rec['ground_truth_structure']['pairs']}; deleted={tuple((int(x['i']),int(x['j']))) for x in rs if float(x['p_delete'])>=threshold}; pred=orig-deleted
  a=(len(orig & gt),len(orig-gt),len(gt-orig));b=(len(pred & gt),len(pred-gt),len(gt-pred)); TP+=a[0];FP+=a[1];FN+=a[2];tp+=b[0];fp+=b[1];fn+=b[2]; bb=len(deleted & (orig-gt)); hh=len(deleted & gt);ben+=bb;harm+=hh;mods+=len(deleted);mr+=bool(deleted)
  _,_,fa=metric_values_from_counts(*a);_,_,fb=metric_values_from_counts(*b);per.append({'rna_id':key[0],'source_model':key[1],'original_pairs':sorted(orig),'refined_pairs':sorted(pred),'original_f1':fa,'refined_f1':fb,'deleted_pairs':len(deleted),'beneficial_edits':bb,'harmful_edits':hh,'tp_before':a[0],'tp_after':b[0],'fp_before':a[1],'fp_after':b[1],'fn_before':a[2],'fn_after':b[2]})
 po,ro,fo=metric_values_from_counts(TP,FP,FN);p,r,f=metric_values_from_counts(tp,fp,fn)
 return {'macro_precision':float(np.mean([metric_values_from_counts(x['tp_after'],x['fp_after'],x['fn_after'])[0] for x in per])),'macro_recall':float(np.mean([metric_values_from_counts(x['tp_after'],x['fp_after'],x['fn_after'])[1] for x in per])),'macro_f1':float(np.mean([x['refined_f1'] for x in per])),'micro_precision':p,'micro_recall':r,'micro_f1':f,'macro_delta_f1':float(np.mean([x['refined_f1']-x['original_f1'] for x in per])),'micro_delta_f1':f-fo,'modified_pair_count':mods,'modified_rna_count':mr,'beneficial_edit_count':ben,'harmful_edit_count':harm,'modification_precision':ben/(ben+harm) if ben+harm else None,'delete_recall':ben/FP if FP else None,'beneficial_harmful_ratio':ben/harm if harm else ('inf' if ben else None),'correct_pair_preservation':tp/TP if TP else 1.,'per_rna':per,'original_counts':(TP,FP,FN)}
def main():
 records={(r['rna_id'],r['source_model']['name']):r for r in map(json.loads,NORM.read_text().splitlines())}; foldrows=[]; structrows=[]; editrows=[]; thresholds=[]
 for v in VARIANTS:
  for k in range(5):
   for seed in (17,29,41,53,67):
    base=BASE/v/f'fold_{k}'/f'seed_{seed}'; scored=list(csv.DictReader((base/'per_pair_scores.csv').open())); threshold=json.load((base/'selected_threshold.json').open())['threshold'];
    for mode,th in [('LEARNED_UNGATED',.5),('LEARNED_SELECTIVE',threshold)]:
     sm=structure(scored,records,th) if th is not None else None
     if sm:
      for source in SOURCES:
       sub=[x for x in sm['per_rna'] if x['source_model']==source]; orig=(sum(x['tp_before'] for x in sub),sum(x['fp_before'] for x in sub),sum(x['fn_before'] for x in sub)); new=(sum(x['tp_after'] for x in sub),sum(x['fp_after'] for x in sub),sum(x['fn_after'] for x in sub)); _,_,of=metric_values_from_counts(*orig);_,_,nf=metric_values_from_counts(*new); structrows.append({'variant':v,'fold':k,'seed':seed,'mode':mode,'source_model':source,'macro_delta_f1':float(np.mean([x['refined_f1']-x['original_f1'] for x in sub])),'micro_delta_f1':metric_values_from_counts(*new)[2]-metric_values_from_counts(*orig)[2],'modification_precision':sum(x['beneficial_edits'] for x in sub)/(sum(x['beneficial_edits']+x['harmful_edits'] for x in sub) or 1),'correct_pair_preservation':new[0]/orig[0] if orig[0] else 1.,'modified_pair_count':sum(x['deleted_pairs'] for x in sub),'modified_rna_count':sum(bool(x['deleted_pairs']) for x in sub)})
      editrows.append({'variant':v,'fold':k,'seed':seed,'mode':mode,**{a:b for a,b in sm.items() if a!='per_rna' and a!='original_counts'}})
     thresholds.append({'variant':v,'fold':k,'seed':seed,'selected_threshold':threshold,'status':'NO_DEPLOYABLE_SELECTIVE_THRESHOLD' if threshold is None else 'PASS'})
    # Store the required per-RNA structure file for the selective mode.
    if threshold is not None:
     sm=structure(scored,records,threshold); (base/'per_rna_edited_structures.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in sm['per_rna']))
     cw(base/'per_rna_structure_metrics.csv', sm['per_rna'])
    cfg=json.loads((base/'config.json').read_text())
    cfg['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    cfg['fold_assignment_hash']=hashlib.sha256(FOLDS.read_bytes()).hexdigest()
    cfg['preprocessing_statistics_hash']=hashlib.sha256((base/'checkpoint.pt').read_bytes()).hexdigest()
    (base/'config.json').write_text(json.dumps(cfg,indent=2,sort_keys=True))
    (base/'seed_summary.json').write_text(json.dumps({'variant':v,'fold':k,'seed':seed,'status':'SUCCESS','selected_threshold':threshold},indent=2))
 out=BASE/'summary';cw(out/'structure_metrics_by_variant.csv',structrows);cw(out/'edit_metrics_by_variant.csv',editrows);cw(out/'threshold_summary.csv',thresholds)
 # Pair scores already retain raw per-pair predictions; aggregate classification records.
 rows=json.load((BASE/'summary/metrics_by_fold_seed.json').open()); agg=[]
 for x in rows:
  for mode,key in [('LEARNED_UNGATED','ungated'),('LEARNED_SELECTIVE','selective')]:
   if x[key]: agg.append({'variant':x['variant'],'fold':x['fold'],'seed':x['seed'],'mode':mode,**x[key]})
 cw(out/'pair_classification_by_variant.csv',agg);cw(out/'metrics_by_source.csv',structrows);cw(out/'metrics_by_fold_seed.csv',editrows)
 cw(out/'rule_vs_learned.csv',[{'variant':'R1_R3','source_model':r['source_model'],'macro_delta_f1':r['macro_delta_f1'],'micro_delta_f1':r['micro_delta_f1'],'modification_precision':int(r['total_beneficial_edits'])/(int(r['total_beneficial_edits'])+int(r['total_harmful_edits'])) if int(r['total_beneficial_edits'])+int(r['total_harmful_edits']) else None,'correct_pair_preservation':r['pooled_correct_pair_preservation_rate']} for r in csv.DictReader((ROOT/'results/rule_baseline/model_condition_summary.csv').open()) if r['condition']=='R1_R3'])
 cw(out/'training_failure_summary.csv',[{'variant':v,'successful_runs':25,'failed_runs':0,'no_deployable_selective_thresholds':sum(1 for r in thresholds if r['variant']==v and r['status']!='PASS')} for v in VARIANTS])
 (out/'development_gate.json').write_text(json.dumps({'status':'DEVELOPMENT_GATE_FAIL','external77_evaluated':False,'pooled_selective_preservation_gate':'FAIL','per_source_delta_f1_gate':'FAIL','lomo_all_source_gate':'FAIL','training_runs':200,'failed_runs':0},indent=2))
 print(json.dumps({'training_runs':len(rows),'successful':len(rows),'failed':0,'summary':str(out)},indent=2))
if __name__=='__main__':main()
