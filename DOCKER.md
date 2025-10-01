# Docker Deployment Guide

This guide covers the complete Docker deployment of the Dynamic DCA strategy.

## Quick Start

1. **Setup**:
   ```bash
   # Clone repository and navigate to directory
   cd dynamic-dca
   
   # Run setup script (optional)
   ./setup-docker.sh
   
   # Or manually:
   cp env.example .env
   mkdir -p data
   ```

2. **Configure** your `.env` file:
   ```bash
   # Required
   KRAKEN_API_KEY=your_actual_api_key
   KRAKEN_PRIVATE_KEY=your_actual_private_key
   
   # Optional customization
   CRON_SCHEDULE=0 1 * * *  # Daily at 1 AM
   TZ=UTC
   BASE_ORDER_SIZE=5.0
   MAX_MULTIPLICATOR=5.0
   ```

3. **Deploy**:
   ```bash
   docker-compose up -d
   ```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CRON_SCHEDULE` | `0 1 * * *` | Cron expression for execution schedule |
| `TZ` | `UTC` | Timezone for cron execution |
| `DATA_VOLUME_PATH` | `./data` | Local directory for data persistence |
| `BASE_ORDER_SIZE` | `5.0` | Base order size in EUR |
| `MAX_MULTIPLICATOR` | `5.0` | Maximum order size multiplier |
| `KRAKEN_API_KEY` | - | Your Kraken API key (required) |
| `KRAKEN_PRIVATE_KEY` | - | Your Kraken private key (required) |
| `TELEGRAM_BOT_TOKEN` | - | Telegram bot token (optional) |
| `TELEGRAM_CHAT_ID` | - | Telegram chat ID (optional) |

## Docker Commands

### Basic Operations

```bash
# Start service
docker-compose up -d

# Stop service
docker-compose down

# View logs
docker-compose logs -f dynamic-dca

# Restart service
docker-compose restart dynamic-dca
```

### Development & Testing

```bash
# Build image
docker-compose build

# Run once for testing (bypasses cron)
docker-compose run --rm dynamic-dca python dynamic_dca.py

# Access container shell
docker-compose exec dynamic-dca bash

# View cron jobs inside container
docker-compose exec dynamic-dca crontab -l
```

### Maintenance

```bash
# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Clean up everything
docker-compose down --rmi all --volumes --remove-orphans

# View container status
docker-compose ps

# View resource usage
docker stats dynamic-dca
```

## Data Persistence

All application data is stored in the `./data` directory:

```
data/
├── ath_price.txt         # Current All-Time High
├── cumulative_data.txt   # Investment and BTC totals
├── dca_log.csv          # Complete execution history
└── dca_strategy.log     # Application logs
```

This directory is mounted as a volume, so data persists across container restarts.

## Monitoring & Troubleshooting

### Log Monitoring

```bash
# Follow all logs
docker-compose logs -f

# Follow only application logs
docker-compose logs -f dynamic-dca

# View last 100 lines
docker-compose logs --tail=100 dynamic-dca

# View logs with timestamps
docker-compose logs -t dynamic-dca
```

### Health Checks

The container includes health checks to monitor the cron daemon:

```bash
# Check container health
docker-compose ps

# View health check logs
docker inspect dynamic-dca | grep -A 10 Health
```
