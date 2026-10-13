"""Command line interface.

    launch-radar queries            print the default X search queries + URLs
    launch-radar queries --all      the exhaustive sweep
    launch-radar scan posts.json    score a JSON dump of posts, print the ranked table
    launch-radar scan posts.json --json --min 40   machine-readable feed
    launch-radar check "text ..."   score one piece of text quickly
    launch-radar watch dumps/       poll a folder of JSON dumps, print only never-seen posts
    launch-radar history            what the radar has seen so far (from radar.db)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .models import Post
from .queries import default_queries, exhaustive_queries
from .scoring import rank, score
from .store import Store


def _load_posts(path: Path) -> list[Post]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("posts") or data.get("data") or []
    return [Post.from_dict(d) for d in data]


def _print_table(cands) -> None:
    if not cands:
        print("nothing above threshold")
        return
    print(f"{'score':>5}  {'status':<6} {'author':<18} {'chain':<8} {'cat':<7} text")
    print("-" * 100)
    for c in cands:
        text = c.post.text.replace("\n", " ")
        if len(text) > 60:
            text = text[:57] + "..."
        print(f"{c.score:>5}  {c.status:<6} {'@' + c.post.author.handle:<18} "
              f"{(c.chain or '-'):<8} {(c.category or '-'):<7} {text}")
    print()
    for c in cands[:5]:
        print(f"[{c.score}] {c.post.url}")
        for r in c.reasons:
            print(f"      - {r}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="launch-radar", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("queries", help="print X search queries")
    q.add_argument("--all", action="store_true", help="exhaustive sweep instead of the 6 defaults")
    q.add_argument("--lang", default="en")
    q.add_argument("--urls", action="store_true", help="print clickable x.com URLs")

    s = sub.add_parser("scan", help="score a JSON file of posts")
    s.add_argument("file", type=Path)
    s.add_argument("--min", type=int, default=0, help="minimum score to show (40 = feed, 70 = alert)")
    s.add_argument("--json", action="store_true", help="output JSON instead of a table")

    c = sub.add_parser("check", help="score a single text")
    c.add_argument("text", nargs="+")

    w = sub.add_parser("watch", help="poll a file or folder of JSON dumps; print only new posts")
    w.add_argument("path", type=Path, help="a posts.json or a folder of *.json dumps")
    w.add_argument("--db", type=Path, default=Path("radar.db"))
    w.add_argument("--min", type=int, default=40, help="minimum score to print (default 40 = feed)")
    w.add_argument("--every", type=int, default=60, help="seconds between polls; 0 = run once")
    w.add_argument("--json", action="store_true")

    h = sub.add_parser("history", help="show what the radar has already seen")
    h.add_argument("--db", type=Path, default=Path("radar.db"))
    h.add_argument("--limit", type=int, default=30)
    h.add_argument("--min", type=int, default=0)
    h.add_argument("--top", action="store_true", help="order by score instead of time")

    a = ap.parse_args(argv)

    if a.cmd == "queries":
        qs = exhaustive_queries(a.lang) if a.all else default_queries(a.lang)
        for x in qs:
            print(f"# {x.name}\n{x.q}")
            if a.urls:
                print(x.url)
            print()
        return 0

    if a.cmd == "scan":
        posts = _load_posts(a.file)
        cands = rank(posts, minimum=a.min)
        if a.json:
            json.dump([x.to_dict() for x in cands], sys.stdout, ensure_ascii=False, indent=2)
            print()
        else:
            _print_table(cands)
        return 0

    if a.cmd == "check":
        text = " ".join(a.text)
        cand = score(Post.from_dict({"id": "0", "text": text, "author": {"handle": "unknown"}}))
        print(f"score {cand.score} ({cand.status})")
        for r in cand.reasons:
            print(f"  - {r}")
        if cand.tickers:
            print(f"  tickers: {', '.join(cand.tickers)}")
        if cand.contracts:
            print(f"  contracts: {', '.join(cand.contracts)}")
        return 0

    if a.cmd == "watch":
        return _watch(a)

    if a.cmd == "history":
        store = Store(a.db)
        rows = store.top(a.limit) if a.top else store.history(a.limit, a.min)
        if not rows:
            print(f"{a.db}: empty")
            return 0
        print(f"{'score':>5}  {'status':<6} {'seen':<20} {'author':<18} text")
        print("-" * 100)
        for r in rows:
            text = (r["text"] or "").replace("\n", " ")
            if len(text) > 50:
                text = text[:47] + "..."
            print(f"{r['score']:>5}  {r['status']:<6} {r['first_seen'][:19]:<20} {'@' + r['author']:<18} {text}")
        print(f"\n{store.count()} posts in {a.db}")
        return 0

    return 1


def _dump_files(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(p for p in path.glob("*.json") if p.is_file())
    return [path] if path.exists() else []


def _watch(a) -> int:
    store = Store(a.db)
    print(f"watching {a.path}  db={a.db}  min={a.min}  every={a.every}s  (ctrl-c to stop)", file=sys.stderr)
    try:
        while True:
            posts: list[Post] = []
            for f in _dump_files(a.path):
                try:
                    posts.extend(_load_posts(f))
                except (ValueError, OSError) as e:  # half-written file, keep going
                    print(f"skip {f.name}: {e}", file=sys.stderr)
            fresh = [c for c in store.ingest(rank(posts)) if c.score >= a.min]
            if fresh:
                if a.json:
                    for c in fresh:
                        print(json.dumps(c.to_dict(), ensure_ascii=False))
                else:
                    stamp = time.strftime("%H:%M:%S")
                    for c in fresh:
                        text = c.post.text.replace("\n", " ")
                        if len(text) > 70:
                            text = text[:67] + "..."
                        print(f"{stamp}  [{c.score:>3} {c.status:<5}] @{c.post.author.handle}: {text}")
                        print(f"          {c.post.url}")
                sys.stdout.flush()
            if a.every <= 0:
                return 0
            time.sleep(a.every)
    except KeyboardInterrupt:
        print(f"\nstopped. {store.count()} posts in {a.db}", file=sys.stderr)
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
