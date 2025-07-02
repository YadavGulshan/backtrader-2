#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
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

import backtrader as bt
from . import Indicator


__all__ = ['VolumeWeightedAveragePrice', 'VWAP', 'SessionVWAP', 'WeightedVWAP']


class VolumeWeightedAveragePrice(Indicator):
    '''
    Volume Weighted Average Price (VWAP) is a trading benchmark used by traders
    that gives the average price a security has traded at throughout the day,
    based on both volume and price.

    VWAP is calculated by adding up the dollars traded for every transaction
    (price multiplied by volume) and then dividing by the total shares traded
    for the day.

    Formula:
      - typical_price = (high + low + close) / 3
      - cumulative_pv = cumulative_sum(typical_price * volume)
      - cumulative_vol = cumulative_sum(volume)
      - vwap = cumulative_pv / cumulative_vol

    See:
      - https://en.wikipedia.org/wiki/Volume-weighted_average_price
      - https://www.investopedia.com/terms/v/vwap.asp
    '''
    alias = ('VWAP',)
    lines = ('vwap',)

    plotinfo = dict(subplot=False)

    def __init__(self):
        # Calculate typical price (HLC/3)
        typical_price = (self.data.high + self.data.low + self.data.close) / 3.0
        
        # Calculate price * volume
        price_volume = typical_price * self.data.volume
        
        # Cumulative sums using the built-in Accum indicator
        self.cum_pv = bt.indicators.Accum(price_volume)
        self.cum_vol = bt.indicators.Accum(self.data.volume)
        
        # VWAP calculation
        self.lines.vwap = self.cum_pv / self.cum_vol
        
        super(VolumeWeightedAveragePrice, self).__init__()


class SessionVWAP(Indicator):
    '''
    Session-based Volume Weighted Average Price (VWAP) that resets at the
    beginning of each trading session.

    This version is more commonly used in intraday trading as it provides
    a fresh VWAP calculation for each trading session.

    Formula:
      - At session start: reset cumulative values
      - typical_price = (high + low + close) / 3
      - session_pv += typical_price * volume
      - session_vol += volume
      - vwap = session_pv / session_vol

    Parameters:
      - session_start: time when session starts (default: 9:30)
      - session_end: time when session ends (default: 16:00)
    '''
    alias = ('SessionVWAP', 'SVWAP',)
    lines = ('vwap',)
    
    params = (
        ('session_start', None),  # Will use data's session start if None
        ('session_end', None),    # Will use data's session end if None
    )

    plotinfo = dict(subplot=False)

    def __init__(self):
        # Initialize cumulative variables
        self.cum_pv = 0.0
        self.cum_vol = 0.0
        self.last_date = None
        
        super(SessionVWAP, self).__init__()

    def _is_new_session(self):
        """Check if we're at the start of a new trading session"""
        current_date = self.data.datetime.date(0)
        
        if self.last_date is None or current_date != self.last_date:
            self.last_date = current_date
            return True
        
        # If session times are specified, check them
        if self.p.session_start is not None:
            current_time = self.data.datetime.time(0)
            if current_time == self.p.session_start:
                return True
        
        return False

    def next(self):
        # Reset at new session
        if self._is_new_session():
            self.cum_pv = 0.0
            self.cum_vol = 0.0
        
        # Calculate typical price
        typical_price = (self.data.high[0] + self.data.low[0] + self.data.close[0]) / 3.0
        
        # Update cumulative values
        self.cum_pv += typical_price * self.data.volume[0]
        self.cum_vol += self.data.volume[0]
        
        # Calculate VWAP (avoid division by zero)
        if self.cum_vol > 0:
            self.lines.vwap[0] = self.cum_pv / self.cum_vol
        else:
            self.lines.vwap[0] = typical_price


class WeightedVWAP(Indicator):
    '''
    A period-based VWAP that calculates the volume weighted average price
    over a rolling window of specified periods.

    This version uses a rolling window approach rather than cumulative,
    making it suitable for longer-term analysis.

    Formula:
      - For each period in window:
        - typical_price = (high + low + close) / 3
        - sum_pv = sum(typical_price * volume for period)
        - sum_vol = sum(volume for period)
        - vwap = sum_pv / sum_vol

    Parameters:
      - period: number of bars to include in calculation (default: 14)
    '''
    alias = ('WeightedVWAP', 'WVWAP', 'PeriodVWAP')
    lines = ('vwap',)
    
    params = (('period', 14),)

    plotinfo = dict(subplot=False)

    def _plotlabel(self):
        return [self.p.period]

    def next(self):
        # Get data for the period
        highs = self.data.high.get(size=self.p.period)
        lows = self.data.low.get(size=self.p.period)
        closes = self.data.close.get(size=self.p.period)
        volumes = self.data.volume.get(size=self.p.period)
        
        # Calculate typical prices for the period
        typical_prices = [(h + l + c) / 3.0 for h, l, c in zip(highs, lows, closes)]
        
        # Calculate sum of price * volume and sum of volume
        sum_pv = sum(tp * vol for tp, vol in zip(typical_prices, volumes))
        sum_vol = sum(volumes)
        
        # Calculate VWAP (avoid division by zero)
        if sum_vol > 0:
            self.lines.vwap[0] = sum_pv / sum_vol
        else:
            # Fallback to current typical price
            self.lines.vwap[0] = (self.data.high[0] + self.data.low[0] + self.data.close[0]) / 3.0

    def once(self, start, end):
        # Optimized batch calculation
        highs = self.data.high.array
        lows = self.data.low.array
        closes = self.data.close.array
        volumes = self.data.volume.array
        vwap_array = self.lines.vwap.array
        period = self.p.period

        for i in range(start, end):
            # Get slice for this period
            start_idx = max(0, i - period + 1)
            end_idx = i + 1
            
            # Calculate typical prices and weighted sum
            sum_pv = 0.0
            sum_vol = 0.0
            
            for j in range(start_idx, end_idx):
                typical_price = (highs[j] + lows[j] + closes[j]) / 3.0
                sum_pv += typical_price * volumes[j]
                sum_vol += volumes[j]
            
            # Calculate VWAP
            if sum_vol > 0:
                vwap_array[i] = sum_pv / sum_vol
            else:
                vwap_array[i] = (highs[i] + lows[i] + closes[i]) / 3.0 