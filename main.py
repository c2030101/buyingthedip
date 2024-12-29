from data_processor import SPXLDataProcessor
from signal_generator import SignalGenerator
from position_manager import PositionManager
from portfolio_tracker import PortfolioTracker
from performance_analyzer import PerformanceAnalyzer
import pandas as pd
import json
from datetime import datetime
import os


def create_trade_summary(trades_df, positions_df, output_dir='./output'):
    """Create a simplified trade summary focusing on entries and exits"""
    os.makedirs(output_dir, exist_ok=True)

    # Ensure trades DataFrame has the correct date format and reset index if needed
    if isinstance(trades_df.index, pd.DatetimeIndex):
        trades_df = trades_df.reset_index()
        trades_df = trades_df.rename(columns={'index': 'Date'})

    # Convert any remaining Timestamp objects to strings
    if 'Date' in trades_df.columns:
        trades_df['Date'] = trades_df['Date'].astype(str)

    # Save trades CSV
    trades_df.to_csv(os.path.join(output_dir, 'trades.csv'), index=False)

    # Create trade sequences for analysis
    trade_sequences = []
    current_sequence = {'entries': [], 'exits': []}

    for _, trade in trades_df.iterrows():
        trade_info = {
            'date': str(trade['Date']),  # Ensure date is string
            'price': float(round(trade['Price'], 2)),  # Ensure price is float
            'shares': int(abs(trade['Shares'])),  # Ensure shares is int
            'value': float(round(abs(trade['Value']), 2))  # Ensure value is float
        }

        if 'ENTER' in trade['Type']:
            current_sequence['entries'].append({
                **trade_info,
                'type': str(trade['Type']).replace('ENTER_', '')  # Ensure type is string
            })
        elif 'EXIT' in trade['Type']:
            current_sequence['exits'].append({
                **trade_info,
                'type': str(trade['Type']).replace('EXIT_', '')  # Ensure type is string
            })
            if current_sequence['entries']:
                trade_sequences.append(current_sequence)
                current_sequence = {'entries': [], 'exits': []}

    # Add last sequence if it has entries
    if current_sequence['entries']:
        trade_sequences.append(current_sequence)

    # Save trade sequences as JSON
    with open(os.path.join(output_dir, 'trade_sequences.json'), 'w') as f:
        json.dump(trade_sequences, f, indent=2, default=str)  # Use default=str for any remaining datetime objects

    return trade_sequences
def create_html_report(trade_sequences, performance_metrics, output_dir='./output'):
    """Create a detailed HTML report"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SPXL Trading Strategy Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
            .header { background: #f8f9fa; padding: 20px; margin-bottom: 20px; }
            .metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 30px; }
            .metric-card { background: #fff; padding: 15px; border: 1px solid #ddd; }
            .sequence { background: #fff; border: 1px solid #ddd; margin: 10px 0; padding: 15px; }
            .entries { color: #28a745; }
            .exits { color: #dc3545; }
            h2 { color: #333; }
            .metric-title { font-weight: bold; color: #666; }
            .metric-value { font-size: 1.2em; color: #333; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SPXL Trading Strategy Analysis</h1>
            <p>Strategy: Multiple Entry Points with 20% Profit Target</p>
        </div>

        <h2>Performance Metrics</h2>
        <div class="metrics">
    """

    # Add performance metrics
    for key, value in performance_metrics.items():
        formatted_key = key.replace('_', ' ').title()
        formatted_value = f"{value:,.2f}%" if 'return' in key.lower() or 'drawdown' in key.lower() else f"{value:,.2f}"
        html += f"""
            <div class="metric-card">
                <div class="metric-title">{formatted_key}</div>
                <div class="metric-value">{formatted_value}</div>
            </div>
        """

    html += """
        </div>
        <h2>Trade Sequences</h2>
    """

    # Add trade sequences
    for idx, sequence in enumerate(trade_sequences):
        html += f"""
        <div class="sequence">
            <h3>Trade Sequence #{idx + 1}</h3>
            <div class="entries">
                <h4>Entries:</h4>
                {''.join(f'<p>{entry["date"]} - {entry["type"]} @ ${entry["price"]} ({entry["shares"]} shares)</p>'
                         for entry in sequence['entries'])}
            </div>
        """

        if sequence['exits']:
            html += f"""
            <div class="exits">
                <h4>Exits:</h4>
                {''.join(f'<p>{exit["date"]} - {exit["type"]} @ ${exit["price"]} ({exit["shares"]} shares)</p>'
                         for exit in sequence['exits'])}
            </div>
            """

        html += "</div>"

    html += """
    </body>
    </html>
    """

    # Save HTML report
    with open(os.path.join(output_dir, 'strategy_report.html'), 'w') as f:
        f.write(html)


def main(years=5, initial_capital=100000, force_download=False):
    """Main function to run the SPXL trading strategy"""
    print(f"\nInitializing SPXL Trading Strategy Backtest")
    print(f"{'=' * 50}")
    print(f"Settings:")
    print(f"- Test Period: {years} years")
    print(f"- Initial Capital: ${initial_capital:,}")
    print(f"- Force Download: {force_download}")
    print(f"{'=' * 50}\n")

    # Create output directory
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)

    # Initialize and load data
    print("Loading SPXL data...")
    processor = SPXLDataProcessor()
    processor.load_or_download_data(years=years, force_download=force_download)
    data = processor.calculate_signals()

    # Generate trading signals
    print("\nGenerating trading signals...")
    signal_gen = SignalGenerator(data)
    signals = signal_gen.generate_signals()

    # Run backtest
    print("\nRunning backtest...")
    position_manager = PositionManager(data, signals, initial_capital=initial_capital)
    trades_df, positions_df = position_manager.run_backtest()

    # Create trade summary
    print("\nAnalyzing trade sequences...")
    trade_sequences = create_trade_summary(trades_df, positions_df, output_dir)

    # Calculate performance metrics
    print("\nCalculating performance metrics...")
    portfolio_tracker = PortfolioTracker(trades_df, positions_df)
    portfolio_stats = portfolio_tracker.track_portfolio()

    # Generate performance analysis
    analyzer = PerformanceAnalyzer(portfolio_stats)
    performance_metrics = {
        'total_return': portfolio_stats['positions']['Portfolio_Value'].iloc[-1] / initial_capital * 100 - 100,
        'max_drawdown': analyzer.metrics['drawdown']['max_drawdown'],
        'win_rate': analyzer.metrics['trades']['win_rate'],
        'profit_factor': analyzer.metrics['trades']['profit_factor'],
        'total_trades': analyzer.metrics['trades']['total_trades']
    }

    # Create HTML report
    create_html_report(trade_sequences, performance_metrics, output_dir)

    # Print summary
    print("\nStrategy Performance Summary:")
    print(f"{'=' * 50}")
    print(f"Total Return: {performance_metrics['total_return']:.2f}%")
    print(f"Maximum Drawdown: {performance_metrics['max_drawdown']:.2f}%")
    print(f"Win Rate: {performance_metrics['win_rate']:.2f}%")
    print(f"Profit Factor: {performance_metrics['profit_factor']:.2f}")
    print(f"Total Trades: {performance_metrics['total_trades']}")
    print(f"{'=' * 50}")

    print(f"\nDetailed reports have been saved to {output_dir}/")
    print("- trades.csv: Complete trade list")
    print("- trade_sequences.json: Detailed trade sequences")
    print("- strategy_report.html: Visual strategy report")

    return portfolio_stats, analyzer


if __name__ == "__main__":
    portfolio_stats, analyzer = main(years=5, initial_capital=100000, force_download=True)