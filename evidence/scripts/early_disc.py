import json,sys,re
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
seats=json.load(open('seats.json'))
PAT=re.compile(r"(already (?:exited|ended|finished|dead|gone|landed|on dev|merged|pushed|done|committed)|not running|no longer (?:running|exists|true)|is dead|has exited|died|stale|(?:brief|continuation) (?:says|said|names|claims|lists|has)|differs? from|doesn't match|does not match|mismatch|isn't on|is not on (?:dev|origin)|not pushed|unpushed|uncommitted|unaudited|no PID file|orphan)",re.I)
for s in seats:
    if s['n']==1: continue
    ir=json.load(open(f"ir/{s['agent']}.json")); m=ir['messages']
    hits=[]
    for i,x in enumerate(m[:160]):
        if x['role']!='assistant': continue
        t=irlib.text_of(x)
        mm=PAT.search(t)
        if mm:
            a=max(0,mm.start()-160); b=min(len(t),mm.end()+160)
            hits.append(f"#{i}: ...{t[a:b]}...".replace('\n',' '))
    if hits:
        print(f"== {s['line']}{s['n']} ({s['agent'][:8]})")
        for h in hits[:3]: print('  ',h)
