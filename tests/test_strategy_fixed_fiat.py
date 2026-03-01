import json
import pytest
from unittest.mock import patch


class TestCalculateOrderSize:

    @pytest.fixture
    def strategy(self, mock_krakenex, data_dir):
        with patch("strategy_base.NOTIFICATION_ENABLED", False):
            from strategy_fixed_fiat import FixedFiatStrategy
            return FixedFiatStrategy()

    def test_returns_fixed_amount(self, strategy):
        with patch("strategy_fixed_fiat.FIXED_FIAT_AMOUNT", 8.0):
            order_size, ath, mult = strategy.calculate_order_size(85_000.0)
        assert order_size == 8.0
        assert ath == 0.0
        assert mult == 1.0

    def test_ignores_price(self, strategy):
        """Order size should be the same regardless of current price."""
        with patch("strategy_fixed_fiat.FIXED_FIAT_AMOUNT", 20.0):
            size_low, _, _ = strategy.calculate_order_size(50_000.0)
            size_high, _, _ = strategy.calculate_order_size(100_000.0)
        assert size_low == size_high == 20.0


class TestFixedFiatExecute:

    @pytest.fixture
    def strategy(self, mock_krakenex, data_dir):
        with patch("strategy_base.NOTIFICATION_ENABLED", False):
            from strategy_fixed_fiat import FixedFiatStrategy
            return FixedFiatStrategy()

    def _setup_kraken_mocks(self, mock_krakenex, price=85_000.0):
        mock_krakenex.query_public.return_value = {
            "error": [],
            "result": {"XXBTZEUR": {"c": [str(price), "0.001"]}},
        }
        mock_krakenex.query_private.return_value = {
            "error": [],
            "result": {
                "txid": ["ORDER-456"],
                "descr": {"order": "buy ..."},
            },
        }

    def test_full_execute_flow(self, strategy, mock_krakenex, data_dir):
        self._setup_kraken_mocks(mock_krakenex)

        with patch("strategy_fixed_fiat.FIXED_FIAT_AMOUNT", 8.0):
            strategy.execute()

        # Order was placed
        mock_krakenex.query_private.assert_called_once()

        # Cumulative data written
        cumul = json.loads((data_dir / "cumulative_data.txt").read_text())
        assert cumul["investment"] == pytest.approx(8.0, rel=1e-2)
        assert cumul["btc_amount"] > 0

        # CSV log written with correct mode
        csv_text = (data_dir / "dca_log.csv").read_text()
        assert "fixed-fiat" in csv_text

    def test_multiple_executions_accumulate(self, strategy, mock_krakenex, data_dir):
        self._setup_kraken_mocks(mock_krakenex)

        with patch("strategy_fixed_fiat.FIXED_FIAT_AMOUNT", 8.0):
            strategy.execute()
            strategy.execute()

        cumul = json.loads((data_dir / "cumulative_data.txt").read_text())
        assert cumul["investment"] == pytest.approx(16.0, rel=1e-2)

        lines = (data_dir / "dca_log.csv").read_text().strip().split("\n")
        assert len(lines) == 3  # header + 2 rows

    def test_execute_sends_notification(self, mock_krakenex, data_dir):
        with patch("strategy_base.NOTIFICATION_ENABLED", True), \
             patch("strategy_base.NOTIFICATION_METHOD", "telegram"), \
             patch("strategy_base.TelegramNotifier") as MockTelegram:
            mock_tg = MockTelegram.return_value
            from strategy_fixed_fiat import FixedFiatStrategy
            s = FixedFiatStrategy()

            self._setup_kraken_mocks(mock_krakenex)
            with patch("strategy_fixed_fiat.FIXED_FIAT_AMOUNT", 8.0):
                s.execute()

            mock_tg.send_message.assert_called_once()
            msg = mock_tg.send_message.call_args[0][0]
            assert "Fixed-Fiat" in msg
