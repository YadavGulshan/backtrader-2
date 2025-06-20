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

from dataclasses import asdict, dataclass
from typing import List, Optional

from backtrader import Analyzer, Trade


__all__ = ['TradeMetrics', 'TradeMetricsData']


@dataclass
class TradeMetricsData:
    """Data structure to hold detailed trade metrics and analysis information."""
    max_upside_price: float
    max_upside_time: str
    max_downside_price: float
    max_downside_time: str
    position_size: int
    entry_time: str
    entry_price: float
    entry_reason: Optional[str] = None
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    entry_indicator_state: Optional[dict] = None
    exit_indicator_state: Optional[dict] = None

    def get_pnl(self):
        """Calculate PnL if both entry and exit prices are available."""
        if self.exit_price is not None:
            return (self.exit_price - self.entry_price) * self.position_size
        return None

    def get_max_favorable_excursion(self):
        """Calculate maximum favorable excursion (MFE).
        
        MFE represents the largest unrealized profit that occurred during
        the trade before it was closed. For long positions, this is the
        highest price reached minus the entry price. For short positions,
        this is the entry price minus the lowest price reached.
        
        Returns:
            float: The maximum favorable excursion in currency units.
                  Returns 0.0 if no favorable movement occurred.
        """
        if self.position_size > 0:  # Long position
            return max(0.0, (self.max_upside_price - self.entry_price) * self.position_size)
        else:  # Short position
            return max(0.0, (self.entry_price - self.max_downside_price) * abs(self.position_size))

    def get_max_adverse_excursion(self):
        """Calculate maximum adverse excursion (MAE).
        
        MAE represents the largest unrealized loss that occurred during
        the trade before it was closed. For long positions, this is the
        entry price minus the lowest price reached. For short positions,
        this is the highest price reached minus the entry price.
        
        Returns:
            float: The maximum adverse excursion in currency units.
                  Returns 0.0 if no adverse movement occurred.
        """
        if self.position_size > 0:  # Long position
            return max(0.0, (self.entry_price - self.max_downside_price) * self.position_size)
        else:  # Short position
            return max(0.0, (self.max_upside_price - self.entry_price) * abs(self.position_size))


