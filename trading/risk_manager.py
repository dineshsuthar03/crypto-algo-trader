from core.logger import get_logger
from core.config import (
    MAX_POSITION_SIZE_PCT,
    MAX_LEVERAGE_UTILIZATION,
    FUTURES_STOP_BUFFER,
    OPTIONS_MAX_PREMIUM_PCT
)
import numpy as np
from datetime import datetime, timedelta

logger = get_logger()

class RiskManager:
    def __init__(self, client):
        self.client = client
        self.position_limits = {}
        self.daily_loss_limit = None
        self.volatility_limits = {}
        self.correlation_matrix = {}
        
    def calculate_position_size(self, symbol, account_size, market_type):
        """Calculate safe position size based on risk parameters"""
        try:
            # Get account balance
            if market_type in ['futures', 'margin']:
                account = self.client.get_margin_account()
                balance = float(account['totalAssetOfBtc'])
            else:
                account = self.client.get_account()
                balance = float(account['totalAssetOfBtc'])
                
            # Calculate max position size
            max_position = balance * MAX_POSITION_SIZE_PCT
            
            # Adjust for leverage if applicable
            if market_type == 'futures':
                leverage = float(self.client.futures_position_information(symbol=symbol)[0]['leverage'])
                max_position = max_position * min(leverage, MAX_LEVERAGE_UTILIZATION)
            elif market_type == 'margin':
                margin_info = self.client.get_margin_account(symbol=symbol)
                leverage = float(margin_info['marginLevel'])
                max_position = max_position * min(leverage, MAX_LEVERAGE_UTILIZATION)
                
            return max_position
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return None
            
    def validate_order_risk(self, symbol, quantity, price, market_type):
        """Validate if order meets risk criteria"""
        try:
            # Calculate order value
            order_value = quantity * price
            
            # Get account info
            account = self.client.get_account()
            total_balance = float(account['totalAssetOfBtc'])
            
            # Check position size limit
            max_position = self.calculate_position_size(symbol, total_balance, market_type)
            if order_value > max_position:
                logger.warning(f"Order value {order_value} exceeds position limit {max_position}")
                return False
                
            # Check daily loss limit
            if market_type in ['futures', 'margin']:
                daily_pnl = self.calculate_daily_pnl(symbol)
                if abs(daily_pnl) > total_balance * 0.02:  # 2% daily loss limit
                    logger.warning(f"Daily loss limit reached: {daily_pnl:.2f}")
                    return False
                    
            # Check volatility for options
            if market_type == 'options':
                if self.check_high_volatility(symbol):
                    logger.warning(f"High volatility detected for {symbol}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating order risk: {e}")
            return False
            
    def calculate_daily_pnl(self, symbol):
        """Calculate daily PnL for a symbol"""
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            # Get today's trades
            trades = self.client.get_my_trades(
                symbol=symbol,
                startTime=int(datetime.combine(today, datetime.min.time()).timestamp() * 1000),
                endTime=int(datetime.combine(tomorrow, datetime.min.time()).timestamp() * 1000)
            )
            
            total_pnl = sum(float(trade['realizedPnl']) for trade in trades if 'realizedPnl' in trade)
            return total_pnl
            
        except Exception as e:
            logger.error(f"Error calculating daily PnL: {e}")
            return 0
            
    def check_high_volatility(self, symbol, window=14):
        """Check if symbol has high volatility"""
        try:
            # Get recent klines
            klines = self.client.get_klines(symbol=symbol, interval='1h', limit=window)
            
            # Calculate returns
            prices = [float(k[4]) for k in klines]  # Close prices
            returns = np.diff(np.log(prices))
            
            # Calculate volatility
            volatility = np.std(returns) * np.sqrt(24 * 365)  # Annualized
            
            # Check against threshold (50% annualized)
            return volatility > 0.5
            
        except Exception as e:
            logger.error(f"Error checking volatility: {e}")
            return True  # Conservative - assume high volatility on error
            
    def calculate_portfolio_risk(self):
        """Calculate overall portfolio risk metrics"""
        try:
            # Get all positions
            positions = []
            
            # Spot positions
            account = self.client.get_account()
            for balance in account['balances']:
                if float(balance['free']) > 0 or float(balance['locked']) > 0:
                    positions.append({
                        'asset': balance['asset'],
                        'amount': float(balance['free']) + float(balance['locked']),
                        'type': 'spot'
                    })
                    
            # Margin positions
            margin = self.client.get_margin_account()
            for asset in margin['userAssets']:
                if float(asset['netAsset']) != 0:
                    positions.append({
                        'asset': asset['asset'],
                        'amount': float(asset['netAsset']),
                        'type': 'margin'
                    })
                    
            # Futures positions
            futures = self.client.futures_position_information()
            for position in futures:
                if float(position['positionAmt']) != 0:
                    positions.append({
                        'asset': position['symbol'],
                        'amount': float(position['positionAmt']),
                        'type': 'futures'
                    })
                    
            # Calculate metrics
            total_value = sum(p['amount'] for p in positions)
            position_weights = {p['asset']: p['amount']/total_value for p in positions}
            
            return {
                'total_positions': len(positions),
                'position_weights': position_weights,
                'largest_position': max(position_weights.values()) if position_weights else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {e}")
            return None
            
    def should_reduce_exposure(self):
        """Determine if overall exposure should be reduced"""
        try:
            risk_metrics = self.calculate_portfolio_risk()
            if not risk_metrics:
                return True  # Conservative approach
                
            # Check various risk factors
            if risk_metrics['largest_position'] > MAX_POSITION_SIZE_PCT:
                logger.warning("Position concentration too high")
                return True
                
            if risk_metrics['total_positions'] > 10:  # Max 10 concurrent positions
                logger.warning("Too many open positions")
                return True
                
            # Market volatility check
            if self.check_market_volatility():
                logger.warning("High market volatility")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking exposure: {e}")
            return True
            
    def check_market_volatility(self, symbols=None):
        """Check overall market volatility"""
        try:
            if not symbols:
                symbols = ['BTCUSDT', 'ETHUSDT']  # Major pairs as market indicators
                
            high_vol_count = sum(1 for s in symbols if self.check_high_volatility(s))
            return high_vol_count / len(symbols) > 0.5  # If more than 50% showing high vol
            
        except Exception as e:
            logger.error(f"Error checking market volatility: {e}")
            return True  # Conservative