#!/usr/bin/env python3
"""
Test script for Phase 2 backtest strategies
"""
import sys
import asyncio
from datetime import datetime

# Add backend to path
sys.path.insert(0, 'backend')

from models.backtest import BacktestConfig
from engines.backtest import engine


async def test_strategy(strategy_name, ticker="AAPL"):
    """Test a single strategy"""
    print(f"\n{'='*60}")
    print(f"Testing: {strategy_name} on {ticker}")
    print(f"{'='*60}")

    config = BacktestConfig(
        strategy_type=strategy_name,
        ticker=ticker,
        start_date="2023-01-01",
        end_date="2024-01-01",
        initial_capital=100000.0,
        position_size=1.0,
        commission=0.001,
        slippage=0.001,
        stop_loss=0.10,  # 10% stop loss
        take_profit=0.20,  # 20% take profit
    )

    try:
        result = await engine.run_backtest(config)

        print(f"\n✅ {strategy_name.upper()} Results:")
        print(f"   Total Return: {result.total_return:.2%}")
        print(f"   Annual Return: {result.annual_return:.2%}")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"   Max Drawdown: {result.max_drawdown:.2%}")
        print(f"   Total Trades: {result.total_trades}")
        print(f"   Win Rate: {result.win_rate:.2%}")
        print(f"   Profit Factor: {result.profit_factor:.2f}")
        print(f"   Final Value: ${result.final_value:,.2f}")
        print(f"   Benchmark Return: {result.benchmark_return:.2%}")
        print(f"   Alpha: {result.alpha:.2%}")

        if result.total_trades > 0:
            print(f"\n   Trade Details:")
            for i, trade in enumerate(result.trades[:3], 1):  # Show first 3 trades
                print(f"     Trade {i}: {trade.entry_date} → {trade.exit_date}")
                print(f"       Entry: ${trade.entry_price:.2f}, Exit: ${trade.exit_price:.2f}")
                print(f"       P&L: ${trade.pnl:.2f} ({trade.return_pct:.2%})")
                print(f"       Reason: {trade.entry_reason} → {trade.exit_reason}")
            if result.total_trades > 3:
                print(f"     ... and {result.total_trades - 3} more trades")

        return True

    except Exception as e:
        print(f"\n❌ {strategy_name.upper()} Failed:")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test all Phase 2 strategies"""
    print("="*60)
    print("PHASE 2 BACKTEST STRATEGY TESTING")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing 7 strategies on AAPL (2023-01-01 to 2024-01-01)")

    strategies = [
        "buy_hold",      # Phase 1
        "rsi_reversal",  # Phase 1
        "macd_cross",    # Phase 2
        "ma_cross",      # Phase 2
        "bb_breakout",   # Phase 2
        "momentum",      # Phase 2
        "multi_factor",  # Phase 2
    ]

    results = {}
    for strategy in strategies:
        success = await test_strategy(strategy)
        results[strategy] = success
        await asyncio.sleep(1)  # Brief pause between tests

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nTests Passed: {passed}/{total}")
    for strategy, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {strategy}")

    if passed == total:
        print(f"\n🎉 All Phase 2 strategies are working correctly!")
    else:
        print(f"\n⚠️  Some strategies failed - check errors above")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
