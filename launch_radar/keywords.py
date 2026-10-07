"""Phrase groups that signal a brand-new project announcement on X.

Launch posts use a surprisingly stable vocabulary. People have been writing
the same 20-30 phrases ("Introducing...", "We're live", "Just launched") for
a decade, which makes them a cheap and reliable first-pass signal.

Each group carries a weight used by :mod:`launch_radar.scoring`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PhraseGroup:
    key: str
    title: str
    weight: int
    phrases: tuple[str, ...]
    patterns: tuple[re.Pattern[str], ...] = field(default_factory=tuple, compare=False)

    def matches(self, text: str) -> list[str]:
        """Return the phrases from this group found in ``text``."""
        return [p for p, rx in zip(self.phrases, self.patterns) if rx.search(text)]


def _compile(phrases: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    out = []
    for p in phrases:
        # "[name]" is a wildcard for a project name; "$TICKER" for any cashtag.
        esc = re.escape(p)
        esc = esc.replace(re.escape("[name]"), r"[\w$.'-]{2,30}")
        esc = esc.replace(re.escape("$TICKER"), r"\$[A-Za-z][A-Za-z0-9]{1,11}")
        # treat spaces loosely (double spaces, line breaks)
        esc = esc.replace(r"\ ", r"\s+")
        out.append(re.compile(rf"(?<![\w$]){esc}(?![\w])", re.IGNORECASE))
    return tuple(out)


def group(key: str, title: str, weight: int, phrases: list[str]) -> PhraseGroup:
    ph = tuple(phrases)
    return PhraseGroup(key=key, title=title, weight=weight, phrases=ph, patterns=_compile(ph))


# 1. Direct announcement. Strongest textual signal.
DIRECT = group("direct", "Direct launch announcement", 30, [
    "introducing", "introducing our", "meet [name]", "say hello to",
    "allow us to introduce", "we're live", "we are live", "now live",
    "just launched", "launching today", "today we launch", "today we're launching",
    "officially launching", "officially live", "launch day", "it's here",
    "it is here", "it's finally here", "we just shipped", "just shipped",
    "we shipped", "announcing", "excited to announce", "thrilled to announce",
    "proud to announce", "happy to announce", "big announcement", "we built",
    "we've built", "we have built", "unveiling", "first look at", "sneak peek",
    "welcome to [name]", "[name] is live", "$TICKER is live", "is now live",
    "is officially live", "we're launching", "we are launching",
])

# 2. First-post vocabulary. A fresh account saying hello.
FIRST_POST = group("first_post", "First post of a new account", 15, [
    "hello world", "gm world", "first tweet", "first post", "our first tweet",
    "we're here", "we are here", "who we are", "what we're building",
    "what we are building", "1/ introducing", "new account",
    "follow us for updates", "follow for updates", "stay tuned", "more soon",
    "more coming soon", "we have arrived", "the journey begins", "day 1",
    "day one", "genesis", "chapter 1", "it begins",
])

# 3. Building / stealth / beta vocabulary.
BUILDING = group("building", "Coming out of stealth, beta, waitlist", 15, [
    "we've been building", "we have been building", "been cooking",
    "we've been cooking", "cooking something", "something new is coming",
    "something big is coming", "out of stealth", "emerging from stealth",
    "coming out of stealth", "after months of building", "after a year of building",
    "finally ready to share", "ready to share", "we're building", "we are building",
    "building in public", "from 0 to 1", "soft launch", "stealth launch",
    "quiet launch", "beta is live", "open beta", "public beta", "closed beta",
    "alpha is live", "early access", "join the waitlist", "waitlist is open",
    "waitlist open", "sign up for early access",
])

# 4. Crypto-native launch vocabulary. Weighted higher than 2/3.
CRYPTO = group("crypto", "Crypto launch vocabulary", 20, [
    "fair launch", "no presale", "no team allocation", "CA:", "contract:",
    "contract address", "CA is live", "token is live", "live on pump.fun",
    "launched on pump.fun", "live on raydium", "mainnet is live", "mainnet live",
    "testnet is live", "testnet live", "dev doxxed", "liquidity locked",
    "LP burned", "mint is live", "minting now", "whitelist is open",
    "presale is live", "airdrop is live", "points are live", "season 1 is live",
    "epoch 1", "TGE", "token generation event", "we're going live on",
    "launching on solana", "launching on base", "launching on ethereum",
    "gm, we're live",
])

# 5. Product-availability vocabulary (web2 flavoured).
PRODUCT = group("product", "Product is available", 15, [
    "our website is live", "website is live", "site is live", "app is live",
    "the app is live", "available now", "download now", "now available on",
    "live on the app store", "live on google play", "live on product hunt",
    "we're on product hunt", "launched on product hunt", "try it now",
    "try it out", "go try it", "start using", "sign up now", "get started",
])

# 6. Stop phrases. Same words, different meaning. Penalised unless a strong
#    project signal sits next to them.
STOP = group("stop", "Stop phrases (not a project)", -25, [
    "introducing myself", "introducing my", "introduce yourself",
    "just launched my newsletter", "launched my podcast", "now live on twitch",
    "live on kick", "giveaway", "retweet to win", "tag 3 friends", "follow + rt",
    "follow and rt", "drop your wallet", "first 100 to", "like and retweet",
])

SIGNAL_GROUPS: tuple[PhraseGroup, ...] = (DIRECT, FIRST_POST, BUILDING, CRYPTO, PRODUCT)
ALL_GROUPS: tuple[PhraseGroup, ...] = SIGNAL_GROUPS + (STOP,)


def match_all(text: str) -> dict[str, list[str]]:
    """Map group key -> matched phrases for every group that fired."""
    hits: dict[str, list[str]] = {}
    for g in ALL_GROUPS:
        m = g.matches(text)
        if m:
            hits[g.key] = m
    return hits


__all__ = [
    "PhraseGroup", "DIRECT", "FIRST_POST", "BUILDING", "CRYPTO", "PRODUCT",
    "STOP", "SIGNAL_GROUPS", "ALL_GROUPS", "match_all",
]
