#!/usr/bin/env python3
"""
DCA Strategy entry point — selects and runs the configured strategy.
"""
import os
import logging

from config import DCA_MODE, DATA_DIR, LOGS_DIR
from strategy_dynamic import DynamicStrategy
from strategy_fixed_fiat import FixedFiatStrategy

# Setup logging
log_file = os.path.join(LOGS_DIR, "dca_strategy.log")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

STRATEGIES = {
    "dynamic": DynamicStrategy,
    "fixed-fiat": FixedFiatStrategy,
}


def main():
    try:
        strategy_cls = STRATEGIES.get(DCA_MODE)
        if strategy_cls is None:
            raise ValueError(f"Unknown DCA_MODE: '{DCA_MODE}'. Valid modes: {', '.join(STRATEGIES)}")
        strategy = strategy_cls()
        strategy.execute()
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
        exit(1)


if __name__ == "__main__":
    main()
