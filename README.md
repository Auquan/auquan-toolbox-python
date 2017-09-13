**This is the old Auquan Toolbox, which is a stripped down version of our new, [more powerful toolbox]((https://bitbucket.org/auquan/auquantoolbox/wiki/Home)). If you are new to writing strategies, practice with this toolbox. 
Find the new, expanded version [here](https://bitbucket.org/auquan/auquantoolbox/wiki/Home)**


# About Auquan Toolbox
[Auquan](http://www.auquan.com) provides a backtesting toolbox to develop your trading algorithms. The toolbox is free and open source which you can use to create and backtest strategies

We provide daily price data for 600 stocks listed on NASDAQ which are (or were) a part of S&P500 since 2001. The code below will automatically download the stocks data for you. The full list of stocks is [here](https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/nasdaq/nasdaq.txt)

The modules are in the folder auquanToolbox. We also provide sample strategies to demonstrate how to use the toolbox.

## Table of Contents
1. [Installation](https://github.com/Auquan/auquan-toolbox-python#1-installation)
2. [How to write a trading strategy?](https://github.com/Auquan/auquan-toolbox-python#2-how-to-write-a-trading-strategy)
3. [Backtesting](https://github.com/Auquan/auquan-toolbox-python#3-backtesting)

# 1. Installation
### Python 2.7
You need Python 2.7 (Python 3 will be supported later) to run this toolbox. There are several distributions of Python 2.7 that can be used. For an easy installation process, we recommend Anaconda since it will reliably install all the necessary dependencies. Download [Anaconda](http://continuum.io/downloads) and follow the instructions on the [installation page](http://docs.continuum.io/anaconda/install). Once you have Python, you can then install the toolbox.

### Auquan Toolbox
There are multiple ways to install this toolbox.

The easiest way and the most recommended way is via pip. Just run the following command:
`pip install -U auquanToolbox`
It will also install all the dependencies. Now you can just call `import auquanToolbox` within your code to import the toolbox. If you want to run a  strategy, find the path for the strategy, and run `python {path_to_strategy}`. If we publish any updates to the toolbox, the same command `pip install -U auquanToolbox` will also automatically get the new version of the toolbox.

You can also choose to clone the master branch of this repo or [download](https://github.com/Auquan/auquan-toolbox-python/archive/master.zip) the code from this repo. After you do that, navigate to the root folder of this project and run `python setup.py install`. This will also install all the dependencies, and you are good to run an existing strategy or create a new one. You would have to redownload the toolbox code, if we published any changes to the toolbox.

### Dependencies
- Python 2.7 (Python 3 will be supported soon)
- numpy
- pandas
- matplotlib


# 2. How to write a trading strategy
Follow the template provided in TradingStrategyTemplate.py. For starters, we have provided some [sample strategies here](https://github.com/Auquan/sample-strategies).  
Basically, there are two functions in the sample file to modify: settings, and tradingstrategy.

### settings:
This function takes no arguments and has to return the following parameters:

| Parameter | Example value | Description |
| --------- | ------------- | ----------- |
|exchange | "nasdaq"   |       Exchange to download data for. Right now we only support nasdaq
|markets | ['AAPL','ALL']|     Stocks to download data for. Leave empty([]) to load data for all stocks
|date_start | '2016-11-01'|    Date to start the backtest
|date_end | '2016-11-30'   |   Date to end the backtest
|lookback | 90              |  The number of days of historical data you want to use in each iteration of trading system. On any day t, your algorithm will have historical data from t-lookback to t-1 day

### trading_strategy:
This function is called each day of the backtesting period to analyze prior data and make trading decisison.  

It takes `lookback_data` as argument, which is historical data for the past "lookback"(as defined in settings) number of days. It is a dictionary of following features:

| Parameter | Description | Dimensions (rows x columns) |
| --- | --- | --- |
|OPEN		|the first price of the day	|Lookback x # of Markets
|HIGH		|the highest price of the day	|Lookback x # of Markets
|LOW		|the lowest price of the day	|Lookback x # of Markets
|CLOSE		|the last price of the day	|Lookback x # of Markets
|VOL		|stocks traded in the day	|Lookback x # of Markets
|COST TO TRADE	|cost to trade 1 stock		|Lookback x # of Markets
|POSITION	|number of stocks you own	|Lookback x # of Markets
|ORDER		|you order for previous days	|Lookback x # of Markets
|FILLED_ORDER 	|order that was executed	|Lookback x # of Markets
|DAILY_PNL 	|daily profit(loss) from trades	|Lookback x # of Markets
|TOTAL_PNL 	|total profit(loss)from trades	|Lookback x # of Markets
|FUNDS 		|cash available to buy stocks	|Lookback x 1
|VALUE 		|total portfolio value		|Lookback x 1
     
Any feature data can be accessed as `lookback_data['OPEN']`. The output is a pandas dataframe with dates as the index (row) and markets as columns. **The function has to return a pandas dataframe with markets you are trading as index(row) and SIGNAL, PRICE and WEIGHTS as columns.**

| KeyName | Description |
| --- | --- |
| SIGNAL	| Long (+1), short (-1) or no position (0) for all securities in markets[]
| WEIGHTS | The weight of each stock in your portfolio.
| PRICE	| *Optional.* If specified, buy orders are executed only if next day's open price is equal or lower than the price and sell orders are executed if it is equal or higher than the price. Set as 0 if you don't want to specify a price.

    
# 3. Backtesting:
The system is run by calling the command  
`backtest(exchange, markets, trading_strategy, date_start, date_end, lookback)`  
You can set an optional verbose=True to see more details  

Execution happens at the day's open price. When executed, the system will automatically calculate the quantity of each stock to buy and sell to maintain the portfolio weights specified by you. For example if you are trading AAPL and GOOG, your portfolio value is 1,000,000 and your order is:

| Market |SIGNAL|WEIGHTS|PRICE|
|---|---|---|---|
| AAPL| 1 | 0.65 | 0 |
| GOOG|-1 | 0.35 | 0 |

The system will buy $650,000 worth of Apple shares and sell $350,000 worth of Google shares. If your order remains the same next day and your portfolio value increases to 1,100,000, the system will automatically rebalance to long $715,000 worth of Apple shares and short $385,000 of Google shares. 

If no price is specified(as in this example), order exection happens at stock's open price. If you specify a price, the system will buy the specified quantity of stock if it's open price <= price specified here and sell the specified quantity of a stock if it's price >= price specified here. No action is taken if the price criteria is not met. 

**Cost to Trade**: The system automatically accounts for trading costs. We apply a commssion (*fees charged by the exchange and the broker*) and slippage (*the difference inprice at which you placed your order and the price at which you actually traded.*)  
We use 0.10 per stock as commission and 5% of the daily range slippage((HIGH - LOW) * 0.05)  
Total cost to trade = 0.10 + (HIGH - LOW) * 0.05  

After evaluation, the sytem plots a chart of daily and total pnl for the strategy and daily long/short exposure. We also plot total pnl for a benchmark index.
You can view performance for individual stocks using the GUI.
Run logs and order,position and pnl information is stored in csv in the runlogs folder.

