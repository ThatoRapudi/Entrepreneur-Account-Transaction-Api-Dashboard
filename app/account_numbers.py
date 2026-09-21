"""
Account number format: "ACC-" followed by a fixed 9 digits (e.g.
ACC-100000001) - short and sequential, instead of the old ACC-<uuid4>
(~40 characters). One shared generator used by both the seed script and
the live POST /api/accounts endpoint, so the format can't drift between
mock data and live-created accounts (the same pattern already used for
lifecycle_stage in app/lifecycle.py).

Numbers start at 100_000_000 so every account number is always exactly
9 digits (never fewer, if we ever got below that by counting from 1).
"""

import re

ACCOUNT_NUMBER_PREFIX = "ACC-"
ACCOUNT_NUMBER_DIGITS = 9
ACCOUNT_NUMBER_START = 100_000_000

_ACCOUNT_ID_PATTERN = re.compile(rf"^{ACCOUNT_NUMBER_PREFIX}(\d{{{ACCOUNT_NUMBER_DIGITS}}})$")


def format_account_id(number: int) -> str:
    return f"{ACCOUNT_NUMBER_PREFIX}{number:0{ACCOUNT_NUMBER_DIGITS}d}"


def next_account_number(db) -> int:
    """
    One past the highest existing ACC-DDDDDDDDD number in the accounts
    table - old long-format (ACC-<uuid4>) rows don't match the pattern
    and are simply ignored, so this picks up the new short sequence
    correctly even in a database that still has old-format rows in it.

    A single query, not called in a loop - the seed script calls this
    once before generating a whole batch and increments locally from
    there; the live create-account endpoint calls it once per request.
    """
    from app import models  # local import - avoids a circular import with models.py

    max_number = ACCOUNT_NUMBER_START - 1
    for (account_id,) in db.query(models.Account.account_id).all():
        match = _ACCOUNT_ID_PATTERN.match(account_id or "")
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number + 1
