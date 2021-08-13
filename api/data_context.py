#pandas and nmpy
import requests
import pandas as pd


def get_candle_data(tick, session):
    res = requests.get(
        f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={tick}&outputsize={session}&apikey=X15RFLY6YDXUU1ZP')

    data = res.json()
    return data


def get_chart_data(tick, session):
    res = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={tick}&outputsize={session}&apikey=R4LCCSM6NDQQWW9E')

    
    data = res.json()
    #print(data)
    df = pd.DataFrame(
        columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    )

    for i in data['Time Series (Daily)']:
        new_row = {'Date': i, 'Open': data['Time Series (Daily)'][i]['1. open'], 'High': data['Time Series (Daily)'][i]['2. high'], 'Low': data['Time Series (Daily)'][i]['3. low'],
                'Close': data['Time Series (Daily)'][i]['4. close'], 'Adj Close': data['Time Series (Daily)'][i]['5. adjusted close'], 'Volume': data['Time Series (Daily)'][i]['6. volume']}
        df = df.append(new_row, ignore_index=True)

    df = df.iloc[::-1]

    return df



def general_info(tick):
    res = requests.get(
        f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={tick}&apikey=3WEE9NP1CG44SBN5')
    data = res.json()
    return data
