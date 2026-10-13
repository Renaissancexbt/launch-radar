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

## Pipeline

```
X search / filtered stream (queries.py)     ← you collect, into JSON dumps
  → stop-phrase and bot filter               (scoring.py)
  → author enrichment: age, tweets, followers, bio, pinned
  → entity extraction: name, $ticker, CA, website, chain, category
  → score
  → store (sqlite): dedup one project = one author + one link/CA   (store.py)
  → watch: print only what is new                                  (cli.py)
  → planned: re-poll metrics at 10 / 30 / 60 min, feed / alerts above threshold
```

## Store

`store.py` keeps two tables in one sqlite file. `posts` holds every post ever scored with its
latest score and the full `Candidate.to_dict()` payload as JSON, so a later version can
re-read history without re-fetching. `seen` holds dedup keys. The key is
`author|ca:<contract>` when a contract is present, `author|link:<first link>` otherwise,
and `author|post:<id>` as the fallback, so a launch reposted by its own author collapses to
one row while the same link from a different handle stays a separate signal.

`watch` re-reads the whole input every pass instead of tailing it. Dumps are small and
this makes a half-written or rewritten file harmless.

## Design rules

* No network calls inside the library. Fetching is the caller's job.
* No dependencies. `pip install -e .` and it runs.
* Every weight is explained in a `reasons` list so a human can see why a post scored.
* Tests pin the ranking of the sample set; change weights, run tests.
