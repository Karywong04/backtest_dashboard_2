import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from backtest.backtest_runner import backtest_strategy
from datetime import datetime
import quantstats as qs
from utils.data_handler import load_stock_list
import time



st.title("Multiple Stocks Analysis")

stock_list_type = st.selectbox(
    "Select Stock List",
    ["NASDAQ", "S&P 500", "HSI", "Cryptocurrencies", "Custom"]
)

if stock_list_type == "NASDAQ":
    stock_list = load_stock_list("nasdaq_list.txt")
elif stock_list_type == "S&P 500":
    stock_list = load_stock_list("sp500_list.txt")
elif stock_list_type == "HSI":
    stock_list = load_stock_list("hsi_list.txt")
elif stock_list_type == "Cryptocurrencies":
    stock_list = load_stock_list("crypto_list.txt")
else:  # Custom input
    stock_input = st.text_area(
        "Enter Custom Stock Codes (comma-separated)",
        value="AAPL, MSFT, GOOGL, AMZN"
    )
    stock_list = [stock.strip() for stock in stock_input.split(",")]

start_date = st.date_input("Start Date", datetime(2012, 1, 1))
end_date = st.date_input("End Date")
initial_cash = st.number_input("Initial Cash", value=100000)
commission = st.number_input("Commission", value=0.001)

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

show_individual_results = st.radio(
    "Display Mode", 
    ("Show Each Backtest Result", "Show Summary Only")
)

if st.button("Run Batch Analysis"):
    metrics = []

    # Progress
    num_of_stocks = len(stock_list)  
    progress_bar = st.progress(0) 
    progress_text = st.empty() 

    # Loop 
    for i, stock in enumerate(stock_list):
        stock = stock.strip()

        try:
            progress_text.text(f"Finishing processing {i + 1} stocks out of {num_of_stocks} stocks.")
            progress_bar.progress((i + 1) / num_of_stocks)  

            returns = backtest_strategy(
                code=stock,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                initial_cash=initial_cash,
                commission=commission,
                strategy=selected_strategy,
                strategy_params=strategy_params,
                show_individual_results=(show_individual_results == "Show Each Backtest Result")
            )

            if returns is not None and not returns.empty:
                sharpe = qs.stats.sharpe(returns)
                calmar = qs.stats.calmar(returns)

                # Store the metrics 
                metrics.append({
                    'Stock': stock,
                    'Sharpe Ratio': sharpe,
                    'Calmar Ratio': calmar
                })
            else:
                metrics.append({
                    'Stock': stock,
                    'Sharpe Ratio': None,
                    'Calmar Ratio': None
                })

        except Exception as e:
            st.write(f"Error with {stock}: {str(e)}")
            metrics.append({
                'Stock': stock,
                'Sharpe Ratio': None,
                'Calmar Ratio': None
            })

        time.sleep(0.1)

    metrics_df = pd.DataFrame(metrics)
    metrics_df_sorted = metrics_df.sort_values(by='Sharpe Ratio', ascending=False)

    st.subheader("Backtest Metrics")
    st.dataframe(metrics_df_sorted, use_container_width=True)