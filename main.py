from data_processor import SPXLDataProcessor
from signal_generator import SignalGenerator
from position_manager import PositionManager
from portfolio_tracker import PortfolioTracker
from performance_analyzer import PerformanceAnalyzer

def main(years=1, force_download=False):
    # Initialize and load data
    processor = SPXLDataProcessor()
    processor.load_or_download_data(years=years, force_download=force_download)

    # Process data and generate signals
    data = processor.calculate_signals()
    signal_gen = SignalGenerator(data)
    signals = signal_gen.generate_signals()

    # Initialize position manager and run backtest
    position_manager = PositionManager(data, signals)
    trades_df, positions_df = position_manager.run_backtest()

    # Save intermediate results
    trades_df.to_csv('trades.csv')
    positions_df.to_csv('positions.csv')
    signals.to_csv('trading_signals.csv')

    # Initialize portfolio tracker and run analysis
    portfolio_tracker = PortfolioTracker(trades_df, positions_df)
    portfolio_stats = portfolio_tracker.track_portfolio()

    # Print basic portfolio summary
    current_state = portfolio_tracker.get_current_portfolio_state()
    print("\nBasic Portfolio Summary:")
    print("-" * 30)
    print(f"Final Portfolio Value: ${current_state['Portfolio_Value']:,.2f}")
    print(f"Total P&L: ${current_state['Total_PnL']:,.2f}")
    print(f"Current Cash: ${current_state['Cash']:,.2f}")
    print(f"Current Exposure: {current_state['Exposure']:.2%}")

    # Run performance analysis
    print("\nGenerating detailed performance analysis...")
    analyzer = PerformanceAnalyzer(portfolio_stats)
    print(analyzer.generate_summary_report())

    print("\nBacktest completed!")
    return portfolio_stats, analyzer  # Return for interactive analysis if needed

if __name__ == "__main__":
    portfolio_stats, analyzer = main(years=10, force_download=True)