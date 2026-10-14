import json,sys
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
seats={s['line']+str(s['n']):s for s in json.load(open('seats.json'))}
k=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3]); W=int(sys.argv[4]) if len(sys.argv)>4 else 300
s=seats.get(k)
ir=json.load(open(f"ir/{s['agent']}.json")) if s else json.load(open(k))
m=ir['messages']
calls={c['index']:c for c in irlib.tool_calls(m)}
for i in range(a,min(b,len(m))):
    x=m[i]
    if x['role']=='assistant':
        t=irlib.text_of(x).strip()
        if t: print(f"#{i} A: {t[:W]}".replace('\n',' '))
        for c in x['content']:
            if c['type']=='tool_use':
                inp=c['input']; d=inp.get('description') or inp.get('command') or inp.get('file_path') or inp.get('message') or ''
                print(f"#{i}   [{c['name']}] {str(d)[:150]}".replace('\n',' '))
    elif x['role']=='user' and x['kind']!='prompt':
        t=irlib.text_of(x)
        if 'sent a message' in t[:200]: print(f"#{i} IN: {t[:W]}".replace('\n',' '))
    elif x['role']=='user': print(f"#{i} PROMPT: {irlib.text_of(x)[:W]}".replace('\n',' '))
