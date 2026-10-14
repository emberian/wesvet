import json,subprocess,os,sys,re
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib, orientation_cost as oc
rows=json.load(open('succ_briefs2.json'))
seat_agents={s['agent'] for s in json.load(open('seats.json'))}
out=[]
for proj,f,t,match,head in rows:
    root=f.split('/')[-3]; ag=f.split('/')[-1][len('agent-'):-len('.jsonl')]
    if ag in seat_agents: continue
    p=f"irx/{ag}.json"
    if not os.path.exists(p):
        r=subprocess.run(['cv','show',root,'--agent',ag,'--json'],capture_output=True,text=True)
        if r.returncode!=0: continue
        open(p,'w').write(r.stdout)
    try: ir=json.load(open(p))
    except Exception: continue
    if not ir.get('messages'): continue
    r=oc.measure(ir,0)
    out.append(dict(proj=proj,root=root,agent=ag,start=t,match=match,head=head,o=r))
json.dump(out,open('xproj_orient.json','w'))
print(len(out))
