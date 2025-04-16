# backtest.py
import pandas as pd
from data import fetch_ohlcv
from strategy import calculate_indicators, get_trade_direction, generate_grid_prices
import logging

def backtest(symbol='BTCUSDT', timeframe='1h', limit=1000):
    df = fetch_ohlcv(symbol, timeframe, limit)
    df = calculate_indicators(df)
    balance = 1000  # Initial USDT balance
    positions = []
    trades = []

    for i in range(1, len(df)):
        current_price = df['close'].iloc[i]
        direction = get_trade_direction(df.iloc[:i+1])
        if direction != 'neutral':
            grid_prices = generate_grid_prices(current_price)
            for price in grid_prices:
                if (direction == 'long' and price < current_price) or (direction == 'short' and price > current_price):
                    side = 'buy' if price < current_price else 'sell'
                    if df['low'].iloc[i] <= price <= df['high'].iloc[i]:
                        entry_price = price
                        sl = price * (1 - 0.02 if side == 'buy' else 1 + 0.02)
                        tp = price * (1 + 0.03 if side == 'buy' else 1 - 0.03)
                        positions.append({'side': side, 'entry': entry_price, 'sl': sl, 'tp': tp, 'size': 0.001})

        # Check for SL/TP hits
        for pos in positions[:]:
            if (pos['side'] == 'buy' and df['low'].iloc[i] <= pos['sl']) or \
               (pos['side'] == 'sell' and df['high'].iloc[i] >= pos['sl']):
                balance += (pos['sl'] - pos['entry']) * pos['size'] * 10 if pos['side'] == 'buy' else (pos['entry'] - pos['sl']) * pos['size'] * 10
                trades.append({'type': 'SL', 'profit': balance - 1000})
                positions.remove(pos)
            elif (pos['side'] == 'buy' and df['high'].iloc[i] >= pos['tp']) or \
                 (pos['side'] == 'sell' and df['low'].iloc[i] <= pos['tp']):
                balance += (pos['tp'] - pos['entry']) * pos['size'] * 10 if pos['side'] == 'buy' else (pos['entry'] - pos['tp']) * pos['size'] * 10
                trades.append({'type': 'TP', 'profit': balance - 1000})
                positions.remove(pos)

    logging.info(f"Backtest complete. Final balance: {balance}, Trades: {len(trades)}")
    return balance, trades

if __name__ == "__main__":
    balance, trades = backtest()
    print(f"Final Balance: {balance} USDT")
    print(f"Number of Trades: {len(trades)}")