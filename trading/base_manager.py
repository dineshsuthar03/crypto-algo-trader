from core.logger import get_logger
from binance.exceptions import BinanceAPIException
from functools import wraps
import time

logger = get_logger()

def retry_on_error(max_retries=3, delay=1):
    """Decorator to retry operations on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except BinanceAPIException as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Final retry failed for {func.__name__}: {e}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class BaseTradeManager:
    """Base class for all trade managers with common functionality"""
    
    def __init__(self, client, symbol):
        self.client = client
        self.symbol = symbol
        self.order_history = []
        self.position_history = []
        self.initialized = False
        
    def log_order(self, order):
        """Log order details"""
        if order:
            self.order_history.append({
                'orderId': order.get('orderId'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'type': order.get('type'),
                'quantity': order.get('origQty'),
                'price': order.get('price'),
                'status': order.get('status'),
                'timestamp': order.get('time')
            })
            
    def log_position(self, position):
        """Log position details"""
        self.position_history.append({
            'symbol': position.symbol,
            'side': position.side,
            'entry_price': position.entry_price,
            'quantity': position.quantity,
            'pnl': position.realized_pnl if hasattr(position, 'realized_pnl') else None,
            'timestamp': int(time.time() * 1000)
        })
        
    def validate_symbol(self):
        """Check if symbol is valid and has sufficient liquidity"""
        ticker = self.client.get_ticker(symbol=self.symbol)
        volume = float(ticker['volume']) * float(ticker['lastPrice'])
        if volume < 1000000:  # $1M daily volume minimum
            logger.warning(f"Low liquidity for {self.symbol}: ${volume:,.2f} 24h volume")
            return False
        return True
        
    def check_maintenance(self):
        """Check for exchange maintenance"""
        try:
            system_status = self.client.get_system_status()
            if system_status['status'] != 0:
                logger.warning("Exchange under maintenance")
                return False
            return True
        except:
            return False
            
    def get_wallet_balance(self, asset):
        """Get wallet balance for an asset"""
        account = self.client.get_account()
        balance = next((b for b in account['balances'] 
                       if b['asset'] == asset), None)
        return float(balance['free']) if balance else 0.0
        
    def calculate_fees(self, order):
        """Calculate fees for an order"""
        quantity = float(order['origQty'])
        price = float(order['price'])
        commission_asset = order.get('commissionAsset', self.symbol.replace('USDT', ''))
        
        if commission_asset == 'BNB':
            bnb_price = float(self.client.get_symbol_ticker(symbol='BNBUSDT')['price'])
            return float(order['commission']) * bnb_price
        elif commission_asset == 'USDT':
            return float(order['commission'])
        else:
            return float(order['commission']) * price
            
    def get_trade_history(self, limit=100):
        """Get recent trade history"""
        return self.client.get_my_trades(symbol=self.symbol, limit=limit)
        
    def get_order_book_imbalance(self, depth=10):
        """Calculate order book imbalance"""
        book = self.client.get_order_book(symbol=self.symbol, limit=depth)
        
        bid_volume = sum(float(bid[1]) for bid in book['bids'])
        ask_volume = sum(float(ask[1]) for ask in book['asks'])
        
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return 0
            
        return (bid_volume - ask_volume) / total_volume
        
    def get_funding_payment_time(self):
        """Get time until next funding payment (futures/margin)"""
        funding_info = self.client.get_funding_info(symbol=self.symbol)
        next_payment = int(funding_info['nextFundingTime'])
        current_time = int(time.time() * 1000)
        return (next_payment - current_time) / 1000  # seconds until payment
        
    def cleanup(self):
        """Cleanup resources"""
        self.initialized = False
        logger.info(f"Cleaned up {self.__class__.__name__} for {self.symbol}")
        
    def __str__(self):
        """String representation"""
        return f"{self.__class__.__name__}(symbol={self.symbol}, initialized={self.initialized})"