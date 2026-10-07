"""Extract project entities from a post: tickers, contract addresses, links,
chain and rough category."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

CASHTAG_RE = re.compile(r"(?<![\w$])\$([A-Za-z][A-Za-z0-9]{1,11})\b")
EVM_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
# Solana base58, 32-44 chars, no 0 O I l.
SOL_RE = re.compile(r"(?<![1-9A-HJ-NP-Za-km-z])[1-9A-HJ-NP-Za-km-z]{32,44}(?![1-9A-HJ-NP-Za-km-z])")
URL_RE = re.compile(r"https?://[^\s)\]}>\"']+", re.IGNORECASE)

LAUNCHPAD_HOSTS = {
    "pump.fun": "solana", "bonk.fun": "solana", "letsbonk.fun": "solana",
    "raydium.io": "solana", "dexscreener.com": None, "dextools.io": None,
    "zora.co": "base", "clanker.world": "base", "virtuals.io": "base",
    "four.meme": "bsc",
}

CHAIN_WORDS = {
    "solana": ("solana", "sol ", "$sol", "pump.fun", "raydium", "phantom"),
    "base": ("on base", "base chain", "@base", "zora", "clanker"),
    "ethereum": ("ethereum", "eth mainnet", "on eth", "uniswap"),
    "bsc": ("bsc", "bnb chain", "four.meme", "pancakeswap"),
    "monad": ("monad",),
    "hyperliquid": ("hyperliquid", "hyperevm"),
}

CATEGORY_WORDS = {
    "token": ("token", "$", "ca:", "contract", "fair launch", "memecoin", "meme coin"),
    "ai": ("ai agent", "agent", "llm", "model", "autonomous", "swarm", "grok", "gpt"),
    "defi": ("defi", "yield", "perp", "lending", "swap", "liquidity", "vault", "staking"),
    "nft": ("nft", "mint", "collection", "pfp"),
    "game": ("game", "play", "gaming", "arena", "duel", "quest"),
    "infra": ("protocol", "sdk", "api", "chain", "rollup", "node", "indexer"),
    "social": ("social", "feed", "posts", "creator", "followers", "community"),
    "app": ("app", "platform", "dashboard", "tool", "extension"),
}

STABLES = {"SOL", "ETH", "BTC", "USDC", "USDT", "BNB", "USD", "BASE"}


@dataclass
class Entities:
    tickers: list[str] = field(default_factory=list)
    contracts: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    launchpad: str | None = None
    chain: str | None = None
    category: str | None = None

    @property
    def has_link(self) -> bool:
        return bool(self.urls or self.contracts)


def _host(url: str) -> str:
    h = re.sub(r"^https?://", "", url, flags=re.IGNORECASE).split("/")[0].lower()
    return h[4:] if h.startswith("www.") else h


def extract(text: str, bio: str = "") -> Entities:
    """Pull tickers, contract addresses, links, chain and category out of text."""
    e = Entities()
    e.urls = URL_RE.findall(text)
    e.tickers = sorted({t.upper() for t in CASHTAG_RE.findall(text)} - STABLES)

    body_no_urls = URL_RE.sub(" ", text)
    e.contracts = sorted(set(EVM_RE.findall(body_no_urls)) | set(SOL_RE.findall(body_no_urls)))

    for u in e.urls:
        h = _host(u)
        for pad, chain in LAUNCHPAD_HOSTS.items():
            if h == pad or h.endswith("." + pad):
                e.launchpad = pad
                if chain:
                    e.chain = chain
        # pump.fun mint addresses live in the URL path
        if "pump.fun" in h:
            m = SOL_RE.search(u)
            if m and m.group(0) not in e.contracts:
                e.contracts.append(m.group(0))

    low = f"{text}\n{bio}".lower()
    if not e.chain:
        if any(c.startswith("0x") for c in e.contracts):
            e.chain = "evm"
        elif e.contracts:
            e.chain = "solana"
    if not e.chain:
        for chain, words in CHAIN_WORDS.items():
            if any(w in low for w in words):
                e.chain = chain
                break

    best, best_n = None, 0
    for cat, words in CATEGORY_WORDS.items():
        n = sum(low.count(w) for w in words)
        if n > best_n:
            best, best_n = cat, n
    e.category = best
    return e


__all__ = ["Entities", "extract", "CASHTAG_RE", "EVM_RE", "SOL_RE", "URL_RE"]
