#!/usr/bin/env python3
"""
Base DCA strategy with shared infrastructure (ordering, logging, notifications).
"""
import os
import csv
import json
import logging
from datetime import datetime
from typing import Dict, Tuple

from config import (
    KRAKEN_API_KEY, KRAKEN_PRIVATE_KEY, TRADING_PAIR, MAKER_FEE_OFFSET,
    NOTIFICATION_ENABLED, NOTIFICATION_METHOD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    LOG_FILE, CUMULATIVE_FILE,
)
from kraken import KrakenClient
from telegram import TelegramNotifier

logger = logging.getLogger(__name__)


class BaseStrategy:
    """Shared infrastructure for all DCA strategies."""

    mode_label = "base"

    def __init__(self):
        self.kraken_client = KrakenClient(KRAKEN_API_KEY, KRAKEN_PRIVATE_KEY)
        self.telegram_notifier = None
        if NOTIFICATION_ENABLED and NOTIFICATION_METHOD == "telegram":
            self.telegram_notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

    # -- price --

    def get_current_btc_price(self) -> float:
        price = self.kraken_client.get_ticker_price(TRADING_PAIR)
        logger.info(f"Current BTC/EUR price: {price}")
        return price

    # -- cumulative data --

    def get_cumulative_data(self) -> Tuple[float, float]:
        try:
            if os.path.exists(CUMULATIVE_FILE):
                with open(CUMULATIVE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('investment', 0.0), data.get('btc_amount', 0.0)
            return 0.0, 0.0
        except Exception as e:
            logger.error(f"Error reading cumulative data: {e}")
            return 0.0, 0.0

    def update_cumulative_data(self, investment_add: float, btc_add: float) -> None:
        cumulative_investment, cumulative_btc = self.get_cumulative_data()
        cumulative_investment += investment_add
        cumulative_btc += btc_add
        with open(CUMULATIVE_FILE, 'w') as f:
            json.dump({'investment': cumulative_investment, 'btc_amount': cumulative_btc}, f, indent=2)
        logger.info(f"Updated cumulative data - Investment: {cumulative_investment:.2f} EUR, BTC: {cumulative_btc:.8f}")

    # -- order placement --

    def place_order(self, order_size: float, current_price: float) -> Dict:
        order_price = current_price * (1 - MAKER_FEE_OFFSET)
        btc_volume = order_size / order_price
        logger.info(f"Placing order: {btc_volume:.8f} BTC at {order_price:.1f} EUR")
        result = self.kraken_client.place_limit_order(
            trading_pair=TRADING_PAIR,
            order_type='buy',
            volume=btc_volume,
            price=order_price,
            validate=False,
        )
        return {
            'order_id': result['order_id'],
            'btc_volume': btc_volume,
            'order_price': order_price,
            'order_size': order_size,
        }

    # -- CSV logging --

    def log_to_csv(self, order_data: Dict, current_price: float, ath_price: float,
                   multiplicator: float, cumulative_investment: float, cumulative_btc: float) -> None:
        file_exists = os.path.exists(LOG_FILE)
        with open(LOG_FILE, 'a', newline='') as csvfile:
            fieldnames = [
                'timestamp', 'mode', 'current_price', 'ath_price', 'percent_diff', 'multiplicator',
                'order_size_eur', 'order_price', 'btc_volume', 'order_id',
                'cumulative_investment', 'cumulative_btc', 'avg_price',
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            percent_diff = (ath_price - current_price) / ath_price if ath_price > 0 else 0
            avg_price = cumulative_investment / cumulative_btc if cumulative_btc > 0 else 0
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'mode': self.mode_label,
                'current_price': current_price,
                'ath_price': ath_price,
                'percent_diff': f"{percent_diff:.4f}",
                'multiplicator': f"{multiplicator:.4f}",
                'order_size_eur': f"{order_data['order_size']:.2f}",
                'order_price': f"{order_data['order_price']:.2f}",
                'btc_volume': f"{order_data['btc_volume']:.8f}",
                'order_id': order_data['order_id'],
                'cumulative_investment': f"{cumulative_investment:.2f}",
                'cumulative_btc': f"{cumulative_btc:.8f}",
                'avg_price': f"{avg_price:.2f}",
            })
        logger.info("Order logged to CSV successfully")

    # -- notifications --

    def send_notification(self, message: str) -> None:
        if not NOTIFICATION_ENABLED:
            return
        if self.telegram_notifier:
            self.telegram_notifier.send_message(message)
        else:
            logger.info(f"Notification method '{NOTIFICATION_METHOD}' not configured")

    # -- strategy interface (subclasses implement these) --

    def calculate_order_size(self, current_price: float) -> Tuple[float, float, float]:
        """Return (order_size, ath_price, multiplicator)."""
        raise NotImplementedError

    def build_notification(self, order_data: Dict, current_price: float,
                           ath_price: float, multiplicator: float) -> str:
        """Return Telegram notification message."""
        raise NotImplementedError

    # -- main execution flow --

    def execute(self) -> None:
        try:
            logger.info(f"Starting DCA Strategy execution (mode: {self.mode_label})")
            current_price = self.get_current_btc_price()
            order_size, ath_price, multiplicator = self.calculate_order_size(current_price)
            order_data = self.place_order(order_size, current_price)
            self.update_cumulative_data(order_data['order_size'], order_data['btc_volume'])
            cumulative_investment, cumulative_btc = self.get_cumulative_data()
            self.log_to_csv(order_data, current_price, ath_price, multiplicator,
                           cumulative_investment, cumulative_btc)
            self.send_notification(self.build_notification(
                order_data, current_price, ath_price, multiplicator))
            logger.info("DCA Strategy execution completed successfully")
        except Exception as e:
            error_message = f"DCA Strategy execution failed: {str(e)}"
            logger.error(error_message)
            self.send_notification(error_message)
            raise
