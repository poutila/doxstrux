
from __future__ import annotations
import time
from pathlib import Path

def benchmark_dummy(runs: int = 3, n_tokens: int = 10000):
    # Synthetic token stream
    class Tok:
        def __init__(self, t, nesting=0, tag="", map_=None, info=None, href=None, content=""):
            self.type = t
            self.nesting = nesting
            self.tag = tag
            self.map = map_
            self.info = info
            self._href = href
            self.content = content
        def attrGet(self, name):
            return self._href if name == "href" else None

    tokens = []
    # Repeat pattern: paragraph -> [link_open inline link_close] -> paragraph_close
    for i in range(n_tokens // 5):
        tokens.append(Tok("paragraph_open", 1, "", (i, i+1)))
        tokens.append(Tok("link_open", 1, "", (i, i+1), href="https://ex"))
        tokens.append(Tok("inline", 0, "", None, content="t"))
        tokens.append(Tok("link_close", -1, ""))
        tokens.append(Tok("paragraph_close", -1, "", (i, i+1)))

    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    from doxstrux.markdown.collectors_phase8.links import LinksCollector

    times = []
    for _ in range(runs):
        start = time.perf_counter()
        wh = TokenWarehouse(tokens, tree=None)
        col = LinksCollector()
        wh.register_collector(col)
        wh.dispatch_all()
        _ = wh.finalize_all()
        times.append(time.perf_counter() - start)
    return {"runs": runs, "median_ms": sorted(times)[runs//2] * 1000}

if __name__ == "__main__":
    print(benchmark_dummy())
