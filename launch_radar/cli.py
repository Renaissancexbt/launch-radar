"""Command line interface.

    launch-radar queries            print the default X search queries + URLs
    launch-radar queries --all      the exhaustive sweep
    launch-radar scan posts.json    score a JSON dump of posts, print the ranked table
    launch-radar scan posts.json --json --min 40   machine-readable feed
    launch-radar check "text ..."   score one piece of text quickly
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import Post
from .queries import default_queries, exhaustive_queries
from .scoring import rank, score


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

    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
