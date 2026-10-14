import json,sys,re
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
f=sys.argv[1]; pat=re.compile(sys.argv[2],re.I); lim=int(sys.argv[3]) if len(sys.argv)>3 else 8; roles=sys.argv[4].split(',') if len(sys.argv)>4 else ['assistant','user']
m=json.load(open(f))['messages']; n=0
for i,x in enumerate(m):
    if x['role'] not in roles: continue
    t=irlib.text_of(x)
    mm=pat.search(t)
    if mm:
        a=max(0,mm.start()-220); b=min(len(t),mm.end()+260)
        print(f"#{i} [{x['role']}] {x['timestamp'][:16]} ...{t[a:b]}...".replace('\n',' ')); n+=1
        if n>=lim: break
