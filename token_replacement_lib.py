
from markdown_it import MarkdownIt

from mdit_py_plugins.tasklists import tasklists_plugin as tasklists


md = (
    MarkdownIt("commonmark", options_update={"html": False, "linkify": True}).enable('table')
)
md.use(tasklists)

text = "- [ ] An item that needs doing\n- [x] An item that is complete"
# md.
def iter_blocks(text):
    tokens = md.parse(text)
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.type in {"fence", "code_block"}:
            yield {"kind": "code", "lang": (t.info or "").strip() or None, "map": t.map}
        elif t.type == "heading_open":
            inline = tokens[i+1] if i + 1 < len(tokens) else None
            heading_text = ""
            if inline and inline.type == "inline" and inline.children:
                heading_text = "".join(c.content for c in inline.children if c.type == "text")
            yield {"kind": "heading", "level": int(t.tag[1]), "text": heading_text, "map": t.map}
        i += 1

def extract_links_and_images(text):
    tokens = md.parse(text)
    links, images = [], []
    stack = list(tokens)
    while stack:
        tok = stack.pop()
        if tok.children:
            stack.extend(tok.children)
        if tok.type == "link_open":
            href = dict(tok.attrs or {}).get("href","")
            links.append(href)
        elif tok.type == "image":
            attrs = dict(tok.attrs or {})
            src = attrs.get("src","")
            alt = ""
            if tok.children:
                alt = "".join(c.content for c in tok.children if c.type == "text")
            images.append((src, alt))
    return links, images
