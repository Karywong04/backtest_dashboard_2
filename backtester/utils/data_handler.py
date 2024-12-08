import yfinance as yf
from datetime import datetime
import pandas as pd
import backtrader as bt
from .config import STRATEGY_PARAMS\
# from backtester.database.sqlite import query_data 


def get_ohlcv(code, start_date, end_date):
    extended_start = (datetime.strptime(start_date, '%Y-%m-%d') - pd.Timedelta(days=100)).strftime('%Y-%m-%d')
    ticker = yf.Ticker(code)
    df = ticker.history(start=extended_start, end=end_date)
    df = df[start_date:]
    df['Date'] = df.index
    df['Ticker'] = code
    return df

# import sqlite3
# import pandas as pd

# db_path = 'C:\\Users\\User\\Desktop\\backtester\\database\\daily_stock_prices.db'


# def connect_to_db(db_path):
#     try:
#         # Establish the connection
#         conn = sqlite3.connect(db_path)
#         print("Successfully connected to the database.")
#         return conn
#     except sqlite3.Error as e:
#         print(f"Database connection failed: {e}")
#         return None

# def query_data(ticker, start_time, end_time, db_path):
#     start_time = pd.to_datetime(start_time).strftime('%Y-%m-%d')
#     end_time = pd.to_datetime(end_time).strftime('%Y-%m-%d')

#     conn = sqlite3.connect(db_path)
    
#     query = """
#     SELECT * FROM daily_prices
#     WHERE ticker = ?
#     AND date(timestamp) BETWEEN ? AND ?
#     ORDER BY timestamp ASC
#     """
#     df = pd.read_sql(query, conn, params=(ticker, start_time, end_time))

#     conn.close()

#     df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')

#     return df

# def get_ohlcv(ticker, start_time, end_time, db_path):
#     # Query the database for OHLCV data
#     df = query_data(ticker, start_time, end_time, db_path)

#     # Process df to return only the relevant columns and capitalize their names
#     df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
#     df.columns = df.columns.str.capitalize()  # Capitalize the first letter of each column name

#     return df




def get_direction(df, threshold, atr_mode): ### For trend_change
    up_trend = True
    last_high_i = 0
    last_low_i = 0
    last_high = df['High'].iloc[0]
    last_low = df['High'].iloc[0]
    directions = []

    for i in range(len(df)):
        if atr_mode:
            threshold = df['ATR'].iloc[i]
        if up_trend:
            if df['High'].iloc[i] > last_high:
                last_high_i = i
                last_high = df['High'].iloc[i]
            elif (not atr_mode and (df['Close'].iloc[i] < last_high * (1 - threshold))) or \
                    (atr_mode and (df['Close'].iloc[i] < last_high - threshold)):
                up_trend = False
                last_low_i = i
                last_low = df['Low'].iloc[i]
        else:
            if df['Low'].iloc[i] < last_low:
                last_low_i = i
                last_low = df['Low'].iloc[i]
            elif (not atr_mode and (df['Close'].iloc[i] > last_low * (1 + threshold))) or \
                    (atr_mode and (df['Close'].iloc[i] > last_low + threshold)):
                up_trend = True
                last_high_i = i
                last_high = df['High'].iloc[i]

        directions.append(1 if up_trend else -1)  # numerical values for backtrader

    return directions


def calculate_rsi(data, periods=14): ## For rsi_diff
    delta = data.diff()

    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))

    avg_gain = gain.rolling(window=periods).mean()
    avg_loss = loss.rolling(window=periods).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

def get_secondary_data(df, params=None):
    if params is None:
        params = STRATEGY_PARAMS  # Use default parameters

    # ATR calculation
    df['TR'] = pd.DataFrame({
        'HL': df['High'] - df['Low'],
        'HC': abs(df['High'] - df['Close'].shift(1)),
        'LC': abs(df['Low'] - df['Close'].shift(1))
    }).max(axis=1)
    df['ATR'] = df['TR'].rolling(window=params['ATR_window']).mean() * params['ATR_multiplier']

    # Direction calculation
    df['Direction'] = get_direction(df, params['Direction_threshold'], params['Use_absolute'])

    # RSI calculations
    df['RSI_7'] = calculate_rsi(df['Close'], periods=params['RSI_periods']['short'])
    df['RSI_30'] = calculate_rsi(df['Close'], periods=params['RSI_periods']['long'])
    df['RSI_Diff'] = df['RSI_30'] - df['RSI_7']

    return df

def load_stock_list(file_name):
    try:
        file_path = f"utils/{file_name}"
        with open(file_path, 'r') as file:
            stock_list = [line.strip() for line in file.readlines()]

        if "hsi" in file_name.lower():
            stock_list = [f"{str(stock).zfill(4)}.HK" if len(str(stock).strip()) < 4 else f"{stock.strip()}.HK" for stock in stock_list]
        
        return stock_list
    except FileNotFoundError:
        print(f"File {file_name} not found.")
        return []
