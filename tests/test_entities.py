from launch_radar.entities import extract

SOL = "7cYaQc21w9dzKkGP6LgkqtmL5yzoK5UJE1GeamTRHwny"
EVM = "0x" + "ab" * 20


def test_ticker_extraction_drops_majors():
    e = extract("buying $RADAR with $SOL and $ETH")
    assert e.tickers == ["RADAR"]


def test_solana_ca_and_pumpfun_url():
    e = extract(f"CA: {SOL} https://pump.fun/coin/{SOL}")
    assert SOL in e.contracts
    assert e.launchpad == "pump.fun"
    assert e.chain == "solana"
    assert e.has_link


def test_evm_address_sets_chain():
    e = extract(f"contract: {EVM}")
    assert EVM in e.contracts
    assert e.chain == "evm"


def test_chain_from_words_when_no_contract():
    e = extract("launching on base next week https://x.co/abc")
    assert e.chain == "base"


def test_category_guess():
    e = extract("an AI agent swarm that trades perps")
    assert e.category in {"ai", "defi"}


def test_url_not_mistaken_for_contract():
    e = extract("https://example.com/abcdefghijklmnopqrstuvwxyzABCDEFGHIJK")
    assert e.contracts == []
    assert e.urls
