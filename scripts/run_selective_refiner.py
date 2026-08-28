#!/usr/bin/env python3
"""Execute the preregistered Legacy121 selective-refiner MLP development CV."""
from __future__ import annotations
import csv,json,hashlib,math,random,sys
from pathlib import Path
import numpy as np
import torch
from torch import nn
from rna_ccfa.selective_refiner import extract_feature_rows,CATEGORIES,NUMERIC
from rna_ccfa.metrics import metric_values_from_counts

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
DEVICE=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
GPU_NAME=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
CUDA_VERSION=torch.version.cuda
ROOT=Path(__file__).resolve().parents[1]; NORM=ROOT/'normalized/legacy121_v1/predictions.jsonl'; FOLDS=ROOT/'results/selective_refiner_protocol/legacy121_grouped_cv_folds.csv'; OUT=ROOT/'results/selective_refiner/v1'
SEEDS=(17,29,41,53,67); THRESHOLDS=(.5,.55,.6,.65,.7,.75,.8,.85,.9,.95); SOURCES=('rnafold','petfold','trrosettarna2_native_ss')
VARIANTS=('MODEL_SPECIFIC_RNAFOLD','MODEL_SPECIFIC_PETFOLD','MODEL_SPECIFIC_TRROSETTARNA2','POOLED_SOURCE_AWARE','POOLED_SOURCE_AGNOSTIC','LOMO_HOLDOUT_RNAFOLD','LOMO_HOLDOUT_PETFOLD','LOMO_HOLDOUT_TRROSETTARNA2')

def csvwrite(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True); fields=list(dict.fromkeys(k for r in rows for k in r));
 with p.open('w',newline='',encoding='utf-8') as h:
  w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(rows)
def auc(y,s,positive=True):
 y=np.asarray(y); s=np.asarray(s); pos=s[y==1]; neg=s[y==0]
 if len(pos)==0 or len(neg)==0:return None
 order=np.argsort(s,kind='mergesort'); ranks=np.empty(len(s),dtype=float); ranks[order]=np.arange(1,len(s)+1)
 return float((ranks[y==1].sum()-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg)))
def auprc(y,s):
 y=np.asarray(y); s=np.asarray(s); n=int(y.sum())
 if n==0:return None
 order=np.argsort(-s,kind='mergesort'); yy=y[order]; return float(sum(yy[:i+1].sum()/(i+1) for i in range(len(yy)) if yy[i])/n)
def pair_metrics(rows,thr):
 y=np.array([r.label for r in rows]); scores=np.array([r.score for r in rows]); p=np.array(scores>=thr,int); tp=int(((y==1)&(p==1)).sum()); fp=int(((y==0)&(p==1)).sum()); fn=int(((y==1)&(p==0)).sum()); pr,re,f1=metric_values_from_counts(tp,fp,fn); return {'delete_precision':pr,'delete_recall':re,'delete_f1':f1,'auroc':auc(y,scores),'auprc':auprc(y,scores),'tp':tp,'fp':fp,'fn':fn}
def structure_metrics(rows,thr,records):
 by={};
 for r in rows:
  by.setdefault((r.rna_id,r.source_model),set()).add(r.pair) if r.score<thr else by.setdefault((r.rna_id,r.source_model),set())
 out=[]; ben=harm=mods=modrnas=0; tp0=tp1=fp0=fp1=fn0=fn1=0
 for key,rec in records.items():
  orig=set(rec['predicted_structure']['pairs']); pred=by.get(key,set(orig)); deleted=orig-pred; gt=set(map(tuple,rec['ground_truth_structure']['pairs']))
  b=len(deleted & (orig-gt)); h=len(deleted & gt); ben+=b; harm+=h; mods+=len(deleted); modrnas+=bool(deleted)
  t0=len(orig & gt); f0=len(orig-gt); n0=len(gt-orig); t1=len(pred & gt); f1=len(pred-gt); n1=len(gt-pred); tp0+=t0;fp0+=f0;fn0+=n0;tp1+=t1;fp1+=f1;fn1+=n1
  p0,r0,f10=metric_values_from_counts(t0,f0,n0); p1,r1,f11=metric_values_from_counts(t1,f1,n1); out.append({'rna_id':key[0],'source_model':key[1],'original_f1':f10,'refined_f1':f11,'deleted_pairs':len(deleted),'beneficial_edits':b,'harmful_edits':h,'tp_before':t0,'tp_after':t1,'fp_before':f0,'fp_after':f1,'fn_before':n0,'fn_after':n1})
 p,r,f=metric_values_from_counts(tp1,fp1,fn1); po,ro,fo=metric_values_from_counts(tp0,fp0,fn0)
 return {'macro_precision':float(np.mean([x['refined_f1']*0+x['refined_f1'] for x in out])) if out else 0.,'macro_recall':None,'macro_f1':float(np.mean([x['refined_f1'] for x in out])) if out else 0.,'micro_precision':p,'micro_recall':r,'micro_f1':f,'macro_delta_f1':float(np.mean([x['refined_f1']-x['original_f1'] for x in out])) if out else 0.,'micro_delta_f1':f-fo,'modified_pair_count':mods,'modified_rna_count':modrnas,'beneficial_edit_count':ben,'harmful_edit_count':harm,'modification_precision':ben/(ben+harm) if ben+harm else None,'delete_recall':ben/(fp0) if fp0 else None,'beneficial_harmful_ratio':ben/harm if harm else (None if not ben else 'inf'),'correct_pair_preservation':tp1/tp0 if tp0 else 1.,'per_rna':out,'original_counts':(tp0,fp0,fn0)}
