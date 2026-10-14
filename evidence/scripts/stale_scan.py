import json,sys,re
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
seats=json.load(open('seats.json'))
PAT=re.compile(r"(continuation (?:file )?(?:is|was) (?:stale|wrong|out of date|behind)|stale (?:continuation|file|brief|sha|id)|the continuation (?:says|said|claims|names)[^.]{0,80}(?:but|however|actually)|(?:already|was) (?:landed|done|pushed|merged|fixed) (?:by|in|at|on)[^.]{0,40}(?:predecessor|seat|previous)|my predecessor (?:had|already|did|left|was)|predecessor'?s? [^.]{0,60}(?:wrong|stale|missing|not in|omitted|didn't|did not)|not in the continuation|the brief (?:is|was) wrong|redo|re-?derive|re-?discover|rediscover|I (?:had|have) (?:missed|re-?run)|duplicat(?:e|ed) (?:work|run|certify))",re.I)
for s in seats:
    ir=json.load(open(f"ir/{s['agent']}.json"))
    for i,m in enumerate(ir['messages']):
        if m['role'] not in ('assistant','user'): continue
        t=irlib.text_of(m)
        for mm in PAT.finditer(t):
            a=max(0,mm.start()-200); b=min(len(t),mm.end()+200)
            print(f"{s['line']}{s['n']} {s['agent'][:8]}#{i} [{m['role'][:4]}/{m.get('kind')}] ...{t[a:b]}...".replace('\n',' '))
            break
