from trading.order_utils import calculate_quantity, validate_order, format_price
from core.config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET,
    FUTURES_LEVERAGE, FUTURES_MARGIN_TYPE, FUTURES_POSITION_MODE,
    FUTURES_COMMISSION_RATE, FUTURES_FUNDING_LIMIT
)
from binance.client import Client
from binance.exceptions import BinanceAPIException
from core.logger import get_logger
import math

logger = get_logger()

# Initialize Binance client
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=USE_TESTNET)

def setup_futures_account(symbol):
    """Set up futures account for trading"""
    try:
        # Switch to futures account
        client.futures_account_transfer(asset='USDT', amount=100, type=1)  # Spot to Futures
        
        # Set position mode
        try:
            if FUTURES_POSITION_MODE == 'HEDGE':
                client.futures_change_position_mode(dualSidePosition=True)
            else:
                client.futures_change_position_mode(dualSidePosition=False)
        except BinanceAPIException as e:
            if 'position mode is same' not in str(e):
                raise e
                
        # Set margin type
        try:
            client.futures_change_margin_type(symbol=symbol, marginType=FUTURES_MARGIN_TYPE)
        except BinanceAPIException as e:
            if 'margin type is same' not in str(e):
                raise e
                
        # Set leverage
        client.futures_change_leverage(symbol=symbol, leverage=FUTURES_LEVERAGE)
        
        logger.info(f"Futures account setup complete. Using {FUTURES_LEVERAGE}x leverage with {FUTURES_MARGIN_TYPE} margin")
        return True
        
    except BinanceAPIException as e:
        logger.error(f"Error setting up futures account: {e}")
        return False

def get_futures_info(symbol):
    """Get futures account information"""
    try:
        # Get account info
        account = client.futures_account()
        position = next((p for p in account['positions'] if p['symbol'] == symbol), None)
        
        if position:
            return {
                'leverage': float(position['leverage']),
                'isolated': position['isolated'],
                'position_amt': float(position['positionAmt']),
                'entry_price': float(position['entryPrice']),
                'unrealized_pnl': float(position['unrealizedProfit']),
                'margin_type': position['marginType']
            }
        return None
        
    except BinanceAPIException as e:
        logger.error(f"Error getting futures info: {e}")
        return None

def check_funding_rate(symbol):
    """Check current funding rate"""
    try:
        funding = client.futures_funding_rate(symbol=symbol, limit=1)[0]
        rate = float(funding['fundingRate'])
        
        if abs(rate) > FUTURES_FUNDING_LIMIT:
            logger.warning(f"Funding rate {rate:.4%} exceeds limit {FUTURES_FUNDING_LIMIT:.4%}")
            return False
        return True
        
    except BinanceAPIException as e:
        logger.error(f"Error checking funding rate: {e}")
        return False

def place_futures_order(symbol, side, quantity, position_side='BOTH', price=None, stop_price=None):
    """Place a futures order"""
    try:
        # Basic order parameters
        params = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity
        }
        
        # Add position side for hedge mode
        if FUTURES_POSITION_MODE == 'HEDGE':
            params['positionSide'] = position_side
            
        # Determine order type and add price parameters
        if price and stop_price:
            params['type'] = 'STOP'
            params['price'] = format_price(price)
            params['stopPrice'] = format_price(stop_price)
            params['timeInForce'] = 'GTC'
        elif price:
            params['type'] = 'LIMIT'
            params['price'] = format_price(price)
            params['timeInForce'] = 'GTC'
        else:
            params['type'] = 'MARKET'
            
        # Place the order
        order = client.futures_create_order(**params)
        logger.info(f"Futures {side} order placed: {order['orderId']}")
        return order
        
    except BinanceAPIException as e:
        logger.error(f"Error placing futures order: {e}")
        return None

def close_futures_position(symbol, position):
    """Close a futures position"""
    try:
        # Get current position
        info = get_futures_info(symbol)
        if not info or info['position_amt'] == 0:
            return True
            
        # Calculate closing quantity
        qty = abs(info['position_amt'])
        side = 'SELL' if info['position_amt'] > 0 else 'BUY'
        
        # Place closing order
        order = place_futures_order(
            symbol=symbol,
            side=side,
            quantity=qty,
            position_side='BOTH' if FUTURES_POSITION_MODE == 'ONEWAY' else ('LONG' if side == 'SELL' else 'SHORT')
        )
        
        return order is not None
        
    except Exception as e:
        logger.error(f"Error closing futures position: {e}")
        return False