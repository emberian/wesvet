import json,sys,subprocess,os
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib, carry_recall as cr, sharpen
from context_extract import last_continuation
seats={s['line']+str(s['n']):s for s in json.load(open('seats.json'))}
pairs=[('P7','P8'),('P8','P9'),('P9','P10'),('M21','M22'),('M22','M23'),('L14','L15'),('L15','L16'),('B17','B18'),('B18','B19'),('A18','A19'),('A19','A20'),('C19','C20'),('C20','C21'),('O5','O6'),('D13','D14')]
common=['/Users/ember/dev/fn/build/coordinator/briefs/SEAT-COMMON-20261012.md','/Users/ember/dev/fn/build/coordinator/COORDINATION.md']
out=[]
for a,b in pairs:
    A=seats[a]; B=seats[b]
    pi=f"ir/{A['agent']}.json"; si=f"ir/{B['agent']}.json"
    pm=json.load(open(pi)); sm=json.load(open(si))['messages']
    d=f"packs/batch/{a}-{b}"; os.makedirs(d,exist_ok=True)
    open(f"{d}/brief.txt",'w').write(irlib.text_of(sm[0]))
    line=a[0].lower()
    reads=[c for c in irlib.tool_calls(sm)[:40] if (f'builder-{line}-continuation' in json.dumps(c['input']) or 'tool-results/' in json.dumps(c['input'])) and c['name'] in ('Bash','Read')]
    ctext='\n'.join(c['result'] for c in reads)
    cont={'index':len(ctext)}
    open(f"{d}/continuation.txt",'w').write(ctext)
    open(f"{d}/given.txt",'w').write(irlib.text_of(sm[0])+'\n'+ctext)
    if not os.path.exists(f"{d}/distill.md"):
        subprocess.run(['cv','distill','agent-'+A['agent'],'--pack',f"{d}/distill.md"],capture_output=True)
    base1,st1=sharpen.sharpen(pm,d,25,None,1)
    base,st=sharpen.sharpen(pm,d,25,None,2)
    open(f"{d}/full.txt",'w').write(cr.all_text(pm['messages']))
    packs=[('brief',f"{d}/brief.txt"),('continuation',f"{d}/continuation.txt"),('brief+continuation',f"{d}/given.txt"),('distill',f"{d}/distill.md"),('sharpened_v1',base1+'.sharpened.jsonl'),('sharpened_v2',base+'.sharpened.jsonl'),('full',f"{d}/full.txt")]
    r=cr.run(pm['messages'],sm,packs,common)
    r['pair']=f"{a}->{b}"; r['pred_peak']=st['recorded_context_at_end']; r['sharpened_v1_est_ctx']=st1['est_context_after']; r['sharpened_v2_est_ctx']=st['est_context_after']
    r['continuation_bytes']=len(ctext.encode())
    out.append(r)
    print(r['pair'],'needed',r['needed'],' '.join(f"{p['pack']}={p['recall']}/{p['recall_weighted']}({p['bytes']//1000}kB)" for p in r['packs']), 'ctx',r['pred_peak']//1000,'->',r['sharpened_v1_est_ctx']//1000,r['sharpened_v2_est_ctx']//1000)
json.dump(out,open('recall_batch.json','w'),indent=1)
