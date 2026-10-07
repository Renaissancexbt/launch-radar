from launch_radar import keywords as kw


def test_direct_phrase_matches_case_insensitive():
    hits = kw.match_all("INTRODUCING our new thing")
    assert "direct" in hits
    assert "introducing" in hits["direct"]


def test_name_wildcard():
    hits = kw.match_all("Meet Nightfall, the calm perps venue")
    assert "direct" in hits
    assert any(h.startswith("meet") for h in hits["direct"])


def test_ticker_wildcard():
    hits = kw.match_all("$RADAR is live on pump.fun")
    assert "direct" in hits and "crypto" in hits


def test_stop_phrase_fires():
    hits = kw.match_all("introducing myself to the team")
    assert "stop" in hits


def test_no_false_hit_inside_words():
    # "announcing" should not fire on "unannouncing" style substrings
    hits = kw.match_all("preannouncing nothing")
    assert "direct" not in hits


def test_every_group_has_unique_phrases():
    for g in kw.ALL_GROUPS:
        assert len(set(p.lower() for p in g.phrases)) == len(g.phrases), g.key
