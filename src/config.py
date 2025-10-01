import os
from dotenv import load_dotenv

load_dotenv()

# Trading Configuration
BASE_ORDER_SIZE = float(os.getenv("BASE_ORDER_SIZE", "5.0"))  # EUR
MAX_MULTIPLICATOR = float(os.getenv("MAX_MULTIPLICATOR", "5.0"))
TRADING_PAIR = "XXBTZEUR"  # Kraken's BTC/EUR pair
MAKER_FEE_OFFSET = 0.0005  # 0.05% under current price for maker fee

# File paths - use absolute paths relative to project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(_PROJECT_ROOT, "data"))
LOGS_DIR = os.getenv("LOGS_DIR", os.path.join(_PROJECT_ROOT, "logs"))
ATH_FILE = os.path.join(DATA_DIR, "ath_price.txt")
LOG_FILE = os.path.join(DATA_DIR, "dca_log.csv")
CUMULATIVE_FILE = os.path.join(DATA_DIR, "cumulative_data.txt")

# Kraken API Configuration
KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY")
KRAKEN_PRIVATE_KEY = os.getenv("KRAKEN_PRIVATE_KEY")

# Notification Configuration
NOTIFICATION_ENABLED = True
NOTIFICATION_METHOD = "telegram"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
