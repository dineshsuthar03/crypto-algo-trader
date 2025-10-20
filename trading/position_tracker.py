import redis
import threading
import time
from datetime import datetime
from core.config import (
    REDIS_HOST, REDIS_PORT, REFRESH_INTERVAL,
    TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC,
    EXIT_STRATEGY_SIGNAL_PRIORITY, EXIT_TARGET_PRIORITY,
    EXIT_STOPLOSS_PRIORITY, EXIT_TIME_PRIORITY,
    EXIT_STRATEGY_SIGNAL_ENABLE, EXIT_TARGET_ENABLE,
    EXIT_STOPLOSS_ENABLE, EXIT_TIME_ENABLE
)
from trading.order_utils import calculate_pnl, format_price
from storage.mongo_handler import log_trade
from core.logger import get_logger

logger = get_logger()
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


class Position:
    def __init__(self, symbol, side, entry_price, market_type, strategy, quantity, entry_fee):
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.market_type = market_type
        self.strategy = strategy
        self.quantity = quantity
        self.entry_fee = entry_fee
        self.open_time = datetime.now()
        self.closed = False
        self.exit_price = None
        self.exit_fee = None
        self.pnl_usdt = None
        self.pnl_percent = None
        
        # Trade management
        from trading.trade_manager import TradeManager
        self.trade_manager = TradeManager(
            initial_price=entry_price,
            side=side
        )
        self.current_stop = None
        self.current_target = None
        
    def __repr__(self):
        return f"Position({self.symbol}, {self.side}, Entry: {self.entry_price}, Qty: {self.quantity})"


