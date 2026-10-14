import json,glob,re,collections
PAT=re.compile(r"(taking over|successor to|succeed(?:s|ing)? [A-Z]|you are continuing|continuing the [\w`-]+ lane|continuation file|predecessor (?:lane|agent|seat)|your predecessor|previous (?:lane|agent|seat)'s|the (?:lane|agent) before you|handed off at|resum(?:e|ing) the [\w-]+ lane|second seat|third seat|\(successor\))",re.I)
rows=[]
for f in glob.glob('/Users/ember/.claude/projects/*/*/subagents/agent-*.jsonl'):
    proj=f.split('/projects/')[1].split('/')[0]
    try:
        with open(f) as fh:
            for ln in fh:
                r=json.loads(ln)
                if r.get('type')=='user':
                    c=r.get('message',{}).get('content')
                    t=c if isinstance(c,str) else ' '.join(b.get('text','') for b in c if isinstance(b,dict) and b.get('type')=='text')
                    break
            else: continue
    except Exception: continue
    if 'fork-boilerplate' in t[:40]: continue
    m=PAT.search(t)
    if m: rows.append((proj,f,r.get('timestamp'),m.group(0),t[:400].replace('\n',' ')))
json.dump(rows,open('succ_briefs2.json','w'))
c=collections.Counter(r[0] for r in rows)
for k,v in c.most_common(30): print(v,k)
