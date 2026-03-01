import json
import os
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Multiplicator formula tests (pure math, no mocking needed)
# ---------------------------------------------------------------------------

class TestCalculateMultiplicator:
    """Test the quadratic multiplicator formula in isolation."""

    @pytest.fixture
    def strategy(self, mock_krakenex, data_dir):
        with patch("strategy_base.NOTIFICATION_ENABLED", False):
            from strategy_dynamic import DynamicStrategy
            return DynamicStrategy()

    def test_at_ath_returns_one(self, strategy):
        assert strategy.calculate_multiplicator(100_000, 100_000) == 1.0

    def test_no_ath_returns_one(self, strategy):
        assert strategy.calculate_multiplicator(80_000, 0) == 1.0

    def test_75_percent_drop_returns_max(self, strategy):
        with patch("strategy_dynamic.MAX_MULTIPLICATOR", 5.0):
            mult = strategy.calculate_multiplicator(25_000, 100_000)
            assert mult == pytest.approx(5.0)

    def test_small_drop_scales_quadratically(self, strategy):
        # 15% drop from ATH → percent_diff = 0.15
        # multiplicator = 1 + (5-1) * (0.15/0.75)^2 = 1 + 4 * 0.04 = 1.16
        with patch("strategy_dynamic.MAX_MULTIPLICATOR", 5.0):
            mult = strategy.calculate_multiplicator(85_000, 100_000)
            assert mult == pytest.approx(1.16, rel=1e-2)

    def test_beyond_75_percent_capped_at_max(self, strategy):
        # 90% drop would exceed max without capping
        with patch("strategy_dynamic.MAX_MULTIPLICATOR", 5.0):
            mult = strategy.calculate_multiplicator(10_000, 100_000)
            assert mult == 5.0

    def test_multiplicator_never_below_one(self, strategy):
        # Price above ATH edge case (shouldn't happen in practice,
        # but calculate_multiplicator should still be safe)
        mult = strategy.calculate_multiplicator(110_000, 100_000)
        assert mult >= 1.0


# ---------------------------------------------------------------------------
# ATH tracking
# ---------------------------------------------------------------------------

class TestATHTracking:

    @pytest.fixture
    def strategy(self, mock_krakenex, data_dir):
        with patch("strategy_base.NOTIFICATION_ENABLED", False):
            from strategy_dynamic import DynamicStrategy
            return DynamicStrategy()

    def test_reads_ath_from_file(self, strategy, data_dir):
        ath_file = data_dir / "ath_price.txt"
        ath_file.write_text("95000.0")
        assert strategy.get_ath_price() == 95000.0

    def test_returns_zero_when_no_file(self, strategy):
        assert strategy.get_ath_price() == 0.0

    def test_updates_ath_file(self, strategy, data_dir):
        ath_file = data_dir / "ath_price.txt"
        strategy.update_ath_price(100_000.0)
        assert float(ath_file.read_text()) == 100_000.0

    def test_calculate_order_size_updates_ath_when_new_high(self, strategy, data_dir):
        ath_file = data_dir / "ath_price.txt"
        ath_file.write_text("90000.0")
        with patch("strategy_dynamic.BASE_ORDER_SIZE", 10.0):
            order_size, ath, mult = strategy.calculate_order_size(95_000.0)
        # ATH should be updated to new high
        assert float(ath_file.read_text()) == 95_000.0
        assert ath == 95_000.0
        # At ATH, multiplicator should be 1.0
        assert mult == 1.0
        assert order_size == 10.0


# ---------------------------------------------------------------------------
# Full execute flow
# ---------------------------------------------------------------------------

class TestDynamicExecute:

    @pytest.fixture
    def strategy(self, mock_krakenex, data_dir):
        with patch("strategy_base.NOTIFICATION_ENABLED", False):
            from strategy_dynamic import DynamicStrategy
            s = DynamicStrategy()
            return s

    def _setup_kraken_mocks(self, mock_krakenex, price=85_000.0):
        mock_krakenex.query_public.return_value = {
            "error": [],
            "result": {"XXBTZEUR": {"c": [str(price), "0.001"]}},
        }
        mock_krakenex.query_private.return_value = {
            "error": [],
            "result": {
                "txid": ["ORDER-123"],
                "descr": {"order": "buy ..."},
            },
        }

    def test_full_execute_flow(self, strategy, mock_krakenex, data_dir):
        ath_file = data_dir / "ath_price.txt"
        ath_file.write_text("100000.0")
        self._setup_kraken_mocks(mock_krakenex, price=85_000.0)

        with patch("strategy_dynamic.BASE_ORDER_SIZE", 10.0), \
             patch("strategy_dynamic.MAX_MULTIPLICATOR", 5.0):
            strategy.execute()

        # Order was placed
        mock_krakenex.query_private.assert_called_once()

        # Cumulative data was written
        cumul_file = data_dir / "cumulative_data.txt"
        assert cumul_file.exists()
        cumul = json.loads(cumul_file.read_text())
        assert cumul["investment"] > 0
        assert cumul["btc_amount"] > 0

        # CSV log was written
        csv_file = data_dir / "dca_log.csv"
        assert csv_file.exists()
        lines = csv_file.read_text().strip().split("\n")
        assert len(lines) == 2  # header + 1 row

    def test_execute_sends_notification_on_success(self, mock_krakenex, data_dir):
        with patch("strategy_base.NOTIFICATION_ENABLED", True), \
             patch("strategy_base.NOTIFICATION_METHOD", "telegram"), \
             patch("strategy_base.TelegramNotifier") as MockTelegram:
            mock_tg = MockTelegram.return_value
            from strategy_dynamic import DynamicStrategy
            s = DynamicStrategy()

            (data_dir / "ath_price.txt").write_text("100000.0")
            self._setup_kraken_mocks(mock_krakenex, price=85_000.0)

            with patch("strategy_dynamic.BASE_ORDER_SIZE", 10.0), \
                 patch("strategy_dynamic.MAX_MULTIPLICATOR", 5.0):
                s.execute()

            mock_tg.send_message.assert_called_once()
            msg = mock_tg.send_message.call_args[0][0]
            assert "Dynamic" in msg

    def test_execute_sends_notification_on_failure(self, mock_krakenex, data_dir):
        with patch("strategy_base.NOTIFICATION_ENABLED", True), \
             patch("strategy_base.NOTIFICATION_METHOD", "telegram"), \
             patch("strategy_base.TelegramNotifier") as MockTelegram:
            mock_tg = MockTelegram.return_value
            from strategy_dynamic import DynamicStrategy
            s = DynamicStrategy()

            mock_krakenex.query_public.side_effect = Exception("API down")

            with pytest.raises(Exception, match="API down"):
                s.execute()

            mock_tg.send_message.assert_called_once()
            msg = mock_tg.send_message.call_args[0][0]
            assert "failed" in msg
