
from __future__ import annotations
import sys, time, json, tracemalloc, argparse
from pathlib import Path

def make_token(obj):
    # Create a lightweight token object that matches required attributes and methods
    class Tok:
        def __init__(self, o):
            self.type = o.get("type")
            self.nesting = int(o.get("nesting") or 0)
            self.tag = o.get("tag") or ""
            # map may be list or tuple
            mp = o.get("map")
            if mp is not None and isinstance(mp, (list, tuple)) and len(mp) == 2:
                self.map = (mp[0], mp[1])
            else:
                self.map = None
            self.info = o.get("info")
            # support attrGet used by collectors
            self._href = o.get("href")
            self.content = o.get("content") or ""
            # emulate raising attrGet for sentinel
            def attrGet(name):
                if self._href == "RAISE_ATTRGET":
                    raise RuntimeError("emulated attrGet failure")
                if name == "href":
                    return self._href
                return None
            self.attrGet = attrGet
    return Tok(obj)

def run(path, runs=1, show_sample=5):
    p = Path(path)
    if not p.exists():
        print("File not found:", path); return 2
    objs = json.loads(p.read_text(encoding="utf-8"))
    tokens = [make_token(o) for o in objs]
    # lazy import to avoid requiring package when not running
    from doxstrux.markdown.utils.token_warehouse import TokenWarehouse
    from doxstrux.markdown.collectors_phase8.links import LinksCollector

    print(f"Loaded {len(tokens)} tokens from {p}")
    times = []
    mem_peaks = []
    for i in range(runs):
        tracemalloc.start()
        t0 = time.perf_counter()
        wh = TokenWarehouse(tokens, tree=None)
        col = LinksCollector()
        wh.register_collector(col)
        wh.dispatch_all()
        results = wh.finalize_all()
        t1 = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        dur_ms = (t1 - t0) * 1000.0
        times.append(dur_ms)
        mem_peaks.append(peak / (1024 * 1024))
        print(f"Run {i+1}: {dur_ms:.2f} ms, peak memory {peak/(1024*1024):.2f} MB, links found: {len(results.get('links', []))}, collector_errors: {len(getattr(wh, '_collector_errors', []))}")
    med = sorted(times)[len(times)//2]
    med_mem = sorted(mem_peaks)[len(mem_peaks)//2]
    print("Median time (ms):", f"{med:.2f}", "Median peak mem (MB):", f"{med_mem:.2f}")
    # sample output
    links = results.get("links", [])
    print("\\nSample links (first %d):" % show_sample)
    for l in links[:show_sample]:
        print(l)
    # write a simple JSON report
    report = {
        "tokens": len(tokens),
        "runs": runs,
        "times_ms": times,
        "mem_peaks_mb": mem_peaks,
        "links_count": len(links),
        "collector_errors": getattr(wh, "_collector_errors", []),
    }
    out = p.parent / (p.stem + "_report.json")
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Wrote report to", out)
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run adversarial corpus through TokenWarehouse and collectors.')
    parser.add_argument('path', help='Path to adversarial_corpus.json')
    parser.add_argument('--runs', type=int, default=1, help='Number of runs to average')
    parser.add_argument('--sample', type=int, default=5, help='Number of sample links to print')
    args = parser.parse_args()
    sys.exit(run(args.path, runs=args.runs, show_sample=args.sample))
