"""Asset identifier validation and conservative resolution from free text."""

import re

from ..cache import ttl_cache
from ..db import queries
from ..db.sql import run_query
from ..errors import InvalidRequest, UnknownAsset

ASSET_ID_RE = re.compile(r"^[A-Z]{2,5}-\d{1,6}$")
_IN_TEXT_RE = re.compile(r"\b([A-Za-z]{2,5})[-\s]?(\d{1,6})\b")


@ttl_cache()
def known_asset_ids() -> frozenset[str]:
    return frozenset(r["asset_id"] for r in run_query(queries.ASSET_IDS))


def normalize(asset_id: str) -> str:
    value = (asset_id or "").strip().upper()
    if not ASSET_ID_RE.match(value):
        raise InvalidRequest("Asset IDs look like 'TX-184'.")
    return value


def validate(asset_id: str) -> str:
    value = normalize(asset_id)
    if value not in known_asset_ids():
        raise UnknownAsset(value)
    return value


def find_in_question(question: str) -> list[str]:
    """Known asset IDs mentioned in the text, in order of first mention.

    Only IDs that exist in the portfolio count, so ordinary words with a
    number (e.g. 'June 2026', 'WO-2841') are never mistaken for assets.
    """
    known = known_asset_ids()
    found: list[str] = []
    for prefix, num in _IN_TEXT_RE.findall(question or ""):
        candidate = f"{prefix.upper()}-{num}"
        if candidate in known and candidate not in found:
            found.append(candidate)
    return found
