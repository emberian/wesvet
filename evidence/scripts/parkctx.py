import json,sys
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
seats={s['line']+str(s['n']):s for s in json.load(open('seats.json'))}
for k in sys.argv[1:]:
    s=seats[k]; ir=json.load(open(f"ir/{s['agent']}.json")); m=ir['messages']
    calls=irlib.tool_calls(m)
    parks=[c for c in calls if c['name']=='SendMessage' and str(c['input'].get('to'))=='main' and 'PARK' in str(c['input'].get('message','')).upper()[:400]]
    p=parks[0]
    us=[(i,u) for i,_,u in irlib.usage_rows(m)]
    ctx=[irlib.ctx_size(u) for i,u in us if i<=p['index']][-1]
    print(f"=== {k} {s['agent']} park#{p['index']} {p['ts'][:16]} ctx {ctx/1e3:.0f}k / {len(m)} msgs, end {m[-1]['timestamp'][:16]}")
    print('  PARK:',str(p['input'].get('message'))[:300].replace('\n',' '))
    n=0
    for i in range(p['index']+1,len(m)):
        x=m[i]
        if x['role']=='user' and 'sent a message' in irlib.text_of(x)[:200]:
            print(f'  #{i} {x["timestamp"][:16]} IN:',irlib.text_of(x)[:260].replace('\n',' ')); n+=1
            if n>=4: break
    ms=[c for c in calls if c['index']>p['index'] and c['name']=='SendMessage' and str(c['input'].get('to'))=='main']
    for c in ms[-2:]: print(f'  #{c["index"]} {c["ts"][:16]} OUT:',str(c['input'].get('message'))[:260].replace('\n',' '))
