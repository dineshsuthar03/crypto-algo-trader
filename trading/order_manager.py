from trading.position_tracker import tracker
from trading.order_utils import calculate_quantity, validate_order, format_price
from core.config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET,
    MAX_POSITIONS_PER_SYMBOL
)
from binance.client import Client
from binance.exceptions import BinanceAPIException
from core.logger import get_logger

logger = get_logger()

# Initialize Binance client
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=USE_TESTNET)


def get_symbol_info(symbol, market_type="spot"):
    """Get symbol trading rules from exchange"""
    try:
        if market_type == "spot":
            info = client.get_symbol_info(symbol)
        else:
            info = client.futures_exchange_info()
            info = next((s for s in info['symbols'] if s['symbol'] == symbol), None)
        return info
    except Exception as e:
        logger.error(f"Error getting symbol info: {e}")
        return None


def place_order(symbol, side, price, market_type, strategy="Breakout"):
    """
    Place order with proper quantity calculation and fee handling
    """
    
    # Check position limits and spot trading rules
    open_positions = [p for p in tracker.positions if p.symbol == symbol and not p.closed]
    
    if market_type == "spot":
        # For spot trading:
        # - BUY is allowed only if we have no open positions
        # - SELL is allowed only if we have a BUY position
        if side.upper() == "BUY" and len(open_positions) > 0:
            logger.warning(f"Already have an open position for {symbol}. Skipping BUY order.")
            return None
        elif side.upper() == "SELL":
            # Check if we have a BUY position to sell
            buy_positions = [p for p in open_positions if p.side.upper() == "BUY"]
            if not buy_positions:
                logger.warning(f"No BUY position found for {symbol}. Cannot place SELL order in spot trading.")
                return None
    else:
        # For futures trading, use standard position limit
        if len(open_positions) >= MAX_POSITIONS_PER_SYMBOL:
            logger.warning(f"Max positions reached for {symbol}. Skipping order.")
            return None
    
    try:
        # Calculate proper quantity
        quantity, notional, estimated_fee = calculate_quantity(symbol, price, market_type)
        
        # Validate order
        is_valid, error_msg = validate_order(symbol, quantity, price, market_type)
        if not is_valid:
            logger.error(f"Order validation failed: {error_msg}")
            return None
        
        logger.info(f"Placing {market_type.upper()} {side.upper()} order | {symbol} @ {price}")
        logger.info(f"Quantity: {quantity} | Notional: {notional:.2f} USDT | Est. Fee: {estimated_fee:.4f} USDT")
        
        # Open position in tracker first
        tracker.open_position(symbol, side, price, market_type, strategy, quantity, estimated_fee)
        
        # Place actual order on exchange
        if market_type == "spot":
            try:
                # For spot trading, ensure quantity precision matches exchange rules
                info = get_symbol_info(symbol, "spot")
                if info:
                    lot_size_filter = next(f for f in info['filters'] if f['filterType'] == 'LOT_SIZE')
                    step_size = float(lot_size_filter['stepSize'])
                    
                    if side.upper() == "SELL":
                        # For selling, reduce quantity to account for fees
                        # Binance spot fee is typically 0.1% (0.001)
                        fee_adjustment = 0.001  # SPOT_COMMISSION_RATE from config
                        quantity = float(quantity) * (1 - fee_adjustment)  # Reduce quantity by fee percentage
                    
                    # Round quantity to valid step size
                    quantity = float(quantity)
                    quantity = round(quantity - (quantity % step_size), len(str(step_size).split('.')[1]))
                
                order = client.create_order(
                    symbol=symbol,
                    side=side.upper(),
                    type="MARKET",
                    quantity=quantity
                )
            except BinanceAPIException as e:
                if "insufficient balance" in str(e).lower():
                    logger.error(f"Insufficient balance for {side} order. Required quantity: {quantity}")
                    # Remove position from tracker if it was a failed order
                    if side.upper() == "BUY":
                        tracker.positions.pop()  # Remove last added position
                raise
        else:
            # For futures
            order = client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type="MARKET",
                quantity=quantity
            )
        
        logger.info(f" Order executed | OrderId: {order.get('orderId')} | Status: {order.get('status')}")
        
        # Update position with actual fill price if available
        fills = order.get('fills', [])
        if fills:
            avg_price = sum(float(f['price']) * float(f['qty']) for f in fills) / sum(float(f['qty']) for f in fills)
            actual_fee = sum(float(f['commission']) for f in fills)
            logger.info(f"Avg Fill Price: {avg_price:.8f} | Actual Fee: {actual_fee:.8f}")
        
        return order
        
    except BinanceAPIException as e:
        logger.error(f"Binance API Error: {e.status_code} - {e.message}")
        return None
    except Exception as e:
        logger.error(f"Order placement error: {str(e)}", exc_info=True)
        return None


def close_position(position, exit_price, reason):
    """
    Close position with market order
    """
    try:
        symbol = position.symbol
        quantity = position.quantity
        market_type = position.market_type
        
        # Determine close side (opposite of entry)
        close_side = "SELL" if position.side.upper() == "BUY" else "BUY"
        
        logger.info(f"Closing position | {symbol} | {close_side} {quantity} @ {exit_price}")
        
        # Place closing order
        if market_type == "spot":
            order = client.create_order(
                symbol=symbol,
                side=close_side,
                type="MARKET",
                quantity=quantity
            )
        else:
            order = client.futures_create_order(
                symbol=symbol,
                side=close_side,
                type="MARKET",
                quantity=quantity
            )
        
        logger.info(f" Position closed | Reason: {reason} | OrderId: {order.get('orderId')}")
        return order
        
    except Exception as e:
        logger.error(f"Error closing position: {str(e)}", exc_info=True)
        return None