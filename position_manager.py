import pandas as pd
import numpy as np


class PositionManager:
    def __init__(self, price_data, signals_data, initial_capital=100000):
        self.price_data = price_data
        self.signals_data = signals_data
        self.initial_capital = initial_capital
        self.cash = initial_capital

        # Position sizing for each entry
        self.position_sizes = {
            'Entry1': 0.20,  # 20% of portfolio
            'Entry2': 0.15,  # 15% of portfolio
            'Entry3': 0.20,  # 20% of portfolio
            'Entry4': 0.20,  # 20% of portfolio
            'Entry5': 0.15  # 15% of portfolio
        }

        # Initialize tracking
        self.reset_positions()

        self.trades = []
        self.daily_positions = []

    def reset_positions(self):
        """Reset all position tracking"""
        self.active_positions = {f'Entry{i}': 0 for i in range(1, 6)}
        self.entry_prices = {f'Entry{i}': 0 for i in range(1, 6)}

    def calculate_average_entry(self):
        """Calculate weighted average entry price across all positions"""
        total_shares = sum(self.active_positions.values())
        if total_shares == 0:
            return 0

        weighted_sum = sum(
            self.entry_prices[entry] * self.active_positions[entry]
            for entry in self.active_positions.keys()
        )
        return weighted_sum / total_shares

    def get_total_exposure(self):
        """Calculate total portfolio exposure"""
        current_price = self.price_data['Close'].iloc[-1]
        total_position_value = sum(
            self.active_positions[entry] * current_price
            for entry in self.active_positions.keys()
        )
        return total_position_value / self.initial_capital

    def enter_position(self, entry_type, price, date):
        """Enter a new position"""
        # Calculate position size in shares
        position_dollars = self.initial_capital * self.position_sizes[entry_type]
        shares = int(position_dollars / price)

        # Check if we have enough cash
        position_cost = shares * price
        if position_cost > self.cash:
            return False

        # Execute trade
        self.active_positions[entry_type] = shares
        self.entry_prices[entry_type] = price
        self.cash -= position_cost

        # Record trade
        self.trades.append({
            'Date': date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else date,
            'Type': f'ENTER_{entry_type}',
            'Shares': shares,
            'Price': price,
            'Value': -position_cost,
            'Cash': self.cash
        })

        return True

    def exit_all_positions(self, current_price, date):
        """Exit all positions at once"""
        total_proceeds = 0

        for entry_type in list(self.active_positions.keys()):
            if self.active_positions[entry_type] > 0:
                shares = self.active_positions[entry_type]
                proceeds = shares * current_price
                total_proceeds += proceeds

                # Record exit trade
                self.trades.append({
                    'Date': date,
                    'Type': f'EXIT_{entry_type}',
                    'Shares': -shares,
                    'Price': current_price,
                    'Value': proceeds,
                    'Cash': self.cash + proceeds
                })

                # Clear position
                self.active_positions[entry_type] = 0
                self.entry_prices[entry_type] = 0

        # Update cash
        self.cash += total_proceeds
        return True

    def record_daily_position(self, date, current_price):
        """Record daily position information"""
        total_shares = sum(self.active_positions.values())
        position_value = total_shares * current_price

        self.daily_positions.append({
            'Date': date,
            'Portfolio_Value': self.cash + position_value,
            'Cash': self.cash,
            'Total_Shares': total_shares,
            'Avg_Entry': self.calculate_average_entry(),
            'Current_Price': current_price
        })

    def run_backtest(self):
        """Run the backtest"""
        for date in self.price_data.index:
            current_price = self.price_data.loc[date, 'Close']
            signals = self.signals_data.loc[date]

            # Check exit signal first
            if signals['Exit']:
                self.exit_all_positions(current_price, date)

            # Process entry signals
            else:
                for entry_num in range(1, 6):
                    entry_type = f'Entry{entry_num}'
                    if signals[entry_type] and self.active_positions[entry_type] == 0:
                        self.enter_position(entry_type, current_price, date)

            # Record daily position
            self.record_daily_position(date, current_price)

        # Convert tracking data to DataFrames
        trades_df = pd.DataFrame(self.trades)
        positions_df = pd.DataFrame(self.daily_positions)

        return trades_df, positions_df