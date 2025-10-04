# Dynamic DCA Strategy for Bitcoin

A Python script that implements a dynamic Dollar Cost Averaging (DCA) strategy for Bitcoin using the Kraken API. The strategy adjusts order sizes based on the current price's distance from the All-Time High (ATH).

## Features

- **Dynamic Order Sizing**: Order size increases as Bitcoin price drops from ATH
- **Kraken API Integration**: Fetches real-time prices and places orders
- **ATH Tracking**: Automatically updates ATH when price reaches new highs
- **Maker Fee Optimization**: Places orders slightly below market price for maker fees
- **Comprehensive Logging**: CSV logging with cumulative investment tracking
- **Notification System**: Get notified of each execution via Telegram
- **Persistent State**: Maintains ATH and cumulative data across runs

## How It Works

1. **Price Fetching**: Gets current BTC/EUR price from Kraken
2. **ATH Management**: Compares with stored ATH and updates if higher
3. **Multiplicator Calculation**: 
   - `%diff = (ATH - Current) / ATH`
   - `multiplicator = 1 + ((MAX_MULT - 1) / 0.75) * %diff`
   - Maximum multiplicator (5x) is reached at 75% drop from ATH
4. **Order Sizing**: `order_size = BASE_ORDER_SIZE * multiplicator`
5. **Order Placement**: Places limit order 0.05% below current price
6. **Logging**: Records all parameters and cumulative data to CSV

## Installation

1. **Clone and setup**:
   ```bash
   cd dynamic-dca
   pip install -r requirements.txt
   python setup.py
   ```

2. **Configure API credentials** in `src/config.py`:
   ```python
   KRAKEN_API_KEY = "your_api_key_here"
   KRAKEN_PRIVATE_KEY = "your_private_key_here"
   ```

3. **Configure notifications** (optional):
   ```python
   TELEGRAM_BOT_TOKEN = "your_bot_token"
   TELEGRAM_CHAT_ID = "your_chat_id"
   ```

## Configuration

Key parameters in `src/config.py`:

- `BASE_ORDER_SIZE = 5.0` - Base order size in EUR
- `MAX_MULTIPLICATOR = 5.0` - Maximum order size multiplier
- `MAKER_FEE_OFFSET = 0.0005` - 0.05% below market price
- `TRADING_PAIR = "XBTEUR"` - Kraken's BTC/EUR pair

## Usage

### Standalone Python Scheduler (Recommended for Local Setup)

Run the scheduler directly with Python - no Docker or cron needed:

```bash
# Set environment variables in .env file
cp env.example .env
# Edit .env with your API keys and schedule

# Run the scheduler
python3 scheduler.py
```

The scheduler will:
- Read your `CRON_SCHEDULE` from the `.env` file
- Run the DCA strategy automatically at scheduled times
- Log all activities to both console and `logs/scheduler.log`
- Continue running indefinitely until stopped (Ctrl+C)

**Example schedules:**
- `0 1 * * *` - Daily at 1:00 AM
- `0 */6 * * *` - Every 6 hours
- `30 9,21 * * *` - Twice daily at 9:30 AM and 9:30 PM

**Running as a system service (optional):**

To run the scheduler as a systemd service that starts automatically on boot:

```bash
# Edit the service file with your paths
nano dynamic-dca.service

# Copy to systemd directory
sudo cp dynamic-dca.service /etc/systemd/system/

# Enable and start the service
sudo systemctl enable dynamic-dca
sudo systemctl start dynamic-dca

# Check status
sudo systemctl status dynamic-dca

# View logs
sudo journalctl -u dynamic-dca -f
```

### Docker Deployment (Recommended for Production)

The easiest way to run this strategy is using Docker with automated Python-based scheduling.

#### Quick Start

1. **Clone and configure**:
   ```bash
   git clone <repository-url>
   cd dynamic-dca
   cp env.example .env
   ```

2. **Edit `.env` file** with your configuration:
   ```bash
   # Required: Add your Kraken API credentials
   KRAKEN_API_KEY=your_actual_api_key
   KRAKEN_PRIVATE_KEY=your_actual_private_key
   
   # Optional: Customize schedule (default: daily at 1 AM)
   CRON_SCHEDULE=0 1 * * *
   TZ=Europe/Prague
   
   # Optional: Customize trading parameters
   BASE_ORDER_SIZE=10.0
   MAX_MULTIPLICATOR=5.0
   ```

3. **Start the container**:
   ```bash
   docker-compose up -d
   ```

4. **Monitor logs**:
   ```bash
   docker-compose logs -f
   ```

#### Docker Configuration Options

**Data Persistence:**
All data files (ATH, logs, cumulative data) are stored in the `./data` directory and persist across container restarts.

**Environment Variables:**
- `CRON_SCHEDULE` - Cron expression for execution schedule (e.g., "0 1 * * *" for daily at 1 AM)
- `TZ` - Timezone for scheduler execution
- `DATA_VOLUME_PATH` - Local directory for data persistence
- `BASE_ORDER_SIZE` - Base order size in EUR
- `MAX_MULTIPLICATOR` - Maximum order size multiplier
- `KRAKEN_API_KEY` - Your Kraken API key (required)
- `KRAKEN_PRIVATE_KEY` - Your Kraken private key (required)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token (optional)
- `TELEGRAM_CHAT_ID` - Telegram chat ID (optional)


## Project Structure

```
dynamic-dca/
├── src/                    # Source code
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration settings
│   ├── dynamic_dca.py     # Main strategy implementation
│   └── test_strategy.py   # Test suite
├── data/                  # Data files (persistent)
│   ├── ath_price.txt      # All-time high price
│   ├── cumulative_data.txt # Investment tracking
│   └── dca_log.csv        # Execution history
├── logs/                  # Log files
│   └── dca_strategy.log   # Application logs
├── main.py               # Main entry point
├── scheduler.py          # Python scheduler (replaces cron)
├── test.py               # Test runner
├── setup.py              # Initial setup script
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
└── README.md             # This file
```

## Files Generated

When running with Docker, all files are stored in the mounted `./data` directory:

- `data/ATH` - Stores current All-Time High
- `data/cumulative_data.log` - Stores cumulative investment and BTC amounts  
- `data/dca_log.csv` - Complete execution history
- `data/dca_strategy.log` - Application logs
