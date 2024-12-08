import requests
import time

API_KEY = 'HWQH1OAX69SVRZQP'

def get_stock_symbols(symbol):
    url = f'https://www.alphavantage.co/query?function=ETF_PROFILE&symbol={symbol}&apikey={API_KEY}'
    r = requests.get(url)
    data = r.json()
    return [holding['symbol'] for holding in data.get('holdings', [])]

# def get_crypto_symbols(crypto_symbol):

def fetch_and_save_etf_constituents(etf_symbol, file_path):
    # ETF profile from Alpha Vantage
    url = f'https://www.alphavantage.co/query?function=ETF_PROFILE&symbol={etf_symbol}&apikey={API_KEY}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        if 'holdings' in data:
            constituents = [holding['symbol'] for holding in data['holdings']]
            
            with open(file_path, 'w') as f:
                for ticker in constituents:
                    f.write(f"{ticker}\n")
            
            print(f"Saved {len(constituents)} constituents of {etf_symbol} to {file_path}")
        else:
            print(f"No holdings found for {etf_symbol}. Response: {data}")
    else:
        print("Failed to fetch data from Alpha Vantage")


