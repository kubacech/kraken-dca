#!/usr/bin/env python3
"""
Simple Python scheduler for DCA Strategy
Replaces cron with a pure Python solution.
"""

import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from dca import main as run_dca
from config import DCA_MODE, BASE_ORDER_SIZE, MAX_MULTIPLICATOR, FIXED_FIAT_AMOUNT

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(
            os.getenv('LOGS_DIR', 'logs'), 
            'scheduler.log'
        ))
    ]
)
logger = logging.getLogger(__name__)


def parse_cron_schedule(cron_string):
    """
    Parse cron schedule string and return a human-readable description.
    Format: minute hour day month weekday
    
    Examples:
    - "0 1 * * *" -> Every day at 01:00
    - "0 */6 * * *" -> Every 6 hours
    - "30 9,21 * * *" -> At 09:30 and 21:30
    """
    parts = cron_string.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron format: {cron_string}. Expected 5 parts (minute hour day month weekday)")
    
    minute, hour, day, month, weekday = parts

    # Handle hours
    if hour == "*":
        hour_desc = "every hour"
    elif "/" in hour:
        interval = hour.split("/")[1]
        hour_desc = f"every {interval} hours"
    elif "," in hour:
        hours_list = hour.split(",")
        hour_desc = f"at hours {', '.join(hours_list)}"
    else:
        hour_desc = f"at {hour.zfill(2)}:00"
    
    return f"{hour_desc} ({cron_string})"


def calculate_next_run(cron_string):
    """
    Calculate the next run time based on cron schedule.
    Returns seconds until next run.
    """
    parts = cron_string.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron format: {cron_string}")
    
    minute, hour, day, month, weekday = parts
    
    now = datetime.now()
    
    # Simple interval-based scheduling
    if hour.startswith("*/"):
        # Every X hours
        interval_hours = int(hour.split("/")[1])

        # Calculate next run
        current_hour = now.hour
        hours_since_midnight = current_hour
        next_hour = ((hours_since_midnight // interval_hours) + 1) * interval_hours
        
        if next_hour >= 24:
            next_hour = 0
        
        target_minute = int(minute) if minute != "*" else 0
        next_run = now.replace(hour=next_hour % 24, minute=target_minute, second=0, microsecond=0)
        
        if next_run <= now:
            # Move to next interval
            next_run = now.replace(minute=target_minute, second=0, microsecond=0)
            seconds_in_interval = interval_hours * 3600
            seconds_since_start = (now.hour % interval_hours) * 3600 + now.minute * 60 + now.second
            seconds_until_next = seconds_in_interval - seconds_since_start
            return seconds_until_next
        
        return (next_run - now).total_seconds()
    
    elif minute.startswith("*/"):
        # Every X minutes
        interval_minutes = int(minute.split("/")[1])

        # Calculate seconds since last interval
        minutes_now = now.minute
        seconds_since_start = (minutes_now % interval_minutes) * 60 + now.second
        seconds_until_next = interval_seconds - seconds_since_start
        
        return seconds_until_next
    
    else:
        # Daily schedule (e.g., "0 1 * * *")
        target_hour = int(hour) if hour != "*" else 0
        target_minute = int(minute) if minute != "*" else 0
        
        next_run = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        if next_run <= now:
            # Already passed today, schedule for tomorrow
            from datetime import timedelta
            next_run = next_run + timedelta(days=1)
        
        return (next_run - now).total_seconds()


def run_dca_with_error_handling():
    """Wrapper to run DCA with error handling and logging."""
    try:
        logger.info("=" * 60)
        logger.info(f"Starting DCA execution (strategy: {DCA_MODE})")
        logger.info("=" * 60)
        
        run_dca()
        
        logger.info("=" * 60)
        logger.info("DCA execution completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Error during DCA execution: {str(e)}", exc_info=True)
        logger.error("=" * 60)


def main():
    """Main scheduler loop."""
    
    # Get cron schedule from environment
    cron_schedule = os.getenv("CRON_SCHEDULE", "0 1 * * *")
    
    logger.info("=" * 60)
    logger.info("DCA Scheduler Started")
    logger.info("=" * 60)
    logger.info(f"Strategy: {DCA_MODE}")
    if DCA_MODE == "fixed-fiat":
        logger.info(f"Fixed Fiat Amount: {FIXED_FIAT_AMOUNT} EUR")
    else:
        logger.info(f"Base Order Size: {BASE_ORDER_SIZE} EUR")
        logger.info(f"Max Multiplicator: {MAX_MULTIPLICATOR}")
    logger.info(f"Schedule: {parse_cron_schedule(cron_schedule)}")
    logger.info(f"Timezone: {os.getenv('TZ', 'system default')}")
    logger.info("=" * 60)
    
    # Validate schedule
    try:
        parse_cron_schedule(cron_schedule)
    except ValueError as e:
        logger.error(f"Invalid CRON_SCHEDULE: {e}")
        sys.exit(1)
    
    # Main loop
    while True:
        try:
            # Calculate next run
            seconds_until_next = calculate_next_run(cron_schedule)
            next_run_time = datetime.now().timestamp() + seconds_until_next
            next_run_dt = datetime.fromtimestamp(next_run_time)
            
            logger.info(f"Next execution scheduled for: {next_run_dt.strftime('%Y-%m-%d %H:%M:%S')} "
                       f"(in {int(seconds_until_next // 60)} minutes)")
            
            # Sleep until next run
            time.sleep(seconds_until_next)
            
            # Execute DCA
            run_dca_with_error_handling()
            
            # Small buffer to prevent double execution
            time.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}", exc_info=True)
            logger.info("Continuing scheduler after error...")
            time.sleep(60)  # Wait a minute before retrying


if __name__ == "__main__":
    main()

