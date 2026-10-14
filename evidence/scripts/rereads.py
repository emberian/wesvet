import json,sys,glob,collections,re,os
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
for f in sorted(glob.glob('anat/*.json')):
    if 'doctor' in f: continue
    ir=json.load(open(f)); m=ir['messages']; calls=irlib.tool_calls(m)
    seen={}; rr=0; rrb=0; reads=0; rb=0; edited=collections.defaultdict(list)
    for c in calls:
        if irlib.classify(c)[0]=='edit': edited[os.path.basename(str(c['input'].get('file_path') or irlib.classify(c)[1]))].append(c['index'])
    for c in calls:
        for p,_ in irlib.read_targets(c):
            reads+=1; b=len(c['result'].encode()); rb+=b
            if p in seen:
                # was it edited since last read?
                if not any(seen[p]<e<c['index'] for e in edited[os.path.basename(p)]):
                    rr+=1; rrb+=b
            seen[p]=c['index']
    print(f"{f.split('/')[1][:-5]:22s} path-reads {reads:4d} ({rb/1e3:.0f} kB)  re-reads of an unedited path {rr:4d} ({rrb/1e3:.0f} kB, {rrb/max(rb,1)*100:.0f}% of read bytes)")
