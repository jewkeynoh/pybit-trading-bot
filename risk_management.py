# risk_management.py
from pybit.unified_trading import HTTP
import config
import logging

# Initialize Bybit client
bybit = HTTP(
    testnet=config.BYBIT_TESTNET,
    api_key=config.BYBIT_API_KEY,
    api_secret=config.BYBIT_API_SECRET
)

LEVERAGE = 5  # Match current leverage in logs

# Set leverage and margin mode
def set_leverage(symbol='BTCUSDT'):
    try:
        # Check current leverage and margin mode
        pos_info = bybit.get_positions(category='linear', symbol=symbol)
        current_leverage = pos_info['result']['list'][0].get('leverage', 'unknown')
        logging.info(f"Current leverage for {symbol}: {current_leverage}x")
        
        # Check margin mode
        account_info = bybit.get_account_info()
        margin_mode = account_info['result'].get('marginMode', 'unknown')
        logging.info(f"Current margin mode: {margin_mode}")
        
        # Set leverage if needed
        if current_leverage != str(LEVERAGE):
            bybit.set_leverage(
                category='linear',
                symbol=symbol,
                buy_leverage=str(LEVERAGE),
                sell_leverage=str(LEVERAGE)
            )
            logging.info(f"Set {LEVERAGE}x leverage for {symbol}")
        
        # Set margin mode if not already isolated
        if margin_mode != 'ISOLATED':
            bybit.set_margin_mode(
                category='linear',
                symbol=symbol,
                marginMode='ISOLATED'
            )
            logging.info(f"Set isolated margin mode for {symbol}")
        else:
            logging.info(f"Margin mode already ISOLATED for {symbol}")
    except Exception as e:
        logging.warning(f"Failed to set leverage or margin mode: {e}. Using existing leverage: {current_leverage}x")

# Check position limits
def check_position_limits(symbol='BTCUSDT', position_size=0.001):
    try:
        positions = bybit.get_positions(category='linear', symbol=symbol)
        total_size = sum(float(pos['size']) for pos in positions['result']['list'])
        if total_size + position_size > 0.1:  # Example max size limit
            logging.warning(f"Position size limit exceeded for {symbol}")
            return False
        return True
    except Exception as e:
        logging.error(f"Error checking position limits: {e}")
        return False