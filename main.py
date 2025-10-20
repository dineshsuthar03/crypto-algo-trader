import threading
import time
import signal
import sys
from datetime import datetime

from data_feed import live_feed, candle_store
from strategy.strategy_engine import StrategyEngine
from trading import order_manager
from trading.position_tracker import tracker
from core.config import SYMBOLS, MARKET_TYPES
from core.logger import get_logger

logger = get_logger()

# Global flag for graceful shutdown
shutdown_flag = threading.Event()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("\n Shutdown signal received. Closing positions and exiting...")
    shutdown_flag.set()
    
    # Give time for threads to finish
    time.sleep(2)
    
    # Print final summary
    summary = tracker.get_position_summary()
    logger.info(f"\n{'=' * 60}")
    logger.info(f" FINAL SUMMARY")
    logger.info(f"Total Positions: {summary['total_positions']}")
    logger.info(f"Open Positions: {summary['open_positions']}")
    logger.info(f"Closed Positions: {summary['closed_positions']}")
    logger.info(f"Total PnL: {summary['total_pnl_usdt']:.2f} USDT")
    logger.info(f"{'=' * 60}\n")
    
    sys.exit(0)


def strategy_loop():
    """Main strategy execution loop"""
    last_signal_times = {sym: None for sym in SYMBOLS}
    cooldown_until = {sym: None for sym in SYMBOLS}
    
    logger.info(" Strategy loop started")
    
    while not shutdown_flag.is_set():
        try:
            # Get signals from strategy engine
            signals = engine.run()
            
            for (sym, strat_name), sig in signals.items():
                # Check cooldown
                if cooldown_until[sym] and datetime.now() < cooldown_until[sym]:
                    continue
                
                # Get latest candle
                candle = candle_store.get_last_candle(sym)
                if not candle:
                    continue
                
                # Only process if it's a new candle
                if last_signal_times[sym] == candle['timestamp']:
                    continue
                
                last_signal_times[sym] = candle['timestamp']
                
                # Check for valid signal
                if sig in ["BUY", "SELL"]:
                    price = candle['close']
                    mtype = MARKET_TYPES[SYMBOLS.index(sym)]
                    
                    logger.info(f" Signal: {sig} | {sym} | Price: {price:.8f} | Strategy: {strat_name}")
                    
                    # Place order
                    order = order_manager.place_order(sym, sig, price, mtype, strategy=strat_name)
                    
                    if order:
                        # Set cooldown (60 seconds after order)
                        cooldown_until[sym] = datetime.now() + timedelta(seconds=60)
                        logger.info(f" Cooldown active for {sym} until {cooldown_until[sym].strftime('%H:%M:%S')}")
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error in strategy loop: {str(e)}", exc_info=True)
            time.sleep(5)  # Wait before retrying


def main():
    """Main entry point"""
    logger.info("=" * 70)
    logger.info(" CRYPTO TRADING BOT STARTING")
    logger.info("=" * 70)
    logger.info(f"Symbols: {', '.join(SYMBOLS)}")
    logger.info(f"Market Types: {', '.join(MARKET_TYPES)}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start WebSocket connections for all symbols
        ws_threads = []
        for sym, mtype in zip(SYMBOLS, MARKET_TYPES):
            logger.info(f" Starting WebSocket for {sym} ({mtype})")
            t = live_feed.start_ws(sym, mtype)
            ws_threads.append(t)
            time.sleep(0.5)  # Stagger connections
        
        logger.info(f" WebSocket connections established for {len(SYMBOLS)} symbols")
        
        # Wait for initial data
        logger.info(" Waiting for initial market data...")
        time.sleep(5)
        
        # Start strategy loop
        strategy_thread = threading.Thread(target=strategy_loop)
        strategy_thread.daemon = True
        strategy_thread.start()
        
        logger.info(" Strategy engine running")
        logger.info("=" * 70)
        logger.info(" System is now live! Press Ctrl+C to stop.")
        logger.info("=" * 70)
        
        # Keep main thread alive
        while not shutdown_flag.is_set():
            time.sleep(10)
            
            # Periodic status update
            summary = tracker.get_position_summary()
            if summary['open_positions'] > 0:
                logger.debug(f"Open positions: {summary['open_positions']} | Total PnL: {summary['total_pnl_usdt']:.2f} USDT")
    
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}", exc_info=True)
        shutdown_flag.set()


if __name__ == "__main__":
    # Initialize strategy engine
    engine = StrategyEngine()
    
    # Import timedelta here to avoid issues
    from datetime import timedelta
    
    # Run main
    main()