from trading.order_utils import calculate_quantity, validate_order, format_price
from core.config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET,
    MARGIN_TYPE, LEVERAGE, MARGIN_MULTIPLIER,
    MARGIN_COMMISSION_RATE, BTC_BORROW_RATE
)
from binance.client import Client
from binance.exceptions import BinanceAPIException
from core.logger import get_logger
import math

logger = get_logger()

# Initialize Binance client
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=USE_TESTNET)

def setup_margin_account(symbol):
    """Set up margin account for trading"""
    try:
        # Get margin account info
        margin_account = client.get_margin_account()
        
        # Check if margin is already enabled
        if not margin_account.get('marginEnabled'):
            logger.info("Enabling margin account...")
            client.enable_margin_account()
        
        # Set margin type (ISOLATED/CROSS)
        if MARGIN_TYPE == 'ISOLATED':
            client.set_isolated_margin_account(symbol=symbol, enabled=True)
        
        # Get margin pair info
        pair_info = client.get_margin_pair(symbol=symbol)
        max_leverage = float(pair_info['maxLeverage'])
        
        # Set leverage (within allowed range)
        requested_leverage = min(LEVERAGE, max_leverage)
        if MARGIN_TYPE == 'ISOLATED':
            client.set_margin_leverage(symbol=symbol, leverage=requested_leverage)
            
        logger.info(f"Margin account setup complete. Using {requested_leverage}x leverage with {MARGIN_TYPE} margin")
        return True
        
    except BinanceAPIException as e:
        logger.error(f"Error setting up margin account: {e}")
        return False

def get_margin_info(symbol):
    """Get margin account information for a symbol"""
    try:
        if MARGIN_TYPE == 'ISOLATED':
            info = client.get_isolated_margin_account(symbols=[symbol])
            asset = next((a for a in info['assets'] if a['symbol'] == symbol), None)
            if not asset:
                return None
            
            borrowed = float(asset['baseAsset']['borrowed']) + float(asset['quoteAsset']['borrowed'])
            free = float(asset['baseAsset']['free']) + float(asset['quoteAsset']['free'])
            total = float(asset['baseAsset']['totalAsset']) + float(asset['quoteAsset']['totalAsset'])
            
        else:  # CROSS margin
            info = client.get_margin_account()
            asset = next((a for a in info['userAssets'] if a['asset'] in symbol), None)
            if not asset:
                return None
                
            borrowed = float(asset['borrowed'])
            free = float(asset['free'])
            total = float(asset['totalAsset'])
            
        return {
            'borrowed': borrowed,
            'free': free,
            'total': total,
            'margin_ratio': borrowed / total if total > 0 else 0
        }
        
    except BinanceAPIException as e:
        logger.error(f"Error getting margin info: {e}")
        return None

def place_margin_order(symbol, side, quantity, price=None, order_type='MARKET'):
    """Place a margin order"""
    try:
        # Validate margin status
        margin_info = get_margin_info(symbol)
        if not margin_info:
            logger.error(f"Could not get margin info for {symbol}")
            return None
            
        # Check margin ratio
        if margin_info['margin_ratio'] >= MARGIN_MULTIPLIER:
            logger.error(f"Margin ratio too high: {margin_info['margin_ratio']:.2f}")
            return None
            
        # Calculate borrow amount needed
        price = price or float(client.get_symbol_ticker(symbol=symbol)['price'])
        borrow_amount = (quantity * price) / LEVERAGE
        
        # Check if we need to borrow
        if side == 'BUY':
            # Borrow quote asset (USDT)
            if margin_info['free'] < borrow_amount:
                logger.info(f"Borrowing {borrow_amount:.8f} USDT")
                client.create_margin_loan(asset='USDT', amount=borrow_amount)
        else:
            # Borrow base asset (BTC)
            if margin_info['free'] < quantity:
                logger.info(f"Borrowing {quantity:.8f} {symbol.replace('USDT', '')}")
                client.create_margin_loan(asset=symbol.replace('USDT', ''), amount=quantity)
                
        # Place the order
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        if price and order_type == 'LIMIT':
            params['price'] = format_price(price)
            params['timeInForce'] = 'GTC'
            
        if MARGIN_TYPE == 'ISOLATED':
            params['isIsolated'] = 'TRUE'
            order = client.create_margin_order(**params)
        else:
            order = client.create_margin_order(**params)
            
        logger.info(f"Margin {side} order placed: {order['orderId']}")
        return order
        
    except BinanceAPIException as e:
        logger.error(f"Error placing margin order: {e}")
        return None

def repay_margin_loan(symbol, asset, amount):
    """Repay borrowed margin"""
    try:
        if MARGIN_TYPE == 'ISOLATED':
            client.repay_margin_loan(asset=asset, amount=amount, isIsolated='TRUE', symbol=symbol)
        else:
            client.repay_margin_loan(asset=asset, amount=amount)
        logger.info(f"Repaid {amount} {asset} margin loan")
        return True
    except BinanceAPIException as e:
        logger.error(f"Error repaying margin loan: {e}")
        return False

def close_margin_position(symbol, position):
    """Close a margin position and repay loans"""
    try:
        # Get current position info
        margin_info = get_margin_info(symbol)
        if not margin_info:
            return False
            
        # Close the position
        if position.side == 'BUY':
            order = place_margin_order(symbol, 'SELL', position.quantity)
        else:
            order = place_margin_order(symbol, 'BUY', position.quantity)
            
        if not order:
            return False
            
        # Repay borrowed assets
        if position.side == 'BUY':
            # Repay borrowed USDT
            borrowed_usdt = margin_info['borrowed']
            if borrowed_usdt > 0:
                repay_margin_loan(symbol, 'USDT', borrowed_usdt)
        else:
            # Repay borrowed base asset
            borrowed_base = margin_info['borrowed']
            if borrowed_base > 0:
                repay_margin_loan(symbol, symbol.replace('USDT', ''), borrowed_base)
                
        return True
        
    except Exception as e:
        logger.error(f"Error closing margin position: {e}")
        return False