class PositionTracker:
    def __init__(self):
        self.positions = []
        self.lock = threading.Lock()
    
    def open_position(self, symbol, side, price, market_type, strategy="Breakout", quantity=0, entry_fee=0):
        """Open a new position"""
        with self.lock:
            # For spot trading, validate position state
            if market_type == "spot":
                open_positions = [p for p in self.positions if p.symbol == symbol and not p.closed]
                if side.upper() == "BUY" and open_positions:
                    logger.warning(f"Already have open position for {symbol}. Cannot open new BUY position.")
                    return None
                elif side.upper() == "SELL":
                    buy_positions = [p for p in open_positions if p.side.upper() == "BUY"]
                    if not buy_positions:
                        logger.warning(f"No BUY position found for {symbol}. Cannot place SELL order.")
                        return None

            pos = Position(symbol, side, price, market_type, strategy, quantity, entry_fee)
            self.positions.append(pos)
            
            logger.info(f" Position opened: {pos}")
            
            # Start monitoring in separate thread
            t = threading.Thread(target=self.monitor_position, args=(pos,))
            t.daemon = True
            t.start()
            
            return pos
    
    def monitor_position(self, pos):
        """Monitor position for exit conditions"""
        logger.info(f" Monitoring {pos.symbol} position...")
        
        while not pos.closed:
            try:
                # Get latest price from Redis
                ltp_bytes = r.get(f"LTP:{pos.symbol}")
                if ltp_bytes is None:
                    time.sleep(REFRESH_INTERVAL)
                    continue
                
                live_price = float(ltp_bytes)
                
                # Calculate PnL with fees
                pnl_usdt, pnl_percent, total_fees = calculate_pnl(
                    pos.entry_price,
                    live_price,
                    pos.quantity,
                    pos.side,
                    pos.market_type
                )
                
                elapsed = (datetime.now() - pos.open_time).seconds
                
                # Get OHLC data from Redis for ATR calculation
                ohlc_key = f"OHLC:{pos.symbol}"
                ohlc_data = r.hgetall(ohlc_key)
                if ohlc_data:
                    current_high = float(ohlc_data.get(b'high', live_price))
                    current_low = float(ohlc_data.get(b'low', live_price))
                else:
                    current_high = current_low = live_price
                
                # Update trade management levels
                stop_level, target_level = pos.trade_manager.calculate_dynamic_levels(
                    live_price, current_high, current_low
                )
                pos.current_stop = stop_level
                pos.current_target = target_level
                
                # Check dynamic exit conditions
                should_exit, dynamic_reason = pos.trade_manager.should_exit(live_price)
                
                # Initialize exit reason as None
                exit_reason = dynamic_reason if should_exit else None
                exit_conditions = []
                
                # Log current levels every 10 seconds
                if elapsed % 10 == 0:
                    logger.debug(
                        f"Position: {pos.symbol} | "
                        f"Entry: {pos.entry_price:.8f} | "
                        f"Current: {live_price:.8f} | "
                        f"Stop: {stop_level:.8f} | "
                        f"Target: {target_level:.8f} | "
                        f"PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT) | "
                        f"Time: {elapsed}s"
                    )
                
                try:
                    # 1. Check strategy signal
                    if EXIT_STRATEGY_SIGNAL_ENABLE:
                        signal_key = f"SIGNAL:{pos.symbol}:{pos.strategy}"
                        signal_bytes = r.get(signal_key)
                        if signal_bytes and signal_bytes.decode() == "SELL" and pos.side.upper() == "BUY":
                            exit_conditions.append({
                                'reason': "STRATEGY_SIGNAL",
                                'priority': EXIT_STRATEGY_SIGNAL_PRIORITY,
                                'message': f"Strategy SELL signal! {pos.symbol} | PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT)"
                            })
                    
                    # 2. Check target
                    if EXIT_TARGET_ENABLE and pnl_percent >= TARGET_PERCENT:
                        exit_conditions.append({
                            'reason': "TARGET",
                            'priority': EXIT_TARGET_PRIORITY,
                            'message': f"🎯 Target hit! {pos.symbol} | PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT)"
                        })
                    
                    # 3. Check stop loss
                    if EXIT_STOPLOSS_ENABLE and pnl_percent <= -STOPLOSS_PERCENT:
                        exit_conditions.append({
                            'reason': "STOPLOSS",
                            'priority': EXIT_STOPLOSS_PRIORITY,
                            'message': f"Stop loss hit! {pos.symbol} | PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT)"
                        })
                    
                    # 4. Check time exit
                    if EXIT_TIME_ENABLE and elapsed >= MAX_HOLD_TIME_SEC:
                        exit_conditions.append({
                            'reason': "TIME_EXIT",
                            'priority': EXIT_TIME_PRIORITY,
                            'message': f"Time exit! {pos.symbol} | PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT)"
                        })
                    
                    # Sort by priority and take the highest priority exit condition
                    if exit_conditions:
                        exit_conditions.sort(key=lambda x: x['priority'])
                        chosen_exit = exit_conditions[0]
                        exit_reason = chosen_exit['reason']
                        logger.info(chosen_exit['message'])
                
                except Exception as e:
                    logger.error(f"Error checking exit conditions: {str(e)}", exc_info=True)
                    # Keep exit_reason as None if there's an error
                
                # Exit position if condition met
                if exit_reason:
                    self.close_position(pos, live_price, exit_reason, pnl_usdt, pnl_percent, total_fees)
                    break
                
                # Log position status periodically (every 10 seconds)
                if elapsed % 10 == 0:
                    logger.debug(
                        f"Position: {pos.symbol} | "
                        f"Entry: {pos.entry_price:.8f} | "
                        f"Current: {live_price:.8f} | "
                        f"PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT) | "
                        f"Time: {elapsed}s"
                    )
                
            except Exception as e:
                logger.error(f"Error monitoring position {pos.symbol}: {str(e)}", exc_info=True)
            
            time.sleep(REFRESH_INTERVAL)
    
    def close_position(self, pos, exit_price, reason, pnl_usdt, pnl_percent, total_fees):
        """Close position and log to database"""
        
        # Skip if already closed
        if pos.closed:
            return
            
        # For spot trading, execute the SELL order first
        if pos.market_type == "spot" and pos.side.upper() == "BUY":
            try:
                # Import here to avoid circular import
                from trading.order_manager import place_exchange_order
                
                # Place market SELL order
                sell_response = place_exchange_order(
                    symbol=pos.symbol,
                    side="SELL",
                    quantity=pos.quantity,
                    price=exit_price,
                    market_type="spot"
                )
                logger.info(f"SELL order executed: {sell_response['orderId']}")
                
                # Update exit price from actual execution
                if 'fills' in sell_response:
                    total_qty = sum(float(fill['qty']) for fill in sell_response['fills'])
                    total_price = sum(float(fill['price']) * float(fill['qty']) for fill in sell_response['fills'])
                    exit_price = total_price / total_qty if total_qty > 0 else exit_price
            except Exception as e:
                logger.error(f"Failed to execute SELL order: {str(e)}")
                # Continue with position closing even if order fails
        
        pos.closed = True
        pos.exit_price = exit_price
        
        # Account for fees in final PnL calculation
        if pos.market_type == "spot":
            # For spot trading, both entry and exit have fees
            total_fees = (pos.entry_fee or 0) + (total_fees or 0)
            # Adjust PnL for total fees
            pnl_usdt = pnl_usdt - total_fees
            # Recalculate percentage including fees
            initial_value = pos.quantity * pos.entry_price
            pnl_percent = (pnl_usdt / initial_value) * 100 if initial_value > 0 else 0
            
        pos.pnl_usdt = pnl_usdt
        pos.pnl_percent = pnl_percent
        
        logger.info(
            f"{'=' * 60}\n"
            f" POSITION CLOSED\n"
            f"Symbol: {pos.symbol}\n"
            f"Strategy: {pos.strategy}\n"
            f"Side: {pos.side.upper()}\n"
            f"Entry Price: {pos.entry_price:.8f}\n"
            f"Exit Price: {exit_price:.8f}\n"
            f"Quantity: {pos.quantity}\n"
            f"Entry Fee: {pos.entry_fee:.4f} USDT\n"
            f"Total Fees: {total_fees:.4f} USDT\n"
            f"PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT)\n"
            f"Duration: {(datetime.now() - pos.open_time).seconds}s\n"
            f"Reason: {reason}\n"
            f"{'=' * 60}"
        )
        
        # Log to MongoDB
        trade_data = {
            "symbol": pos.symbol,
            "market_type": pos.market_type,
            "strategy": pos.strategy,
            "side": pos.side.upper(),
            "entry_price": pos.entry_price,
            "exit_price": exit_price,
            "quantity": pos.quantity,
            "entry_time": pos.open_time,
            "exit_time": datetime.now(),
            "entry_fee": pos.entry_fee,
            "total_fees": total_fees,
            "pnl_usdt": pnl_usdt,
            "pnl_percent": pnl_percent,
            "reason": reason,
            "duration_seconds": (datetime.now() - pos.open_time).seconds
        }
        
        try:
            log_trade(trade_data)
            logger.info("Trade logged to MongoDB")
        except Exception as e:
            logger.error(f"Error logging trade to MongoDB: {str(e)}")
    
    def get_open_positions(self, symbol=None, side=None):
        """Get all open positions, optionally filtered by symbol and side"""
        with self.lock:
            positions = [p for p in self.positions if not p.closed]
            if symbol:
                positions = [p for p in positions if p.symbol == symbol]
            if side:
                positions = [p for p in positions if p.side.upper() == side.upper()]
            return positions
            
    def cleanup_duplicate_positions(self):
        """Clean up any duplicate open positions"""
        with self.lock:
            # Group open positions by symbol
            symbol_positions = {}
            for pos in self.positions:
                if not pos.closed:
                    if pos.symbol not in symbol_positions:
                        symbol_positions[pos.symbol] = []
                    symbol_positions[pos.symbol].append(pos)
            
            # Keep only the most recent position if duplicates exist
            for symbol, positions in symbol_positions.items():
                if len(positions) > 1:
                    logger.warning(f"Found {len(positions)} open positions for {symbol}. Cleaning up duplicates.")
                    # Sort by open time, newest first
                    positions.sort(key=lambda x: x.open_time, reverse=True)
                    # Close all but the most recent
                    for pos in positions[1:]:
                        pos.closed = True
                        logger.info(f"Closed duplicate position: {pos}")
    
    def get_position_summary(self):
        """Get summary of all positions"""
        open_pos = self.get_open_positions()
        closed_pos = [p for p in self.positions if p.closed]
        
        total_pnl = sum(p.pnl_usdt for p in closed_pos if p.pnl_usdt is not None)
        
        return {
            "total_positions": len(self.positions),
            "open_positions": len(open_pos),
            "closed_positions": len(closed_pos),
            "total_pnl_usdt": total_pnl,
            "positions": self.positions
        }


# Global tracker instance
tracker = PositionTracker()