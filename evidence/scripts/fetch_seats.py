import json,glob,re,subprocess,os
seen={}
for f in sorted(glob.glob('lanes/*.json')):
  s=f.split('/')[1][:8]
  for l in json.load(open(f)):
    a=l['agent_id']
    if a in seen: continue
    l['root']=s; seen[a]=l
seats=[]
for l in seen.values():
  m=re.match(r'fn (?:Builder )?([A-Z])(\d*)\b[ :(]',l['description'] or '')
  if m and (l['started_at'] or '')>='2026-10-09':
    seats.append((m.group(1),int(m.group(2) or 1),l))
json.dump([dict(line=x,n=n,agent=l['agent_id'],root=l['root'],desc=l['description'],start=l['started_at'],status=l['status'],tokens=l['tokens']['total'],messages=l['messages']) for x,n,l in sorted(seats,key=lambda t:(t[0],t[1],t[2]['started_at']))],open('seats.json','w'),indent=0)
for x,n,l in seats:
  p=f"ir/{l['agent_id']}.json"
  if not os.path.exists(p):
    subprocess.run(f"cv show {l['root']} --agent {l['agent_id']} --json > {p}",shell=True)
print(len(seats))
