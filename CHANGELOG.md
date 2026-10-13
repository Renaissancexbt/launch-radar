# Changelog

## 0.2.0 — 2026-10-13
- `launch-radar watch PATH`: poll a JSON file or a folder of dumps every N seconds, print only never-seen posts
- `launch-radar history`: newest / top / alerts-only view of everything scored so far
- `store.py`: sqlite memory with a dedup key of author + first contract or link
- 4 new tests (25 total)

## 0.1.0 — 2026-10-07
- Six phrase groups, ~150 launch phrases, stop phrases
- Entity extraction: cashtags, Solana/EVM contracts, links, launchpad, chain, category
- 0–100 scoring with explained reasons; feed/alert thresholds
- X search query builder with clickable URLs
- CLI: `queries`, `scan`, `check`
- 21 tests, sample dataset
