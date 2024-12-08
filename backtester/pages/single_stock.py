import streamlit as st
from backtest.backtest_runner import backtest_strategy
from datetime import datetime
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import quantstats as qs
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

st.title("Backtest and Optimization Dashboard")

# Input fields
stock_code = st.text_input("Enter Stock Code", value="AAPL")
start_date = st.date_input("Start Date", datetime(2012, 1, 1))
end_date = st.date_input("End Date")
initial_cash = st.number_input("Initial Cash", value=100000)
commission = st.number_input("Commission", value=0.001)

# Strategy Selection
strategies = ["Trend Change", "RSI Diff"]
selected_strategy = st.selectbox("Select Strategy", strategies)

strategy_params = {}
if selected_strategy == "Trend Change":
    atr_window = st.number_input("ATR Window", value=14)
    atr_multiplier = st.number_input("ATR Multiplier", value=3.0)
    direction_threshold = st.number_input("Direction Threshold", value=0.05)
    use_absolute = st.checkbox("Use Absolute Direction", value=True)
    strategy_params = {
        'atr_window': atr_window,
        'atr_multiplier': atr_multiplier,
        'direction_threshold': direction_threshold,
        'use_absolute': use_absolute,
    }
elif selected_strategy == "RSI Diff":
    rsi_short = st.number_input("RSI Short Period", value=7)
    rsi_long = st.number_input("RSI Long Period", value=30)
    rsi_diff_threshold = st.number_input("RSI Diff Threshold", value=20)
    strategy_params = {
        'rsi_short': rsi_short,
        'rsi_long': rsi_long,
        'rsi_diff_threshold': rsi_diff_threshold,
    }

# Buttons
col1, col2 = st.columns(2)
run_backtest = col1.button("Run Backtest")
run_optimization = col2.button("Run Optimization")

if run_backtest:
    st.write(f"Running backtest for {selected_strategy} strategy...")
    returns = backtest_strategy(
        code=stock_code,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        initial_cash=initial_cash,
        commission=commission,
        strategy=selected_strategy,
        strategy_params=strategy_params,
    )

    if returns is not None and not returns.empty:
        st.write("Backtest completed successfully.")
        st.subheader("QuantStats Analysis")
        cumulative_returns = qs.stats.compsum(returns)
        final_cumulative_return = cumulative_returns.iloc[-1]

        st.write(f"**Final Cumulative Return**: {final_cumulative_return:.2%}")
        st.write(f"**Annualized Return (CAGR)**: {qs.stats.cagr(returns):.2%}")
        st.write(f"**Max Drawdown**: {qs.stats.max_drawdown(returns):.2%}")
        st.write(f"**Sharpe Ratio**: {qs.stats.sharpe(returns):.2f}")

        static_dir = "static"
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        report_name = f"{stock_code}_{selected_strategy}_report.html".replace(" ", "_")
        output_path = os.path.join(static_dir, report_name)
        qs.reports.html(returns, output=output_path)

        with open(output_path, "r") as f:
            st.download_button(
                label=f"Download {report_name}",
                data=f,
                file_name=report_name,
                mime="text/html",
            )
    else:
        st.write("No returns data available from the backtest.")

if run_optimization:
    st.write("Running optimization with multithreading...")

    if selected_strategy == "Trend Change":
        atr_window_range = range(5, 51, 5)
        atr_multiplier_range = np.arange(1.0, 5.1, 0.5)
        param_grid = [(w, m) for w in atr_window_range for m in atr_multiplier_range]
    elif selected_strategy == "RSI Diff":
        rsi_short_range = range(3, 21, 2)
        rsi_long_range = range(20, 51, 5)
        param_grid = [(s, l) for s in rsi_short_range for l in rsi_long_range]

    # Progress
    progress_bar = st.progress(0)
    total_combinations = len(param_grid)
    sharpe_results = []

    def run_single_optimization(params):
        """Function to run backtest for a single set of parameters."""
        if selected_strategy == "Trend Change":
            temp_params = {'atr_window': params[0], 'atr_multiplier': params[1]}
        elif selected_strategy == "RSI Diff":
            temp_params = {'rsi_short': params[0], 'rsi_long': params[1]}
        
        returns = backtest_strategy(
            code=stock_code,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            initial_cash=initial_cash,
            commission=commission,
            strategy=selected_strategy,
            strategy_params=temp_params,
        )
        
        if returns is not None and not returns.empty:
            sharpe_ratio = qs.stats.sharpe(returns)
            return (*params, sharpe_ratio)
        return (*params, None)

    # Multithreading
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(run_single_optimization, params): params for params in param_grid}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result[-1] is not None:  # Check if Sharpe Ratio is available
                sharpe_results.append(result)
            progress_bar.progress((i + 1) / total_combinations)

    if selected_strategy == "Trend Change":
        sharpe_df = pd.DataFrame(
            sharpe_results,
            columns=["atr_window", "atr_multiplier", "Sharpe Ratio"]
        )
    elif selected_strategy == "RSI Diff":
        sharpe_df = pd.DataFrame(
            sharpe_results,
            columns=["rsi_short", "rsi_long", "Sharpe Ratio"]
        )

    st.write("Optimization Completed. Results:")
    st.dataframe(sharpe_df)

    # Best Parameters and Heatmap
    best_params = sharpe_df.loc[sharpe_df["Sharpe Ratio"].idxmax()]
    st.write(f"**Best Parameters:** {best_params.to_dict()}")
