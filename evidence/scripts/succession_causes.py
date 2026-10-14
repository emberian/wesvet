# Classify each fn seat succession by cause: regex over the successor's brief and the predecessor's
# end cause (endcause.json from endcause.py). Run from the scratch directory holding seats.json and ir/.
import json,re,collections,sys
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
seats=json.load(open('seats.json')); e=json.load(open('endcause.json'))
by=collections.defaultdict(list)
for s in seats: by[s['line']].append(s)
C=collections.Counter(); ex=collections.defaultdict(list)
for line,v in by.items():
    v.sort(key=lambda s:s['start'])
    for i in range(1,len(v)):
        pred,succ=v[i-1],v[i]
        b=irlib.text_of(json.load(open(f"ir/{succ['agent']}.json"))['messages'][0])[:1500]
        pe=e[pred['agent']]['cause']
        if re.search(r'post-restart|harness restart|coordinator restart|session change|post-prune|restart at|killed by a',b,re.I): cause='parent session restart/prune'
        elif re.search(r'abeyance|macOS update|laptop restart',b,re.I) or pe=='abeyance': cause='abeyance (planned stop)'
        elif re.search(r'weekly|usage limit|usage wall|the wall',b,re.I) or pred['status']=='failed': cause='usage wall / failure'
        elif re.search(r'wound down|wind-down|winding',b,re.I) or pe=='wind-down': cause='wind-down'
        elif pe in ('ceiling-park',) or re.search(r'parked at (about |~)?\d{3}K|at its (context )?(mark|ceiling)|350K',b,re.I): cause='context ceiling park (policy)'
        elif pe=='park': cause='park (other/unspecified)'
        else: cause='other: '+pe
        C[cause]+=1; ex[cause].append(f"{pred['line']}{pred['n']}->{succ['line']}{succ['n']}")
for k,v in C.most_common(): print(v,k,ex[k][:8])
print(sum(C.values()))
