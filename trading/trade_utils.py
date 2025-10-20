import numpy as np
from datetime import datetime, timedelta
import pandas as pd

def calculate_volatility(prices, window=14):
    """Calculate rolling volatility"""
    returns = np.log(prices).diff()
    return returns.rolling(window).std() * np.sqrt(252)

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """Calculate Sharpe ratio"""
    excess_returns = returns - risk_free_rate/252
    return np.sqrt(252) * excess_returns.mean() / returns.std()

def calculate_max_drawdown(prices):
    """Calculate maximum drawdown"""
    peak = prices.expanding(min_periods=1).max()
    drawdown = (prices - peak) / peak
    return drawdown.min()

def calculate_var(returns, confidence=0.95):
    """Calculate Value at Risk"""
    return np.percentile(returns, (1 - confidence) * 100)

def calculate_cvar(returns, confidence=0.95):
    """Calculate Conditional Value at Risk (Expected Shortfall)"""
    var = calculate_var(returns, confidence)
    return returns[returns <= var].mean()

def calculate_position_size(account_balance, risk_per_trade, stop_loss_pct):
    """Calculate position size based on risk"""
    if stop_loss_pct == 0:
        return 0
    risk_amount = account_balance * risk_per_trade
    return risk_amount / stop_loss_pct

def calculate_kelly_criterion(win_rate, win_loss_ratio):
    """Calculate Kelly Criterion for position sizing"""
    q = 1 - win_rate
    return (win_rate * win_loss_ratio - q) / win_loss_ratio

def calculate_risk_of_ruin(win_rate, risk_per_trade, trades=1000):
    """Calculate risk of ruin probability"""
    if win_rate <= 0.5 or risk_per_trade >= 1:
        return 1.0
    return (1 - 2 * win_rate) / (1 - risk_per_trade)

def calculate_optimal_leverage(returns, target_volatility=0.15):
    """Calculate optimal leverage based on volatility targeting"""
    vol = returns.std() * np.sqrt(252)
    return target_volatility / vol if vol > 0 else 0

def calculate_correlation_matrix(symbols, client, timeframe='1d', lookback=30):
    """Calculate correlation matrix between symbols"""
    prices = {}
    end_time = datetime.now()
    start_time = end_time - timedelta(days=lookback)
    
    for symbol in symbols:
        klines = client.get_historical_klines(
            symbol, 
            timeframe,
            str(int(start_time.timestamp() * 1000)),
            str(int(end_time.timestamp() * 1000))
        )
        prices[symbol] = [float(k[4]) for k in klines]  # Close prices
        
    # Convert to returns
    returns_df = pd.DataFrame(prices).pct_change().dropna()
    return returns_df.corr()

def calculate_funding_cost(position_value, funding_rate, days):
    """Calculate funding costs for futures/margin"""
    return position_value * funding_rate * days / 365

def calculate_option_greeks(S, K, T, r, sigma, option_type='call'):
    """Calculate basic option Greeks"""
    from scipy.stats import norm
    
    d1 = (np.log(S/K) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    if option_type.lower() == 'call':
        delta = norm.cdf(d1)
        theta = -(S*sigma*norm.pdf(d1))/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2)
        gamma = norm.pdf(d1)/(S*sigma*np.sqrt(T))
        vega = S*np.sqrt(T)*norm.pdf(d1)
    else:  # put
        delta = norm.cdf(d1) - 1
        theta = -(S*sigma*norm.pdf(d1))/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*norm.cdf(-d2)
        gamma = norm.pdf(d1)/(S*sigma*np.sqrt(T))
        vega = S*np.sqrt(T)*norm.pdf(d1)
        
    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega
    }

def backtest_strategy(prices, signals, commission=0.001):
    """Simple strategy backtesting"""
    position = 0
    balance = 1.0  # Starting with 1 unit of capital
    trades = []
    
    for i in range(1, len(prices)):
        # Close previous position
        if position != 0:
            balance *= (prices[i]/prices[i-1])**position
            balance *= (1-commission)  # Apply commission
            
        # Open new position
        position = signals[i]
        
        if position != 0:
            balance *= (1-commission)  # Apply commission
            trades.append({
                'entry': prices[i],
                'position': position,
                'balance': balance
            })
            
    return {
        'final_balance': balance,
        'return': (balance-1)*100,
        'trades': trades,
        'sharpe': calculate_sharpe_ratio(pd.Series(balance).pct_change().dropna())
    }