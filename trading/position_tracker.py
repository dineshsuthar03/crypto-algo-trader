import redis
import threading
import time
from datetime import datetime
from core.config import (
    REDIS_HOST, REDIS_PORT, REFRESH_INTERVAL,
    TARGET_PERCENT, STOPLOSS_PERCENT, MAX_HOLD_TIME_SEC
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
        
    def __repr__(self):
        return f"Position({self.symbol}, {self.side}, Entry: {self.entry_price}, Qty: {self.quantity})"


class PositionTracker:
    def __init__(self):
        self.positions = []
        self.lock = threading.Lock()
    
    def open_position(self, symbol, side, price, market_type, strategy="Breakout", quantity=0, entry_fee=0):
        """Open a new position"""
        pos = Position(symbol, side, price, market_type, strategy, quantity, entry_fee)
        
        with self.lock:
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
                
                # Check exit conditions
                exit_reason = None
                
                if pnl_percent >= TARGET_PERCENT:
                    exit_reason = "TARGET"
                    logger.info(f"🎯 Target hit! {pos.symbol} | PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT)")
                    
                elif pnl_percent <= -STOPLOSS_PERCENT:
                    exit_reason = "STOPLOSS"
                    logger.warning(f" Stoploss hit! {pos.symbol} | PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT)")
                    
                elif elapsed >= MAX_HOLD_TIME_SEC:
                    exit_reason = "TIME_EXIT"
                    logger.info(f"⏰ Time exit! {pos.symbol} | PnL: {pnl_percent:.2f}% ({pnl_usdt:.2f} USDT)")
                
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
            
        pos.closed = True
        pos.exit_price = exit_price
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
    
    def get_open_positions(self, symbol=None):
        """Get all open positions, optionally filtered by symbol"""
        with self.lock:
            if symbol:
                return [p for p in self.positions if not p.closed and p.symbol == symbol]
            return [p for p in self.positions if not p.closed]
    
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