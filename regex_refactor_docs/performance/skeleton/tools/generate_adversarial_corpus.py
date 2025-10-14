
from __future__ import annotations
import json, random
from pathlib import Path

OUT = Path('adversarial_corpus.json')

def generate_adversarial(n_tokens=20000):
    toks = []
    toks.append({"type":"heading_open","nesting":1,"tag":"h1","map":[-1000,-999]})
    toks.append({"type":"inline","nesting":0,"content":"BadHeading"})
    toks.append({"type":"heading_close","nesting":-1,"tag":"h1","map":[-1000,-999]})
    for i in range(n_tokens):
        if i%5==0:
            toks.append({"type":"paragraph_open","nesting":1,"map":[i,i+1]})
        elif i%5==1:
            scheme = random.choice(["http","https","javascript","data","file"])
            if scheme in ("data","file"):
                href = f"{scheme}://evil/{i}"
            elif scheme=="javascript":
                href = "javascript:alert(1)"
            else:
                href = f"https://example.com/{i}"
            toks.append({"type":"link_open","nesting":1,"map":[i,i+1],"href":href})
        elif i%5==2:
            toks.append({"type":"inline","nesting":0,"content":"x"})
        elif i%5==3:
            toks.append({"type":"link_close","nesting":-1})
        else:
            toks.append({"type":"paragraph_close","nesting":-1,"map":[i,i+1]})
    toks.append({"type":"link_open","nesting":1,"map":[999999,1000000],"href":"RAISE_ATTRGET"})
    OUT.write_text(json.dumps(toks))
    print('Wrote', OUT.absolute())

if __name__=='__main__':
    generate_adversarial(20000)
