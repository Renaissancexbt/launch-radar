"""launch-radar: find brand-new project launches on X before the crowd does."""

from .models import Author, Candidate, Post
from .scoring import ALERT_THRESHOLD, FEED_THRESHOLD, rank, score
from .queries import default_queries, exhaustive_queries
from .entities import extract
from .keywords import match_all

__version__ = "0.1.0"

__all__ = [
    "Author", "Candidate", "Post", "rank", "score", "extract", "match_all",
    "default_queries", "exhaustive_queries", "FEED_THRESHOLD", "ALERT_THRESHOLD",
    "__version__",
]
