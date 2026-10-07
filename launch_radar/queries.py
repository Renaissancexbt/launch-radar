"""Build X search queries (and ready-to-open URLs) from the phrase groups.

X advanced search operators that matter here:

* ``filter:links``                 announcements almost always carry a link; cuts ~70% of noise
* ``-filter:replies -filter:retweets``   originals only
* ``min_faves:N``                  engagement floor; keep low (1-3) to catch early, filter by score later
* ``since:/until:``                time window; for a live stream use the last 15 minutes
* ``lang:en``                      default; add zh/ko/ja branches if you want them
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from . import keywords as kw


@dataclass(frozen=True)
class Query:
    name: str
    q: str

    @property
    def url(self) -> str:
        return f"https://x.com/search?q={quote(self.q, safe='')}&src=typed_query&f=live"


def _or(phrases: list[str]) -> str:
    return "(" + " OR ".join(f'"{p}"' for p in phrases) + ")"


def _clean(phrases: tuple[str, ...], limit: int) -> list[str]:
    # drop wildcard templates, X search cannot use them
    out = [p for p in phrases if "[name]" not in p and "$TICKER" not in p]
    return out[:limit]


BASE = "-filter:replies -filter:retweets"


def default_queries(lang: str = "en", min_faves: int = 2) -> list[Query]:
    L = f"lang:{lang}"
    return [
        Query(
            "direct",
            _or(["introducing", "we're live", "just launched", "now live", "announcing", "launching today"])
            + f" filter:links {BASE} {L} min_faves:{min_faves}",
        ),
        Query(
            "meet",
            f'{_or(["introducing", "say hello to", "meet"])} (protocol OR app OR platform OR token OR agent) {BASE} {L}',
        ),
        Query(
            "crypto",
            f'{_or(["fair launch", "stealth launch", "CA:", "contract address", "live on pump.fun", "token is live"])} '
            f"-filter:retweets {L}",
        ),
        Query(
            "first_post",
            f'{_or(["hello world", "first tweet", "gm world", "day 1"])} filter:links -filter:replies '
            f"(building OR launch OR protocol OR app OR token)",
        ),
        Query(
            "stealth",
            _or(["we've been building", "out of stealth", "been cooking", "open beta", "early access"])
            + f" filter:links {BASE} {L}",
        ),
        Query(
            "product",
            f'{_or(["app is live", "website is live", "live on product hunt", "available now"])} '
            f"filter:links {BASE} {L} min_faves:{min_faves}",
        ),
    ]


def exhaustive_queries(lang: str = "en", chunk: int = 8) -> list[Query]:
    """One query per chunk of phrases, for a slow but thorough sweep."""
    out: list[Query] = []
    for g in kw.SIGNAL_GROUPS:
        phrases = _clean(g.phrases, 999)
        for i in range(0, len(phrases), chunk):
            part = phrases[i:i + chunk]
            flt = "filter:links " if g.key != "crypto" else ""
            out.append(Query(f"{g.key}_{i // chunk + 1}", f"{_or(part)} {flt}{BASE} lang:{lang}"))
    return out


__all__ = ["Query", "default_queries", "exhaustive_queries"]
