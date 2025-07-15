"""Test stockgrid fetchers."""

import pytest
from openbb_core.app.service.user_service import UserService
from openbb_stockgrid.models.short_volume import StockgridShortVolumeFetcher

test_credentials = UserService().default_user_settings.credentials.model_dump(
    mode="json"
)


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration."""
    return {
        "filter_headers": [("User-Agent", None)],
        "filter_query_parameters": [
            ("token", "MOCK_TOKEN"),
        ],
    }


@pytest.mark.record_http
def test_stockgrid_short_volume_fetcher(credentials=test_credentials):
    """Test short volume fetcher."""
    params = {"symbol": "AAPL"}

    fetcher = StockgridShortVolumeFetcher()
    result = fetcher.test(params, credentials)
    assert result is None
