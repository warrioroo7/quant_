"""Nasdaq Top Retail Model."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from openbb_core.app.model.abstract.error import OpenBBError
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.top_retail import (
    TopRetailData,
    TopRetailQueryParams,
)
from pydantic import field_validator


class NasdaqTopRetailQueryParams(TopRetailQueryParams):
    """Nasdaq Top Retail Query.

    Source: https://data.nasdaq.com/databases/RTAT/data
    """


class NasdaqTopRetailData(TopRetailData):
    """Nasdaq Top Retail Data."""

    @field_validator("date", mode="before", check_fields=False)
    def validate_date(cls, v: Any) -> Any:  # pylint: disable=E0213
        """Validate the date."""
        return datetime.strptime(v, "%Y-%m-%d").date()


class NasdaqTopRetailFetcher(
    Fetcher[NasdaqTopRetailQueryParams, List[NasdaqTopRetailData]]
):
    """Transform the query, extract and transform the data from the Nasdaq endpoints."""

    @staticmethod
    def transform_query(params: Dict[str, Any]) -> NasdaqTopRetailQueryParams:
        """Transform the params to the provider-specific query."""
        return NasdaqTopRetailQueryParams(**params)

    @staticmethod
    def extract_data(
        query: NasdaqTopRetailQueryParams,  # pylint: disable=unused-argument
        credentials: Optional[Dict[str, str]],
        **kwargs: Any,
    ) -> List[Dict]:
        """Get data from Nasdaq."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.helpers import make_request

        api_key = credentials.get("nasdaq_api_key") if credentials else None
        response = make_request(
            f"https://data.nasdaq.com/api/v3/datatables/NDAQ/RTAT10/?api_key={api_key}",
        )
        if response.status_code != 200:
            reason = getattr(response, "reason", "Unknown")
            raise OpenBBError(f"Failed to get data from Nasdaq -> {reason}")
        content = response.json()
        return content["datatable"]["data"][: query.limit]

    @staticmethod
    def transform_data(
        query: TopRetailQueryParams,
        data: List[Dict],
        **kwargs: Any,
    ) -> List[NasdaqTopRetailData]:
        """Transform the data."""
        transformed_data: List[NasdaqTopRetailData] = []
        for row in data:
            transformed_data.append(
                NasdaqTopRetailData.model_validate(
                    {
                        "date": row[0],
                        "symbol": row[1],
                        "activity": row[2],
                        "sentiment": row[3],
                    }
                )
            )

        return transformed_data
