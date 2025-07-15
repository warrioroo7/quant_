"""TMX Equity Profile fetcher."""

# pylint: disable=unused-argument

from typing import Any, Dict, List, Optional

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_info import (
    EquityInfoData,
    EquityInfoQueryParams,
)
from pydantic import Field, model_validator


class TmxEquityProfileQueryParams(EquityInfoQueryParams):
    """TMX Equity Profile query params."""

    __json_schema_extra__ = {"symbol": {"multiple_items_allowed": True}}


class TmxEquityProfileData(EquityInfoData):
    """TMX Equity Profile Data."""

    __alias_dict__ = {
        "short_description": "shortDescription",
        "long_description": "longDescription",
        "company_url": "website",
        "business_phone_no": "phoneNumber",
        "business_address": "fullAddress",
        "stock_exchange": "exchangeCode",
        "industry_category": "industry",
        "industry_group": "qmdescription",
        "issue_type": "issueType",
        "share_outstanding": "shareOutStanding",
        "shares_escrow": "sharesESCROW",
        "total_shares_outstanding": "totalSharesOutStanding",
    }

    email: Optional[str] = Field(description="The email of the company.", default=None)
    issue_type: Optional[str] = Field(
        description="The issuance type of the asset.",
        default=None,
    )
    shares_outstanding: Optional[int] = Field(
        description="The number of listed shares outstanding.",
        default=None,
    )
    shares_escrow: Optional[int] = Field(
        description="The number of shares held in escrow.",
        default=None,
    )
    shares_total: Optional[int] = Field(
        description="The total number of shares outstanding from all classes.",
        default=None,
    )
    dividend_frequency: Optional[str] = Field(
        description="The dividend frequency.", default=None
    )

    @model_validator(mode="before")
    @classmethod
    def validate_empty_strings(cls, values) -> Dict:
        """Validate the query parameters."""
        return {k: None if v == "" else v for k, v in values.items()}


class TmxEquityProfileFetcher(
    Fetcher[
        TmxEquityProfileQueryParams,
        List[TmxEquityProfileData],
    ]
):
    """TMX Equity Profile Fetcher."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> TmxEquityProfileQueryParams:
        """Transform the query."""
        return TmxEquityProfileQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: TmxEquityProfileQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict]:
        """Return the raw data from the TMX endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        import json  # noqa
        from openbb_tmx.utils import gql  # noqa
        from openbb_tmx.utils.helpers import get_data_from_gql, get_random_agent  # noqa

        symbols = query.symbol.split(",")

        # The list where the results will be stored and appended to.
        results: List[Dict] = []
        user_agent = get_random_agent()

        url = "https://app-money.tmx.com/graphql"

        async def create_task(symbol: str, results) -> None:
            """Make a POST request to the TMX GraphQL endpoint for a single symbol."""
            symbol = (
                symbol.upper().replace("-", ".").replace(".TO", "").replace(".TSX", "")
            )

            payload = gql.stock_info_payload.copy()
            payload["variables"]["symbol"] = symbol

            data = {}
            r = await get_data_from_gql(
                method="POST",
                url=url,
                data=json.dumps(payload),
                headers={
                    "authority": "app-money.tmx.com",
                    "referer": f"https://money.tmx.com/en/quote/{symbol}",
                    "locale": "en",
                    "Content-Type": "application/json",
                    "User-Agent": user_agent,
                    "Accept": "*/*",
                },
                timeout=3,
            )
            if r["data"].get("getQuoteBySymbol"):
                data = r["data"]["getQuoteBySymbol"]
                results.append(data)

        tasks = [create_task(symbol, results) for symbol in symbols]
        await asyncio.gather(*tasks)
        return results

    @staticmethod
    def transform_data(
        query: TmxEquityProfileQueryParams,
        data: List[Dict],
        **kwargs: Any,
    ) -> List[TmxEquityProfileData]:
        """Return the transformed data."""
        # Get only the items associated with `equity.profile()`.
        items_list = [
            "shortDescription",
            "longDescription",
            "website",
            "phoneNumber",
            "fullAddress",
            "sector",
            "qmdescription",
            "industry",
            "exchangeCode",
            "shareOutStanding",
            "sharesESCROW",
            "totalSharesOutStanding",
            "email",
            "issueType",
            "name",
            "symbol",
            "dividendFrequency",
            "employees",
        ]
        data = [{k: v for k, v in d.items() if k in items_list} for d in data]
        # Sort the data by the order of the symbols in the query.
        symbols = query.symbol.split(",")
        symbol_to_index = {symbol: index for index, symbol in enumerate(symbols)}
        data = sorted(data, key=lambda d: symbol_to_index[d["symbol"]])

        return [TmxEquityProfileData.model_validate(d) for d in data]
