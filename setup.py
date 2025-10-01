#!/usr/bin/env python3
import os
import json

def create_initial_files():
    """Create initial data files if they don't exist"""
    
    # Ensure directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Create ATH file with 0 if it doesn't exist
    if not os.path.exists('data/ath_price.txt'):
        with open('data/ath_price.txt', 'w') as f:
            f.write('0.0')
        print("Created data/ath_price.txt with initial value 0.0")
    
    # Create cumulative data file if it doesn't exist
    if not os.path.exists('data/cumulative_data.txt'):
        initial_data = {
            'investment': 0.0,
            'btc_amount': 0.0
        }
        with open('data/cumulative_data.txt', 'w') as f:
            json.dump(initial_data, f, indent=2)
        print("Created data/cumulative_data.txt with initial values")
    
    # Create CSV header if file doesn't exist
    if not os.path.exists('data/dca_log.csv'):
        import csv
        fieldnames = [
            'timestamp', 'current_price', 'ath_price', 'percent_diff', 'multiplicator',
            'order_size_eur', 'order_price', 'btc_volume', 'order_id',
            'cumulative_investment', 'cumulative_btc', 'avg_price'
        ]
        with open('data/dca_log.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        print("Created data/dca_log.csv with headers")

def main():
    print("Setting up Dynamic DCA Strategy...")
    create_initial_files()
    print("Setup completed!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Update config.py with your Kraken API credentials")
    print("3. Configure notification settings in config.py")
    print("4. Run the strategy: python main.py")

if __name__ == "__main__":
    main()
