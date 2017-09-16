#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, print_function, unicode_literals
import pandas as pd
import numpy as np
from auquanToolbox.toolbox import backtest

def settings():
    exchange = "nasdaq"           # Exchange to download data for (only nasdaq for now)
    markets = ['AAPL','NFLX','GOOG','IBM','AMZN']            # Stocks to download data for. 
    date_start = '2014-06-30'   # Date to start the backtest
    date_end = '2016-11-06'     # Date to end the backtest
    lookback = 120               # Number of days you want historical data for

    """ To make a decision for day t, your algorithm will have historical data
    from t-lookback to t-1 days"""
    return [exchange, markets, date_start, date_end, lookback]

def trading_strategy(lookback_data):

    order = pd.DataFrame(0, index=lookback_data['POSITION'].columns, columns = ['SIGNAL','WEIGHTS','PRICE'])

    ##YOUR CODE HERE
    """This is an implementation of a mean reversion strategy. Mean reversion strategy tries to isolate noise from long terms trends.
    
    We calculate simple moving averages of closing price over two different time periods.
    The longer time period average is the true trend and the shorter time period average is the noise around the trend
    - If the small time period average is lower than the larger time period average, the current price is too low and likely to increase. 
      Hence this is a signal to buy
    - Similarly, If the small time period average is higher than the larger time period average, the current price is too high and likely to decrease. 
      Hence this is a signal to sell
    """

    #Pick two time periods
    period1 = 90
    period2 = 30

    #Calculate averages of closing price -  sum of the values within the time-period divided by the length of the time-period

    markets_close = lookback_data['CLOSE']
    avg_p1 = markets_close[-period1 : ].sum() / period1
    avg_p2 = markets_close[-period2 : ].sum() / period2

    #Take the difference of the two moving averages
    difference = avg_p1 - avg_p2
    deviation = difference.copy()
    total_deviation = np.absolute(deviation).sum()
    if total_deviation==0:
        return order
    else:  
        # Decide wether to go long or short each market
        # If the small time period average is lower than the larger time period average, deviation is positive otherwise it's negative
        # Positive sign implies go long the marktet. Similarly, negative sign implies go short the market
        order['SIGNAL'] = np.sign(deviation)
        # Calculate the weight of each stock in the portfolio. Weights are based on the difference between the two averages
        # Higher the difference, larger the position
        order['WEIGHTS']= np.absolute(deviation/total_deviation)

        return order

if __name__ == '__main__':
    [exchange, markets, date_start, date_end, lookback] = settings()
    backtest(exchange, markets, trading_strategy, date_start, date_end, lookback)#,verbose=True)