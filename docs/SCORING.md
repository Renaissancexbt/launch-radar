# Scoring

Every post gets 0–100. Feed threshold 40, alert threshold 70.

| Factor | Points | Note |
|---|---:|---|
| Direct announcement phrase ("introducing", "we're live", "just launched"…) | +30 | strongest text signal |
| Crypto launch phrase ("fair launch", "mainnet is live", "TGE"…) | +20 | |
| First-post / building / product phrase | +15 | one group counted once, groups stack |
| Has link or contract address | +15 | an announcement without a link is almost useless |
| Has $ticker or contract-shaped string | +10 | rarely fires on product launches |
| Link points to a known launch platform | +5 | |
| Account younger than 7 days | +15 | |
| Account younger than 60 days | +10 | |
| Announcement is the pinned post | +5 | classic launch move |
| Engagement growth between two measurements | +0…+20 | (likes + 3·reposts) per minute × 10, capped |
| Stop phrase without hard evidence (link/ticker/CA) | −25 | "introducing myself", "retweet to win"… |
| Bot / spam signals (≥6 mentions, ≥8 hashtags, follow-farm ratios) | −30 | |
| Account older than 2 years with >5000 tweets | −10 | more likely news than a new project |
| Reply or repost | −20 | |
| No launch phrase at all | cap 25 | a link plus a ticker is still just a post |

Stacking is intentional: a brand-new account that says "introducing", links the product and
pins the post hits 100 and that is exactly the case we want to catch within minutes.

## Tuning

Weights live at the top of each `PhraseGroup` in `launch_radar/keywords.py` and in
`launch_radar/scoring.py`. Run `pytest` after changing them; the sample set in
`examples/sample_posts.json` pins the ranking we expect.
