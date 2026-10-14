import json,subprocess,re,os,collections
d=json.load(open('codex_all.json'))
d=[s for s in d if '/dev/fn' in (s.get('cwd') or '') and s['created_at']>='2026-10-09' and s['size_bytes']>300000]
out=[]
for s in d:
    p=f"cxp/{s['id']}.json"
    if not os.path.exists(p):
        r=subprocess.run(['cv','show','codex:'+s['id'],'--kind','prompt','--json'],capture_output=True,text=True)
        open(p,'w').write(r.stdout)
    try: rows=json.load(open(p))
    except Exception: continue
    seats=[]
    for r in rows:
        m=re.search(r'\b(?:Seat |Builder |Seat:? ?)?\b([ABCDLMOP])(\d{1,2})\b(?: \(succeeds| to |:| here|,)',r['text'][:300])
        if m: seats.append(m.group(1)+m.group(2))
    comp=subprocess.run(['grep','-c','"type":"compacted"',s['path']],capture_output=True,text=True).stdout.strip()
    out.append(dict(id=s['id'],cwd=s['cwd'].replace('/Users/ember/dev/fn/build/lanes/',''),created=s['created_at'],updated=s['updated_at'],prompts=len(rows),seats=sorted(set(seats),key=lambda x:(x[0],int(x[1:]))),compactions=int(comp or 0),mb=round(s['size_bytes']/1e6,1)))
json.dump(out,open('codex_seats.json','w'),indent=0)
multi=[o for o in out if len(o['seats'])>=2]
print('codex fn sessions >300KB since 10-09:',len(out),' resumed by >=2 distinct seats:',len(multi),' prompts total',sum(o['prompts'] for o in out))
print('prompts>1:',sum(1 for o in out if o['prompts']>1),' compacted>=1:',sum(1 for o in out if o['compactions']>0))
for o in sorted(multi,key=lambda o:-len(o['seats']))[:25]: print(o['id'][:8],o['cwd'][:24],o['created'][5:16],o['updated'][5:16],'prompts',o['prompts'],'compact',o['compactions'],o['mb'],'MB',o['seats'])
