import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from core.logger import get_logger

logger = get_logger()

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, set):
            return list(obj)
        return super(CustomEncoder, self).default(obj)

class StrategyResultsAnalyzer:
    def __init__(self, results_dir="test_results"):
        self.results_dir = results_dir
        
    def load_results(self, file_pattern=None):
        """Load all results files or files matching pattern"""
        results = {}
        for filename in os.listdir(self.results_dir):
            # Skip analysis reports and non-json files
            if not filename.endswith('.json') or filename.startswith('analysis'):
                continue
            if file_pattern and file_pattern not in filename:
                continue
                
            filepath = os.path.join(self.results_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    # Get strategy name without timestamp
                    strategy_name = filename.split('_')[0]
                    data = f.read()
                    # Clean up potential invalid characters
                    data = data.replace('\n', '').replace('\r', '').strip()
                    results[strategy_name] = json.loads(data)
                    logger.info(f"Loaded results from {filename}")
            except json.JSONDecodeError as e:
                logger.error(f"Error loading {filename}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error loading {filename}: {str(e)}")
                
        return results
        
    def calculate_strategy_metrics(self, strategy_results):
        """Calculate comprehensive metrics for a strategy"""
        metrics = {
            'timeframes': {},
            'overall': {
                'total_signals': 0,
                'accuracy': 0,
                'profit_potential': 0,
                'risk_metrics': {}
            }
        }
        
        # Analyze each timeframe
        for timeframe, data in strategy_results['timeframes'].items():
            signals = data.get('signals', [])
            if not signals:
                continue
                
            # Convert to DataFrame for analysis
            df = pd.DataFrame(signals)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Calculate timeframe metrics
            timeframe_metrics = self._calculate_timeframe_metrics(df)
            metrics['timeframes'][timeframe] = timeframe_metrics
            
            # Update overall metrics
            metrics['overall']['total_signals'] += timeframe_metrics['total_signals']
            metrics['overall']['accuracy'] += timeframe_metrics['accuracy']
            
        # Average the accuracy across timeframes
        if metrics['timeframes']:
            metrics['overall']['accuracy'] /= len(metrics['timeframes'])
            
        return metrics
    
    def _calculate_timeframe_metrics(self, df):
        """Calculate detailed metrics for a timeframe"""
        metrics = {
            'total_signals': len(df),
            'signal_distribution': {},
            'accuracy': 0,
            'patterns': {},
            'best_params': None,
            'risk_metrics': {}
        }
        
        if 'pattern' in df.columns:
            metrics['patterns'] = df['pattern'].value_counts().to_dict()
            
        if 'params' in df.columns:
            # Group by parameters and count signals
            if 'params_str' in df.columns:
                param_groups = df.groupby('params_str').size()
                metrics['best_params'] = eval(param_groups.idxmax())
        
        # Calculate signal distribution
        if 'signal' in df.columns:
            metrics['signal_distribution'] = df['signal'].value_counts().to_dict()
        
        # Calculate basic accuracy (if we had actual results)
        # This would need real trade data to be accurate
        metrics['accuracy'] = 0.5  # Placeholder
        
        # Calculate risk metrics
        metrics['risk_metrics'] = self._calculate_risk_metrics(df)
        
        return metrics
    
    def _calculate_risk_metrics(self, df):
        """Calculate risk-related metrics"""
        risk_metrics = {
            'max_consecutive_signals': 0,
            'signal_clustering': 0,
            'volatility_correlation': 0
        }
        
        if len(df) < 2:
            return risk_metrics
            
        # Calculate time between signals
        df['time_delta'] = df.index.to_series().diff()
        
        # Count consecutive signals (signals within 1 hour)
        consecutive = (df['time_delta'] <= pd.Timedelta(hours=1)).sum()
        risk_metrics['max_consecutive_signals'] = consecutive
        
        # Calculate signal clustering
        time_deltas = df['time_delta'].dt.total_seconds()
        risk_metrics['signal_clustering'] = time_deltas.std()
        
        return risk_metrics
    
    def find_best_parameters(self, strategy_results):
        """Find the best performing parameters for each timeframe"""
        best_params = {}
        
        for timeframe, data in strategy_results['timeframes'].items():
            signals = data.get('signals', [])
            if not signals:
                continue
                
            # Group signals by parameters
            param_performance = {}
            for signal in signals:
                params = tuple(signal.get('params', {}).items())
                if not params:
                    continue
                    
                if params not in param_performance:
                    param_performance[params] = {
                        'count': 0,
                        'patterns': set(),
                        'accuracy': 0  # Would need real trade data
                    }
                
                param_performance[params]['count'] += 1
                if 'pattern' in signal:
                    param_performance[params]['patterns'].add(signal['pattern'])
            
            # Find best parameters
            if param_performance:
                best_param = max(param_performance.items(), 
                               key=lambda x: len(x[1]['patterns']))
                best_params[timeframe] = {
                    'parameters': dict(best_param[0]),
                    'metrics': best_param[1]
                }
        
        return best_params
    
    def generate_report(self, results=None):
        """Generate a comprehensive analysis report"""
        if results is None:
            results = self.load_results()
            
        report = {
            'timestamp': datetime.now().isoformat(),
            'strategies': {}
        }
        
        for strategy_name, strategy_results in results.items():
            logger.info(f"\nAnalyzing {strategy_name} strategy...")
            
            # Calculate metrics
            metrics = self.calculate_strategy_metrics(strategy_results)
            
            # Find best parameters
            best_params = self.find_best_parameters(strategy_results)
            
            # Store in report
            report['strategies'][strategy_name] = {
                'metrics': metrics,
                'best_parameters': best_params
            }
            
            # Log summary
            self._log_strategy_summary(strategy_name, metrics, best_params)
            
        # Save report
        self._save_report(report)
        
        return report
    
    def _log_strategy_summary(self, strategy_name, metrics, best_params):
        """Log summary of strategy analysis"""
        logger.info(f"\n{'='*50}")
        logger.info(f"Strategy: {strategy_name}")
        logger.info(f"{'='*50}")
        
        logger.info("\nOverall Metrics:")
        logger.info(f"Total Signals: {metrics['overall']['total_signals']}")
        logger.info(f"Average Accuracy: {metrics['overall']['accuracy']:.2%}")
        
        for timeframe, tf_metrics in metrics['timeframes'].items():
            logger.info(f"\nTimeframe: {timeframe}")
            logger.info(f"Signals: {tf_metrics['total_signals']}")
            
            if tf_metrics['patterns']:
                logger.info("\nPattern Distribution:")
                for pattern, count in tf_metrics['patterns'].items():
                    logger.info(f"{pattern}: {count}")
            
            if timeframe in best_params:
                logger.info("\nBest Parameters:")
                for param, value in best_params[timeframe]['parameters'].items():
                    logger.info(f"{param}: {value}")
    
    def _save_report(self, report):
        """Save analysis report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.results_dir, f'analysis_report_{timestamp}.json')
        with open(filename, 'w') as f:
            json.dump(report, f, indent=4, cls=CustomEncoder)
            
        logger.info(f"\nAnalysis report saved to {filename}")

def main():
    analyzer = StrategyResultsAnalyzer()
    analyzer.generate_report()

if __name__ == "__main__":
    main()