import pandas as pd
import numpy as np


class PositionManager:
    def __init__(self, price_data, signals_data, initial_capital=100000):
        # Initialize portfolio tracking
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.cash = initial_capital

        # Store historical data
        self.price_data = price_data
        self.signals_data = signals_data

        # Position sizing for each entry
        self.position_sizes = {
            'Entry1': 0.20,  # 20% of portfolio
            'Entry2': 0.15,  # 15% of portfolio
            'Entry3': 0.20,  # 20% of portfolio
            'Entry4': 0.20,  # 20% of portfolio
            'Entry5': 0.15  # 15% of portfolio
        }

        # Initialize tracking dictionaries
        self.active_positions = {entry: 0 for entry in self.position_sizes.keys()}
        self.entry_prices = {entry: 0 for entry in self.position_sizes.keys()}

        # Track all trades and daily positions
        self.trades = []
        self.daily_positions = []

    def calculate_position_size(self, entry_type, current_price):
        position_dollars = self.initial_capital * self.position_sizes[entry_type]
        return int(position_dollars / current_price)

    def enter_position(self, entry_type, price, date):
        if self.get_total_exposure() + self.position_sizes[entry_type] > 0.90:
            return False

        shares = self.calculate_position_size(entry_type, price)
        position_cost = shares * price

        if position_cost > self.cash:
            return False

        self.active_positions[entry_type] = shares
        self.entry_prices[entry_type] = price
        self.cash -= position_cost

        # Record trade
        self.trades.append({
            'Date': date,
            'Type': f'ENTER_{entry_type}',
            'Shares': shares,
            'Price': price,
            'Value': position_cost,
            'Cash': self.cash
        })

        return True

    def exit_position(self, entry_type, price, date):
        shares = self.active_positions[entry_type]
        proceeds = shares * price

        self.active_positions[entry_type] = 0
        self.entry_prices[entry_type] = 0
        self.cash += proceeds

        # Record trade
        self.trades.append({
            'Date': date,
            'Type': f'EXIT_{entry_type}',
            'Shares': -shares,
            'Price': price,
            'Value': proceeds,
            'Cash': self.cash
        })

        return True

    def get_average_entry_price(self):
        total_shares = sum(self.active_positions.values())
        if total_shares == 0:
            return 0
        weighted_sum = sum(
            self.entry_prices[entry] * self.active_positions[entry]
            for entry in self.active_positions.keys()
        )
        return weighted_sum / total_shares

    def get_total_exposure(self):
        total_position_value = sum(
            self.active_positions[entry] * self.entry_prices[entry]
            for entry in self.active_positions.keys()
        )
        return total_position_value / self.initial_capital

    def reduce_position(self, current_price, date, reduction_amount=0.10):
        if self.get_total_exposure() > 0.75:
            total_shares = sum(self.active_positions.values())
            shares_to_sell = int(total_shares * reduction_amount)

            for entry in self.active_positions.keys():
                if self.active_positions[entry] > 0:
                    share_reduction = int(
                        (self.active_positions[entry] / total_shares) * shares_to_sell
                    )
                    self.active_positions[entry] -= share_reduction
                    proceeds = share_reduction * current_price
                    self.cash += proceeds

                    # Record reduction trade
                    self.trades.append({
                        'Date': date,
                        'Type': f'REDUCE_{entry}',
                        'Shares': -share_reduction,
                        'Price': current_price,
                        'Value': proceeds,
                        'Cash': self.cash
                    })

    def record_daily_position(self, date, current_price):
        """Record daily position information"""
        total_position_value = sum(
            self.active_positions[entry] * current_price
            for entry in self.active_positions.keys()
        )

        self.daily_positions.append({
            'Date': date,
            'Portfolio_Value': self.cash + total_position_value,
            'Cash': self.cash,
            'Exposure': self.get_total_exposure(),
            'Total_Shares': sum(self.active_positions.values()),
            'Price': current_price
        })

    def run_backtest(self):
        """Run through historical data and execute trades"""
        for date in self.price_data.index:
            current_price = self.price_data.loc[date, 'Close']
            signals = self.signals_data.loc[date]

            # Check exit conditions
            if signals['Exit'] and sum(self.active_positions.values()) > 0:
                avg_entry = self.get_average_entry_price()
                if current_price >= avg_entry * 1.20:
                    for entry_type in self.active_positions.keys():
                        if self.active_positions[entry_type] > 0:
                            self.exit_position(entry_type, current_price, date)

            # Check break-even reduction
            avg_entry = self.get_average_entry_price()
            if avg_entry > 0 and self.get_total_exposure() > 0.75:
                if current_price >= avg_entry:
                    self.reduce_position(current_price, date)

            # Check entry conditions
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