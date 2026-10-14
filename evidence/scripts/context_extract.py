import json,sys,re
sys.path.insert(0,'/Users/ember/dev/wesvet/tools')
import irlib
def last_continuation(pred_msgs, line):
    """The last whole write of builder-<line>-continuation.md in the predecessor's transcript."""
    best=None
    for c in irlib.tool_calls(pred_msgs):
        inp=c['input']
        if c['name']=='Write' and f'builder-{line}-continuation' in inp.get('file_path',''):
            best=inp.get('content','')
        elif c['name']=='Bash':
            cmd=inp.get('command','')
            m=re.search(r"(?:cat|tee)\s*>?\s*\S*builder-"+line+r"-continuation\.md\s*<<-?\s*'?(\w+)'?\n(.*?)\n\1\s*(?:\n|$)",cmd,re.S)
            if m: best=m.group(2)
    return best
if __name__=='__main__':
    m=json.load(open(sys.argv[1]))['messages']; t=last_continuation(m,sys.argv[2])
    print(len(t) if t else None); print((t or '')[:400])
