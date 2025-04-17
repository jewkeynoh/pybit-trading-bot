# strategy.py
import pandas as pd
import pandas_ta as ta
import numpy as np
import logging

# Bot configuration
SYMBOL = 'BTCUSDT'
NUM_ORDERS = 2  # One buy (VAL), one sell (VAH)
STOP_LOSS = 0.015  # 1.5%
TAKE_PROFIT = 0.025  # 2.5%

def calculate_indicators(df):
    """Calculate RSI, VWAP, ATR, and other indicators."""
    df['ema_fast'] = ta.ema(df['close'], length=10)
    df['ema_slow'] = ta.ema(df['close'], length=50)
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['vwap'] = ((df['close'] * df['volume']).cumsum() / df['volume'].cumsum())
    df['vwap'] = df.groupby(df.index // 24)['vwap'].transform('last')
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    return df

def calculate_dynamic_lookback(df, max_bars=336, min_bars=48):
    """Calculate dynamic lookback based on volatility (ATR) and price range."""
    try:
        latest = df.iloc[-1]
        current_price = latest['close']
        atr = latest['atr']
        
        # Volatility-based lookback (ATR as % of price)
        atr_percent = (atr / current_price) * 100
        if atr_percent > 2:  # High volatility
            lookback = min_bars  # 2 days
        elif atr_percent < 1:  # Low volatility
            lookback = max_bars  # 14 days
        else:  # Medium volatility
            lookback = 168  # 7 days
        
        # Price range-based lookback (latest swing high/low)
        swing_window = min(len(df), max_bars)
        recent_data = df[-swing_window:]
        swing_high_idx = recent_data['high'].idxmax()
        swing_low_idx = recent_data['low'].idxmin()
        swing_bars = abs(swing_high_idx - swing_low_idx)
        
        # Combine: Use shorter of volatility-based or swing-based, within bounds
        lookback = max(min_bars, min(lookback, swing_bars, max_bars))
        
        logging.info(f"Dynamic lookback: {lookback} bars (ATR: {atr_percent:.2f}%, Swing: {swing_bars} bars)")
        return int(lookback)
    except Exception as e:
        logging.error(f"Error calculating dynamic lookback: {e}. Using default 168 bars")
        return 168

def calculate_frvp(df, lookback_bars=None):
    """Calculate Fixed Range Volume Profile: POC, VAH, VAL with dynamic lookback."""
    if lookback_bars is None:
        lookback_bars = calculate_dynamic_lookback(df)
    
    df_range = df[-lookback_bars:].copy()
    price_min, price_max = df_range['close'].min(), df_range['close'].max()
    bins = np.linspace(price_min, price_max, 100)
    volume_profile = pd.cut(df_range['close'], bins=bins, labels=bins[:-1], include_lowest=True)
    volume_profile = df_range.groupby(volume_profile, observed=False)['volume'].sum()
    poc = volume_profile.idxmax()
    total_volume = volume_profile.sum()
    target_volume = total_volume * 0.7
    sorted_vol = volume_profile.sort_values(ascending=False)
    cumulative_vol = 0
    va_prices = []
    for price, vol in sorted_vol.items():
        if cumulative_vol < target_volume:
            va_prices.append(price)
            cumulative_vol += vol
    vah = max(va_prices) if va_prices else poc
    val = min(va_prices) if va_prices else poc
    return float(poc), float(vah), float(val)

def get_trade_direction(df, poc, vah, val):
    """Determine trade direction based on price, RSI, VWAP, and FRVP."""
    latest = df.iloc[-1]
    current_price = latest['close']
    rsi = latest['rsi']
    vwap = latest['vwap']
    atr = latest['atr']
    atr_threshold = current_price * 0.03
    
    val_upper = val * 1.01
    vah_lower = vah * 0.99
    
    if (current_price <= val_upper) and rsi < 50 and current_price > vwap and atr < atr_threshold:
        return 'long'
    elif (current_price >= vah_lower) and rsi > 50 and current_price < vwap and atr < atr_threshold:
        return 'short'
    logging.info(f"Neutral direction - Price: {current_price}, VAL: {val}, VAH: {vah}, RSI: {rsi}, VWAP: {vwap}, ATR: {atr}")
    return 'neutral'

def generate_grid_prices(current_price, df, poc, vah, val):
    """Generate buy/sell prices based on VAL and VAH."""
    atr = df.iloc[-1]['atr']
    buy_price = val * 0.999
    sell_price = vah * 1.001
    stop_loss_distance = 1.5 * atr
    take_profit_distance = 2.5 * atr
    return [
        {'price': buy_price, 'side': 'Buy', 'stop_loss': buy_price - stop_loss_distance, 'take_profit': buy_price + take_profit_distance},
        {'price': sell_price, 'side': 'Sell', 'stop_loss': sell_price + stop_loss_distance, 'take_profit': sell_price - take_profit_distance}
    ]