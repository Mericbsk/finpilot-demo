import json,os,sys,numpy as np,pandas as pd
ROOT='/sessions/stoic-practical-tesla/mnt/Borsa'
DIRS=[d for d in [ROOT+'/data/price_cache_signal_eval_2026-10-23',ROOT+'/data/price_cache'] if os.path.isdir(d)]
H=21; COST=0.55
S=pd.read_pickle(sys.argv[1] if len(sys.argv)>1 else '/tmp/ev/signals.pkl')
for c in ['price','stop_loss','take_profit']: S[c]=pd.to_numeric(S[c],errors='coerce')
_bars={}
def bars(sym):
    if sym in _bars: return _bars[sym]
    out={}
    for d in reversed(DIRS):   # later dirs (supplement) override
        p=f'{d}/{sym}.json'
        if os.path.exists(p):
            try:
                for b in json.load(open(p)):
                    if isinstance(b,dict) and isinstance(b.get('date'),str) and all(b.get(k) not in (None,'') for k in ('open','high','low','close')):
                        out[b['date'][:10]]=b
            except Exception: pass
    _bars[sym]=[out[k] for k in sorted(out)]
    return _bars[sym]
res=[]
for r in S.itertuples():
    b=bars(r.symbol); d=r.scan_day.strftime('%Y-%m-%d')
    e,sl,tp=r.price,r.stop_loss,r.take_profit
    rec=dict(symbol=r.symbol,day=d,entry=e,sl=sl,tp=tp,status='no_data')
    if not b or not e or e<=0: res.append(rec); continue
    day0=[x for x in b if x['date'][:10]==d]
    after=[x for x in b if x['date'][:10]>d][:H]
    c0=float(day0[0]['close']) if day0 else np.nan
    rec['dev']=(e/c0-1)*100 if c0==c0 else np.nan
    if len(after)<H: rec['status']='open'; res.append(rec); continue
    tp_pct=(tp/e-1)*100 if tp and tp>0 else np.nan; sl_pct=(sl/e-1)*100 if sl and sl>0 else np.nan
    rec.update(tp_pct=tp_pct,sl_pct=sl_pct)
    # first-touch: TP vs SL (gap-aware), and +3/+5 vs SL
    def first(up_lvl,dn_lvl):
        for i,x in enumerate(after):
            o,h,l=float(x['open']),float(x['high']),float(x['low'])
            if dn_lvl and o<=dn_lvl: return 'stop',i+1,(o/e-1)*100
            if up_lvl and o>=up_lvl: return 'up',i+1,(o/e-1)*100
            hu= up_lvl and h>=up_lvl; hd= dn_lvl and l<=dn_lvl
            if hu and hd: return 'both',i+1,(dn_lvl/e-1)*100   # same day: conservative = stop
            if hd: return 'stop',i+1,(dn_lvl/e-1)*100
            if hu: return 'up',i+1,(up_lvl/e-1)*100
        return 'none',H,(float(after[-1]['close'])/e-1)*100
    slv=sl if sl and 0<sl<e else None
    rec['bar'],rec['bar_day'],rec['bar_ret']=first(tp if tp and tp>e else None,slv)
    rec['f3'],_,_=first(e*1.03,slv); rec['f5'],_,_=first(e*1.05,slv)
    p5=after[:5]
    rec['mfe5']=(max(float(x['high']) for x in p5)/e-1)*100
    rec['mae5']=(min(float(x['low']) for x in p5)/e-1)*100
    rec['c5']=(float(p5[-1]['close'])/e-1)*100
    rec['dir1']='up' if float(after[0]['close'])>=e else 'down'
    rec['status']='done'; res.append(rec)
R=pd.DataFrame(res); R['month']=R.day.str[:7]
R.to_pickle(sys.argv[2] if len(sys.argv)>2 else '/tmp/ev/results.pkl')
print('status',R.status.value_counts().to_dict())
D=R[R.status=='done'].copy()
bad=D.dev.abs()>2; print('entry vs scan-day close >2% off:',bad.sum(),' (excluded below)'); D=D[~bad]
def summ(X,name):
    n=len(X)
    if n==0: return
    bc=X.bar.value_counts()
    print(f"\n== {name}: n={n}")
    print(f" TP vs STOP first (21d): TP {bc.get('up',0)/n*100:.1f}% | STOP {bc.get('stop',0)/n*100:.1f}% | same-day both {bc.get('both',0)/n*100:.1f}% | neither {bc.get('none',0)/n*100:.1f}%")
    for k in ('f3','f5'):
        v=X[k].value_counts(); print(f" +{k[1]}% before stop: {v.get('up',0)/n*100:.1f}% | stop first {(v.get('stop',0)+v.get('both',0))/n*100:.1f}% | neither {v.get('none',0)/n*100:.1f}%")
    print(f" 5d: touched +3% {(X.mfe5>=3).mean()*100:.1f}% | +5% {(X.mfe5>=5).mean()*100:.1f}% | close T+5 mean {X.c5.mean():+.2f}% median {X.c5.median():+.2f}%")
    print(f" first day close up: {(X.dir1=='up').mean()*100:.1f}%")
    print(f" barrier result gross: mean {X.bar_ret.mean():+.2f}% median {X.bar_ret.median():+.2f}% | net(0.55) mean {X.bar_ret.mean()-COST:+.2f}%")
    print(f" planned TP median {X.tp_pct.median():.1f}% | SL median {X.sl_pct.median():.1f}%")
summ(D,'ALL BUY signals (entry_ok), clean')
for m,X in D.groupby('month'): 
    bc=X.bar.value_counts(); n=len(X)
    print(f"  {m} n={n:4d} TP {bc.get('up',0)/n*100:5.1f}% STOP {(bc.get('stop',0)+bc.get('both',0))/n*100:5.1f}% none {bc.get('none',0)/n*100:5.1f}% | +3%-before-stop {(X.f3=='up').mean()*100:5.1f}% | mean {X.bar_ret.mean():+.2f}%")
