"""ECB Balance of Payments Model."""

# pylint: disable=unused-argument,too-many-ancestors

from typing import Any, Dict, List, Optional

from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.balance_of_payments import (
    BalanceOfPaymentsQueryParams,
    ECBCountry,
    ECBDirectInvestment,
    ECBInvestmentIncome,
    ECBMain,
    ECBOtherInvestment,
    ECBPortfolioInvestment,
    ECBServices,
    ECBSummary,
)
from openbb_ecb.utils.bps_series import (
    BPS_COUNTRIES,
    BPS_FREQUENCIES,
    BPS_REPORT_TYPES,
    generate_bps_series_ids,
)
from pydantic import Field


class ECBBalanceOfPaymentsQueryParams(BalanceOfPaymentsQueryParams):
    """ECB Balance of Payments Query."""

    report_type: BPS_REPORT_TYPES = Field(
        default="main",
        description="The report type, the level of detail in the data.",
    )
    frequency: BPS_FREQUENCIES = Field(
        default="monthly",
        description="The frequency of the data.  Monthly is valid only for ['main', 'summary'].",
    )
    country: BPS_COUNTRIES = Field(
        default=None,
        description="The country/region of the data.  This parameter will override the 'report_type' parameter.",
    )


class ECBBalanceOfPaymentsData(
    ECBMain,
    ECBSummary,
    ECBServices,
    ECBInvestmentIncome,
    ECBDirectInvestment,
    ECBPortfolioInvestment,
    ECBOtherInvestment,
    ECBCountry,
):
    """ECB Balance of Payments Data."""


class ECBBalanceOfPaymentsFetcher(
    Fetcher[ECBBalanceOfPaymentsQueryParams, List[ECBBalanceOfPaymentsData]]
):
    """Transform the query, extract and transform the data from the ECB endpoints."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> ECBBalanceOfPaymentsQueryParams:
        """Transform query."""
        return ECBBalanceOfPaymentsQueryParams(**params)

    @staticmethod
    async def aextract_data(
        query: ECBBalanceOfPaymentsQueryParams,
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict]:
        """Extract data."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_ecb.utils.ecb_helpers import get_series_data  # noqa
        from pandas import DataFrame  # noqa

        results: List[Dict] = []

        _series_ids = generate_bps_series_ids(
            query.frequency, query.report_type, country=query.country
        )
        names = list(_series_ids)
        series_ids = list(_series_ids.values())
        data: Dict = {}

        async def get_one(series_id, name):
            result = {}
            temp = await get_series_data(series_id)
            result.update({name: {d["PERIOD"]: d["OBS_VALUE_AS_IS"] for d in temp}})
            data.update(result)

        await asyncio.gather(
            *[get_one(series_id, name) for series_id, name in zip(series_ids, names)]
        )

        try:
            results = (
                DataFrame(data)
                .sort_index()
                .reset_index()
                .rename(columns={"index": "period"})
                .to_dict("records")
            )
            return results
        except Exception as error:
            raise OpenBBError() from error

    @staticmethod
    def transform_data(
        query: ECBBalanceOfPaymentsQueryParams, data: List[Dict], **kwargs: Any
    ) -> List[ECBBalanceOfPaymentsData]:
        """Transform and validate data through the model."""
        return [ECBBalanceOfPaymentsData.model_validate(d) for d in data]
