"""
Single source of truth for turning "how many days since this account
opened" into a lifecycle stage.

Why this file exists: lifecycle_stage used to be set two different,
disagreeing ways - the seed script computed it from a date, while the
live POST /api/accounts endpoint hardcoded "beginning" regardless of
date and never revisited it. That's how 51 real accounts ended up
permanently stuck at "beginning" with days_since_open=0 forever.

Every place that needs a lifecycle stage should compute it from
days_since_open using classify_lifecycle_stage() below, instead of
picking a stage independently of the account's actual age. That makes
stage-vs-date drift structurally impossible instead of something to
remember to keep in sync.
"""

# (min_days, max_days) inclusive, for each stage. Rescaled to fit
# within the mock dataset's Nov 2025-to-today window (see
# seed_database.py) rather than the multi-year ranges used before -
# "aged" now means "opened near the start of that window", not
# "opened 3-5 years ago".
STAGE_DAY_RANGES = {
    "brand_new": (0, 7),
    "early": (8, 21),
    "growing": (22, 60),
    "mature": (61, 150),
    "aged": (151, None),  # None = open-ended upper bound
}


def classify_lifecycle_stage(days_since_open: int) -> str:
    """Map an account's age in days to exactly one lifecycle stage."""
    for stage, (low, high) in STAGE_DAY_RANGES.items():
        if days_since_open >= low and (high is None or days_since_open <= high):
            return stage
    # Unreachable given the ranges above (aged has no upper bound and
    # low starts at 0), but keep a safe fallback rather than raising.
    return "aged"
