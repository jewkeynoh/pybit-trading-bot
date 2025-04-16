# data.py
import ccxt
import pandas as pd
from pybit.unified_trading import HTTP, WebSocket
import config
import logging

logging.basicConfig(filename='logs/trading_bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Bybit client
bybit = HTTP(
    testnet=config.BYBIT_TESTNET,
    api_key=config.BYBIT_API_KEY,
    api_secret=config.BYBIT_API_SECRET
)

# Fetch historical OHLCV data
def fetch_ohlcv(symbol='BTCUSDT', timeframe='1h', limit=100):
    try:
        exchange = ccxt.bybit({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info(f"Fetched {len(df)} OHLCV candles for {symbol}")
        return df
    except Exception as e:
        logging.error(f"Error fetching OHLCV: {e}")
        return None

# Real-time price via WebSocket
def get_realtime_price(symbol='BTCUSDT'):
    ws = WebSocket(testnet=config.BYBIT_TESTNET)
    def handle_message(message):
        if 'topic' in message and message['topic'] == f'tickers.{symbol}':
            return float(message['data']['lastPrice'])
    ws.ticker_stream(symbol=symbol, callback=handle_message)
    return ws