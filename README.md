# Kraken DCA Bot

Bitcoin Dollar Cost Averaging bot for the [Kraken](https://www.kraken.com/) exchange. Automatically places recurring limit buy orders on a cron schedule with optional Telegram notifications.

## Modes

- **Dynamic** — Order size scales with distance from all-time high (ATH). The further BTC is from ATH, the more you buy. Uses a quadratic formula capped at a configurable maximum multiplier.
- **Fixed-fiat** — Buys a constant EUR amount every execution.

## Quick Start

```bash
cp env.example .env   # fill in your API keys and preferences
docker-compose up -d
docker-compose logs -f
```

Or run locally:

```bash
pip install -r requirements.txt
python3 src/scheduler.py
```

## Configuration

All settings are via environment variables (see [`env.example`](env.example) for full details):

| Variable | Default | Description |
|---|---|---|
| `DCA_MODE` | `dynamic` | `dynamic` or `fixed-fiat` |
| `CRON_SCHEDULE` | `0 1 * * *` | Cron expression for execution schedule |
| `TZ` | `UTC` | Timezone |
| `BASE_ORDER_SIZE` | `5.0` | Base order in EUR (dynamic mode) |
| `MAX_MULTIPLICATOR` | `5.0` | Max multiplier at 75% ATH drop (dynamic mode) |
| `FIXED_FIAT_AMOUNT` | `8.0` | Fixed buy amount in EUR (fixed-fiat mode) |
| `KRAKEN_API_KEY` | — | Kraken API key (required) |
| `KRAKEN_PRIVATE_KEY` | — | Kraken private key (required) |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token (optional) |
| `TELEGRAM_CHAT_ID` | — | Telegram chat ID (optional) |
| `DATA_VOLUME_PATH` | `./data` | Persistent data directory |

### Kraken API Permissions

Your API key needs: **Query Funds**, **Create & Modify Orders**, **Query Open/Closed Orders**.

## How It Works

1. The scheduler runs on the configured cron schedule
2. Fetches the current BTC/EUR price from Kraken
3. Calculates order size based on the active strategy
4. Places a limit buy order 0.05% below market price (to get maker fees)
5. Logs the execution to CSV and sends a Telegram notification

### Dynamic Multiplier

The dynamic strategy increases buy size as BTC drops from its ATH:

```
multiplier = 1 + (MAX_MULT - 1) * ((percent_diff / 0.75) ^ 2)
```

- At ATH: multiplier = 1.0x (base order)
- At 75% drop: multiplier = MAX_MULTIPLICATOR

## Persistent State

Stored in the `data/` directory:

- `ath_price.txt` — Tracked all-time high (dynamic mode)
- `cumulative_data.txt` — Total investment and BTC accumulated
- `dca_log.csv` — Execution history

## Tests

```bash
source .venv/bin/activate
pytest -v
```

If the venv doesn't exist yet:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
```

Tests mock all external services (Kraken API, Telegram) and use temporary directories for file state — no API keys or network access needed.
