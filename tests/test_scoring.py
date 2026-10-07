import json
from datetime import datetime, timezone
from pathlib import Path

from launch_radar import Post, rank, score
from launch_radar.scoring import ALERT_THRESHOLD, FEED_THRESHOLD

NOW = datetime(2026, 10, 7, 4, 0, tzinfo=timezone.utc)
SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample_posts.json"


def _posts():
    return [Post.from_dict(d) for d in json.loads(SAMPLE.read_text())]


def _by_id(cands, pid):
    return next(c for c in cands if c.post.id == pid)


def test_sample_ranking_puts_real_launches_on_top():
    cands = rank(_posts(), now=NOW)
    ids = [c.post.id for c in cands]
    # the fresh launch and the out-of-stealth beta beat everything
    assert ids[0] == "1001"
    assert ids.index("1005") < ids.index("1003")
    assert ids.index("1007") < ids.index("1006")


def test_fresh_account_launch_is_alert():
    c = _by_id(rank(_posts(), now=NOW), "1001")
    assert c.score >= ALERT_THRESHOLD
    assert c.status == "alert"
    assert c.links
    assert any("pinned" in r for r in c.reasons)


def test_giveaway_is_noise():
    c = _by_id(rank(_posts(), now=NOW), "1004")
    assert c.score < FEED_THRESHOLD


def test_introducing_myself_is_noise():
    c = _by_id(rank(_posts(), now=NOW), "1003")
    assert c.score < FEED_THRESHOLD
    assert any("stop phrase" in r for r in c.reasons)


def test_podcast_now_live_is_noise():
    c = _by_id(rank(_posts(), now=NOW), "1006")
    assert c.score < FEED_THRESHOLD


def test_new_account_hello_world_reaches_feed():
    c = _by_id(rank(_posts(), now=NOW), "1002")
    assert c.score >= FEED_THRESHOLD


def test_text_without_signal_is_capped():
    p = Post.from_dict({"id": "x", "text": "check https://example.com $ABC", "author": {"handle": "a"}})
    assert score(p, now=NOW).score <= 25


def test_growth_adds_points():
    base = {"id": "g", "text": "we're live https://a.b", "author": {"handle": "a"}, "likes": 0, "reposts": 0}
    slow = score(Post.from_dict(base), now=NOW).score
    fast = score(Post.from_dict({**base, "later": {"minutes": 10, "likes": 20, "reposts": 5}}), now=NOW).score
    assert fast > slow


def test_score_bounds():
    for c in rank(_posts(), now=NOW):
        assert 0 <= c.score <= 100
