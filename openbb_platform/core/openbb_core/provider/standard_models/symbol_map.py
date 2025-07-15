"""Commitment of Traders Reports Search Standard Model."""

from typing import Optional

from openbb_core.provider.abstract.query_params import QueryParams
from pydantic import Field


class SymbolMapQueryParams(QueryParams):
    """Commitment of Traders Reports Search Query."""

    query: str = Field(description="Search query.")
    use_cache: Optional[bool] = Field(
        default=True,
        description="Whether or not to use cache. If True, cache will store for seven days.",
    )
