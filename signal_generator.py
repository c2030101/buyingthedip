import pandas as pd
import numpy as np


class SignalGenerator:
    def __init__(self, data):
        self.data = data.copy()
        self.signals = pd.DataFrame(index=self.data.index)

        # Initialize signal columns
        for i in range(1, 6):
            self.signals[f'Entry{i}'] = False
        self.signals['Exit'] = False

    def generate_signals(self):
        """Generate trading signals based on specified rules"""
        # Calculate 20-day rolling high
        self.data['RollingHigh'] = self.data['High'].rolling(window=20, min_periods=1).max()

        # Track state
        in_trade = False
        entry_prices = {}
        current_entry = 0

        for i in range(20, len(self.data)):  # Start after enough data for rolling window
            current_price = self.data['Close'].iloc[i]

            if not in_trade:
                # Look for first entry - 15% drop from rolling high
                rolling_high = self.data['RollingHigh'].iloc[i]
                drawdown = ((current_price - rolling_high) / rolling_high) * 100

                if drawdown <= -15:
                    self.signals.loc[self.signals.index[i], 'Entry1'] = True
                    entry_prices[1] = current_price
                    current_entry = 1
                    in_trade = True

            else:
                # Check for additional entries if we're in a trade
                last_entry_price = entry_prices[current_entry]

                if current_entry == 1:
                    # Check for second entry - 10% drop from first entry
                    drawdown = ((current_price - last_entry_price) / last_entry_price) * 100
                    if drawdown <= -10:
                        self.signals.loc[self.signals.index[i], 'Entry2'] = True
                        entry_prices[2] = current_price
                        current_entry = 2

                elif current_entry == 2:
                    # Check for third entry - 7% drop from second entry
                    drawdown = ((current_price - last_entry_price) / last_entry_price) * 100
                    if drawdown <= -7:
                        self.signals.loc[self.signals.index[i], 'Entry3'] = True
                        entry_prices[3] = current_price
                        current_entry = 3

                elif current_entry == 3:
                    # Check for fourth entry - 10% drop from third entry
                    drawdown = ((current_price - last_entry_price) / last_entry_price) * 100
                    if drawdown <= -10:
                        self.signals.loc[self.signals.index[i], 'Entry4'] = True
                        entry_prices[4] = current_price
                        current_entry = 4

                elif current_entry == 4:
                    # Check for fifth entry - 10% drop from fourth entry
                    drawdown = ((current_price - last_entry_price) / last_entry_price) * 100
                    if drawdown <= -10:
                        self.signals.loc[self.signals.index[i], 'Entry5'] = True
                        entry_prices[5] = current_price
                        current_entry = 5

                # Check for exit condition - 20% gain from average entry
                if len(entry_prices) > 0:
                    # Calculate weighted average entry price
                    weights = {1: 0.20, 2: 0.15, 3: 0.20, 4: 0.20, 5: 0.15}
                    total_weight = sum(weights[k] for k in entry_prices.keys())
                    avg_entry = sum(price * weights[k] / total_weight
                                    for k, price in entry_prices.items())

                    gain = ((current_price - avg_entry) / avg_entry) * 100
                    if gain >= 20:
                        self.signals.loc[self.signals.index[i], 'Exit'] = True
                        # Reset state
                        in_trade = False
                        entry_prices = {}
                        current_entry = 0

        # Print signal summary
        entry_signals = self.signals[self.signals.filter(like='Entry').any(axis=1)]
        exit_signals = self.signals[self.signals['Exit']]

        print(f"\nSignal Generation Summary:")
        print(f"Number of Entry Signals: {len(entry_signals)}")
        print(f"Number of Exit Signals: {len(exit_signals)}")

        if len(entry_signals) > 0:
            print("\nFirst few entry signals:")
            print(entry_signals.head())

        return self.signals