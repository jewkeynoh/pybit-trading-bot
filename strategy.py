# strategy.py
import pandas as pd
import ta
import logging

# Bot configuration
SYMBOL = 'BTCUSDT'
GRID_SIZE = 0.005  # 0.5% price interval
NUM_GRIDS = 3  # Reduced number of grid levels
POSITION_SIZE = 0.001  # Minimum order size for BTCUSDT
RSI_PERIOD = 14
EMA_FAST = 12
EMA_SLOW = 26
STOP_LOSS = 0.02  # 2% SL
TAKE_PROFIT = 0.03  # 3% TP

# Calculate indicators
def calculate_indicators(df):
    try:
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=RSI_PERIOD).rsi()
        df['ema_fast'] = ta.trend.EMAIndicator(df['close'], window=EMA_FAST).ema_indicator()
        df['ema_slow'] = ta.trend.EMAIndicator(df['close'], window=EMA_SLOW).ema_indicator()
        return df
    except Exception as e:
        logging.error(f"Error calculating indicators: {e}")
        return df

# Determine trade direction
def get_trade_direction(df):
    latest = df.iloc[-1]
    if pd.isna(latest['rsi']) or pd.isna(latest['ema_fast']):
        return 'neutral'
    if latest['ema_fast'] > latest['ema_slow'] and latest['rsi'] < 70:
        return 'long'
    elif latest['ema_fast'] < latest['ema_slow'] and latest['rsi'] > 30:
        return 'short'
    return 'neutral'

# Generate grid prices
def generate_grid_prices(current_price):
    grid_prices = []
    for i in range(-NUM_GRIDS, NUM_GRIDS + 1):
        if i != 0:  # Skip current price
            price = current_price * (1 + i * GRID_SIZE)
            grid_prices.append(round(price, 2))
    return grid_prices