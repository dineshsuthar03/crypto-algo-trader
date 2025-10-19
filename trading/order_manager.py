# TODO: Implement this module
from datetime import datetime
from trading.position_tracker import PositionTracker

# Initialize global position tracker
tracker = PositionTracker()

def place_order(symbol, side, price):
    """
    Mock order placement
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {side.upper()} ORDER | {symbol} @ {price}")
    tracker.open_position(symbol, side, price)
