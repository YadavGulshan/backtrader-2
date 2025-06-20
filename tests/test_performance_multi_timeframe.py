#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2025 Gulshan Yadav
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import gc
import os

import testcommon

import backtrader as bt
import backtrader.indicators as btind

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MultiTimeframeStrategy(bt.Strategy):
    """
    Performance testing strategy using multiple timeframes.

    This strategy tests performance impact of using multiple timeframes
    (1min, 5min, 15min, 30min) with indicators applied to each timeframe.
    """

    params = (
        ("printdata", False),
        ("sma_period", 20),
        ("ema_period", 12),
        ("rsi_period", 14),
        ("macd_fast", 12),
        ("macd_slow", 26),
        ("bb_period", 20),
    )

    def log(self, txt, dt=None):
        if self.p.printdata:
            dt = dt or self.datas[0].datetime[0]
            dt = bt.num2date(dt)
            print(f"{dt.isoformat()}, {txt}")

    def __init__(self):
        self.bars_processed = 0
        self.timeframes_used = 0
        self.indicators_created = 0
        self.order_count = 0

        # Expect 4 data feeds: 1min, 5min, 15min, 30min
        self.timeframes_used = len(self.datas)
        
        # Indicators for 1-minute timeframe
        if len(self.datas) > 0:
            self.data_1min = self.datas[0]
            self.sma_1min = btind.SMA(self.data_1min, period=self.p.sma_period)
            self.ema_1min = btind.EMA(self.data_1min, period=self.p.ema_period)
            self.rsi_1min = btind.RSI(self.data_1min, period=self.p.rsi_period)
            self.indicators_created += 3
        else:
            self.data_1min = None

        # Indicators for 5-minute timeframe
        if len(self.datas) > 1:
            self.data_5min = self.datas[1]
            self.sma_5min = btind.SMA(self.data_5min, period=self.p.sma_period)
            self.ema_5min = btind.EMA(self.data_5min, period=self.p.ema_period)
            self.macd_5min = btind.MACD(
                self.data_5min, period_me1=self.p.macd_fast, period_me2=self.p.macd_slow
            )
            self.indicators_created += 3
        else:
            self.data_5min = None

        # Indicators for 15-minute timeframe
        if len(self.datas) > 2:
            self.data_15min = self.datas[2]
            self.sma_15min = btind.SMA(self.data_15min, period=self.p.sma_period)
            self.bb_15min = btind.BollingerBands(
                self.data_15min, period=self.p.bb_period
            )
            self.rsi_15min = btind.RSI(self.data_15min, period=self.p.rsi_period)
            self.indicators_created += 3
        else:
            self.data_15min = None

        # Indicators for 30-minute timeframe
        if len(self.datas) > 3:
            self.data_30min = self.datas[3]
            self.sma_30min = btind.SMA(self.data_30min, period=self.p.sma_period)
            self.ema_30min = btind.EMA(self.data_30min, period=self.p.ema_period)
            self.macd_30min = btind.MACD(
                self.data_30min,
                period_me1=self.p.macd_fast,
                period_me2=self.p.macd_slow,
            )
            self.indicators_created += 3
        else:
            self.data_30min = None

        # Multi-timeframe trading signals
        self._setup_trading_signals()

        if self.p.printdata:
            self.log(f"Strategy initialized with {self.timeframes_used} timeframes")
            self.log(f"Total indicators created: {self.indicators_created}")

    def _setup_trading_signals(self):
        """Setup trading signals using multiple timeframes."""
        # Long-term trend from 30min
        self.long_term_trend = None
        if self.data_30min is not None:
            self.long_term_trend = self.data_30min.close > self.sma_30min

        # Medium-term trend from 15min
        self.medium_term_trend = None
        if self.data_15min is not None:
            self.medium_term_trend = self.data_15min.close > self.sma_15min

        # Short-term signals from 5min
        self.short_term_signal = None
        if self.data_5min is not None:
            self.short_term_signal = bt.And(
                self.data_5min.close > self.sma_5min,
                self.macd_5min.macd > self.macd_5min.signal,
            )

        # Entry timing from 1min
        self.entry_timing = None
        if self.data_1min is not None:
            self.entry_timing = bt.And(
                self.rsi_1min < 70, self.data_1min.close > self.ema_1min
            )

    def start(self):
        self.start_time = testcommon.time_clock()
        if self.p.printdata:
            self.log("Multi-timeframe strategy starting")

    def stop(self):
        self.total_time = testcommon.time_clock() - self.start_time
        if self.p.printdata:
            self.log(f"Strategy completed in {self.total_time:.4f} seconds")
            self.log(f"Total bars processed: {self.bars_processed}")
            self.log(f"Orders placed: {self.order_count}")
            if self.bars_processed > 0:
                self.log(
                    f"Time per bar: {self.total_time/self.bars_processed:.6f} seconds"
                )

    def next(self):
        self.bars_processed += 1

        # Multi-timeframe trading logic
        if not self.position:
            # All conditions must align for buy signal
            buy_conditions = []
            if self.long_term_trend is not None:
                buy_conditions.append(self.long_term_trend[0])
            if self.medium_term_trend is not None:
                buy_conditions.append(self.medium_term_trend[0])
            if self.short_term_signal is not None:
                buy_conditions.append(self.short_term_signal[0])
            if self.entry_timing is not None:
                buy_conditions.append(self.entry_timing[0])

            if all(buy_conditions) and len(buy_conditions) > 0:
                self.buy()
                self.order_count += 1
                if self.p.printdata:
                    self.log(f"BUY CREATE, Price: {self.data_1min.close[0]:.2f}")
        else:
            # Simple exit on 1min RSI overbought
            if self.data_1min is not None and self.rsi_1min[0] > 80:
                self.sell()
                self.order_count += 1
                if self.p.printdata:
                    self.log(f"SELL CREATE, Price: {self.data_1min.close[0]:.2f}")


