from core.config import (
    TRADE_AMOUNT_USDT, MIN_NOTIONAL, SPOT_COMMISSION_RATE,
    FUTURES_COMMISSION_RATE, PRICE_PRECISION, QUANTITY_PRECISION
)
from core.logger import get_logger

logger = get_logger()


def round_step_size(quantity, step_size=1.0):
    """Round quantity to match exchange step size"""
    if step_size >= 1:
        return int(quantity)
    precision = len(str(step_size).rstrip('0').split('.')[-1])
    return round(quantity, precision)


def calculate_quantity(symbol, price, market_type="spot", trade_amount=None, side="BUY"):
    """
    Calculate proper quantity for order considering:
    - Minimum notional value
    - Transaction fees
    - Symbol precision
    - Trading side (BUY/SELL)
    
    Returns: (quantity, notional_value, estimated_fee)
    """
    if trade_amount is None:
        trade_amount = TRADE_AMOUNT_USDT
    
    # Get commission rate
    commission_rate = SPOT_COMMISSION_RATE if market_type == "spot" else FUTURES_COMMISSION_RATE
    
    # Calculate base quantity (before fees)
    base_quantity = trade_amount / price
    
    # For spot SELL orders, reduce quantity to account for fees
    if market_type == "spot" and side.upper() == "SELL":
        fee_reduction = commission_rate * 1.1  # Add 10% margin for safety
        base_quantity = base_quantity * (1 - fee_reduction)
    
    # Calculate quantity precision
    qty_precision = QUANTITY_PRECISION.get(symbol, 3)
    
    # Round quantity
    if qty_precision == 0:
        quantity = int(base_quantity)
    else:
        quantity = round(base_quantity, qty_precision)
    
    # Calculate notional value
    notional = quantity * price
    
    # Calculate estimated fee (for buying)
    estimated_fee = notional * commission_rate
    
    # Check minimum notional
    if notional < MIN_NOTIONAL:
        logger.warning(f"Notional {notional:.2f} < MIN_NOTIONAL {MIN_NOTIONAL} for {symbol}")
        # Adjust quantity to meet minimum
        quantity = (MIN_NOTIONAL / price) * 1.01  # Add 1% buffer
        if qty_precision == 0:
            quantity = int(quantity) + 1
        else:
            quantity = round(quantity, qty_precision)
        notional = quantity * price
        estimated_fee = notional * commission_rate
    
    logger.info(f"Order Calc | {symbol} | Price: {price} | Qty: {quantity} | Notional: {notional:.2f} USDT | Fee: {estimated_fee:.4f} USDT")
    
    return quantity, notional, estimated_fee


def calculate_pnl(entry_price, exit_price, quantity, side, market_type="spot"):
    """
    Calculate PnL considering transaction fees for both entry and exit
    
    Returns: (pnl_usdt, pnl_percent, total_fees)
    """
    commission_rate = SPOT_COMMISSION_RATE if market_type == "spot" else FUTURES_COMMISSION_RATE
    
    # Entry cost
    entry_cost = quantity * entry_price
    entry_fee = entry_cost * commission_rate
    
    # Exit value
    exit_value = quantity * exit_price
    exit_fee = exit_value * commission_rate
    
    # Calculate PnL based on side
    if side.upper() == "BUY":
        # Long position: profit when price goes up
        pnl_usdt = (exit_value - entry_cost) - (entry_fee + exit_fee)
    else:
        # Short position: profit when price goes down
        pnl_usdt = (entry_cost - exit_value) - (entry_fee + exit_fee)
    
    # PnL percentage (relative to entry cost including fees)
    total_invested = entry_cost + entry_fee
    pnl_percent = (pnl_usdt / total_invested) * 100
    
    total_fees = entry_fee + exit_fee
    
    return pnl_usdt, pnl_percent, total_fees


def format_price(symbol, price):
    """Format price according to symbol precision"""
    precision = PRICE_PRECISION.get(symbol, 2)
    return round(price, precision)


def validate_order(symbol, quantity, price, market_type="spot"):
    """
    Validate order before placing
    Returns: (is_valid, error_message)
    """
    notional = quantity * price
    
    if notional < MIN_NOTIONAL:
        return False, f"Notional {notional:.2f} < minimum {MIN_NOTIONAL}"
    
    if quantity <= 0:
        return False, "Invalid quantity"
    
    if price <= 0:
        return False, "Invalid price"
    
    return True, None