import pandas as pd
import numpy as np
from datetime import datetime


class PerformanceAnalyzer:
    def __init__(self, portfolio_stats):
        """Initialize with portfolio statistics from PortfolioTracker"""
        # Convert positions DataFrame index to datetime if needed
        positions = portfolio_stats['positions'].copy()
        if not isinstance(positions.index, pd.DatetimeIndex):
            positions.index = pd.to_datetime(positions['Date'])
        self.positions = positions

        # Handle trades data
        self.trades = portfolio_stats['trades']
        self.pnl_summary = portfolio_stats['pnl_summary']
        self.metrics = {}

    def calculate_return_metrics(self):
        """Calculate return-based metrics"""
        # Total return
        initial_value = self.positions['Portfolio_Value'].iloc[0]
        final_value = self.positions['Portfolio_Value'].iloc[-1]
        total_return = (final_value / initial_value - 1) * 100

        # Calculate annualized return
        days = len(self.positions)
        years = days / 252
        annualized_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100

        # Monthly returns
        self.positions['YearMonth'] = pd.to_datetime(self.positions.index).strftime('%Y-%m')
        monthly_returns = self.positions.groupby('YearMonth')['Portfolio_Value'].last().pct_change() * 100

        # Volatility (annualized)
        daily_returns = self.positions['Portfolio_Value'].pct_change()
        volatility = daily_returns.std() * np.sqrt(252) * 100

        self.metrics['returns'] = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': annualized_return / volatility if volatility != 0 else 0,
            'monthly_returns': monthly_returns.to_dict()
        }

    def calculate_drawdown_metrics(self):
        """Calculate drawdown metrics"""
        portfolio_value = self.positions['Portfolio_Value']
        rolling_max = portfolio_value.expanding().max()
        drawdown = ((portfolio_value - rolling_max) / rolling_max) * 100

        self.metrics['drawdown'] = {
            'max_drawdown': drawdown.min(),
            'avg_drawdown': drawdown[drawdown < 0].mean(),
            'current_drawdown': drawdown.iloc[-1]
        }

    def calculate_trade_metrics(self):
        """Calculate trade-related metrics"""
        trades = self.trades
        winning_trades = trades[trades['PnL'] > 0]
        losing_trades = trades[trades['PnL'] < 0]

        self.metrics['trades'] = {
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(trades) * 100 if len(trades) > 0 else 0,
            'avg_win': winning_trades['PnL'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['PnL'].mean() if len(losing_trades) > 0 else 0,
            'largest_win': trades['PnL'].max(),
            'largest_loss': trades['PnL'].min(),
            'profit_factor': abs(winning_trades['PnL'].sum() / losing_trades['PnL'].sum())
            if len(losing_trades) > 0 and losing_trades['PnL'].sum() != 0 else 0
        }

    def calculate_exposure_metrics(self):
        """Calculate exposure-related metrics"""
        exposure = self.positions['Exposure']
        self.metrics['exposure'] = {
            'average_exposure': exposure.mean() * 100,
            'max_exposure': exposure.max() * 100,
            'current_exposure': exposure.iloc[-1] * 100
        }

    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        self.calculate_return_metrics()
        self.calculate_drawdown_metrics()
        self.calculate_trade_metrics()
        self.calculate_exposure_metrics()

        report = f"""
Performance Summary Report
========================
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Return Metrics
-------------
Total Return: {self.metrics['returns']['total_return']:.2f}%
Annualized Return: {self.metrics['returns']['annualized_return']:.2f}%
Volatility (Ann.): {self.metrics['returns']['volatility']:.2f}%
Sharpe Ratio: {self.metrics['returns']['sharpe_ratio']:.2f}

Risk Metrics
-----------
Maximum Drawdown: {self.metrics['drawdown']['max_drawdown']:.2f}%
Average Drawdown: {self.metrics['drawdown']['avg_drawdown']:.2f}%
Current Drawdown: {self.metrics['drawdown']['current_drawdown']:.2f}%

Trade Statistics
---------------
Total Trades: {self.metrics['trades']['total_trades']}
Win Rate: {self.metrics['trades']['win_rate']:.2f}%
Average Win: ${self.metrics['trades']['avg_win']:.2f}
Average Loss: ${self.metrics['trades']['avg_loss']:.2f}
Profit Factor: {self.metrics['trades']['profit_factor']:.2f}

Exposure Analysis
----------------
Average Exposure: {self.metrics['exposure']['average_exposure']:.2f}%
Maximum Exposure: {self.metrics['exposure']['max_exposure']:.2f}%
Current Exposure: {self.metrics['exposure']['current_exposure']:.2f}%
"""
        return report

    def save_metrics(self, filename='performance_metrics.csv'):
        """Save metrics to CSV file"""
        # Flatten metrics dictionary
        flat_metrics = {}
        for category in self.metrics:
            for metric, value in self.metrics[category].items():
                if isinstance(value, dict):
                    continue  # Skip nested dictionaries like monthly returns
                flat_metrics[f"{category}_{metric}"] = value

        # Convert to DataFrame and save
        metrics_df = pd.DataFrame([flat_metrics])
        metrics_df.to_csv(filename, index=False)
        print(f"Metrics saved to {filename}")

    def save_monthly_returns(self, filename='monthly_returns.csv'):
        """Save monthly returns to separate CSV file"""
        monthly_returns = pd.Series(self.metrics['returns']['monthly_returns'])
        monthly_returns.to_csv(filename)
        print(f"Monthly returns saved to {filename}")