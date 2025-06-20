backtrader
==========

.. image:: https://img.shields.io/pypi/v/backtrader.svg
   :alt: PyPi Version
   :scale: 100%
   :target: https://pypi.python.org/pypi/backtrader/

..  .. image:: https://img.shields.io/pypi/dm/backtrader.svg
       :alt: PyPi Monthly Donwloads
       :scale: 100%
       :target: https://pypi.python.org/pypi/backtrader/

.. image:: https://img.shields.io/pypi/l/backtrader.svg
   :alt: License
   :scale: 100%
   :target: https://github.com/backtrader/backtrader/blob/master/LICENSE
.. image:: https://travis-ci.org/backtrader/backtrader.png?branch=master
   :alt: Travis-ci Build Status
   :scale: 100%
   :target: https://travis-ci.org/backtrader/backtrader
.. image:: https://img.shields.io/pypi/pyversions/backtrader.svg
   :alt: Python versions
   :scale: 100%
   :target: https://pypi.python.org/pypi/backtrader/

**Yahoo API Note**:

  [2018-11-16] After some testing it would seem that data downloads can be
  again relied upon over the web interface (or API ``v7``)

**Tickets**

  The ticket system is (was, actually) more often than not abused to ask for
  advice about samples.

For **feedback/questions/...** use the `Community <https://community.backtrader.com>`_

Here a snippet of a Simple Moving Average CrossOver. It can be done in several
different ways. Use the docs (and examples) Luke!
::

  from datetime import datetime
  import backtrader as bt

  class SmaCross(bt.SignalStrategy):
      def __init__(self):
          sma1, sma2 = bt.ind.SMA(period=10), bt.ind.SMA(period=30)
          crossover = bt.ind.CrossOver(sma1, sma2)
          self.signal_add(bt.SIGNAL_LONG, crossover)

  cerebro = bt.Cerebro()
  cerebro.addstrategy(SmaCross)

  data0 = bt.feeds.YahooFinanceData(dataname='MSFT', fromdate=datetime(2011, 1, 1),
                                    todate=datetime(2012, 12, 31))
  cerebro.adddata(data0)

  cerebro.run()
  cerebro.plot()

Including a full featured chart. Give it a try! This is included in the samples
as ``sigsmacross/sigsmacross2.py``. Along it is ``sigsmacross.py`` which can be
parametrized from the command line.

Features:
=========

Live Trading and backtesting platform written in Python.

  - Live Data Feed and Trading with

    - Interactive Brokers (needs ``IbPy`` and benefits greatly from an
      installed ``pytz``)
    - *Visual Chart* (needs a fork of ``comtypes`` until a pull request is
      integrated in the release and benefits from ``pytz``)
    - *Oanda* (needs ``oandapy``) (REST API Only - v20 did not support
      streaming when implemented)

  - Data feeds from csv/files, online sources or from *pandas* and *blaze*
  - Filters for datas, like breaking a daily bar into chunks to simulate
    intraday or working with Renko bricks
  - Multiple data feeds and multiple strategies supported
  - Multiple timeframes at once
  - Integrated Resampling and Replaying
  - Step by Step backtesting or at once (except in the evaluation of the Strategy)
  - Integrated battery of indicators
  - *TA-Lib* indicator support (needs python *ta-lib* / check the docs)
  - Easy development of custom indicators
  - Analyzers (for example: TimeReturn, Sharpe Ratio, SQN) and ``pyfolio``
    integration (**deprecated**)
  - Flexible definition of commission schemes
  - Integrated broker simulation with *Market*, *Close*, *Limit*, *Stop*,
    *StopLimit*, *StopTrail*, *StopTrailLimit*and *OCO* orders, bracket order,
    slippage, volume filling strategies and continuous cash adjustmet for
    future-like instruments
  - Sizers for automated staking
  - Cheat-on-Close and Cheat-on-Open modes
  - Schedulers
  - Trading Calendars
  - Plotting (requires matplotlib)

Documentation
=============

The blog:

  - `Blog <http://www.backtrader.com/blog>`_

Read the full documentation at:

  - `Documentation <http://www.backtrader.com/docu>`_

List of built-in Indicators (122)

  - `Indicators Reference <http://www.backtrader.com/docu/indautoref.html>`_

Development and Dependency Management
=====================================

This project uses ``uv`` for fast and robust dependency management. The dependencies are defined in ``pyproject.toml`` and locked in ``uv.lock`` for reproducible builds.

**Prerequisites**

- Python >= 3.11
- ``uv`` package manager. Install from the `uv installation guide <https://docs.astral.sh/uv/getting-started/installation/>`_.

**Initial Setup**

1. Clone the repository and navigate to the project directory.

2. Create and activate the virtual environment:
   ::

     uv venv
     source .venv/bin/activate.fish  # For fish shell
     # or
     source .venv/bin/activate       # For bash/zsh
     # or on Windows
     .venv\Scripts\activate

3. Install the project in development mode with all dependencies:
   ::

     uv sync --all-groups
     uv pip install -e .

**Managing Dependencies**

- **Adding a runtime dependency**:
  ::

    uv add <package-name>

- **Adding a development dependency**:
  ::

    uv add --optional dev <package-name>

- **Removing a dependency**:
  ::

    uv remove <package-name>
    uv remove --optional dev <package-name>  # For dev dependencies

- **Updating all dependencies**: To upgrade all packages to their latest compatible versions:
  ::

    uv lock --upgrade
    uv sync --all-groups

  After updating, commit the changes to ``uv.lock`` to version control.

**Development Tools**

The project includes several development tools configured in ``pyproject.toml``:

- **Code formatting**: ``black`` and ``isort``
- **Linting**: ``flake8``
- **Testing**: ``pytest`` with coverage support
- **Performance testing**: ``pytest-xdist`` for parallel test execution

Run formatting and linting:
::

  black .
  isort .
  flake8 .

Run tests:
::

  pytest
  pytest --cov=backtrader  # With coverage
  pytest -n auto           # Parallel execution

Python 2/3 Support
==================

  - Python >= ``3.11``

  - It also works with ``pypy`` and ``pypy3`` (no plotting - ``matplotlib`` is
    not supported under *pypy*)

Installation
============

``backtrader`` is self-contained with no external dependencies (except if you
want to plot)

**For Users**

From *pypi*:

  - ``pip install backtrader``

  - ``pip install backtrader[plotting]``

    If ``matplotlib`` is not installed and you wish to do some plotting

.. note:: The minimum matplotlib version is ``3.10.3``

**For Development**

If you want to contribute or modify the code, follow the development setup in the
`Development and Dependency Management`_ section above. This uses ``uv`` for better
dependency management and development workflow.

An example for *IB* Data Feeds/Trading:

  - ``IbPy`` doesn't seem to be in PyPi. Do either::

      pip install git+https://github.com/blampe/IbPy.git

    or (if ``git`` is not available in your system)::

      pip install https://github.com/blampe/IbPy/archive/master.zip

For other functionalities like: ``Visual Chart``, ``Oanda``, ``TA-Lib``, check
the dependencies in the documentation.

From source:

  - Place the *backtrader* directory found in the sources inside your project

Version numbering
=================

X.Y.Z.I

  - X: Major version number. Should stay stable unless something big is changed
    like an overhaul to use ``numpy``
  - Y: Minor version number. To be changed upon adding a complete new feature or
    (god forbids) an incompatible API change.
  - Z: Revision version number. To be changed for documentation updates, small
    changes, small bug fixes
  - I: Number of Indicators already built into the platform


====
1. Do not run strategy if all the indicators/timeframes are not ready.
