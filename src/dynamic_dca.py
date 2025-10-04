#!/usr/bin/env python3
"""
Dynamic DCA Strategy for Bitcoin using Kraken API
"""
import os
import csv
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

from config import *
from kraken import KrakenClient
from telegram import TelegramNotifier

# Setup logging
from config import LOGS_DIR
log_file = os.path.join(LOGS_DIR, "dca_strategy.log")

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DynamicDCAStrategy:
    def __init__(self):
        self.kraken_client = KrakenClient(KRAKEN_API_KEY, KRAKEN_PRIVATE_KEY)
        self.telegram_notifier = None
        
        # Initialize Telegram notifier if enabled
        if NOTIFICATION_ENABLED and NOTIFICATION_METHOD == "telegram":
            self.telegram_notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        
    def get_current_btc_price(self) -> float:
        """Get current BTC/EUR price from Kraken"""
        try:
            price = self.kraken_client.get_ticker_price(TRADING_PAIR)
            logger.info(f"Current BTC/EUR price: {price}")
            return price
            
        except Exception as e:
            logger.error(f"Error fetching BTC price: {e}")
            raise
    
    def get_ath_price(self) -> float:
        """Get ATH price from file, return 0 if file doesn't exist"""
        try:
            if os.path.exists(ATH_FILE):
                with open(ATH_FILE, 'r') as f:
                    ath = float(f.read().strip())
                    logger.info(f"Current ATH: {ath}")
                    return ath
            else:
                logger.info("ATH file doesn't exist, starting with 0")
                return 0.0
        except Exception as e:
            logger.error(f"Error reading ATH file: {e}")
            return 0.0
    
    def update_ath_price(self, price: float) -> None:
        """Update ATH price in file"""
        try:
            with open(ATH_FILE, 'w') as f:
                f.write(str(price))
            logger.info(f"Updated ATH to: {price}")
        except Exception as e:
            logger.error(f"Error updating ATH file: {e}")
            raise
    
    def calculate_multiplicator(self, current_price: float, ath_price: float) -> float:
        """Calculate dynamic multiplicator based on %diff from ATH"""
        if ath_price == 0:
            logger.info("No ATH available, using base multiplicator of 1.0")
            return 1.0
        
        # Calculate percentage difference from ATH
        percent_diff = (ath_price - current_price) / ath_price
        logger.info(f"Percentage diff from ATH: {percent_diff:.4f} ({percent_diff*100:.2f}%)")
        
        # Calculate multiplicator: 1 + ((MAX_MULT - 1) / 0.75) * %DIFF
        # This means at 75% drop from ATH, we get maximum multiplicator
        multiplicator = 1 + ((MAX_MULTIPLICATOR - 1) / 0.75) * percent_diff
        
        # Ensure multiplicator is between 1 and MAX_MULTIPLICATOR
        multiplicator = max(1.0, min(MAX_MULTIPLICATOR, multiplicator))
        
        logger.info(f"Calculated multiplicator: {multiplicator:.4f}")
        return multiplicator
    
    def calculate_order_size(self, multiplicator: float) -> float:
        """Calculate order size based on multiplicator"""
        order_size = BASE_ORDER_SIZE * multiplicator
        logger.info(f"Order size: {order_size:.2f} EUR")
        return order_size
    
    def get_cumulative_data(self) -> Tuple[float, float]:
        """Get cumulative investment and BTC amount from file"""
        try:
            if os.path.exists(CUMULATIVE_FILE):
                with open(CUMULATIVE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('investment', 0.0), data.get('btc_amount', 0.0)
            else:
                return 0.0, 0.0
        except Exception as e:
            logger.error(f"Error reading cumulative data: {e}")
            return 0.0, 0.0
    
    def update_cumulative_data(self, investment_add: float, btc_add: float) -> None:
        """Update cumulative investment and BTC amount"""
        try:
            cumulative_investment, cumulative_btc = self.get_cumulative_data()
            cumulative_investment += investment_add
            cumulative_btc += btc_add
            
            data = {
                'investment': cumulative_investment,
                'btc_amount': cumulative_btc
            }
            
            with open(CUMULATIVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.info(f"Updated cumulative data - Investment: {cumulative_investment:.2f} EUR, BTC: {cumulative_btc:.8f}")
            
        except Exception as e:
            logger.error(f"Error updating cumulative data: {e}")
            raise
    
    def place_order(self, order_size: float, current_price: float) -> Optional[Dict]:
        """Place buy order on Kraken slightly below current price"""
        try:
            # Calculate order price (0.05% below current price for maker fee)
            order_price = current_price * (1 - MAKER_FEE_OFFSET)
            
            # Calculate BTC volume to buy
            btc_volume = order_size / order_price
            
            logger.info(f"Placing order: {btc_volume:.8f} BTC at {order_price:.1f} EUR")
            
            # Place actual order via Kraken client
            result = self.kraken_client.place_limit_order(
                trading_pair=TRADING_PAIR,
                order_type='buy',
                volume=btc_volume,
                price=order_price,
                validate=False  # Set to True for testing without actual order
            )
            
            return {
                'order_id': result['order_id'],
                'btc_volume': btc_volume,
                'order_price': order_price,
                'order_size': order_size
            }
            
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    def log_to_csv(self, order_data: Dict, current_price: float, ath_price: float, 
                   multiplicator: float, cumulative_investment: float, cumulative_btc: float) -> None:
        """Log order execution to CSV file"""
        try:
            # Check if CSV file exists to determine if we need headers
            file_exists = os.path.exists(LOG_FILE)
            
            with open(LOG_FILE, 'a', newline='') as csvfile:
                fieldnames = [
                    'timestamp', 'current_price', 'ath_price', 'percent_diff', 'multiplicator',
                    'order_size_eur', 'order_price', 'btc_volume', 'order_id',
                    'cumulative_investment', 'cumulative_btc', 'avg_price'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Calculate percentage difference
                percent_diff = (ath_price - current_price) / ath_price if ath_price > 0 else 0
                avg_price = cumulative_investment / cumulative_btc if cumulative_btc > 0 else 0
                
                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
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
                    'avg_price': f"{avg_price:.2f}"
                })
                
            logger.info("Order logged to CSV successfully")
            
        except Exception as e:
            logger.error(f"Error logging to CSV: {e}")
            raise
    
    def send_notification(self, message: str) -> None:
        """Send notification about execution result"""
        if not NOTIFICATION_ENABLED:
            return
            
        try:
            if self.telegram_notifier:
                self.telegram_notifier.send_message(message)
            else:
                logger.info(f"Notification method '{NOTIFICATION_METHOD}' not configured or not implemented")
                
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def execute_strategy(self) -> None:
        """Execute the complete DCA strategy"""
        try:
            logger.info("Starting Dynamic DCA Strategy execution")
            
            # 1. Get current BTC price
            current_price = self.get_current_btc_price()
            
            # 2. Get ATH price
            ath_price = self.get_ath_price()
            
            # 3. Update ATH if current price is higher
            if current_price > ath_price:
                self.update_ath_price(current_price)
                ath_price = current_price
            
            # 4. Calculate multiplicator
            multiplicator = self.calculate_multiplicator(current_price, ath_price)
            
            # 5. Calculate order size
            order_size = self.calculate_order_size(multiplicator)
            
            # 6. Place order
            order_data = self.place_order(order_size, current_price)
            
            # 7. Update cumulative data
            self.update_cumulative_data(order_data['order_size'], order_data['btc_volume'])
            
            # 8. Get updated cumulative data for logging
            cumulative_investment, cumulative_btc = self.get_cumulative_data()
            
            # 9. Log to CSV
            self.log_to_csv(order_data, current_price, ath_price, multiplicator, 
                           cumulative_investment, cumulative_btc)
            
            # 10. Send notification
            percent_diff = (ath_price - current_price) / ath_price if ath_price > 0 else 0
            avg_price = cumulative_investment / cumulative_btc if cumulative_btc > 0 else 0
            
            notification_message = f"""
🤖 <b>DCA Strategy Executed</b>

💰 <b>Order Details:</b>
• Order Size: {order_data['order_size']:.2f} EUR
• BTC Volume: {order_data['btc_volume']:.8f} BTC
• Order Price: {order_data['order_price']:.2f} EUR

📊 <b>Market Data:</b>
• Current Price: {current_price:.2f} EUR
• ATH Price: {ath_price:.2f} EUR
• Diff from ATH: {percent_diff*100:.2f}%
• Multiplicator: {multiplicator:.4f}

🆔 Order ID: {order_data['order_id']}
"""
            
            self.send_notification(notification_message)
            
            logger.info("Dynamic DCA Strategy execution completed successfully")
            
        except Exception as e:
            error_message = f"❌ DCA Strategy execution failed: {str(e)}"
            logger.error(error_message)
            self.send_notification(error_message)
            raise


def main():
    """Main execution function"""
    try:
        strategy = DynamicDCAStrategy()
        strategy.execute_strategy()
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
        exit(1)


if __name__ == "__main__":
    main()