class TradeMetrics(Analyzer):
    """
    This analyzer provides detailed trade metrics including maximum favorable
    and adverse excursion, entry/exit details, and optional indicator states.

    The analyzer tracks trades from entry to exit, recording:
      - Maximum upside and downside price movements during the trade
      - Entry and exit prices, times, and reasons
      - Position sizes and target/stop levels
      - Optional indicator states at entry and exit (debug mode)

    Params:

      - ``debug_mode`` (default: ``False``)
        
        If ``True``, captures indicator states at entry and exit points.
        This requires the strategy to have an ``expression_evaluator`` 
        attribute with a ``get_current_state`` method.

      - ``safe_mode`` (default: ``True``)
        
        If ``True``, handles missing strategy attributes gracefully without
        raising exceptions. If ``False``, expects strategy to have specific
        methods and attributes.

    Methods:

      - ``get_analysis``

        Returns a list of dictionaries, each containing the metrics for
        a completed trade. Each dictionary has the following keys:

          - ``max_upside_price``: Highest price reached during the trade
          - ``max_upside_time``: Time when highest price was reached
          - ``max_downside_price``: Lowest price reached during the trade  
          - ``max_downside_time``: Time when lowest price was reached
          - ``position_size``: Size of the position
          - ``entry_time``: Trade entry timestamp
          - ``entry_price``: Trade entry price
          - ``entry_reason``: Reason for entry (if available)
          - ``exit_time``: Trade exit timestamp
          - ``exit_price``: Trade exit price
          - ``exit_reason``: Reason for exit (if available)
          - ``take_profit``: Take profit level (if available)
          - ``stop_loss``: Stop loss level (if available)
          - ``entry_indicator_state``: Indicator values at entry (debug mode)
          - ``exit_indicator_state``: Indicator values at exit (debug mode)

      - ``get_trade_objects``

        Returns a list of TradeMetricsData objects for programmatic access
        to trade data with helper methods.

    Note:
      This analyzer assumes certain strategy methods and attributes may exist:
        - ``calculate_target_and_stop()``: Method returning (take_profit, stop_loss)
        - ``entry_reason``: Attribute containing entry reason
        - ``exit_reason``: Attribute containing exit reason
        - ``expression_evaluator``: Object with ``get_current_state()`` method (debug mode)

      If these are not available and ``safe_mode`` is ``True``, the analyzer
      will continue to work but without that specific information.
    """

    alias = ('TradeMetricsAnalyzer',)

    params = (
        ('debug_mode', False),
        ('safe_mode', True),
    )

    def __init__(self):
        super(TradeMetrics, self).__init__()
        self.current_trade: Optional[TradeMetricsData] = None
        self.result: List[TradeMetricsData] = []
        self.is_trade_open = False

    def start(self):
        """Initialize the analyzer."""
        super(TradeMetrics, self).start()

    def notify_trade(self, trade: Trade):
        """Called when a trade changes status."""
        self.is_trade_open = trade.isopen

    def next(self):
        """Called on each bar to update trade metrics."""
        if self.is_trade_open:
            if not self.current_trade:
                self._initialize_new_trade()
            else:
                self._update_current_trade()
        else:
            if self.current_trade:
                self._close_current_trade()

    def _initialize_new_trade(self):
        """Initialize a new trade with starting values."""
        current_price = self.data.close[0]
        current_time = str(self.data.datetime.datetime())
        
        take_profit, stop_loss = self._get_target_and_stop()
        
        entry_reason = self._get_entry_reason()
        
        self.current_trade = TradeMetricsData(
            max_upside_price=current_price,
            max_downside_price=current_price,
            max_upside_time=current_time,
            max_downside_time=current_time,
            position_size=self.strategy.position.size,
            entry_time=current_time,
            entry_price=self.strategy.position.price,
            entry_reason=entry_reason,
            take_profit=take_profit,
            stop_loss=stop_loss,
        )

        if self.p.debug_mode:
            self.current_trade.entry_indicator_state = self._get_indicator_state()

    def _update_current_trade(self):
        """Update current trade with new price extremes."""
        current_price = self.data.close[0]
        current_time = str(self.data.datetime.datetime())
        
        if self.current_trade.position_size != self.strategy.position.size:
            self.current_trade.position_size = self.strategy.position.size
            entry_reason = self._get_entry_reason()
            if entry_reason:
                self.current_trade.entry_reason = entry_reason

        if current_price > self.current_trade.max_upside_price:
            self.current_trade.max_upside_price = current_price
            self.current_trade.max_upside_time = current_time

        if current_price < self.current_trade.max_downside_price:
            self.current_trade.max_downside_price = current_price
            self.current_trade.max_downside_time = current_time

    def _close_current_trade(self):
        """Finalize the current trade and add it to results."""
        if not self.current_trade:
            return
            
        self.current_trade.exit_time = str(self.data.datetime.datetime(-1))
        self.current_trade.exit_price = self.data.close[-1]
        self.current_trade.exit_reason = self._get_exit_reason()

        if self.p.debug_mode:
            self.current_trade.exit_indicator_state = self._get_indicator_state()

        self.result.append(self.current_trade)
        self.current_trade = None

    def _get_target_and_stop(self):
        """Get target and stop levels from strategy if available."""
        if self.p.safe_mode:
            try:
                if hasattr(self.strategy, 'calculate_target_and_stop'):
                    return self.strategy.calculate_target_and_stop()
            except Exception:
                pass
        else:
            if hasattr(self.strategy, 'calculate_target_and_stop'):
                return self.strategy.calculate_target_and_stop()
        
        return None, None

    def _get_entry_reason(self):
        """Get entry reason from strategy if available."""
        if hasattr(self.strategy, 'entry_reason'):
            return getattr(self.strategy, 'entry_reason', None)
        return None

    def _get_exit_reason(self):
        """Get exit reason from strategy if available."""
        if hasattr(self.strategy, 'exit_reason'):
            return getattr(self.strategy, 'exit_reason', None)
        return None

    def _get_indicator_state(self):
        """Get indicator state from strategy if available."""
        if not self.p.debug_mode:
            return None
            
        if self.p.safe_mode:
            try:
                if hasattr(self.strategy, 'expression_evaluator'):
                    evaluator = self.strategy.expression_evaluator
                    if hasattr(evaluator, 'get_current_state'):
                        return evaluator.get_current_state(
                            include_state_vars=True, 
                            remove_nan=True
                        )
            except Exception:
                pass
        else:
            if hasattr(self.strategy, 'expression_evaluator'):
                evaluator = self.strategy.expression_evaluator
                if hasattr(evaluator, 'get_current_state'):
                    return evaluator.get_current_state(
                        include_state_vars=True, 
                        remove_nan=True
                    )
        
        return None

    def get_analysis(self):
        """
        Returns the trade metrics analysis.
        
        Returns:
            List[dict]: List of dictionaries containing trade metrics data
        """
        return [asdict(trade) for trade in self.result]

    def get_trade_objects(self):
        """
        Returns the trade metrics as TradeMetricsData objects.
        
        Returns:
            List[TradeMetricsData]: List of trade metrics data objects with helper methods
        """
        return self.result.copy()


# Backward compatibility alias
TradeMetricsAnalyzer = TradeMetrics
