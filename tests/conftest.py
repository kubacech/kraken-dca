import os
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Kraken fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_krakenex():
    """Patch krakenex.API so KrakenClient never hits the real exchange."""
    with patch("krakenex.API") as MockAPI:
        api_instance = MockAPI.return_value
        yield api_instance


@pytest.fixture
def kraken_client(mock_krakenex):
    from kraken import KrakenClient
    return KrakenClient("fake-key", "fake-secret")


# ---------------------------------------------------------------------------
# Telegram fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_requests_post():
    with patch("telegram.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        yield mock_post


@pytest.fixture
def telegram_notifier(mock_requests_post):
    from telegram import TelegramNotifier
    return TelegramNotifier("fake-token", "fake-chat-id")


# ---------------------------------------------------------------------------
# Temp data directory — redirects all file-based state to tmp_path
# ---------------------------------------------------------------------------

@pytest.fixture
def data_dir(tmp_path):
    """Patch config file paths to use a temporary directory."""
    patches = {
        "strategy_base.CUMULATIVE_FILE": str(tmp_path / "cumulative_data.txt"),
        "strategy_base.LOG_FILE": str(tmp_path / "dca_log.csv"),
        "strategy_dynamic.ATH_FILE": str(tmp_path / "ath_price.txt"),
    }
    with patch.dict("os.environ", {}, clear=False):
        patchers = [patch(target, value) for target, value in patches.items()]
        for p in patchers:
            p.start()
        yield tmp_path
        for p in patchers:
            p.stop()
