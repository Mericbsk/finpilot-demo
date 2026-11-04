import os,re,csv,sys,pandas as pd
csv.field_size_limit(10**8)
rows=[];errs=[]
for f in sorted(os.listdir('.')):
    if not f.endswith('.csv'): continue
    m=re.search(r'_(\d{8})_(\d{4})\.csv$',f)
    if not m or not m.group(1).startswith('20'): continue
    try: df=pd.read_csv(f,engine='python',on_bad_lines='skip')
    except Exception as e: errs.append(f); continue
    if 'entry_ok' not in df: continue
    eo=df['entry_ok'].astype(str).str.lower().isin(['true','1','yes'])
    s=df[eo].copy()
    if s.empty: continue
    s['file']=f; s['scan_day']=m.group(1); s['scan_hm']=m.group(2)
    rows.append(s[[c for c in ['symbol','price','stop_loss','take_profit','direction','reason','score','composite_score','timestamp','file','scan_day','scan_hm','selection_eligible','selected_by_v2','tier','conviction_tier'] if c in s]])
print('read errors',len(errs),errs[:3])
A=pd.concat(rows,ignore_index=True)
A['scan_day']=pd.to_datetime(A.scan_day)
A=A.sort_values(['scan_day','scan_hm'])
first=A.drop_duplicates(['symbol','scan_day'],keep='first')
first.to_pickle('/tmp/ev/signals.pkl')
print('entry_ok rows',len(A),'unique symbol-days',len(first),'days',first.scan_day.nunique(),first.scan_day.min().date(),first.scan_day.max().date(),'symbols',first.symbol.nunique())
print(first.groupby(first.scan_day.dt.to_period('M')).agg(n=('symbol','size'),days=('scan_day','nunique')))
print('direction',first.direction.astype(str).value_counts().head().to_dict())
print('reason starts',first.reason.astype(str).str[:7].value_counts().head(6).to_dict() if 'reason' in first else '')
for c in ['price','stop_loss','take_profit']: print(c,'missing/<=0',(pd.to_numeric(first[c],errors='coerce').fillna(0)<=0).sum())