class TestMultiTimeframePerformance:
    """Test class for multi-timeframe strategy performance testing."""

    def test_multi_timeframe_strategy_performance(self):
        """
        Test performance with 4 timeframes: 1min, 5min, 15min, 30min.
        """
        print("=" * 80)
        print("TESTING MULTI-TIMEFRAME STRATEGY PERFORMANCE")
        print("Timeframes: 1min, 5min, 15min, 30min")
        print("Indicators: 3 per timeframe (12 total)")
        print("=" * 80)

        cerebro = bt.Cerebro()

        # Add base 1-minute data
        data_1min = testcommon.getdata(2)
        cerebro.adddata(data_1min, name="1min")

        # Create resampled data for other timeframes using backtrader resampling
        data_5min = cerebro.resampledata(
            data_1min, timeframe=bt.TimeFrame.Minutes, compression=5, name="5min"
        )

        data_15min = cerebro.resampledata(
            data_1min, timeframe=bt.TimeFrame.Minutes, compression=15, name="15min"
        )

        data_30min = cerebro.resampledata(
            data_1min, timeframe=bt.TimeFrame.Minutes, compression=30, name="30min"
        )

        cerebro.addstrategy(MultiTimeframeStrategy, printdata=False)
        cerebro.broker.setcash(10000.0)

        print("Running multi-timeframe strategy...")

        start_time = testcommon.time_clock()
        strategies = cerebro.run(stdstats=False)
        end_time = testcommon.time_clock()

        total_execution_time = end_time - start_time
        strategy = strategies[0]

        print(f"Execution time: {total_execution_time:.4f}s")
        print(f"Timeframes used: {strategy.timeframes_used}")
        print(f"Bars processed: {strategy.bars_processed}")
        print(f"Indicators created: {strategy.indicators_created}")
        print(f"Orders placed: {strategy.order_count}")
        print(f"Time per bar: {total_execution_time/strategy.bars_processed:.6f}s")
        print(f"Final portfolio value: ${cerebro.broker.getvalue():.2f}")

        # Performance metrics
        throughput = strategy.bars_processed / total_execution_time
        print(f"Throughput: {throughput:.0f} bars/second")

        # Assertions
        assert (
            strategy.timeframes_used == 4
        ), f"Expected 4 timeframes, got {strategy.timeframes_used}"
        assert (
            strategy.indicators_created == 12
        ), f"Expected 12 indicators, got {strategy.indicators_created}"
        assert (
            strategy.bars_processed > 10000
        ), f"Expected >10k bars, got {strategy.bars_processed}"
        assert total_execution_time > 0, "Execution time should be positive"
        assert total_execution_time < 120, "Should complete within 120 seconds"
        assert throughput > 50, "Should process at least 50 bars per second"

        return {
            "total_execution_time": total_execution_time,
            "timeframes_used": strategy.timeframes_used,
            "bars_processed": strategy.bars_processed,
            "indicators_created": strategy.indicators_created,
            "orders_placed": strategy.order_count,
            "final_value": cerebro.broker.getvalue(),
            "throughput": throughput,
        }

    def test_timeframe_scaling_performance(self):
        """
        Test how performance scales with increasing number of timeframes.
        """
        print("\nTIMEFRAME SCALING PERFORMANCE TEST:")
        print("=" * 50)

        results = []

        # Test with 1, 2, 3, and 4 timeframes
        for num_timeframes in [1, 2, 3, 4]:
            print(f"\nTesting with {num_timeframes} timeframe(s)...")

            cerebro = bt.Cerebro()

            # Add base data
            data_1min = testcommon.getdata(2)
            cerebro.adddata(data_1min, name="1min")

            # Add additional timeframes based on test
            if num_timeframes >= 2:
                data_5min = cerebro.resampledata(
                    data_1min,
                    timeframe=bt.TimeFrame.Minutes,
                    compression=5,
                    name="5min",
                )

            if num_timeframes >= 3:
                data_15min = cerebro.resampledata(
                    data_1min,
                    timeframe=bt.TimeFrame.Minutes,
                    compression=15,
                    name="15min",
                )

            if num_timeframes >= 4:
                data_30min = cerebro.resampledata(
                    data_1min,
                    timeframe=bt.TimeFrame.Minutes,
                    compression=30,
                    name="30min",
                )

            cerebro.addstrategy(MultiTimeframeStrategy, printdata=False)
            cerebro.broker.setcash(10000.0)

            start_time = testcommon.time_clock()
            strategies = cerebro.run(stdstats=False)
            end_time = testcommon.time_clock()

            execution_time = end_time - start_time
            strategy = strategies[0]

            result = {
                "timeframes": num_timeframes,
                "execution_time": execution_time,
                "bars_processed": strategy.bars_processed,
                "indicators_created": strategy.indicators_created,
                "throughput": strategy.bars_processed / execution_time,
            }
            results.append(result)

            print(
                f"  {num_timeframes} timeframes: {execution_time:.4f}s, "
                f"{result['indicators_created']} indicators, "
                f"{result['throughput']:.0f} bars/sec"
            )

        # Analyze scaling efficiency
        base_time = results[0]["execution_time"]
        print(f"\nScaling analysis (baseline: {base_time:.4f}s):")

        for result in results[1:]:
            scaling_factor = result["execution_time"] / base_time
            timeframes_ratio = result["timeframes"] / results[0]["timeframes"]
            efficiency = timeframes_ratio / scaling_factor

            print(
                f"  {result['timeframes']} timeframes: {scaling_factor:.2f}x slower, "
                f"efficiency: {efficiency:.2f}"
            )

            # Assert reasonable scaling (allow for more overhead with multiple timeframes)
            assert (
                scaling_factor < result["timeframes"] * 3.0
            ), f"Scaling should be reasonable, got {scaling_factor:.2f}x for {result['timeframes']}x timeframes"

        return results

    def test_memory_efficiency_multi_timeframe(self):
        """
        Test memory efficiency with multiple timeframes.
        """
        if not HAS_PSUTIL:
            print("Skipping memory test (psutil not available)")
            return None

        process = psutil.Process(os.getpid())
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"\nInitial memory usage: {initial_memory:.1f} MB")

        # Run multi-timeframe test
        result = self.test_multi_timeframe_strategy_performance()

        # Final memory
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print("\nMEMORY EFFICIENCY MULTI-TIMEFRAME TEST:")
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Final memory: {final_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")
        print(f"Memory per timeframe: {memory_increase / 4:.2f} MB/timeframe")
        print(
            f"Memory per bar: {memory_increase * 1024 / result['bars_processed']:.3f} KB/bar"
        )

        # Assertions
        assert (
            memory_increase < 300
        ), f"Memory increase should be <300MB, got {memory_increase:.1f}MB"
        assert result["bars_processed"] > 10000

        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "memory_per_timeframe_mb": memory_increase / 4,
            "memory_per_bar_kb": memory_increase * 1024 / result["bars_processed"],
            **result,
        }


