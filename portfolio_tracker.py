import pandas as pd
import numpy as np


class PortfolioTracker:
    def __init__(self, trades_df, positions_df):
        self.trades_df = trades_df
        self.positions_df = positions_df
        self.portfolio_stats = {}

    def calculate_trade_pnl(self):
        """Calculate P&L for each trade"""
        # Create a copy of trades DataFrame
        trades = self.trades_df.copy()

        # Initialize P&L columns
        trades['PnL'] = 0.0
        trades['PnL_Pct'] = 0.0

        # Group trades by entry/exit pairs
        current_position = {}  # Dictionary to track open positions

        for idx, trade in trades.iterrows():
            trade_type = trade['Type']

            if 'ENTER' in trade_type:
                entry_type = trade_type.split('_')[1]
                current_position[entry_type] = {
                    'Shares': trade['Shares'],
                    'Price': trade['Price'],
                    'Cost': abs(trade['Value'])
                }

            elif 'EXIT' in trade_type or 'REDUCE' in trade_type:
                entry_type = trade_type.split('_')[1]
                if entry_type in current_position:
                    entry_data = current_position[entry_type]
                    pnl = (trade['Price'] - entry_data['Price']) * abs(trade['Shares'])
                    pnl_pct = (trade['Price'] / entry_data['Price'] - 1) * 100

                    trades.loc[idx, 'PnL'] = pnl
                    trades.loc[idx, 'PnL_Pct'] = pnl_pct

                    # Update or remove position
                    remaining_shares = entry_data['Shares'] + trade['Shares']
                    if remaining_shares <= 0:
                        del current_position[entry_type]
                    else:
                        current_position[entry_type]['Shares'] = remaining_shares

        return trades

    def calculate_portfolio_metrics(self):
        """Calculate portfolio-level metrics"""
        # Calculate daily returns
        self.positions_df['Daily_Return'] = self.positions_df['Portfolio_Value'].pct_change()

        # Calculate cumulative returns
        self.positions_df['Cumulative_Return'] = (
                (1 + self.positions_df['Daily_Return']).cumprod() - 1
        )

        # Calculate drawdown
        rolling_max = self.positions_df['Portfolio_Value'].expanding().max()
        self.positions_df['Drawdown'] = (
                                                self.positions_df['Portfolio_Value'] - rolling_max
                                        ) / rolling_max * 100

        return self.positions_df

    def calculate_realized_unrealized_pnl(self):
        """Calculate realized and unrealized P&L"""
        # Calculate realized P&L from closed trades
        trades_with_pnl = self.calculate_trade_pnl()
        realized_pnl = trades_with_pnl['PnL'].sum()

        # Calculate unrealized P&L from current positions
        latest_position = self.positions_df.iloc[-1]
        initial_value = self.positions_df.iloc[0]['Portfolio_Value']
        total_pnl = latest_position['Portfolio_Value'] - initial_value
        unrealized_pnl = total_pnl - realized_pnl

        return {
            'Realized_PnL': realized_pnl,
            'Unrealized_PnL': unrealized_pnl,
            'Total_PnL': total_pnl
        }

    def track_portfolio(self):
        """Main method to run all portfolio tracking calculations"""
        # Calculate all metrics
        trades_with_pnl = self.calculate_trade_pnl()
        portfolio_metrics = self.calculate_portfolio_metrics()
        pnl_metrics = self.calculate_realized_unrealized_pnl()

        # Store results
        self.portfolio_stats = {
            'trades': trades_with_pnl,
            'positions': portfolio_metrics,
            'pnl_summary': pnl_metrics
        }

        # Save updated results
        trades_with_pnl.to_csv('trades_with_pnl.csv')
        portfolio_metrics.to_csv('portfolio_metrics.csv')

        return self.portfolio_stats

    def get_current_portfolio_state(self):
        """Get current portfolio state"""
        if len(self.positions_df) == 0:
            return None

        latest = self.positions_df.iloc[-1]
        pnl = self.calculate_realized_unrealized_pnl()

        return {
            'Date': latest['Date'],
            'Portfolio_Value': latest['Portfolio_Value'],
            'Cash': latest['Cash'],
            'Exposure': latest['Exposure'],
            'Realized_PnL': pnl['Realized_PnL'],
            'Unrealized_PnL': pnl['Unrealized_PnL'],
            'Total_PnL': pnl['Total_PnL']
        }