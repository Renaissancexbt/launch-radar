# Contributing

Thanks for stopping by. launch-radar is small on purpose, so contributions are easy.

## The fastest useful PR: a phrase

Found a launch post the radar missed? Add the phrase to the right group in
`launch_radar/keywords.py`, add the post text to `examples/sample_posts.json`
and a one-line assertion in `tests/test_scoring.py`. That is a complete PR.

## Rules of the house

* **Zero dependencies.** If it needs a package, it lives in an optional extra, not in core.
* **No network in the library.** Fetching is the caller's job. `cli.py` may fetch one day; `scoring.py` never will.
* **Every point explained.** If you add a scoring factor, it must append a human-readable line to `reasons`.
* **Tests pin the ranking.** Change weights, run `pytest`, make the sample ranking still make sense.

## Setup

```bash
git clone https://github.com/Renaissancexbt/launch-radar
cd launch-radar
pip install -e ".[dev]"
pytest
```

## Commit messages

Short, lowercase, imperative: `add bonk.fun launchpad`, `fix evm regex`, `tune stop-phrase penalty`.
