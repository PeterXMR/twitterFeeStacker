from flask import Flask, render_template
import plotly.graph_objs as go
import pandas as pd
import requests
from datetime import datetime, timedelta
from time import sleep
import time

app = Flask(__name__)

INVESTMENT_AMOUNT = 8
START_DATE = '2022-11-04'
SATOSHI_PER_BITCOIN = 100_000_000

def get_bitcoin_price_history(start_date):
    def get_bitcoin_price_on_date(date_str):
        url = f'https://api.coingecko.com/api/v3/coins/bitcoin/history?date={date_str}&localization=false'
        response = requests.get(url)
        if response.status_code == 200:
            time.sleep(1)
            data = response.json()
            if 'market_data' in data:
                return data['market_data']['current_price']['usd']
        elif response.status_code == 429:
                time.sleep(60)
                return get_bitcoin_price_on_date(date_str)
        return None

    year, month, _ = map(int, start_date.split('-'))
    start_date = datetime(year, month, 5)
    end_date = datetime.today()
    current_date = start_date
    price_history = []

    while current_date <= end_date:
        if current_date.day == 5:
            date_str = current_date.strftime('%d-%m-%Y')
            price = None
            while price is None:
                price = get_bitcoin_price_on_date(date_str)
                if price is None:
                    time.sleep(0.05)
            price_history.append((current_date.strftime('%Y-%m-%d'), price))

        current_date += timedelta(days=1)


    return pd.DataFrame(price_history, columns=['date', 'price']).set_index('date')

def calculate_investment(bitcoin_price_history, investment_amount):
    investment_df = pd.DataFrame(columns=['date', 'price', 'stacked_sats', 'bitcoin_total', 'value_usd'])
    bitcoin_total = 0

    for date, price in bitcoin_price_history.iterrows():
        stacked_sats = int((investment_amount * SATOSHI_PER_BITCOIN) / price['price'])
        bitcoin_total += stacked_sats
        value_usd = bitcoin_total * price['price'] / SATOSHI_PER_BITCOIN
        investment_df.loc[date] = [date, round(price['price'], 0), stacked_sats, bitcoin_total, round(value_usd, 0)]

    return investment_df


def create_investment_plot(df):
    fig = go.Figure()

    # Add accumulated Bitcoin trace (in BTC)
    fig.add_trace(go.Scatter(x=df.index, y=df['bitcoin_total'],
                             mode='lines',
                             name='Accumulated Bitcoin (sat)'))
    

    fig.update_layout(title='Investment Value of $8/month (twiteer verified account fee) in Bitcoin since November 5, 2022',
                      xaxis_title='Date',
                      yaxis=dict(title='Value (sats)'),
                      legend_title='Legend',
                      yaxis_side='left',
                      margin=dict(l=100, r=100))

    # Create investment data table
    investment_table = pd.DataFrame(columns=['Invested (USD)', 'BTC Price (USD)', 'Stacked sats', 'Total sats'])
    invested_usd = 0
    for date, row in df.iterrows():
        invested_usd += 8
        investment_table.loc[date] = [invested_usd, row['price'], row['stacked_sats'], row['bitcoin_total']]

    return fig.to_html(full_html=False), investment_table



@app.route('/')
def index():
    bitcoin_price_history = get_bitcoin_price_history(START_DATE)

    investment_df = calculate_investment(bitcoin_price_history, INVESTMENT_AMOUNT)
    investment_plot, investment_table = create_investment_plot(investment_df)
    return render_template('index.html', investment_plot=investment_plot, investment_table=investment_table.to_html())

if __name__ == '__main__':
    app.run(debug=True)
