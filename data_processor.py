import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os


class SPXLDataProcessor:
    def __init__(self):
        self.data = None

    def load_or_download_data(self, filename='spxl_data.csv', years=5, force_download=False):
        if not force_download and os.path.exists(filename):
            try:
                self.data = pd.read_csv(filename)
                self.data.index = pd.to_datetime(self.data['Date'] if 'Date' in self.data.columns else self.data.index)

                data_years = (self.data.index.max() - self.data.index.min()).days / 365
                if abs(data_years - years) > 0.1:
                    print(f"Existing data range ({data_years:.1f} years) differs from requested range ({years} years)")
                    force_download = True
                else:
                    print("Found saved data file with correct date range!")

            except Exception as e:
                print(f"Error loading saved data: {e}")
                force_download = True

        if force_download or not os.path.exists(filename):
            print("Downloading new data...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=int(years * 365))

            try:
                self.data = yf.download('SPXL', start=start_date, end=end_date)

                # Handle multi-index columns if they exist
                if isinstance(self.data.columns, pd.MultiIndex):
                    # Keep only the column names without the 'SPXL' level
                    self.data.columns = self.data.columns.get_level_values(0)

                self.data.to_csv(filename)
                print(f"Downloaded and saved new {years}-year data!")
            except Exception as e:
                print(f"Error downloading data: {e}")
                raise

        print("\nFirst 5 rows of data:")
        print(self.data.head())
        print("\nData range:", self.data.index.min().strftime('%Y-%m-%d'),
              "to", self.data.index.max().strftime('%Y-%m-%d'))
        print("\nData columns:", self.data.columns.tolist())

    def calculate_signals(self):
        # Make sure data is numeric
        numeric_cols = ['Open', 'High', 'Low', 'Close']
        for col in numeric_cols:
            if col in self.data.columns:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            else:
                raise ValueError(f"Required column {col} not found in data")

        # Calculate local highs
        self.data['LocalHigh'] = self.data['High'].rolling(window=20).max()

        # Calculate drawdown
        self.data['DrawdownPct'] = (
                (self.data['Close'] - self.data['LocalHigh']) /
                self.data['LocalHigh'] * 100
        ).round(2)

        return self.data