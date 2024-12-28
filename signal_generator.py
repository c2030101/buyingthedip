
import pandas as pd


class SignalGenerator:
    def __init__(self, data):
        self.data = data

    def generate_signals(self):
        signals = pd.DataFrame(index=self.data.index)

        # Entry signals
        signals['Entry1'] = self.data['DrawdownPct'] <= -15
        signals['Entry2'] = self.data['DrawdownPct'] <= -25
        signals['Entry3'] = self.data['DrawdownPct'] <= -32
        signals['Entry4'] = self.data['DrawdownPct'] <= -42
        signals['Entry5'] = self.data['DrawdownPct'] <= -52

        # Exit signal
        signals['Exit'] = (self.data['Close'].pct_change(20) * 100) >= 20

        return signals
