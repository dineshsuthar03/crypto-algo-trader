from trading.margin_manager import (
    setup_margin_account, 
    get_margin_info,
    place_margin_order,
    close_margin_position
)
from core.config import (
    MARGIN_TYPE,
    LEVERAGE,
    MARGIN_MULTIPLIER,
    MARGIN_BORROW_LIMIT
)
from core.logger import get_logger

logger = get_logger()

class MarginStrategyHandler:
    def __init__(self, symbol):
        self.symbol = symbol
        self.setup_complete = False
        
    def initialize(self):
        """Initialize margin trading for the symbol"""
        self.setup_complete = setup_margin_account(self.symbol)
        return self.setup_complete
        
    def check_margin_status(self):
        """Check margin account status and limits"""
        if not self.setup_complete:
            return False
            
        margin_info = get_margin_info(self.symbol)
        if not margin_info:
            return False
            
        # Check margin ratio
        if margin_info['margin_ratio'] >= MARGIN_BORROW_LIMIT:
            logger.warning(f"Margin ratio ({margin_info['margin_ratio']:.2f}) exceeds limit {MARGIN_BORROW_LIMIT}")
            return False
            
        return True
        
    def execute_margin_trade(self, signal, price=None):
        """Execute a margin trade based on strategy signal"""
        if not self.check_margin_status():
            return None
            
        # Place the margin order
        order = place_margin_order(
            symbol=self.symbol,
            side=signal.side,
            quantity=signal.quantity,
            price=price,
            order_type='MARKET' if price is None else 'LIMIT'
        )
        
        if order:
            logger.info(f"Margin {signal.side} order executed: {order['orderId']}")
        
        return order
        
    def close_position(self, position):
        """Close an open margin position"""
        return close_margin_position(self.symbol, position)