#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# VWAP Indicator Test Sample
#
# This sample demonstrates the usage of the different VWAP indicators
# available in backtrader:
# 1. VolumeWeightedAveragePrice (VWAP) - Cumulative VWAP
# 2. SessionVWAP (SVWAP) - Session-based VWAP that resets daily
# 3. WeightedVWAP (WVWAP) - Rolling window VWAP
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime

import backtrader as bt


class VWAPStrategy(bt.Strategy):
    '''
    Strategy to demonstrate VWAP indicators usage
    '''
    params = (
        ('printlog', True),
        ('vwap_period', 14),  # Period for the rolling VWAP
    )

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume

        # Add VWAP indicators
        self.vwap = bt.indicators.VWAP(self.data)
        self.session_vwap = bt.indicators.SessionVWAP(self.data)
        self.rolling_vwap = bt.indicators.WeightedVWAP(self.data, period=self.p.vwap_period)

        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        if len(self.data) < self.p.vwap_period:
            return  # Wait for enough data
            
        current_price = self.dataclose[0]
        vwap_value = self.vwap[0]
        session_vwap_value = self.session_vwap[0]
        rolling_vwap_value = self.rolling_vwap[0]
        
        self.log(f'Close: {current_price:.2f}, '
                f'VWAP: {vwap_value:.2f}, '
                f'Session VWAP: {session_vwap_value:.2f}, '
                f'Rolling VWAP({self.p.vwap_period}): {rolling_vwap_value:.2f}')

        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if current_price > vwap_value:
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % current_price)
                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:
            # Already in the market ... we might sell
            if current_price < vwap_value:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % current_price)
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


def runstrat():
    args = parse_args()

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(VWAPStrategy, 
                       printlog=args.printlog,
                       vwap_period=args.vwap_period)

    # Get the data
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, args.data)

    # Create a Data Feed
    if args.fromdate:
        fromdate = datetime.datetime.strptime(args.fromdate, '%Y-%m-%d')
    else:
        fromdate = None

    if args.todate:
        todate = datetime.datetime.strptime(args.todate, '%Y-%m-%d')
    else:
        todate = None

    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        fromdate=fromdate,
        todate=todate,
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(args.cash)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    result = cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Print analyzer results
    strat = result[0]
    print('Sharpe Ratio:', strat.analyzers.sharpe.get_analysis())
    print('DrawDown:', strat.analyzers.drawdown.get_analysis())

    # Plot the results
    if args.plot:
        cerebro.plot(style='bar', 
                    numfigs=args.numfigs, 
                    volume=True,
                    zdown=False)


def parse_args():
    parser = argparse.ArgumentParser(
        description='VWAP Indicator Sample')

    parser.add_argument('--data', '-d',
                        default='../../datas/orcl-1995-2014.txt',
                        help='Data to read in')

    parser.add_argument('--fromdate', '-f',
                        default='2005-01-01',
                        help='Starting date in YYYY-MM-DD format')

    parser.add_argument('--todate', '-t',
                        default='2006-12-31',
                        help='Ending date in YYYY-MM-DD format')

    parser.add_argument('--cash',
                        default=10000, type=int,
                        help='Starting Cash')

    parser.add_argument('--vwap-period',
                        default=14, type=int,
                        help='Period for rolling VWAP calculation')

    parser.add_argument('--plot', '-p', action='store_true',
                        help='Plot the read data')

    parser.add_argument('--numfigs', '-n', default=1, type=int,
                        help='Plot using numfigs figures')

    parser.add_argument('--printlog', action='store_true',
                        help='Print log of trades')

    return parser.parse_args()


if __name__ == '__main__':
    import os
    import sys
    runstrat() 