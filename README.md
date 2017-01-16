Auquan(http://www.auquan.com) provides a backtesting toolbox to develop of your trading algorithms. The toolbox is free and open source which you can use to create and backtest strategies

Data is in the folder historical Data. We provide daily data for 2740 stocks listed on NASDAQ and 2690 stocks listed on NYSE. The full list of stocks is available in a text file in the respective folders.

The modules are in the folder auquanToolbox. We also provide a sample file to demonstrate how to use the toolbox.

There are two functions in the sample file to modify: settings, and tradingstrategy.

settings:
This function takes no arguments and has to return the following parameters:
exchange = "nasdaq"         # Exchange to download data for
markets = ['AAPL','ALL']    # Stocks to download data for
date_start = '2016-11-01'   # Date to start the backtest
date_end = '2016-11-30'     # Date to end the backtest
lookback = 90               # The number of days of historical data you want to use in each iteration of trading system. On any day t, your algorithm will have historical data from t-lookback to t-1 day

trading_strategy:
This function is called each day of the backtesting period to analyze prior data and make trading decisison.

It takes lookback_data as argument, which is historical data for the past "lookback"(as defined in settings) number of days. It is a dictionary of following features:

Parameter	Description			Dimensions (rows x columns)
OPEN		the first price of the day	Lookback x # of Markets
HIGH		the highest price of the day	Lookback x # of Markets
LOW		the lowest price of the day	Lookback x # of Markets
CLOSE		the last price of the day	Lookback x # of Markets
VOL		stocks traded in the day	Lookback x # of Markets
COST TO TRADE	cost to trade 1 stock		Lookback x # of Markets
POSITION	number of stocks you own	Lookback x # of Markets
ORDER		you order for previous days	Lookback x # of Markets
FILLED_ORDER 	order that was executed		Lookback x # of Markets
DAILY_PNL 	daily profit(loss) from trades	Lookback x # of Markets
TOTAL_PNL 	total profit(loss)from trades	Lookback x # of Markets
FUNDS 		cash available to buy stocks	Lookback x 1
VALUE 		total portfolio value		Lookback x 1
     
Any feature data can be accessed as:lookback_data['OPEN']. The output is a pandas dataframe with dates as the index (row) and markets as columns. 
    
The function has to return a pandas dataframe with markets you are trading as index(row) and signal, price and quantity as columns
SIGNAL	buy (+1), hold (0) or sell (-1) trading signals for all securities in markets[]
PRICE	The price where you want to trade each security. 
	Buy orders are executed at or below the price and sell orders are executed at or above the price
QUANTITY The quantity of each stock you want to trade.
    
Backtesting:
The system is run by calling the command
backtest(exchange, markets, trading_strategy, date_start, date_end, lookback)
You can set an optional verbose=True to see more details

Execution happens at the day's open price. When executed, the system checks if you have enough funds to buy or sell. Entire buy order is cancelled if if order_value > cash available to buy. Sell order is cancelled if cost_to_trade > cash available.
The system will buy the specified quantity of stock if it's price <= price specified here and sell the specified quantity of a stock if it's price >= price specified here.
Currently, there is no margin requirement for short selling.

Cost to Trade: The two main contributors to trading costs are commissions and slippage. Commissions are fees charged by the exchange and the broker. Slippage is the price at which you expected or placed your order and the price at which your order was actually filled. 
We use 0.10 per stock as commission and 5% of the daily range slippage((HIGH - LOW) * 0.05)
Total cost to trade = 0.10 + (HIGH - LOW) * 0.05

After evaluation, the sytem plots a chart of daily and total pnl for the strategy and daily long/short exposure. We also plot total pnl for a benchmark index.
You can view performance for individual stocks using the GUI.
Run logs and order,position and pnl information is stored in csv in the runlogs folder.

