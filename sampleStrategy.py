import pandas as pd

def trading_strategy(lookback_data, markets, budget_curr):
    """
    :param lookback_data: Data for the past n days as set in the main settings.
     It is a dictionary of features available for decision making, such as,
     'OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME', 'SLIPPAGE', 'POSITION', 'ORDER',
     'FILLED_ORDER', 'DAILY_PNL', 'TOTAL_PNL', 'BUDGET', 'VALUE'
     The data is in the form of pandas dataframe with dates as the index (row)
     and markets as columns. Higher index has more recent data.
    :param markets: List of markets that are you are interested in as per main settings
    :param budget: Current available budget based on which the order should be placed
    :return: List of number of stocks per market that you wish to buy (>0) or sell (<0)
    """

    sma_long_period = 90
    sma_short_period = 20
    markets_close = lookback_data['OPEN'] # DataFrame

    avg_long_curr = markets_close[-sma_long_period : ].sum() / sma_long_period
    avg_short_curr = markets_close[-sma_short_period : ].sum() / sma_short_period

    order = pd.Series(0, index = markets)

    order[(avg_short_curr/avg_long_curr) < 1.0] = 1     # buy
    order[(avg_short_curr/avg_long_curr) > 1.0] = -1    # sell

    return order

if __name__ == '__main__':
    import auquanToolbox.auquanToolbox as at
    exchange = "nasdaq"
    markets = ['CIA', 'ALL', 'AAPL']
    date_start = '2015-11-15'
    date_end = '2016-11-10'
    # at.analyze(exchange, markets, start=date_start, end=date_end)
    at.backtest(exchange, markets, trading_strategy, start=date_start, end=date_end, budget=10000, lookback=90)
