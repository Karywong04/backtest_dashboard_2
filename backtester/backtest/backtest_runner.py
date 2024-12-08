import backtrader as bt
from utils.data_handler import get_ohlcv, get_secondary_data
from strategies.trend_change import TrendStrategy, PandasDataWithDirection
from strategies.rsi_diff import RSIDiffStrategy, PandasDataWithRSIDiff
import streamlit as st
import quantstats as qs
import backtrader.analyzers as btanalyzers
import pandas as pd

def get_data_feed(strategy, df):
    strategy_to_feed_class = {
        "Trend Change": PandasDataWithDirection,
        "RSI Diff": PandasDataWithRSIDiff,
    }

    data_feed_class = strategy_to_feed_class.get(strategy)
    if not data_feed_class:
        raise ValueError(f"Strategy '{strategy}' not supported for data feed.")

    common_params = {
        'dataname': df,
        'datetime': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
    }

    if strategy == "Trend Change":
        common_params['direction'] = 'Direction'
    elif strategy == "RSI Diff":
        common_params['rsi_diff'] = 'RSI_Diff'

    return data_feed_class(**common_params)

def load_strategy_class(strategy):

    strategy_to_class = {
        "Trend Change": TrendStrategy,
        "RSI Diff": RSIDiffStrategy,
    }

    strategy_class = strategy_to_class.get(strategy)
    if not strategy_class:
        raise ValueError(f"Strategy '{strategy}' not supported.")
    return strategy_class


def backtest_strategy(code, start_date, end_date, initial_cash=100000, commission=0.001, strategy="Trend Change", strategy_params=None, show_individual_results=True):
    if strategy_params is None:
        strategy_params = {}

    try:
        # Load data
        df = get_ohlcv(code, start_date, end_date)
        df = get_secondary_data(df)

        data_feed = get_data_feed(strategy, df)

        cerebro = bt.Cerebro()
        cerebro.broker.set_cash(initial_cash)
        cerebro.broker.setcommission(commission=commission)
        cerebro.adddata(data_feed)

        # PyFolio Analyzer
        cerebro.addanalyzer(btanalyzers.PyFolio, _name='pyfolio')

        # Load strategy class
        strategy_class = load_strategy_class(strategy)
        cerebro.addstrategy(strategy_class, **strategy_params)

        # Run the strategy
        results = cerebro.run()

        # Plot the results only if the user wants individual plots
        if show_individual_results:
            fig = cerebro.plot(iplot=False)[0][0]
            st.pyplot(fig)

        pyfolio_analyzer = results[0].analyzers.pyfolio
        returns, _, _, _ = pyfolio_analyzer.get_pf_items()

        returns = pd.Series(returns).dropna()

        return returns

    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"An error occurred for {code}: {str(e)}")
