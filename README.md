# Bybit Futures Grid Trading Bot

This is an advanced futures trading bot designed for Bybit, specifically for trading perpetual futures (e.g., BTCUSDT). The bot implements a Grid Trading Strategy with Momentum Filtering using RSI and EMA indicators. It supports leverage, stop-loss, take-profit, and position sizing, making it suitable for automated futures trading with robust risk management.

The bot is built in Python, leveraging Bybit’s API via the pybit library and ccxt for flexibility. It includes modules for data fetching, strategy execution, risk management, and backtesting, ensuring modularity and scalability. This project is ideal for programmers with experience in futures trading who want to automate their strategies on Bybit.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Backtesting](#backtesting)
  - [Testnet Trading](#testnet-trading)
  - [Live Trading](#live-trading)
- [Project Structure](#project-structure)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features
- **Grid Trading Strategy:** Places buy/sell limit orders at fixed price intervals (e.g., 0.5% apart) around the current price to profit from market oscillations.
- **Momentum Filtering:** Uses RSI (14-period) and EMA (12/26) to filter trades, executing long grids in uptrends and short grids in downtrends.
- **Risk Management:**
  - Configurable leverage (default: 10x)
  - Stop-loss (2%) and take-profit (3%) per trade
  - Isolated margin mode
  - Position size limits
- **Real-Time Data:** Fetches live prices via Bybit WebSocket and historical data for analysis.
- **Backtesting:** Simulates the strategy using historical data.
- **Logging:** Records trades, errors, and events.
- **Testnet Support:** Risk-free testing on Bybit’s testnet.
- **Modular Design:** Easy customization through separate modules.

## Architecture
**Data Module (`data.py`):**
- Fetches OHLCV via ccxt
- Streams live prices via WebSocket

**Strategy Module (`strategy.py`):**
- Grid trading logic with RSI/EMA filters
- Calculates indicators, determines direction

**Risk Management Module (`risk_management.py`):**
- Sets leverage, margin mode
- Enforces position limits

**Main Logic (`bot.py`):**
- Integrates modules and manages trading loop

**Backtesting Module (`backtest.py`):**
- Simulates historical performance

## Prerequisites
- **Python 3.8+**
- **Bybit Account:** API keys with Trade and Read permissions
- **Testnet Setup:** For risk-free testing
- **Development Tools:** VS Code, Git, Jupyter (optional)
- **Internet Connection:** Stable for API/WebSocket

## Installation
```bash
git clone https://github.com/your-username/bybit-futures-grid-bot.git
cd bybit-futures-grid-bot

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
pip list
```

## Configuration
Create `config.py`:
```python
BYBIT_API_KEY = 'your_bybit_api_key'
BYBIT_API_SECRET = 'your_bybit_api_secret'
BYBIT_TESTNET = True  # False for live
```

Customize `strategy.py`:
```python
SYMBOL = 'BTCUSDT'
GRID_SIZE = 0.005
NUM_GRIDS = 5
POSITION_SIZE = 0.001
RSI_PERIOD = 14
EMA_FAST = 12
EMA_SLOW = 26
STOP_LOSS = 0.02
TAKE_PROFIT = 0.03
```

Set Leverage in `risk_management.py`:
```python
LEVERAGE = 10
```

## Usage
### Backtesting
```bash
python backtest.py
```
Analyze:
```python
import pandas as pd
df = pd.DataFrame(trades)
print(df['profit'].describe())
```

### Testnet Trading
- Set `BYBIT_TESTNET = True`
- Use testnet keys
- Run:
```bash
python bot.py
```

### Live Trading
- Set `BYBIT_TESTNET = False`
- Use live keys
- Run:
```bash
python bot.py
```

For 24/7 operation:
```bash
npm install -g pm2
pm2 start bot.py
```

## Project Structure
```
bybit-futures-grid-bot/
├── config.py
├── bot.py
├── strategy.py
├── data.py
├── risk_management.py
├── backtest.py
├── logs/
├── requirements.txt
└── README.md
```

## Customization
- **Add Indicators:**
```python
df['macd'] = ta.trend.MACD(df['close']).macd()
```
- **Dynamic Grids with ATR:**
```python
df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
GRID_SIZE = df['atr'].iloc[-1] / current_price
```
- **Multi-Pair:** Update `SYMBOL`
- **Notifications:**
```python
def send_telegram_message(msg):
    requests.post(f"https://api.telegram.org/bot{{token}}/sendMessage", json={'chat_id': chat_id, 'text': msg})
```
- **Advanced Risk Management:**
```python
balance = bybit.get_wallet_balance(accountType='UNIFIED')
```

## Troubleshooting
- **Rate Limit:** Check logs, increase sleep
- **Auth Failed:** Recheck API keys
- **No Trades:** Adjust RSI/EMA
- **Position Limits:** Lower position size
- **WebSocket Issues:** Use REST fallback:
```python
current_price = float(bybit.get_tickers(category='linear', symbol=SYMBOL)['result']['list'][0]['lastPrice'])
```

## Contributing
1. Fork the repo
2. Create branch: `git checkout -b feature/new-feature`
3. Commit: `git commit -m 'Add new feature'`
4. Push: `git push origin feature/new-feature`
5. Open a pull request

Include tests and update documentation.

## License
MIT License. See LICENSE file.

---

**Note for Users:**
This bot is ideal for experienced Bybit futures traders aiming for automation. Bybit was chosen due to its futures focus, API simplicity, and low fees. The strategy leverages grid trading with trend confirmation to reduce drawdowns.

Test on testnet before going live. Start with low leverage and small size. If you want to add MACD, support more pairs, or other features, feel free to reach out or open an issue.

Happy Trading!

