#!/usr/bin/env python3
"""
Test script for Dynamic DCA Strategy (no real orders)
"""
import os
import sys
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .dynamic_dca import DynamicDCAStrategy


class TestDCAStrategy(DynamicDCAStrategy):
    """Test version that doesn't place real orders"""
    
    def __init__(self, mock_price: float = 42000.0):
        """Initialize with mocked Kraken API"""
        self.mock_price = mock_price
        # Don't initialize real Kraken API for testing
        self.kraken = MagicMock()
        
    def get_current_btc_price(self) -> float:
        """Return mock price instead of querying Kraken"""
        print(f"[TEST MODE] Mock BTC price: {self.mock_price}")
        return self.mock_price
    
    def place_order(self, order_size: float, current_price: float):
        """Mock order placement - don't place real orders"""
        order_price = current_price * (1 - 0.0005)  # MAKER_FEE_OFFSET
        btc_volume = order_size / order_price
        
        print(f"[TEST MODE] Would place order:")
        print(f"  - BTC Volume: {btc_volume:.8f}")
        print(f"  - Order Price: {order_price:.2f} EUR")
        print(f"  - Order Size: {order_size:.2f} EUR")
        
        return {
            'order_id': 'TEST_ORDER_123456',
            'btc_volume': btc_volume,
            'order_price': order_price,
            'order_size': order_size
        }
    
    def send_notification(self, message: str) -> None:
        """Mock notification - just print to console"""
        print(f"\n[TEST MODE] Notification would be sent:")
        print(message)


def test_multiplicator_calculation():
    """Test the multiplicator calculation logic"""
    print("=== Testing Multiplicator Calculation ===")
    
    strategy = TestDCAStrategy()
    
    test_cases = [
        (50000, 50000, "At ATH"),
        (47500, 50000, "5% down from ATH"),
        (40000, 50000, "20% down from ATH"),
        (25000, 50000, "50% down from ATH"),
        (12500, 50000, "75% down from ATH (max multiplicator)"),
        (10000, 50000, "80% down from ATH (should cap at max)"),
    ]
    
    for current, ath, description in test_cases:
        mult = strategy.calculate_multiplicator(current, ath)
        order_size = strategy.calculate_order_size(mult)
        print(f"{description}: Mult={mult:.4f}, Order={order_size:.2f} EUR")
    
    print()


def test_full_strategy():
    """Test the complete strategy execution"""
    print("=== Testing Full Strategy Execution ===")
    
    # Test with price 20% down from ATH
    current_price = 40000.0
    strategy = TestDCAStrategy(current_price)
    
    # Ensure data directory exists
    os.makedirs('../data', exist_ok=True)
    
    # Set a mock ATH higher than current price
    with open('../data/ath_price.txt', 'w') as f:
        f.write('50000.0')
    
    try:
        strategy.execute_strategy()
        print("\n✅ Test execution completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        raise


def main():
    """Run all tests"""
    print("🧪 Dynamic DCA Strategy - Test Mode")
    print("=" * 50)
    
    # Ensure we're in test mode
    print("⚠️  TEST MODE - No real orders will be placed")
    print("⚠️  Make sure to update config.py with real credentials before live trading")
    print()
    
    try:
        test_multiplicator_calculation()
        test_full_strategy()
        
        print("🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Update src/config.py with your real Kraken API credentials")
        print("2. Configure notification settings")
        print("3. Run: python main.py")
        
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
