import json,sys,re,os
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib, orientation_cost as oc
seats=json.load(open('seats.json'))
def norm(p):
    p=p.replace('~','/Users/ember')
    p=re.sub(r'^/Users/ember/dev/fn/build/lanes/[^/]+/','<lane>/',p)
    p=re.sub(r'^/Users/ember/dev/fn/','<fn>/',p)
    return p
def reads(ir):
    out=[]
    for c in irlib.tool_calls(ir['messages']):
        for p,_ in irlib.read_targets(c):
            out.append((c['index'],norm(p),len(c['result'].encode())))
    return out
rows=[]
prev={}
for s in sorted(seats,key=lambda s:(s['line'],s['start'])):
    ir=json.load(open(f"ir/{s['agent']}.json"))
    r=oc.measure(ir,0)
    brief=irlib.text_of(ir['messages'][0])
    s.update(brief_len=len(brief), brief_head=brief[:400], o=r)
    rd=reads(ir)
    fw=r['first_work']['index'] if r['first_work'] else 10**9
    s['orient_reads']=sorted({p for i,p,b in rd if i<fw})
    p=prev.get(s['line'])
    if p:
        known=p['all_reads']
        s['pred']=p['agent']
        ov=[(i,pp,b) for i,pp,b in rd if pp in known]
        s['reread_pred_files_n']=len({pp for _,pp,_ in ov})
        s['reread_pred_bytes']=sum(b for _,_,b in ov)
        s['reread_pred_bytes_orient']=sum(b for i,_,b in ov if i<fw)
        s['read_bytes_total']=sum(b for _,_,b in rd)
    s['all_reads']={pp for _,pp,_ in rd}
    prev[s['line']]=s
    rows.append(s)
for s in rows: s['all_reads']=sorted(s['all_reads'])
json.dump(rows,open('seat_orient.json','w'))
for s in rows:
    f=s['o']['first_work']; g=s['o']['first_state_change']
    print(f"{s['line']}{s['n']:<3d} {s['agent'][:8]} {s['start'][5:16]} {s['status'][:4]} {s['o']['total_tokens']/1e6:6.1f}M pk{s['o']['peak_context']/1e3:4.0f}k "
      + (f"| work {f['cls']:8s} {f['seconds']/60:5.1f}m {f['tokens']/1e6:5.2f}M ctx{f['context']/1e3:4.0f}k c{f['calls_before']:<3d}" if f else '| NONE') 
      + (f" | pred-reread {s.get('reread_pred_files_n',0)} files {s.get('reread_pred_bytes_orient',0)/1e3:.0f}kB orient / {s.get('reread_pred_bytes',0)/1e3:.0f}kB total" if 'pred' in s else ''))
