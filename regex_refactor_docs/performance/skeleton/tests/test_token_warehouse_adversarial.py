
from __future__ import annotations

def test_malformed_maps_clamped():
    class Tok:
        def __init__(self, t, nesting=0, tag='', map_=None, info=None, content=''):
            self.type = t; self.nesting = nesting; self.tag = tag; self.map = map_
            self.info = info; self.content = content
        def attrGet(self, name): return None

    tokens = [Tok('heading_open',1,'h1',(-10,-5)), Tok('inline',0,'','',None,'X'), Tok('heading_close',-1,'h1',(-10,-5))]
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    wh = TokenWarehouse(tokens, tree=None)
    secs = wh.sections_list()
    assert secs and secs[0][1] >= 0  # start clamped to >=0

def test_links_flags_unsafe_schemes():
    class Tok:
        def __init__(self, t, nesting=0, tag='', map_=None, info=None, href=None, content=''):
            self.type=t; self.nesting=nesting; self.tag=tag; self.map=map_; self.info=info
            self._href = href; self.content = content
        def attrGet(self, name): 
            if name=='href':
                if isinstance(self._href, Exception):
                    raise self._href
                return self._href
            return None

    tokens = [Tok('link_open',1,'', (0,1), None, 'javascript:alert(1)'), Tok('inline',0,'','',None,'x'), Tok('link_close',-1,'')]
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    from doxstrux.markdown.collectors_phase8.links import LinksCollector
    wh = TokenWarehouse(tokens, tree=None)
    col = LinksCollector()
    wh.register_collector(col)
    wh.dispatch_all()
    data = wh.finalize_all()['links']
    assert data and data[0].get('allowed') is False
