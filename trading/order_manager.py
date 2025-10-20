from trading.position_tracker import tracker
from trading.order_utils import calculate_quantity, validate_order, format_price
from core.config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, USE_TESTNET,
    MAX_POSITIONS_PER_SYMBOL, SPOT_COMMISSION_RATE,
    FUTURES_COMMISSION_RATE
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


def round_step_size(quantity, step_size):
    """Round quantity to step size"""
    precision = len(str(step_size).rstrip('0').split('.')[-1])
    return float(int(quantity * (10 ** precision)) / (10 ** precision))


def place_exchange_order(symbol, side, quantity, price, market_type):
    """Place the actual order on the exchange"""
    try:
        formatted_price = format_price(symbol, price)
        
        # Get symbol info for lot size
        symbol_info = get_symbol_info(symbol, market_type)
        if not symbol_info:
            raise ValueError(f"Could not get symbol info for {symbol}")
            
        # Find LOT_SIZE filter
        lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
        if not lot_size_filter:
            raise ValueError(f"Could not find LOT_SIZE filter for {symbol}")
            
        # Round quantity to valid lot size
        step_size = float(lot_size_filter['stepSize'])
        rounded_quantity = round_step_size(float(quantity), step_size)
        
        logger.debug(f"Original quantity: {quantity}, Rounded to lot size: {rounded_quantity} "
                    f"(step size: {step_size})")
        
        if market_type == "spot":
            # Format quantity to avoid scientific notation
            formatted_quantity = "{:.8f}".format(rounded_quantity).rstrip('0').rstrip('.')
            response = client.create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=formatted_quantity
            )
        else:
            response = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity
            )
        
        logger.info(f"Order placed successfully: {response['orderId']}")
        return response
        
    except BinanceAPIException as e:
        logger.error(f"Failed to place order on exchange: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error placing order: {e}")
        raise


def place_order(symbol, side, price, market_type, strategy="Breakout"):
    """
    Place order with proper quantity calculation and fee handling
    """
    try:
        logger.info(f"Attempting to place {market_type} {side} order for {symbol}")
        logger.debug(f"Order parameters - Price: {price}, Strategy: {strategy}")
        
        # Input validation
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"Invalid symbol: {symbol}")
        if side.upper() not in ["BUY", "SELL"]:
            raise ValueError(f"Invalid side: {side}")
        if not price or float(price) <= 0:
            raise ValueError(f"Invalid price: {price}")
        if market_type not in ["spot", "futures"]:
            raise ValueError(f"Invalid market type: {market_type}")
        
        # Check position limits and spot trading rules
        open_positions = [p for p in tracker.positions if p.symbol == symbol and not p.closed]
        logger.debug(f"Current open positions for {symbol}: {len(open_positions)}")
        
        # Initialize quantity and notional
        quantity = None
        notional = None
        estimated_fee = None
        
        if market_type == "spot":
            # For spot trading:
            if side.upper() == "BUY":
                if len(open_positions) > 0:
                    logger.warning(f"Already have an open position for {symbol}. Skipping BUY order.")
                    return None
            elif side.upper() == "SELL":
                # Find matching BUY position
                buy_positions = [p for p in open_positions if p.side.upper() == "BUY"]
                if not buy_positions:
                    logger.warning(f"No BUY position found for {symbol}. Cannot place SELL order in spot trading.")
                    return None
                    
                # Get quantity from BUY position
                buy_pos = buy_positions[0]
                available_quantity = buy_pos.quantity
                
                # Calculate safe sell quantity with buffer
                fee_rate = SPOT_COMMISSION_RATE
                buffer_percent = 0.001  # 0.1% additional buffer for safety
                total_reduction = fee_rate + buffer_percent
                
                # Get symbol info for lot size
                symbol_info = get_symbol_info(symbol, market_type)
                if not symbol_info:
                    raise ValueError(f"Could not get symbol info for {symbol}")
                    
                # Find LOT_SIZE filter
                lot_size_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
                if not lot_size_filter:
                    raise ValueError(f"Could not find LOT_SIZE filter for {symbol}")
                
                # Calculate and round quantity
                raw_quantity = available_quantity * (1 - total_reduction)
                step_size = float(lot_size_filter['stepSize'])
                quantity = round_step_size(float(raw_quantity), step_size)
                
                # Recalculate notional and fee after rounding
                notional = float(quantity) * float(price)
                estimated_fee = notional * fee_rate
                
                logger.info(f"Original quantity: {available_quantity}")
                logger.info(f"After fee+buffer reduction: {raw_quantity:.8f} -> Rounded: {quantity:.8f}")
                logger.info(f"Fee rate: {fee_rate*100:.3f}%, Buffer: {buffer_percent*100:.3f}%")
        else:
            # For futures trading, use standard position limit
            if len(open_positions) >= MAX_POSITIONS_PER_SYMBOL:
                logger.warning(f"Max positions reached for {symbol}. Skipping order.")
                return None
        
        # Calculate proper quantity only if not already set (for SELL orders in spot)
        if quantity is None:
            logger.debug(f"Calculating quantity for {side} order...")
            # For BUY orders, use normal calculation
            quantity, notional, estimated_fee = calculate_quantity(symbol, price, market_type=market_type, side=side)
            logger.info(f"Calculated order details - Quantity: {quantity:.8f}, "
                       f"Notional: {notional:.4f} USDT, Est. Fee: {estimated_fee:.4f} USDT")
        
        # Validate order
        logger.debug("Validating order parameters...")
        is_valid, error_msg = validate_order(symbol, quantity, price, market_type)
        if not is_valid:
            logger.error(f"Order validation failed: {error_msg}")
            return None
        
        # Place the actual order on the exchange
        response = place_exchange_order(symbol, side, quantity, price, market_type)
        
        # Track the position if order was successful
        if response:
            tracker.open_position(symbol, side, price, market_type, strategy, quantity, estimated_fee)
            logger.info(f"Position tracked successfully: {symbol} {side}")
        
        return response
        
    except ValueError as e:
        logger.error(f"Invalid order parameters: {str(e)}")
        raise
    except BinanceAPIException as e:
        logger.error(f"Binance API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in order placement: {str(e)}")
        raise