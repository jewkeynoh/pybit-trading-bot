# bot.py
from pybit.unified_trading import HTTP
import time
import logging
from data import fetch_ohlcv
from strategy import calculate_indicators, get_trade_direction, generate_grid_prices, calculate_frvp
from risk_management import set_leverage, check_position_limits
import config

# Initialize logging
logging.basicConfig(filename='logs/trading_bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Bybit client
bybit = HTTP(
    testnet=config.BYBIT_TESTNET,
    api_key=config.BYBIT_API_KEY,
    api_secret=config.BYBIT_API_SECRET
)

# Bot configuration
SYMBOL = 'BTCUSDT'
POSITION_SIZE = 0.001
SLEEP_INTERVAL = 300  # 5 minutes

# Validate API keys
def validate_api_keys(bybit):
    try:
        bybit.get_wallet_balance(accountType='UNIFIED')
        logging.info("API keys validated successfully")
        return True
    except Exception as e:
        logging.error(f"API key validation failed: {e}")
        return False

# Check account balance
def check_balance(bybit, min_balance=50):
    try:
        balance = bybit.get_wallet_balance(accountType='UNIFIED')
        logging.info(f"Raw balance response: {balance}")
        result_list = balance.get('result', {}).get('list', [])
        if not result_list:
            logging.error("No account data in balance response")
            return False
        account = result_list[0]
        usdt_balance = float(account.get('totalAvailableBalance', 0))
        if usdt_balance == 0:
            coin_list = account.get('coin', [])
            for coin in coin_list:
                if coin.get('coin') == 'USDT':
                    usdt_balance = float(coin.get('walletBalance', 0))
                    break
        if usdt_balance < min_balance:
            logging.error(f"Insufficient balance: {usdt_balance} USDT. Minimum required: {min_balance} USDT")
            return False
        logging.info(f"Available USDT balance: {usdt_balance}")
        return True
    except Exception as e:
        logging.error(f"Error checking balance: {e}")
        return False

# Get minimum order quantity
def get_min_order_qty(bybit, symbol='BTCUSDT'):
    try:
        info = bybit.get_instruments_info(category='linear', symbol=symbol)
        return float(info['result']['list'][0]['lotSizeFilter']['minOrderQty'])
    except Exception as e:
        logging.error(f"Error fetching min order quantity: {e}")
        return 0.001  # Fallback

# Check for filled orders and cancel others
def check_and_cancel_unfilled_orders():
    try:
        open_orders = bybit.get_open_orders(category='linear', symbol=SYMBOL)
        order_list = open_orders['result']['list']
        positions = bybit.get_positions(category='linear', symbol=SYMBOL)
        has_position = any(float(pos['size']) > 0 for pos in positions['result']['list'])
        
        if has_position:
            for order in order_list:
                bybit.cancel_order(
                    category='linear',
                    symbol=SYMBOL,
                    orderId=order['orderId']
                )
                logging.info(f"Cancelled unfilled order {order['orderId']} due to filled order")
            return True
        return False
    except Exception as e:
        logging.error(f"Error checking/cancelling orders: {e}")
        return False

# Place grid orders
def place_grid_orders(current_price, direction, grid_prices):
    orders = []
    min_qty = get_min_order_qty(bybit, SYMBOL)
    if POSITION_SIZE < min_qty:
        logging.error(f"Position size {POSITION_SIZE} is below minimum {min_qty} for {SYMBOL}")
        return orders
    try:
        for order_info in grid_prices:
            if not check_position_limits(SYMBOL, POSITION_SIZE):
                continue
            if (direction == 'long' and order_info['side'] == 'Buy') or (direction == 'short' and order_info['side'] == 'Sell'):
                order = bybit.place_order(
                    category='linear',
                    symbol=SYMBOL,
                    side=order_info['side'],
                    orderType='Limit',
                    qty=POSITION_SIZE,
                    price=order_info['price'],
                    stopLoss=str(order_info['stop_loss']),
                    takeProfit=str(order_info['take_profit'])
                )
                orders.append(order['result'])
                logging.info(f"Placed {order_info['side']} order at {order_info['price']} for {SYMBOL}")
    except Exception as e:
        logging.error(f"Error placing orders: {e}")
    return orders

# Cancel outdated orders
def cancel_outdated_orders():
    try:
        open_orders = bybit.get_open_orders(category='linear', symbol=SYMBOL)
        for order in open_orders['result']['list']:
            bybit.cancel_order(
                category='linear',
                symbol=SYMBOL,
                orderId=order['orderId']
            )
            logging.info(f"Cancelled order {order['orderId']}")
    except Exception as e:
        logging.error(f"Error cancelling orders: {e}")

# Main bot loop
def main():
    logging.info("Starting Bybit Futures Grid Bot")
    if not validate_api_keys(bybit) or not check_balance(bybit):
        logging.error("Stopping bot due to invalid API keys or insufficient balance")
        return
    set_leverage(SYMBOL)
    while True:
        try:
            if check_and_cancel_unfilled_orders():
                logging.info("Position detected, waiting for stop-loss/take-profit or next cycle")
                time.sleep(60)
                continue

            df = fetch_ohlcv(SYMBOL, '1h', 200)  # Extra bars for FRVP
            if df is None:
                time.sleep(60)
                continue
            df = calculate_indicators(df)
            current_price = float(bybit.get_tickers(category='linear', symbol=SYMBOL)['result']['list'][0]['lastPrice'])
            
            # Calculate FRVP
            poc, vah, val = calculate_frvp(df)
            logging.info(f"FRVP Levels: POC={poc}, VAH={vah}, VAL={val}")
            
            direction = get_trade_direction(df, poc, vah, val)
            cancel_outdated_orders()

            if direction != 'neutral':
                grid_prices = generate_grid_prices(current_price, df, poc, vah, val)
                place_grid_orders(current_price, direction, grid_prices)

            logging.info(f"Cycle complete. Direction: {direction}, Price: {current_price}")
            time.sleep(SLEEP_INTERVAL)
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()