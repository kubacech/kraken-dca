#!/usr/bin/env python3
"""
Fixed-fiat DCA strategy — always buys for a constant EUR amount.
"""
import logging
from typing import Dict, Tuple

from config import FIXED_FIAT_AMOUNT
from strategy_base import BaseStrategy

logger = logging.getLogger(__name__)


class FixedFiatStrategy(BaseStrategy):

    mode_label = "fixed-fiat"

    def calculate_order_size(self, current_price: float) -> Tuple[float, float, float]:
        logger.info(f"Fixed-fiat mode: order size = {FIXED_FIAT_AMOUNT:.2f} EUR")
        return FIXED_FIAT_AMOUNT, 0.0, 1.0

    def build_notification(self, order_data: Dict, current_price: float,
                           ath_price: float, multiplicator: float) -> str:
        return f"""🤖 <b>DCA Strategy Executed (Fixed-Fiat)</b>

💰 <b>Order Details:</b>
• Order Size: {order_data['order_size']:.2f} EUR
• BTC Volume: {order_data['btc_volume']:.8f} BTC
• Order Price: {order_data['order_price']:.2f} EUR

📊 <b>Market Data:</b>
• Current Price: {current_price:.2f} EUR

🆔 Order ID: {order_data['order_id']}"""
