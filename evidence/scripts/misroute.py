import json,sys,glob,re,datetime as dt
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
seats=json.load(open('seats.json'))
info={}
for s in seats:
    ir=json.load(open(f"ir/{s['agent']}.json")); m=ir['messages']
    # park time: last SendMessage to main
    sends=[c for c in irlib.tool_calls(m) if c['name']=='SendMessage' and str(c['input'].get('to'))=='main']
    info[s['agent']]=dict(line=s['line'],n=s['n'],start=irlib.ts(s['start']),end=irlib.ts(m[-1]['timestamp']),park=irlib.ts(sends[-1]['ts']) if sends else irlib.ts(m[-1]['timestamp']))
def resolve(to):
    to=str(to)
    for a in info:
        if len(to)>=8 and a.startswith(to[:17]): return a
    return None
def successor_started(a,t):
    i=info[a]
    return any(j['line']==i['line'] and j['start']>i['start'] and j['start']<=t for j in info.values())
sends=[]
# seat-sent
for s in seats:
    ir=json.load(open(f"ir/{s['agent']}.json"))
    for c in irlib.tool_calls(ir['messages']):
        if c['name']=='SendMessage': sends.append((s['line']+str(s['n']),c))
# coordinator-sent: raw jsonl
for f in glob.glob('/Users/ember/.claude/projects/-Users-ember-dev-minidregg/*.jsonl'):
    if not re.search(r'/(35f3668a|4a22422c|905fe751|608deb34|d5d27b94)[^/]*\.jsonl$',f) or '.flat.' in f: continue
    for ln in open(f):
        try:r=json.loads(ln)
        except: continue
        if r.get('type')!='assistant': continue
        for b in r.get('message',{}).get('content',[]) or []:
            if isinstance(b,dict) and b.get('type')=='tool_use' and b.get('name')=='SendMessage':
                sends.append(('coord:'+f.split('/')[-1][:8],dict(ts=r['timestamp'],input=b.get('input',{}),id=b.get('id'))))
seen=set(); tot=0; mis=[]; toparked=[]
for who,c in sends:
    if c.get('id') in seen: continue
    seen.add(c.get('id'))
    a=resolve(c['input'].get('to'))
    if not a: continue
    tot+=1; t=irlib.ts(c['ts'])
    if t>info[a]['park']+dt.timedelta(seconds=60):
        succ=successor_started(a,t)
        (mis if succ else toparked).append((c['ts'][:16],who,info[a]['line']+str(info[a]['n']),str(c['input'].get('summary') or c['input'].get('message'))[:120].replace('\n',' ')))
print('seat-addressed sends',tot,'to a seat after its park',len(mis)+len(toparked),'of which successor already running',len(mis))
for x in mis: print('MIS',x)
for x in toparked[:40]: print('PARKED',x)
