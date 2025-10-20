from trading.order_utils import calculate_quantity, validate_order, format_price
from core.config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET,
    OPTIONS_EXPIRY_DAYS, OPTIONS_STRIKE_DELTA, OPTIONS_TYPE,
    OPTIONS_COMMISSION_RATE, OPTIONS_MAX_PREMIUM_PCT
)
from binance.client import Client
from binance.exceptions import BinanceAPIException
from core.logger import get_logger
from datetime import datetime, timedelta
import math

logger = get_logger()

# Initialize Binance client
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=USE_TESTNET)

def get_expiry_timestamp():
    """Get closest valid expiry timestamp"""
    expiry = datetime.now() + timedelta(days=OPTIONS_EXPIRY_DAYS)
    # Round to closest Friday
    while expiry.weekday() != 4:  # Friday = 4
        expiry += timedelta(days=1)
    return int(expiry.timestamp() * 1000)

def find_strike_price(symbol, option_type):
    """Find appropriate strike price based on delta"""
    try:
        # Get current price
        spot_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
        
        # Get available strikes
        expiry = get_expiry_timestamp()
        strikes = client.options_chain(symbol=symbol, expiry=expiry)
        
        # Find strike closest to target delta
        target_delta = OPTIONS_STRIKE_DELTA if option_type == 'CALL' else -OPTIONS_STRIKE_DELTA
        best_strike = None
        min_delta_diff = float('inf')
        
        for strike in strikes['data']:
            delta = float(strike['delta'])
            diff = abs(delta - target_delta)
            if diff < min_delta_diff:
                min_delta_diff = diff
                best_strike = float(strike['strike'])
                
        return best_strike
        
    except BinanceAPIException as e:
        logger.error(f"Error finding strike price: {e}")
        return None

def calculate_option_price(symbol, strike_price, option_type):
    """Calculate theoretical option price"""
    try:
        # Get option chain data
        expiry = get_expiry_timestamp()
        chain = client.options_chain(symbol=symbol, expiry=expiry)
        
        # Find matching option
        option = next((o for o in chain['data'] 
                      if float(o['strike']) == strike_price 
                      and o['type'] == option_type), None)
                      
        if option:
            return float(option['markPrice'])
        return None
        
    except BinanceAPIException as e:
        logger.error(f"Error calculating option price: {e}")
        return None

def place_options_order(symbol, option_type, quantity, strike_price=None):
    """Place an options order"""
    try:
        # Get or calculate strike price
        if not strike_price:
            strike_price = find_strike_price(symbol, option_type)
        if not strike_price:
            return None
            
        # Get expiry
        expiry = get_expiry_timestamp()
        
        # Calculate theoretical price
        price = calculate_option_price(symbol, strike_price, option_type)
        if not price:
            return None
            
        # Check premium against account limit
        account = client.get_account()
        total_balance = float(account['totalAssetOfBtc'])
        max_premium = total_balance * OPTIONS_MAX_PREMIUM_PCT
        
        if price * quantity > max_premium:
            logger.warning(f"Option premium ({price * quantity}) exceeds max allowed ({max_premium})")
            return None
            
        # Place the order
        params = {
            'symbol': symbol,
            'side': 'BUY',
            'type': 'LIMIT',
            'quantity': quantity,
            'price': format_price(price),
            'timeInForce': 'GTC',
            'strikePrice': strike_price,
            'expiry': expiry,
            'optionType': option_type
        }
        
        order = client.options_create_order(**params)
        logger.info(f"Options order placed: {order['orderId']}")
        return order
        
    except BinanceAPIException as e:
        logger.error(f"Error placing options order: {e}")
        return None

def close_options_position(symbol, position):
    """Close an options position"""
    try:
        # Get current position
        positions = client.options_position_info()
        pos = next((p for p in positions if p['symbol'] == symbol), None)
        
        if not pos or float(pos['positionAmt']) == 0:
            return True
            
        # Place closing order
        params = {
            'symbol': symbol,
            'side': 'SELL',
            'type': 'MARKET',
            'quantity': abs(float(pos['positionAmt'])),
            'strikePrice': float(pos['strikePrice']),
            'expiry': int(pos['expiry']),
            'optionType': pos['optionType']
        }
        
        order = client.options_create_order(**params)
        return order is not None
        
    except Exception as e:
        logger.error(f"Error closing options position: {e}")
        return False