#!/usr/bin/env python3
"""
Dynamic DCA strategy — order size scales with distance from ATH.
"""
import os
import logging
from typing import Dict, Tuple

from config import BASE_ORDER_SIZE, MAX_MULTIPLICATOR, ATH_FILE
from strategy_base import BaseStrategy

logger = logging.getLogger(__name__)


class DynamicStrategy(BaseStrategy):

    mode_label = "dynamic"

    def get_ath_price(self) -> float:
        try:
            if os.path.exists(ATH_FILE):
                with open(ATH_FILE, 'r') as f:
                    ath = float(f.read().strip())
                    logger.info(f"Current ATH: {ath}")
                    return ath
            logger.info("ATH file doesn't exist, starting with 0")
            return 0.0
        except Exception as e:
            logger.error(f"Error reading ATH file: {e}")
            return 0.0

    def update_ath_price(self, price: float) -> None:
        with open(ATH_FILE, 'w') as f:
            f.write(str(price))
        logger.info(f"Updated ATH to: {price}")

    def calculate_multiplicator(self, current_price: float, ath_price: float) -> float:
        if ath_price == 0:
            logger.info("No ATH available, using base multiplicator of 1.0")
            return 1.0
        percent_diff = (ath_price - current_price) / ath_price
        logger.info(f"Percentage diff from ATH: {percent_diff:.4f} ({percent_diff*100:.2f}%)")
        multiplicator = 1 + (MAX_MULTIPLICATOR - 1) * ((percent_diff / 0.75) ** 2)
        multiplicator = max(1.0, min(MAX_MULTIPLICATOR, multiplicator))
        logger.info(f"Calculated multiplicator: {multiplicator:.4f}")
        return multiplicator

    def calculate_order_size(self, current_price: float) -> Tuple[float, float, float]:
        ath_price = self.get_ath_price()
        if current_price > ath_price:
            self.update_ath_price(current_price)
            ath_price = current_price
        multiplicator = self.calculate_multiplicator(current_price, ath_price)
        order_size = BASE_ORDER_SIZE * multiplicator
        logger.info(f"Order size: {order_size:.2f} EUR (base {BASE_ORDER_SIZE} x {multiplicator:.4f})")
        return order_size, ath_price, multiplicator

    def build_notification(self, order_data: Dict, current_price: float,
                           ath_price: float, multiplicator: float) -> str:
        percent_diff = (ath_price - current_price) / ath_price if ath_price > 0 else 0
        return f"""🤖 <b>DCA Strategy Executed (Dynamic)</b>

💰 <b>Order Details:</b>
• Order Size: {order_data['order_size']:.2f} EUR
• BTC Volume: {order_data['btc_volume']:.8f} BTC
• Order Price: {order_data['order_price']:.2f} EUR

📊 <b>Market Data:</b>
• Current Price: {current_price:.2f} EUR
• ATH Price: {ath_price:.2f} EUR
• Diff from ATH: {percent_diff*100:.2f}%
• Multiplicator: {multiplicator:.4f}

🆔 Order ID: {order_data['order_id']}"""
