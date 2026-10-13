import json
from pathlib import Path

from launch_radar.cli import main
from launch_radar.models import Post
from launch_radar.scoring import rank, score
from launch_radar.store import Store, dedup_key

SAMPLE = Path(__file__).parent.parent / "examples" / "sample_posts.json"


def _post(pid, handle, text):
    return Post.from_dict({"id": pid, "text": text, "author": {"handle": handle}})


def test_ingest_returns_only_new(tmp_path):
    store = Store(tmp_path / "r.db")
    posts = [Post.from_dict(d) for d in json.loads(SAMPLE.read_text())]
    first = store.ingest(rank(posts))
    second = store.ingest(rank(posts))
    assert len(first) > 0
    assert second == []
    assert store.count() == len(posts)


def test_dedup_same_author_same_link(tmp_path):
    store = Store(tmp_path / "r.db")
    a = score(_post("1", "alice", "we just launched! https://lumen.app try it"))
    b = score(_post("2", "alice", "reminder: launched today https://lumen.app/"))
    c = score(_post("3", "bob", "launched today https://lumen.app/"))
    assert dedup_key(a) == dedup_key(b)
    assert dedup_key(a) != dedup_key(c)
    fresh = store.ingest([a, b, c])
    assert [x.post.id for x in fresh] == ["1", "3"]


def test_history_and_top(tmp_path):
    store = Store(tmp_path / "r.db")
    posts = [Post.from_dict(d) for d in json.loads(SAMPLE.read_text())]
    store.ingest(rank(posts))
    hist = store.history(limit=5)
    assert len(hist) == 5
    top = store.top(limit=3)
    assert top[0]["score"] >= top[-1]["score"]


def test_watch_once_and_history_cli(tmp_path, capsys):
    db = tmp_path / "r.db"
    assert main(["watch", str(SAMPLE), "--db", str(db), "--every", "0", "--min", "0"]) == 0
    out1 = capsys.readouterr().out
    assert "x.com" in out1
    assert main(["watch", str(SAMPLE), "--db", str(db), "--every", "0", "--min", "0"]) == 0
    assert capsys.readouterr().out.strip() == ""
    assert main(["history", "--db", str(db), "--limit", "3"]) == 0
    assert "posts in" in capsys.readouterr().out
