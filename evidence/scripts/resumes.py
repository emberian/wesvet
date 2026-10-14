import json,sys,re,datetime as dt
def T(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
for f in sys.argv[1:]:
    prev=None; prev_stop=None; first=None; hits=[]
    for i,ln in enumerate(open(f)):
        try:r=json.loads(ln)
        except: continue
        ts=r.get('timestamp')
        if not ts: continue
        if first is None: first=ts
        t=r.get('type')
        if t=='assistant':
            prev=ts; prev_stop=r.get('message',{}).get('stop_reason')
            continue
        if t!='user' or prev is None: continue
        c=r.get('message',{}).get('content')
        if isinstance(c,list):
            if any(isinstance(b,dict) and b.get('type')=='tool_result' for b in c): continue
            txt=' '.join(b.get('text','') for b in c if isinstance(b,dict) and b.get('type')=='text')
        else: txt=str(c)
        if txt.startswith('[SYSTEM NOTIFICATION'): continue
        gap=(T(ts)-T(prev)).total_seconds()
        if prev_stop=='end_turn' and gap>120:
            hits.append((ts,round(gap/60,1),txt[:200].replace('\n',' ')))
    if hits:
        print(f.split('/projects/')[1])
        for h in hits: print('   ',h)
