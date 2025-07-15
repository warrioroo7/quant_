"""Revenue By Business Line Standard Model."""

from datetime import date as dateType
from typing import Optional, Union

from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import QUERY_DESCRIPTIONS
from pydantic import Field, field_validator


class RevenueBusinessLineQueryParams(QueryParams):
    """Revenue By Business Line Query."""

    symbol: str = Field(description=QUERY_DESCRIPTIONS.get("symbol", ""))

    @field_validator("symbol", mode="before", check_fields=False)
    @classmethod
    def to_upper(cls, v: str):
        """Convert field to uppercase."""
        return v.upper()


class RevenueBusinessLineData(Data):
    """Revenue By Business Line Data."""

    period_ending: dateType = Field(description="The end date of the reporting period.")
    fiscal_period: Optional[str] = Field(
        default=None, description="The fiscal period of the reporting period."
    )
    fiscal_year: Optional[int] = Field(
        default=None, description="The fiscal year of the reporting period."
    )
    filing_date: Optional[dateType] = Field(
        default=None, description="The filing date of the report."
    )
    business_line: Optional[str] = Field(
        default=None,
        description="The business line represented by the revenue data.",
    )
    revenue: Union[int, float] = Field(
        description="The total revenue attributed to the business line.",
        json_schema_extra={"x-unit_measurement": "currency"},
    )
