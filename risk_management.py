# risk_management.py
from pybit.unified_trading import HTTP
import config
import logging

bybit = HTTP(
    testnet=config.BYBIT_TESTNET,
    api_key=config.BYBIT_API_KEY,
    api_secret=config.BYBIT_API_SECRET
)

LEVERAGE = 5
MAX_POSITION = 0.01

def set_leverage(symbol='BTCUSDT'):
    try:
        pos_info = bybit.get_positions(category='linear', symbol=symbol)
        current_leverage = pos_info['result']['list'][0].get('leverage', 'unknown')
        logging.info(f"Current leverage for {symbol}: {current_leverage}x")
        
        account_info = bybit.get_wallet_balance(accountType='UNIFIED')
        margin_mode = account_info['result']['list'][0].get('marginMode', 'unknown')
        logging.info(f"Current margin mode: {margin_mode}")
        
        if current_leverage != str(LEVERAGE):
            bybit.set_leverage(
                category='linear',
                symbol=symbol,
                buyLeverage=str(LEVERAGE),
                sellLeverage=str(LEVERAGE)
            )
            logging.info(f"Set {LEVERAGE}x leverage for {symbol}")
        
        if margin_mode != 'ISOLATED':
            bybit.cancel_all_orders(category='linear', symbol=symbol)
            bybit.close_position(category='linear', symbol=symbol)
            try:
                bybit.switch_margin_mode(
                    category='linear',
                    symbol=symbol,
                    marginMode='ISOLATED'
                )
                logging.info(f"Set isolated margin mode for {symbol}")
            except Exception as e:
                logging.warning(f"Failed to set isolated margin: {e}. Verify manually in Bybit UI.")
        else:
            logging.info(f"Margin mode already ISOLATED for {symbol}")
    except Exception as e:
        logging.warning(f"Error setting leverage/margin mode: {e}. Using existing leverage: {current_leverage}x")

def check_position_limits(symbol='BTCUSDT', position_size=0.001):
    try:
        positions = bybit.get_positions(category='linear', symbol=symbol)
        total_size = sum(float(pos['size']) for pos in positions['result']['list'])
        if total_size + position_size > MAX_POSITION:
            logging.warning(f"Position size limit exceeded for {symbol}")
            return False
        return True
    except Exception as e:
        logging.error(f"Error checking position limits: {e}")
        return False