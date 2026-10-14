import json,sys,re
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
seats=json.load(open('seats.json'))
PAT=re.compile(r"(I was wrong|my mistake|I misread|that was wrong|I had assumed|I assumed|wrongly|my error|I missed|I mis[a-z]+|not what the continuation|the continuation (?:is|was) (?:wrong|stale|out of date)|continuation (?:said|says|claimed|named)|predecessor (?:had|left|said|named|wrote|thought)|already (?:done|landed|merged|pushed|certified|filed) (?:by|in) [A-Z]\d+|[A-Z]\d+ (?:already|had already))",re.I)
for s in seats:
    ir=json.load(open(f"ir/{s['agent']}.json")); m=ir['messages']
    for i,x in enumerate(m):
        if x['role']!='assistant': continue
        t=irlib.text_of(x)
        mm=PAT.search(t)
        if mm:
            a=max(0,mm.start()-220); b=min(len(t),mm.end()+220)
            print(f"{s['line']}{s['n']}#{i}/{len(m)}: ...{t[a:b]}...".replace('\n',' '))
