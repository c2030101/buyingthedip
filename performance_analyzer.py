import pandas as pd
import numpy as np
from datetime import datetime


class PerformanceAnalyzer:
    def __init__(self, portfolio_stats):
        """Initialize with portfolio statistics from PortfolioTracker"""
        # Convert positions DataFrame index to datetime if needed
        positions = portfolio_stats['positions'].copy()
        if not isinstance(positions.index, pd.DatetimeIndex):
            positions.index = pd.to_datetime(positions.index)
        self.positions = positions

        # Handle trades data
        self.trades = portfolio_stats['trades']
        self.pnl_summary = portfolio_stats['pnl_summary']

        # Initialize metrics dictionary
        self.metrics = {
            'returns': {},
            'drawdown': {},
            'trades': {},
            'exposure': {}
        }

        # Calculate all metrics upon initialization
        self.calculate_all_metrics()

    def calculate_all_metrics(self):
        """Calculate all metrics at once"""
        self.calculate_return_metrics()
        self.calculate_drawdown_metrics()
        self.calculate_trade_metrics()
        self.calculate_exposure_metrics()

    def calculate_return_metrics(self):
        """Calculate return-based metrics"""
        # Total return
        initial_value = self.positions['Portfolio_Value'].iloc[0]
        final_value = self.positions['Portfolio_Value'].iloc[-1]
        total_return = (final_value / initial_value - 1) * 100

        # Calculate annualized return
        days = len(self.positions)
        years = days / 252  # Trading days in a year
        annualized_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100

        # Daily returns
        daily_returns = self.positions['Portfolio_Value'].pct_change()
        volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized

        self.metrics['returns'].update({
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': annualized_return / volatility if volatility != 0 else 0
        })

    def calculate_drawdown_metrics(self):
        """Calculate drawdown metrics"""
        portfolio_value = self.positions['Portfolio_Value']
        rolling_max = portfolio_value.expanding().max()
        drawdown = ((portfolio_value - rolling_max) / rolling_max) * 100

        self.metrics['drawdown'].update({
            'max_drawdown': drawdown.min() if not drawdown.empty else 0,
            'avg_drawdown': drawdown[drawdown < 0].mean() if not drawdown.empty else 0,
            'current_drawdown': drawdown.iloc[-1] if not drawdown.empty else 0
        })

    def calculate_trade_metrics(self):
        """Calculate trade-related metrics"""
        if len(self.trades) == 0:
            self.metrics['trades'].update({
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'profit_factor': 0
            })
            return

        # Add PnL if not already present
        if 'PnL' not in self.trades.columns:
            winning_trades = self.trades[self.trades['Type'].str.contains('EXIT')]
            self.metrics['trades'].update({
                'total_trades': len(winning_trades),
                'winning_trades': len(winning_trades[winning_trades['Value'] > 0]),
                'losing_trades': len(winning_trades[winning_trades['Value'] <= 0]),
                'win_rate': 0,  # Will be updated
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'profit_factor': 0
            })
        else:
            winning_trades = self.trades[self.trades['PnL'] > 0]
            losing_trades = self.trades[self.trades['PnL'] < 0]

            self.metrics['trades'].update({
                'total_trades': len(self.trades),
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': len(winning_trades) / len(self.trades) * 100 if len(self.trades) > 0 else 0,
                'avg_win': winning_trades['PnL'].mean() if len(winning_trades) > 0 else 0,
                'avg_loss': losing_trades['PnL'].mean() if len(losing_trades) > 0 else 0,
                'largest_win': self.trades['PnL'].max(),
                'largest_loss': self.trades['PnL'].min(),
                'profit_factor': abs(winning_trades['PnL'].sum() / losing_trades['PnL'].sum())
                if len(losing_trades) > 0 and losing_trades['PnL'].sum() != 0 else 0
            })

    def calculate_exposure_metrics(self):
        """Calculate exposure-related metrics"""
        exposure = self.positions['Portfolio_Value'] / self.positions['Portfolio_Value'].iloc[0] - 1
        self.metrics['exposure'].update({
            'average_exposure': exposure.mean() * 100,
            'max_exposure': exposure.max() * 100,
            'current_exposure': exposure.iloc[-1] * 100
        })

    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
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