class Net(nn.Module):
 def __init__(self,n): super().__init__(); self.net=nn.Sequential(nn.Linear(n,64),nn.ReLU(),nn.Dropout(.1),nn.Linear(64,64),nn.ReLU(),nn.Dropout(.1),nn.Linear(64,1))
 def forward(self,x):return self.net(x).squeeze(1)
def main():
 recs=[json.loads(x) for x in NORM.read_text().splitlines() if x.strip()]; fold={r['rna_id']:int(r['fold']) for r in csv.DictReader(FOLDS.open())}; records={(r['rna_id'],r['source_model']['name']):r for r in recs}; examples=[]
 for r in recs: examples.extend(extract_feature_rows(r['rna_id'],r['sequence'],r['predicted_structure']['pairs'],r['ground_truth_structure']['pairs'],r['source_model']['name'],True))
 counts={s:(sum(x.label==0 and x.source_model==s for x in examples),sum(x.label==1 and x.source_model==s for x in examples)) for s in SOURCES}; assert counts=={'rnafold':(1473,220),'petfold':(1463,241),'trrosettarna2_native_ss':(1461,432)}; assert (sum(x.label==0 for x in examples),sum(x.label==1 for x in examples))==(4397,893)
 feature_hash=hashlib.sha256(json.dumps({'numeric':NUMERIC,'categories':CATEGORIES},sort_keys=True).encode()).hexdigest(); summary=[]
 for variant in VARIANTS:
  held=None
  if variant.startswith('MODEL_SPECIFIC'): use=[variant.split('_')[-1].lower()]; use=[{'rnafold':'rnafold','petfold':'petfold','trrosettarna2':'trrosettarna2_native_ss'}[use[0]]]
  elif variant.startswith('LOMO_'): held={'RNAFOLD':'rnafold','PETFOLD':'petfold','TRROSETTARNA2':'trrosettarna2_native_ss'}[variant.split('_')[-1]]; use=[s for s in SOURCES if s!=held]
  else: use=list(SOURCES)
  aware=variant in ('POOLED_SOURCE_AWARE',)
  for k in range(5):
   train_r={i for i,f in fold.items() if f not in (k,(k+1)%5)}; val_r={i for i,f in fold.items() if f==(k+1)%5}; test_r={i for i,f in fold.items() if f==k}
   tr=[x for x in examples if x.rna_id in train_r and x.source_model in use]; va=[x for x in examples if x.rna_id in val_r and x.source_model in use]; te=[x for x in examples if x.rna_id in test_r and (x.source_model==held if held else x.source_model in use)]
   def vec(x):
    vals=[]
    for n in NUMERIC: vals.append(float(x.features[n]))
    for n,vocab in CATEGORIES.items():
     if n=='source_model' and not aware: continue
     val=x.features.get(n,'N/OTHER' if n.startswith('base') else 'NONE'); vals += [float(val==c) for c in vocab]+[float(val not in vocab)]
    return vals
   X=np.array([vec(x) for x in tr],dtype='float32'); V=np.array([vec(x) for x in va],dtype='float32'); T=np.array([vec(x) for x in te],dtype='float32'); mean=X.mean(0); std=X.std(0); std=np.maximum(std,1e-8); X=(X-mean)/std;V=(V-mean)/std;T=(T-mean)/std; y=np.array([x.label for x in tr],dtype='float32'); yv=np.array([x.label for x in va],dtype='float32'); pos=(y==0).sum()/(y==1).sum()
   for seed in SEEDS:
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed); model=Net(X.shape[1]).to(DEVICE); opt=torch.optim.AdamW(model.parameters(),lr=1e-3,weight_decay=1e-4); lossfn=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(float(pos),device=DEVICE)); best=None; curves=[]; patience=0
    tx=torch.tensor(X,device=DEVICE);ty=torch.tensor(y,device=DEVICE); vx=torch.tensor(V,device=DEVICE)
    for epoch in range(1,101):
     model.train(); order=torch.randperm(len(tx)); batch_losses=[]
     for start in range(0,len(order),256):
      batch=order[start:start+256]; opt.zero_grad(); loss=lossfn(model(tx[batch]),ty[batch]); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),5.); opt.step(); batch_losses.append(float(loss))
     model.eval(); scores=torch.sigmoid(model(vx)).detach().cpu().numpy(); vr=[type('R',(),{'label':int(a),'score':float(b)}) for a,b in zip(yv,scores)]; pm=pair_metrics(vr,.5); curves.append({'epoch':epoch,'train_loss':float(np.mean(batch_losses)),'validation_delete_f1':pm['delete_f1']})
     key=(pm['delete_f1'],-epoch)
     if best is None or key>(best[0],best[1]): best=(pm['delete_f1'],-epoch,epoch,model.state_dict(),scores);patience=0
     else: patience+=1
     if patience>=12: break
    model.load_state_dict(best[3]); model.eval(); s_val=torch.sigmoid(model(torch.tensor(V,device=DEVICE))).detach().cpu().numpy(); s_test=torch.sigmoid(model(torch.tensor(T,device=DEVICE))).detach().cpu().numpy(); vr=[type('R',(),{'label':int(a),'score':float(b)}) for a,b in zip(yv,s_val)]; candidates=[]
    # Validation structure selection uses only the two training-side sources in LOMO.
    val_by={(x.rna_id,x.source_model):x for x in va};
    for th in THRESHOLDS:
     deleted=[x for x,sc in zip(va,s_val) if sc>=th]; tp=sum(x.label==0 for x in va); harm=sum(x.label==0 for x in deleted); candidates.append((th,1-harm/tp if tp else 1.,pair_metrics([type('R',(),{'label':x.label,'score':sc}) for x,sc in zip(va,s_val)],th)['delete_f1'],len(deleted)))
    eligible=[c for c in candidates if c[1]>=.99]; threshold=max(eligible,key=lambda c:(c[2],c[0],-c[3]))[0] if eligible else None
    base=OUT/variant/f'fold_{k}'/f'seed_{seed}';base.mkdir(parents=True,exist_ok=True); torch.save({'model':model.state_dict(),'mean':mean,'std':std,'feature_schema_hash':feature_hash},base/'checkpoint.pt'); csvwrite(base/'train_ids.csv',[{'rna_id':x} for x in sorted(train_r)]);csvwrite(base/'validation_ids.csv',[{'rna_id':x} for x in sorted(val_r)]);csvwrite(base/'test_ids.csv',[{'rna_id':x} for x in sorted(test_r)])
    (base/'config.json').write_text(json.dumps({'protocol_version':'selective_refiner_v1','variant':variant,'fold':k,'seed':seed,'feature_schema_hash':feature_hash,'train_keep':int((y==0).sum()),'train_delete':int((y==1).sum()),'pos_weight':float(pos),'lr':1e-3,'weight_decay':1e-4,'batch_size':256,'max_epochs':100,'patience':12,'gradient_clip':5.0,'selected_checkpoint_epoch':best[2],'device':str(DEVICE),'gpu_model':GPU_NAME,'cuda_version':CUDA_VERSION,'pytorch_version':torch.__version__},indent=2));csvwrite(base/'validation_curves.csv',curves);(base/'selected_threshold.json').write_text(json.dumps({'threshold':threshold,'status':'NO_DEPLOYABLE_SELECTIVE_THRESHOLD' if threshold is None else 'PASS','validation_only':True},indent=2))
    test_rows=[type('R',(),{'label':x.label,'score':float(sc),'rna_id':x.rna_id,'source_model':x.source_model,'pair':x.pair}) for x,sc in zip(te,s_test)]; un=pair_metrics(test_rows,.5); sel=pair_metrics(test_rows,threshold) if threshold else None; summary += [{'variant':variant,'fold':k,'seed':seed,'threshold':threshold,'test_source':held or 'all','ungated':un,'selective':sel}]
    (base/'pair_classification_metrics.json').write_text(json.dumps({'ungated':un,'selective':sel},indent=2)); csvwrite(base/'per_pair_scores.csv',[{'rna_id':x.rna_id,'source_model':x.source_model,'i':x.pair[0],'j':x.pair[1],'label_delete':x.label,'p_delete':float(sc),'partition':'test'} for x,sc in zip(te,s_test)])
  
 out=OUT/'summary';out.mkdir(parents=True,exist_ok=True); (out/'metrics_by_fold_seed.json').write_text(json.dumps(summary,indent=2)); (out/'label_counts.json').write_text(json.dumps({**counts,'pooled':(4397,893)},indent=2));print(json.dumps({'successful_runs':len(summary),'label_counts':counts},indent=2))
if __name__=='__main__':main()
