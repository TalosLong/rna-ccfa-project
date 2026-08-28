#!/usr/bin/env python3
"""Post-hoc Legacy121 diagnostics for the frozen selective-refiner runs."""
import csv, json
from pathlib import Path
from collections import defaultdict
from rna_ccfa.selective_refiner import extract_feature_rows
from rna_ccfa.metrics import metric_values_from_counts

ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'results/selective_refiner/v1'; NORM=ROOT/'normalized/legacy121_v1/predictions.jsonl'
def main():
 recs={}
 for line in NORM.read_text().splitlines():
  r=json.loads(line); recs[(r['rna_id'],r['source_model']['name'])]=r
 out=defaultdict(lambda:[0,0,0]);
 for scorefile in BASE.glob('*/fold_*/seed_*/per_pair_scores.csv'):
  threshold=json.loads((scorefile.parent/'selected_threshold.json').read_text())['threshold']
  if threshold is None: continue
  for x in csv.DictReader(scorefile.open()):
   rec=recs[(x['rna_id'],x['source_model'])]; pair=(int(x['i']),int(x['j']))
   fr=next(z for z in extract_feature_rows(x['rna_id'],rec['sequence'],rec['predicted_structure']['pairs'],rec['ground_truth_structure']['pairs'],x['source_model'],True) if z.pair==pair)
   f=fr.features; cats=[('singleton',str(f['singleton_flag'])),('stem_length',str(f['strict_stem_length'])),('boundary','boundary' if f['outer_boundary_flag'] or f['inner_boundary_flag'] else 'interior'),('pair_type',f['pair_type']),('separation','short' if f['raw_separation']<10 else 'medium' if f['raw_separation']<25 else 'long')]
   for mode,th in [('LEARNED_UNGATED',.5),('LEARNED_SELECTIVE',threshold)]:
    pred=float(x['p_delete'])>=th; keybase=(scorefile.parts[-4],mode)
    for dim,val in cats:
     a=out[(keybase,dim,val)]; a[0]+=int(fr.label==1 and pred); a[1]+=int(fr.label==0 and pred); a[2]+=int(fr.label==1 and not pred)
 rows=[]
 for (key,dim,val),(tp,fp,fn) in sorted(out.items()):
  variant,mode=key; p,r,f=metric_values_from_counts(tp,fp,fn); rows.append({'variant':variant,'mode':mode,'feature_dimension':dim,'category':val,'delete_precision':p,'delete_recall':r,'delete_f1':f,'tp':tp,'fp':fp,'fn':fn})
 path=BASE/'summary/posthoc_feature_diagnostics.csv'; path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
 print('diagnostic_rows',len(rows))
if __name__=='__main__': main()
