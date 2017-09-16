#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, print_function, unicode_literals
import pandas as pd
import numpy as np
from auquanToolbox.toolbox import backtest

def settings():
    exchange = "nasdaq"           # Exchange to download data for (only nasdaq for now)
    markets = ['AAPL','IBM','GOOG','C'] # Stocks to download data for. 
    date_start = '2015-01-03'   # Date to start the backtest
    date_end = '2016-11-06'     # Date to end the backtest
    lookback = 120               # Number of days you want historical data for

    """ To make a decision for day t, your algorithm will have historical data
    from t-lookback to t-1 days"""
    return [exchange, markets, date_start, date_end, lookback]

def trading_strategy(lookback_data):
    """
    Smarter Mean Reversion Strategy
    We again calculate moving averages over two time periods.
    Position is only entered if there is significant difference between two averages (1 standard deviation difference)
    Once we enter into a position, the position is scaled with the difference between two averages till the trend reverses.
    """

    order = pd.DataFrame(0, index=lookback_data['POSITION'].columns, columns = ['SIGNAL','WEIGHTS','PRICE'])

    #Pick two time periods
    period1 = 90
    period2 = 30

    #Calculate averages of closing price -  sum of the values within the time-period divided by the length of the time-period
    markets_close = lookback_data['CLOSE']
    avg_p1 = markets_close[-period1 : ].sum() / period1
    avg_p2 = markets_close[-period2 : ].sum() / period2

    #Calculate Standard Deviation
    sdev_p1 = np.std(markets_close[-period1 : ], axis=0)

    #Take the difference of the two moving averages
    difference = avg_p1 - avg_p2
    deviation = pd.Series(0, index=lookback_data['POSITION'].columns)

    #Define position criteria
    criteria_1 = np.abs(difference)>sdev_p1  #Enter position is difference in price is greater than standard deviation
    criteria_2 = np.sign(difference) == np.sign(lookback_data['POSITION']) #Scale position with difference if we already have a position
    deviation[criteria_1] = difference
    deviation[criteria_2] = difference

    total_deviation = np.absolute(deviation).sum()
    if total_deviation==0:
        return order
    else:
        # Decide wether to go long or short each market
        """ If we have no position :
            deviation is +ve if the small time period average is lower than the larger time period average by atleast one standard deviation  
            deviation is -ve if the small time period average is higher than the larger time period average by atleast one standard deviation
            deviation is 0 if the difference between small time period average and the larger time period average is lower than one standard deviation
            If we aleady hold a position in a market:
            deviation is +ve if the small time period average is lower than the larger time period average and our position is long 
            deviation is -ve if the small time period average is higher than the larger time period average and our position is short
            deviation is 0 otherwise
        """
        order['SIGNAL'] = np.sign(deviation)
        # Calculate the weight of each stock in the portfolio. Weights are based on the difference between the two averages
        # Higher the difference, larger the position
        order['WEIGHTS']= np.absolute(deviation/total_deviation)

        return order

if __name__ == '__main__':
    [exchange, markets, date_start, date_end, lookback] = settings()
    backtest(exchange, markets, trading_strategy, date_start, date_end, lookback)#,verbose=True)