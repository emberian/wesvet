import json,sys,re
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
seats=json.load(open('seats.json'))
out={}
for s in seats:
    ir=json.load(open(f"ir/{s['agent']}.json")); m=ir['messages']
    sends=[c for c in irlib.tool_calls(m) if c['name']=='SendMessage' and str(c['input'].get('to'))=='main']
    last=str(sends[-1]['input'].get('message')) if sends else ''
    lasttxt=''
    for x in reversed(m):
        if x['role']=='assistant' and irlib.text_of(x).strip(): lasttxt=irlib.text_of(x); break
    blob=(last+' '+lasttxt)
    k=re.search(r'(\d{3})\s?[Kk]\b',blob)
    if re.search(r'abeyance',blob,re.I): cause='abeyance'
    elif re.search(r'park',blob,re.I) and k: cause='ceiling-park'
    elif re.search(r'wind|ember.*(park|stop)|winding',blob,re.I): cause='wind-down'
    elif re.search(r'park',blob,re.I): cause='park'
    elif s['status'] in ('killed','failed','running','stopped','returned'): cause='died:'+s['status']
    else: cause='other'
    peak=max((irlib.ctx_size(u) for _,_,u in irlib.usage_rows(m)),default=0)
    out[s['agent']]=dict(cause=cause,k=k.group(1) if k else None,peak=peak,last=last[:300],lasttxt=lasttxt[:300])
    print(f"{s['line']}{s['n']:<3d} {s['status'][:6]:6s} peak{peak/1e3:4.0f}k {cause:13s} {(k.group(1) if k else ''):4s} | {last[:110]!r}")
json.dump(out,open('endcause.json','w'))
