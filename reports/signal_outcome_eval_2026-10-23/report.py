import sys,json,os,numpy as np,pandas as pd
exec(open("eval.py").read().split("res=[]")[0].replace("S=pd.read_pickle(sys.argv[1] if len(sys.argv)>1 else '/tmp/ev/signals.pkl')","S=pd.DataFrame(columns=[\"price\",\"stop_loss\",\"take_profit\"])"))
def fixed(df_sig,R,tp_pct,sl_pct,H=21):
    ok=R[(R.status=='done')&(R.dev.abs()<=20)][['symbol','day']]
    S2=df_sig.assign(day=df_sig.scan_day.dt.strftime('%Y-%m-%d')).merge(ok,on=['symbol','day'])
    out=[]
    for r in S2.itertuples():
        e=float(r.price); up=e*(1+tp_pct/100); dn=e*(1-sl_pct/100)
        after=[x for x in bars(r.symbol) if x['date'][:10]>r.day][:H]; res=None
        for i,x in enumerate(after):
            o,h,l=float(x['open']),float(x['high']),float(x['low'])
            if o<=dn: res=('stop',(o/e-1)*100);break
            if o>=up: res=('tp',(o/e-1)*100);break
            if h>=up and l<=dn: res=('stop',-sl_pct);break
            if l<=dn: res=('stop',-sl_pct);break
            if h>=up: res=('tp',tp_pct);break
        if res is None: res=('none',(float(after[-1]['close'])/e-1)*100)
        out.append(res+(r.day[:7],))
    return pd.DataFrame(out,columns=['o','ret','m'])
def line(X,lab):
    n=len(X); bc=X.bar.value_counts()
    return (f"{lab:34s} n={n:5d} | TP-first {bc.get('up',0)/n*100:5.1f}% STOP-first {(bc.get('stop',0)+bc.get('both',0))/n*100:5.1f}% none {bc.get('none',0)/n*100:4.1f}% | +3%<stop {(X.f3=='up').mean()*100:5.1f}% +5%<stop {(X.f5=='up').mean()*100:5.1f}% | 5d touch +3 {(X.mfe5>=3).mean()*100:4.1f}% +5 {(X.mfe5>=5).mean()*100:4.1f}% | gross mean {X.bar_ret.mean():+.2f}% med {X.bar_ret.median():+.2f}% net {X.bar_ret.mean()-0.55:+.2f}%")
for name,sigf,resf in [('SHORTLIST BUY (entry_ok)','signals.pkl','results_all.pkl'),('DAILY REPORT TOP-10','top10.pkl','results_top10.pkl')]:
    sig=pd.read_pickle(sigf); R=pd.read_pickle(resf); R['month']=R.day.str[:7]
    for c in ['price','stop_loss','take_profit']: sig[c]=pd.to_numeric(sig[c],errors='coerce')
    D=R[R.status=='done']
    print(f"\n######## {name}: total {len(R)} | finished(21d) {len(D)} | still open {(R.status=='open').sum()} | no data {(R.status=='no_data').sum()} | date {R.day.min()}..{R.day.max()}")
    print(line(D[D.dev.abs()<=20],'all finished (|dev|<=20%)'))
    print(line(D[D.dev.abs()<=2],'strict entry (|dev|<=2%)'))
    X=D[D.dev.abs()<=20]
    print(f"  planned SL median {X.sl_pct.median():.2f}% TP median {X.tp_pct.median():.2f}% | stop on day1 {((X.bar.isin(['stop','both']))&(X.bar_day==1)).mean()*100:.1f}% | 5d MFE med {X.mfe5.median():.2f}% MAE med {X.mae5.median():.2f}%")
    print("  monthly (current SL/TP):")
    for m,g in X.groupby('month'):
        k=len(g); bc=g.bar.value_counts()
        print(f"    {m} n={k:4d} TP {bc.get('up',0)/k*100:5.1f}% STOP {(bc.get('stop',0)+bc.get('both',0))/k*100:5.1f}% | +3%<stop {(g.f3=='up').mean()*100:5.1f}% | mean {g.bar_ret.mean():+.2f}%")
    F=fixed(sig,R,4,6); k=len(F); v=F.o.value_counts()
    print(f"  FIXED TP+4/SL-6: n={k} TP {v.get('tp',0)/k*100:.1f}% STOP {v.get('stop',0)/k*100:.1f}% none {v.get('none',0)/k*100:.1f}% | gross mean {F.ret.mean():+.2f}% med {F.ret.median():+.2f}% net {F.ret.mean()-0.55:+.2f}%")
    for m,g in F.groupby('m'):
        kk=len(g); vv=g.o.value_counts(); print(f"    {m} n={kk:4d} TP {vv.get('tp',0)/kk*100:5.1f}% STOP {vv.get('stop',0)/kk*100:5.1f}% mean {g.ret.mean():+.2f}%")
