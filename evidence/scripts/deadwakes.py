import json,sys,re,statistics as st
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
seats=json.load(open('seats.json'))
PARK=re.compile(r'(\bI\b|seat|\b[A-Z]\d+\b)\W{0,3}(am |is |has |have )?(now )?park',re.I)
rows=[]
for s in seats:
    m=json.load(open(f"ir/{s['agent']}.json"))['messages']; calls=irlib.tool_calls(m)
    parks=[c for c in calls if c['name']=='SendMessage' and str(c['input'].get('to'))=='main' and PARK.search(str(c['input'].get('message',''))[:300])]
    if not parks: continue
    p=parks[-1]['index']  # the final park notice
    us=[(i,u) for i,_,u in irlib.usage_rows(m) if i>p]
    wakes=[i for i,x in enumerate(m) if i>p and x['role']=='user' and 'sent a message' in irlib.text_of(x)[:200]]
    work=[c for c in calls if c['index']>p and irlib.classify(c)[0] in irlib.STATE_CLASSES]
    tok=sum(irlib.tok_total(u) for i,u in us)
    rows.append(dict(seat=s['line']+str(s['n']),wakes=len(wakes),work=len(work),tok=tok,reqs=len(us)))
dead=[r for r in rows if r['wakes'] and r['work']==0]
live=[r for r in rows if r['wakes'] and r['work']>0]
print('seats with a final park notice',len(rows))
print('woken after final park, no state change:',len(dead),'seats',sum(r['wakes'] for r in dead),'wakes',round(sum(r['tok'] for r in dead)/1e6,1),'M tokens; median per seat',round(st.median(r['tok'] for r in dead)/1e6,2) if dead else 0)
print('woken after final park, did work:',len(live),[ (r['seat'],r['wakes'],r['work'],round(r['tok']/1e6,1)) for r in live])
json.dump(rows,open('deadwakes.json','w'))
