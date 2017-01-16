from __future__ import absolute_import, division, print_function, unicode_literals
import pandas as pd
import numpy as np
from pythonToolbox.toolbox import backtest

def settings():
    exchange = "nasdaq"           # Exchange to download data for (only nasdaq for now)
    markets = ['AAPL','NFLX','GOOG','IBM','AMZN']            # Stocks to download data for. 
                                # Leave blank to download all stocks for the exchange (~900 stocks)
    date_start = '2014-06-30'   # Date to start the backtest
    date_end = '2016-11-06'     # Date to end the backtest
    lookback = 120               # Number of days you want historical data for

    """ To make a decision for day t, your algorithm will have historical data
    from t-lookback to t-1 days"""
    return [exchange, markets, date_start, date_end, lookback]

def trading_strategy(lookback_data):
    """
    :param lookback_data: Historical Data for the past "lookback" number of days as set in the main settings.
     It is a dictionary of features such as,
     'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME', 'SLIPPAGE', 'POSITION', 'ORDER',
     'FILLED_ORDER', 'DAILY_PNL', 'TOTAL_PNL', 'FUNDS', 'VALUE'
     Any feature data can be accessed as:lookback_data['OPEN']
     The output is a pandas dataframe with dates as the index (row)
     and markets as columns. 
    """"""""""""""""""""""""""
    """""""""""""""""""""""""" 
    To see a complete list of features, uncomment the line below"""
    #print(lookback_data.keys())
    
    """""""""""""""""""""""""""
    :return: A pandas dataframe with markets you are trading as index(row) and 
    signal, price and quantity as columns
    order['SIGNAL']:buy (+1), hold (0) or sell (-1) trading signals for all securities in markets[]
    order['PRICE']: The price where you want to trade each security. Buy orders are executed at or below the price and sell orders are executed at or above the price
    order['QUANTITY']: The quantity of each stock you want to trade.
    System will buy the specified quantity of stock if it's price <= price specified here
    System will sell the specified quantity of a stock if it's price >= price specified here
    """

    """IMPORTANT: Please make sure you have enough funds to buy or sell. 
        Order is cancelled if order_value > available funds(both buy and short sell)"""

    order = pd.DataFrame(0, index=lookback_data['POSITION'].columns, columns = ['SIGNAL','WEIGHTS','PRICE'])

    ##YOUR CODE HERE

    period1 = 90
    period2 = 30

    markets_close = lookback_data['CLOSE']
    market_open = lookback_data['OPEN']
    avg_p1 = markets_close[-period1 : ].sum() / period1
    avg_p2 = markets_close[-period2 : ].sum() / period2

    difference = avg_p1 - avg_p2
    deviation = difference.copy()
    total_deviation = np.absolute(deviation).sum()
    if total_deviation==0:
        return order
    else:  
        order['WEIGHTS']= np.absolute(deviation/total_deviation)
        order['SIGNAL'] = np.sign(deviation)
        # order['PRICE'][order['SIGNAL']>0] = (avg_p1-sdev_p1)[order['SIGNAL']>0]
        # order['PRICE'][order['SIGNAL']<0] = (avg_p1+sdev_p1)[order['SIGNAL']<0]

        return order

if __name__ == '__main__':
    [exchange, markets, date_start, date_end, lookback] = settings()
    backtest(exchange, markets, trading_strategy, date_start, date_end, lookback)#,verbose=True)