def test_run_multi_timeframe_performance_suite():
    """
    Main test function for comprehensive multi-timeframe performance testing.
    """
    test_instance = TestMultiTimeframePerformance()

    print("=" * 80)
    print("BACKTRADER MULTI-TIMEFRAME PERFORMANCE TEST SUITE")
    print("Testing: 1min, 5min, 15min, 30min timeframes")
    print("Indicators: 3 per timeframe")
    print("=" * 80)

    # Run comprehensive tests
    print("1. Testing multi-timeframe strategy performance...")
    performance_results = test_instance.test_multi_timeframe_strategy_performance()

    print("\n2. Testing timeframe scaling performance...")
    scaling_results = test_instance.test_timeframe_scaling_performance()

    print("\n3. Testing memory efficiency...")
    memory_results = test_instance.test_memory_efficiency_multi_timeframe()

    print("\n" + "=" * 80)
    print("MULTI-TIMEFRAME PERFORMANCE SUITE COMPLETED SUCCESSFULLY")
    print(
        f"Final test: {performance_results['timeframes_used']} timeframes, "
        f"{performance_results['indicators_created']} indicators"
    )
    print(f"Execution time: {performance_results['total_execution_time']:.4f}s")
    print(f"Throughput: {performance_results['throughput']:.0f} bars/second")
    print("=" * 80)

    return {
        "performance_results": performance_results,
        "scaling_results": scaling_results,
        "memory_results": memory_results,
    }


if __name__ == "__main__":
    test_run_multi_timeframe_performance_suite()
