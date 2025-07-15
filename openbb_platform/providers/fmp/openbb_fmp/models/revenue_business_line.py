"""FMP Revenue By Business Line Model."""

# pylint: disable=unused-argument

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.revenue_business_line import (
    RevenueBusinessLineData,
    RevenueBusinessLineQueryParams,
)
from openbb_core.provider.utils.descriptions import QUERY_DESCRIPTIONS
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import Field, field_validator


class FMPRevenueBusinessLineQueryParams(RevenueBusinessLineQueryParams):
    """FMP Revenue By Business Line Query.

    Source: https://site.financialmodelingprep.com/developer/docs/sales-revenue-by-segments-api/
    """

    __json_schema_extra__ = {
        "period": {
            "multiple_items_allowed": False,
            "choices": ["quarter", "annual"],
        }
    }

    period: Literal["quarter", "annual"] = Field(
        default="annual", description=QUERY_DESCRIPTIONS.get("period", "")
    )


class FMPRevenueBusinessLineData(RevenueBusinessLineData):
    """FMP Revenue By Business Line Data."""

    @field_validator("period_ending", "filing_date", mode="before", check_fields=False)
    @classmethod
    def date_validate(cls, v):  # pylint: disable=E0213
        """Return the date as a datetime object."""
        return datetime.strptime(v, "%Y-%m-%d") if v else None


class FMPRevenueBusinessLineFetcher(
    Fetcher[
        FMPRevenueBusinessLineQueryParams,
        List[FMPRevenueBusinessLineData],
    ]
):
    """FMP Revenue By Business Line Fetcher."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> FMPRevenueBusinessLineQueryParams:
        """Transform the query params."""
        return FMPRevenueBusinessLineQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: FMPRevenueBusinessLineQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict]:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_fmp.models.cash_flow import FMPCashFlowStatementFetcher
        from openbb_fmp.utils.helpers import get_data_many

        api_key = credentials.get("fmp_api_key") if credentials else ""
        url = "https://financialmodelingprep.com/api/v4/revenue-product-segmentation?"
        url = (
            f"{url}symbol={query.symbol if query.symbol else ''}"
            f"&period={query.period if query.period else ''}"
            f"&structure=flat&apikey={api_key}"
        )
        cf_fetcher = FMPCashFlowStatementFetcher()
        cf_query = cf_fetcher.transform_query(
            {"symbol": query.symbol, "period": query.period, "limit": 200}
        )
        cf_data = await cf_fetcher.aextract_data(cf_query, {"fmp_api_key": api_key})
        filing_dates = sorted(
            [
                {
                    "period_ending": d["date"],
                    "fiscal_year": d["calendarYear"],
                    "fiscal_period": d["period"],
                    "filing_date": d["fillingDate"],
                }
                for d in cf_data
            ],
            key=lambda d: d["period_ending"],
        )
        rev_data = await get_data_many(url, **kwargs)
        rev_data_dict = {list(d.keys())[0]: list(d.values())[0] for d in rev_data}
        combined_data = [
            {**d, "business_line": rev_data_dict[d["period_ending"]]}
            for d in filing_dates
            if d["period_ending"] in rev_data_dict
        ]
        return combined_data

    @staticmethod
    def transform_data(
        query: FMPRevenueBusinessLineQueryParams,
        data: List[Dict],
        **kwargs: Any,
    ) -> List[FMPRevenueBusinessLineData]:
        """Return the transformed data."""
        # pylint: disable=import-outside-toplevel
        from pandas import DataFrame

        if not data:
            raise EmptyDataError("The request was returned empty.")

        # We need to flatten the data entirely.
        df = DataFrame(data)
        results: List = []
        for i in df.index:
            segments_list = []
            period_ending = df.period_ending.iloc[i]
            fiscal_year = df.fiscal_year.iloc[i]
            fiscal_period = df.fiscal_period.iloc[i]
            filing_date = df.filing_date.iloc[i]
            segment = df.business_line.iloc[i]
            for k, v in segment.items():
                regions_dict = {}
                regions_dict["period_ending"] = period_ending
                regions_dict["fiscal_year"] = fiscal_year
                regions_dict["fiscal_period"] = fiscal_period
                regions_dict["filing_date"] = filing_date
                regions_dict["business_line"] = k.strip()
                regions_dict["revenue"] = int(v) if v is not None else None
                if regions_dict["revenue"] is not None:
                    segments_list.append(regions_dict)

            if segments_list:
                results.extend(segments_list)

        new_df = DataFrame(results).sort_values(by=["period_ending", "revenue"])

        return [
            FMPRevenueBusinessLineData.model_validate(d)
            for d in new_df.to_dict(orient="records")
        ]
