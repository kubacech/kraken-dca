import pytest
from unittest.mock import MagicMock


class TestGetTickerPrice:

    def test_returns_price(self, kraken_client, mock_krakenex):
        mock_krakenex.query_public.return_value = {
            "error": [],
            "result": {"XXBTZEUR": {"c": ["85000.0", "0.001"]}},
        }
        price = kraken_client.get_ticker_price("XXBTZEUR")
        assert price == 85000.0
        mock_krakenex.query_public.assert_called_once_with(
            "Ticker", {"pair": "XXBTZEUR"}
        )

    def test_raises_on_api_error(self, kraken_client, mock_krakenex):
        mock_krakenex.query_public.return_value = {
            "error": ["EGeneral:Invalid arguments"],
            "result": {},
        }
        with pytest.raises(Exception, match="Kraken API error"):
            kraken_client.get_ticker_price("XXBTZEUR")

    def test_raises_on_network_error(self, kraken_client, mock_krakenex):
        mock_krakenex.query_public.side_effect = ConnectionError("timeout")
        with pytest.raises(ConnectionError):
            kraken_client.get_ticker_price("XXBTZEUR")


class TestPlaceLimitOrder:

    def test_places_order_successfully(self, kraken_client, mock_krakenex):
        mock_krakenex.query_private.return_value = {
            "error": [],
            "result": {
                "txid": ["OABC-12345-DEFGH"],
                "descr": {"order": "buy 0.00100000 XBTEUR @ limit 84950.0"},
            },
        }
        result = kraken_client.place_limit_order(
            trading_pair="XXBTZEUR",
            order_type="buy",
            volume=0.001,
            price=84950.0,
        )
        assert result["order_id"] == "OABC-12345-DEFGH"
        assert "order" in result["description"]

    def test_raises_on_order_error(self, kraken_client, mock_krakenex):
        mock_krakenex.query_private.return_value = {
            "error": ["EOrder:Insufficient funds"],
            "result": {},
        }
        with pytest.raises(Exception, match="Order placement error"):
            kraken_client.place_limit_order("XXBTZEUR", "buy", 0.001, 84950.0)

    def test_validate_mode(self, kraken_client, mock_krakenex):
        mock_krakenex.query_private.return_value = {
            "error": [],
            "result": {"txid": [], "descr": {"order": "buy ..."}},
        }
        result = kraken_client.place_limit_order(
            "XXBTZEUR", "buy", 0.001, 84950.0, validate=True
        )
        call_args = mock_krakenex.query_private.call_args
        assert call_args[0][1]["validate"] == "true"
        assert result["order_id"] is None


class TestGetAccountBalance:

    def test_returns_balances(self, kraken_client, mock_krakenex):
        mock_krakenex.query_private.return_value = {
            "error": [],
            "result": {"ZEUR": "1000.0000", "XXBT": "0.50000000"},
        }
        balances = kraken_client.get_account_balance()
        assert balances["ZEUR"] == 1000.0
        assert balances["XXBT"] == 0.5

    def test_raises_on_error(self, kraken_client, mock_krakenex):
        mock_krakenex.query_private.return_value = {
            "error": ["EGeneral:Permission denied"],
            "result": {},
        }
        with pytest.raises(Exception, match="Balance query error"):
            kraken_client.get_account_balance()
