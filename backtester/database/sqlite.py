import pandas as pd
import sqlite3
import yfinance as yf
from asset_universe import *

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

### Database connection and table creation ###
conn = sqlite3.connect('daily_stock_prices.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_prices (
    ticker TEXT,
    timestamp TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER
)
''')
conn.commit()

cursor.execute('''
CREATE INDEX IF NOT EXISTS idx_daily_prices_timestamp 
ON daily_prices(timestamp)
''')
conn.commit()

### Price Data ###
def fetch_daily_data(ticker):
    try:
        # Fetch data using yfinance
        df = yf.download(ticker, period='max', interval='1d', auto_adjust=True)
        df.reset_index(inplace=True)
        
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

        df = df.rename(columns={
            'Date': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })

        df['ticker'] = ticker
        df = df[['ticker', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
        return df

    except Exception as e:
        print(f"Failed to fetch data for {ticker}: {e}")
        return None

def get_latest_timestamp(ticker):
    query = "SELECT MAX(timestamp) FROM daily_prices WHERE ticker = ?"
    cursor.execute(query, (ticker,))
    result = cursor.fetchone()[0]
    return result

def store_data_to_db(data, latest_timestamp):
    if data is not None:
        data['timestamp'] = pd.to_datetime(data['timestamp']).dt.strftime('%Y-%m-%d')

        data.columns = ['ticker', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
        data['ticker'] = data['ticker'].astype(str)

        if latest_timestamp:
            data = data[data['timestamp'] > latest_timestamp]

        if not data.empty:
            data.to_sql('daily_prices', conn, if_exists='append', index=False)
            print(f"Data for {data['ticker'].iloc[0]} stored successfully.")
        else:
            print('No new data to store.')
    else:
        print('No data to store.')


### Querying Data ###
def query_data(ticker, start_time, end_time):
    start_time = pd.to_datetime(start_time).strftime('%Y-%m-%d')
    end_time = pd.to_datetime(end_time).strftime('%Y-%m-%d')
    
    query = """
    SELECT * FROM daily_prices
    WHERE ticker = ?
    AND date(timestamp) BETWEEN ? AND ?
    ORDER BY timestamp ASC
    """
    df = pd.read_sql(query, conn, params=(ticker, start_time, end_time))
    
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')
    
    print(f"Data queried for {ticker} between {start_time} and {end_time}:")
    print(df)

    return df

def check_database_stats():
    # Count unique tickers
    query_unique = """
    SELECT COUNT(DISTINCT ticker) as ticker_count
    FROM daily_prices
    """
    cursor.execute(query_unique)
    unique_count = cursor.fetchone()[0]
    
    query_details = """
    SELECT ticker, COUNT(*) as row_count
    FROM daily_prices
    GROUP BY ticker
    ORDER BY row_count DESC
    """
    df_stats = pd.read_sql(query_details, conn)
    
    print(f"\nTotal unique tickers in database: {unique_count}")
    print("\nFirst 10 tickers and their row counts:")
    print(df_stats.head(10))
    
    return df_stats

def get_tracked_tickers():
    query = "SELECT DISTINCT ticker FROM daily_prices"
    df = pd.read_sql(query, conn)
    return set(df['ticker'].tolist())

def update_tracking_list(new_tickers):
    timestamp = pd.Timestamp.now().strftime('%Y-%m-%d')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ticker_tracking (
        ticker TEXT,
        status TEXT,  -- 'active' or 'delisted'
        last_updated TEXT
    )
    ''')
    conn.commit()
    
    cursor.execute("SELECT ticker FROM ticker_tracking WHERE status = 'active'")
    currently_tracked = {row[0] for row in cursor.fetchall()}
    
    new_additions = new_tickers - currently_tracked
    delisted = currently_tracked - new_tickers
    
    # Update statuses
    if new_additions:
        print(f"\nNew tickers to add: {len(new_additions)}")
        print(f"Sample new tickers: {list(new_additions)[:5]}")
        for ticker in new_additions:
            cursor.execute("""
            INSERT INTO ticker_tracking (ticker, status, last_updated)
            VALUES (?, 'active', ?)
            """, (ticker, timestamp))
        
        fetch_and_save_etf_constituents('SPY', r"C:\Users\User\Desktop\backtester\utils\sp500_list.txt") ##PATH
        fetch_and_save_etf_constituents('QQQ', r"C:\Users\User\Desktop\backtester\utils\nasdaq_list.txt") ##PATH
    
    if delisted:
        print(f"\nDelisted tickers: {len(delisted)}")
        print(f"Sample delisted tickers: {list(delisted)[:5]}")
        for ticker in delisted:
            cursor.execute("""
            UPDATE ticker_tracking 
            SET status = 'delisted', last_updated = ?
            WHERE ticker = ?
            """, (timestamp, ticker))
    
    conn.commit()

def main():
    etf_symbols = ['SPY', 'QQQ']
    current_tickers = set()
    
    for etf_symbol in etf_symbols:
        print(f"\nFetching current holdings from: {etf_symbol}")
        tickers = get_stock_symbols(etf_symbol)
        print(f"Number of tickers from {etf_symbol}: {len(tickers)}")
        current_tickers.update(tickers)
    
    print(f"\nTotal unique current tickers: {len(current_tickers)}")
    
    update_tracking_list(current_tickers)
    
    # Get all tickers (current + historical)
    cursor.execute("SELECT ticker FROM ticker_tracking")
    all_tracked_tickers = {row[0] for row in cursor.fetchall()}
    
    print(f"\nTotal tickers to process (including delisted): {len(all_tracked_tickers)}")
    
    processed_count = 0
    error_count = 0
    error_tickers = []

    for ticker in all_tracked_tickers:
        print(f"\nProcessing ticker [{processed_count + 1}/{len(all_tracked_tickers)}]: {ticker}")
        try:
            latest_timestamp = get_latest_timestamp(ticker)
            data = fetch_daily_data(ticker)
            store_data_to_db(data, latest_timestamp)
            processed_count += 1
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            error_count += 1
            error_tickers.append(ticker)
            continue

    print("\nProcessing Complete!")
    print(f"Successfully processed: {processed_count} tickers")
    print(f"Errors encountered: {error_count} tickers")
    if error_tickers:
        print("Tickers with errors:")
        print(error_tickers)        

if __name__ == '__main__':
    check_database_stats()
    print("\nStarting main processing...")
    main()
    check_database_stats()
    conn.close()



