# Architecture

```
launch_radar/
  keywords.py   phrase groups + compiled regexes          (pure data)
  entities.py   ticker / CA / URL / chain / category      (pure functions)
  models.py     Post, Author, Candidate                   (dataclasses, from_dict normaliser)
  scoring.py    score(post) -> Candidate, rank(posts)     (the brain)
  queries.py    X advanced-search strings + URLs          (how to fetch)
  cli.py        queries / scan / check                    (how to use it)
```

Everything is pure and offline. Inputs are plain dicts, so the same code scores posts
from the X API, from a browser extension reading the timeline, or from a JSON file
someone pasted together.

## Planned pipeline

```
X search / filtered stream (queries.py)
  → dedup: one project = one author + one link/CA
  → stop-phrase and bot filter
  → author enrichment: age, tweets, followers, bio, pinned
  → entity extraction: name, $ticker, CA, website, chain, category
  → score
  → store (sqlite) + re-poll metrics at 10 / 30 / 60 min
  → feed / alerts (Telegram, dashboard) above threshold
```

## Design rules

* No network calls inside the library. Fetching is the caller's job.
* No dependencies. `pip install -e .` and it runs.
* Every weight is explained in a `reasons` list so a human can see why a post scored.
* Tests pin the ranking of the sample set; change weights, run tests.
