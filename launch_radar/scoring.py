"""Score a post 0-100 as a "new project launch" candidate.

The text gives you a candidate. The author profile confirms it is a *new*
project and not an old account posting its tenth update. Growth over the
first 30 minutes is the best early indicator of whether anyone cares.

Thresholds (see docs/SCORING.md): >= 40 goes to the feed, >= 70 fires an alert.
"""

from __future__ import annotations

from datetime import datetime, timezone

from . import keywords as kw
from .entities import extract
from .models import Candidate, Post

FEED_THRESHOLD = 40
ALERT_THRESHOLD = 70


def _growth_points(post: Post) -> tuple[int, str | None]:
    """0..20 points for engagement velocity between two measurements."""
    if not post.later:
        return 0, None
    minutes = max(1, int(post.later.get("minutes", 30)))
    d_likes = max(0, int(post.later.get("likes", post.likes)) - post.likes)
    d_reposts = max(0, int(post.later.get("reposts", post.reposts)) - post.reposts)
    velocity = (d_likes + 3 * d_reposts) / minutes  # weighted engagements per minute
    if velocity <= 0:
        return 0, None
    pts = min(20, int(round(velocity * 10)))  # 2 eng/min = 20 pts
    return pts, f"growth {d_likes} likes / {d_reposts} reposts in {minutes}m (+{pts})"


def _bot_signals(post: Post) -> bool:
    text = post.text
    mentions = text.count("@")
    if mentions >= 6:
        return True
    hashtags = text.count("#")
    if hashtags >= 8:
        return True
    a = post.author
    if a.tweets > 2000 and a.followers < 50 and a.following > 1500:
        return True
    return False


def score(post: Post, now: datetime | None = None) -> Candidate:
    now = now or datetime.now(timezone.utc)
    reasons: list[str] = []
    pts = 0

    matched = kw.match_all(post.text)
    ents = extract(post.text, post.author.bio)
    # a stop phrase is forgiven only when there is hard project evidence next to it
    evidence = bool(ents.has_link or ents.tickers or ents.contracts)
    signal_hit = any(k in matched for k in (g.key for g in kw.SIGNAL_GROUPS))

    for g in kw.SIGNAL_GROUPS:
        if g.key in matched:
            pts += g.weight
            reasons.append(f"{g.title}: {', '.join(matched[g.key][:3])} (+{g.weight})")

    if "stop" in matched and not evidence:
        pts += kw.STOP.weight
        reasons.append(f"stop phrase: {', '.join(matched['stop'][:2])} ({kw.STOP.weight})")

    if ents.has_link:
        pts += 15
        reasons.append("has link / contract (+15)")
    if ents.tickers or ents.contracts:
        pts += 10
        reasons.append("ticker or contract address (+10)")
    if ents.launchpad:
        pts += 5
        reasons.append(f"launchpad link {ents.launchpad} (+5)")

    age = post.author.age_days(now)
    if age is not None:
        if age < 7:
            pts += 15
            reasons.append(f"account {age:.0f}d old (+15)")
        elif age < 60:
            pts += 10
            reasons.append(f"account {age:.0f}d old (+10)")
        elif age > 730 and post.author.tweets > 5000:
            pts -= 10
            reasons.append("old, chatty account (-10)")

    if post.author.pinned_post_id and post.author.pinned_post_id == post.id:
        pts += 5
        reasons.append("announcement is pinned (+5)")

    g_pts, g_reason = _growth_points(post)
    pts += g_pts
    if g_reason:
        reasons.append(g_reason)

    if _bot_signals(post):
        pts -= 30
        reasons.append("bot / spam signals (-30)")

    if post.is_reply or post.is_repost:
        pts -= 20
        reasons.append("reply or repost (-20)")

    if not signal_hit:
        # Without any launch vocabulary the rest is just a post with a link.
        pts = min(pts, 25)

    final = max(0, min(100, pts))
    return Candidate(
        post=post,
        score=final,
        matched=matched,
        reasons=reasons,
        tickers=ents.tickers,
        contracts=ents.contracts,
        links=ents.urls,
        launchpad=ents.launchpad,
        chain=ents.chain,
        category=ents.category,
    )


def rank(posts: list[Post], now: datetime | None = None, minimum: int = 0) -> list[Candidate]:
    out = [score(p, now) for p in posts]
    out = [c for c in out if c.score >= minimum]
    out.sort(key=lambda c: c.score, reverse=True)
    return out


__all__ = ["score", "rank", "FEED_THRESHOLD", "ALERT_THRESHOLD"]
