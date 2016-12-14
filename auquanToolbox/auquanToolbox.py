from __future__ import absolute_import, division, print_function, unicode_literals
try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve
import logging
import datetime as dt
import numpy as np
import pandas as pd
import matplotlib
import os
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import style
import matplotlib.pyplot as plt

def download(logger, exchange, ticker, file_name):
    url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/%s/historicalData/%s.csv'%(exchange.lower(), ticker.lower())
    logger.info('Downloading %s data to file: %s'%(ticker, file_name))
    urlretrieve(url, file_name)

def data_available(logger, exchange, markets):
    dir_name = '%s/historicalData/'%exchange.lower()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    for m in markets:
        file_name = '%s%s.csv'%(dir_name, m.lower())
        if not os.path.exists(file_name):
            download(logger, exchange, m, file_name)
    return True

def load_data(logger, exchange, markets, start, end, random=False):
    markets = [m.upper() for m in markets]
    features = ['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME']
    date_range = pd.date_range(start=start, end=end, freq='B')
    back_data = {}

    for feature in features:
        back_data[feature] = pd.DataFrame(index=date_range, columns=markets)

    if random:
        for feature in features:
            back_data[feature] = pd.DataFrame(np.random.randint(10, 50, size=(date_range.size,len(markets))),
                                              index=date_range,
                                              columns=markets)
    else:
        assert data_available(logger, exchange, markets)
        for market in markets:
            csv = pd.read_csv('%s/historicalData/%s.csv'%(exchange.lower(), market.lower()), index_col=0)
            csv.index = pd.to_datetime(csv.index)
            csv.columns = [col.upper() for col in csv.columns]
            csv = csv.reindex(index=csv.index[::-1])
            for feature in features:
                back_data[feature][market] = csv[feature]

        dates_to_drop = pd.Series(False, index=date_range)
        for feature in features:
            dates_to_drop |= pd.isnull(back_data[feature]).any(axis=1)

        dropped_dates = date_range[dates_to_drop]
        date_range = date_range[~dates_to_drop]
        for feature in features:
            back_data[feature] = back_data[feature].drop(dropped_dates)

    back_data['SLIPPAGE'] = (back_data['HIGH'] - back_data['LOW']).abs() * 0.005
    back_data['POSITION'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['FILLED_ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['DAILY_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['TOTAL_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['BUDGET'] = pd.Series(0, index=date_range)
    back_data['VALUE'] = pd.Series(0, index=date_range)
    return back_data, date_range

def commission():
    return 0.1

def execute_sell(logger, order, position, slippage, price, budget):
    position_curr = position.copy()
    position_curr[order < 0] += order[order < 0]
    if (position_curr < 0).any():
        logger.info('Short selling not supported! Selling available quantity.')
    position_curr[position_curr < 0] = 0
    per_commission = (position - position_curr) * commission()
    total_commission = per_commission.sum()
    if total_commission > budget:
        logger.info('Sell order exceeds budget! Sell order cancelled.')
        return position, budget, per_commission*0
    else:
        slippage_adjusted_price = price - slippage
        slippage_adjusted_price[slippage_adjusted_price < 0] = 0
        per_slippage = (price - slippage_adjusted_price)*(position - position_curr)
        return position_curr, \
               budget - total_commission + ((position - position_curr)*slippage_adjusted_price).sum(), \
               per_commission + per_slippage

def execute_buy(logger, order, position, slippage, price, budget):
    order_cost = (order[order > 0] * price[order > 0]).sum()
    per_commission = order * commission()
    per_commission[order < 0] = 0
    total_commission = per_commission.sum()
    per_slippage = order * slippage
    per_slippage[order < 0] = 0
    total_slippage = per_slippage.sum()
    if (order_cost + total_commission + total_slippage) > budget:
        logger.info('Buy order exceeds budget! Buy order cancelled.')
        return position, budget, per_commission*0
    else:
        position_curr = position.copy()
        position_curr[order > 0] += order[order > 0]
        return position_curr, \
               budget - order_cost - total_commission - total_slippage, \
               per_commission + per_slippage

def execute_order(logger, order, position, slippage, price, budget):
    if pd.isnull(price[order != 0]).values.any():
        logger.info('Cannot place order for markets with price unavailable! Order cancelled.')
        return position, budget
    else:
        (position_after_sell, budget_after_sell, sell_order_loss) = execute_sell(logger, order, position, slippage, price, budget)
        (position_after_buy, budget_after_buy, buy_order_loss) = execute_buy(logger, order, position_after_sell, slippage, price, budget_after_sell)
        return position_after_buy, budget_after_buy, (sell_order_loss + buy_order_loss)

def plot(logger, daily_pnl, total_pnl, baseline_daily_pnl, baseline_total_pnl, budget, final_budget):
    daily_return = daily_pnl.sum(axis=1)
    stats = 'Starting Funds: %0.2f'%budget + '\n' + \
            'Final Value: %0.2f'%final_budget + '\n' + \
            'Total PnL: %0.2f%%'%(total_pnl.iloc[total_pnl.index.size-1].sum()) + '\n' + \
            'Annualized Return: %0.2f%%'%annualized_return(daily_return) + '\n' + \
            'Annual Vol: %0.2f%%'%annual_vol(daily_return) + '\n' + \
            'Beta: %0.2f'%beta(daily_return,baseline_daily_pnl) + '\n' + \
            'Sharpe Ratio: %0.2f'%sharpe_ratio(daily_return) + '\n' + \
            'Sortino Ratio: %0.2f'%sortino_ratio(daily_return) + '\n' + \
            'Max Drawdown: %0.2f'%max_drawdown(daily_return)
    logger.info(stats)
    plt.close('all')
    zero_line = np.zeros(daily_pnl.index.size)
    f, plot_arr = plt.subplots(2, sharex=True)
    f.text(0.01, 0.99, stats, transform=plot_arr[0].transAxes, fontsize=10,
           verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plot_arr[0].set_title('Daily % PnL')
    plot_arr[0].plot(daily_pnl.index, zero_line)
    plot_arr[0].plot(daily_pnl.index, daily_pnl.sum(axis=1).values, label='strategy')
    plot_arr[0].plot(daily_pnl.index, baseline_daily_pnl, label='s&p500')
    plot_arr[0].legend(loc='upper left')

    plot_arr[1].set_title('Total % PnL')
    plot_arr[1].plot(total_pnl.index, zero_line)
    plot_arr[1].plot(total_pnl.index, total_pnl.sum(axis=1).values, label='strategy')
    plot_arr[1].plot(daily_pnl.index, baseline_total_pnl, label='s&p500')
    plot_arr[1].legend(loc='upper left')

    plt.show()

def annualized_return(daily_return):
    total_return = daily_return.sum()
    total_days = daily_return.index.size
    if total_return > 0:
        return (1 + total_return)**(256 / total_days) - 1
    else:
        return 1 - (1 - total_return)**(256 / total_days)

def annualized_std(daily_return):
    return 256*np.std(daily_return)

def annualized_downside_std(daily_return):
    mar = 0
    downside_returns = [0 if (x-mar > 0) else (x-mar) for x in daily_return]
    return 256*np.std(downside_returns)

def annual_vol(daily_return):
    return np.sqrt(annualized_std(daily_return))

def sharpe_ratio(daily_return):
    stdev = annualized_std(daily_return)
    if stdev == 0:
        return np.nan
    else:
        return annualized_return(daily_return)/stdev

def sortino_ratio(daily_return):
    stdev = annualized_downside_std(daily_return)
    if stdev == 0:
        return np.nan
    else:
        return annualized_return(daily_return)/stdev

def max_drawdown(daily_return):
    return np.max(np.maximum.accumulate(daily_return) - daily_return)

def beta(daily_return, baseline_daily_return):
    stdev = np.std(baseline_daily_return)
    if stdev == 0:
        return np.nan
    else:
        return np.corrcoef(daily_return, baseline_daily_return)[0,1]*np.std(daily_return)/stdev

def baseline(logger, exchange, base_index, lookback, date_range):
    features = ['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME']
    baseline_data = {}

    for feature in features:
        baseline_data[feature] = pd.Series(index=date_range)

    assert data_available(logger, exchange, [base_index])
    csv = pd.read_csv('nasdaq/historicalData/%s.csv'%base_index.lower(), index_col=0)
    csv.index = pd.to_datetime(csv.index)
    csv.columns = [col.upper() for col in csv.columns]
    csv = csv.reindex(index=csv.index[::-1])
    for feature in features:
        baseline_data[feature] = csv[feature]

    baseline_data['DAILY_PNL'] = pd.Series(0, index=date_range)
    baseline_data['TOTAL_PNL'] = pd.Series(0, index=date_range)

    open_start = baseline_data['OPEN'].iloc[lookback-1]
    for end in range(lookback, date_range.size):
        close_curr = baseline_data['CLOSE'].iloc[end]
        close_last = baseline_data['CLOSE'].iloc[end-1]

        pnl_curr = (close_curr - close_last) * 100 / open_start

        baseline_data['DAILY_PNL'].iloc[end] = pnl_curr
        baseline_data['TOTAL_PNL'].iloc[end] = pnl_curr + baseline_data['TOTAL_PNL'].iloc[end - 1]

    return baseline_data

def get_logger():
    logger_name = dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger_dir = 'runLogs/'
    logger_file = '%srun-%s.txt'%(logger_dir,logger_name)
    if not os.path.exists(logger_dir):
        os.makedirs(logger_dir)
    formatter = logging.Formatter('%(message)s')
    file_handler = logging.FileHandler(logger_file)
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

def backtest(exchange, markets, trading_strategy, start, end, budget, lookback, base_index='INX'):
    logger = get_logger()
    assert (lookback > 0), 'Lookback should be > 0. Exiting!'

    (back_data, date_range) = load_data(logger, exchange, markets, start, end)
    assert (date_range.size > lookback), "Lookback %d is more than the date range %d. Exiting!"%(lookback,date_range.size)

    logger.info('Starting budget: %d'%budget)
    logger.info('------------------------------------')
    budget_curr = budget
    position_curr = back_data['POSITION'].iloc[lookback - 1]
    date_labels = date_range.date
    for end in range(lookback, date_range.size):
        start = end - lookback

        # get order
        lookback_data = {feature: data[start: end] for feature, data in back_data.items()}
        order = trading_strategy(lookback_data, markets, budget_curr)
        logger.info('order: %s'%order.values)

        # evaluate new position based on order and budget
        price_curr = back_data['OPEN'].iloc[end]
        slippage = back_data['SLIPPAGE'].iloc[end - 1]
        position_last = back_data['POSITION'].iloc[end - 1]
        (position_curr, budget_curr, order_loss) = execute_order(logger, order, position_last, slippage, price_curr, budget_curr)

        # set info in back data
        back_data['POSITION'].iloc[end] = position_curr
        back_data['ORDER'].iloc[end] = order
        filled_order = position_curr - position_last
        back_data['FILLED_ORDER'].iloc[end] = filled_order

        open_curr = back_data['OPEN'].iloc[end]
        close_curr = back_data['CLOSE'].iloc[end]
        close_last = back_data['CLOSE'].iloc[end-1]
        pnl_curr = (position_curr * (close_curr - close_last) + filled_order * (close_last - open_curr) - order_loss) * 100 / budget
        back_data['DAILY_PNL'].iloc[end] = pnl_curr
        back_data['TOTAL_PNL'].iloc[end] = pnl_curr + back_data['TOTAL_PNL'].iloc[end - 1]

        back_data['BUDGET'].iloc[end] = budget_curr
        value_curr = budget_curr + (position_curr*close_curr).sum()
        back_data['VALUE'].iloc[end] = value_curr

        status_str = 'Open Price                       : %s'%price_curr.values + '\n' + \
                     'Order                            : %s'%order.values + '\n' + \
                     'Position                         : %s'%position_curr.values + '\n' + \
                     'PnL                              : %s'%pnl_curr.values + '\n' + \
                     'Available funds on day %s: %0.2f'%(date_labels[end], budget_curr) + '\n' + \
                     'Portfolio value on day %s: %0.2f'%(date_labels[end], value_curr) + '\n' + \
                     '-----------------------------------------------------------------------------'
        logger.info(status_str)

    baseline_data = baseline(logger, exchange, base_index, lookback, date_range)
    final_budget = budget_curr + (position_curr * close_curr).sum()
    plot(logger, back_data['DAILY_PNL'], back_data['TOTAL_PNL'],
         baseline_data['DAILY_PNL'], baseline_data['TOTAL_PNL'],
         budget, final_budget)

def analyze(exchange, markets, start, end):
    logger = get_logger()
    (back_data, days) = load_data(logger, exchange, markets, start, end)
    plt.close('all')
    f, plot_arr = plt.subplots(2, sharex=True)
    plot_arr[0].set_title('Open')
    plot_arr[1].set_title('Close')
    for m in markets:
        plot_arr[0].plot(back_data['OPEN'].index, back_data['OPEN'][m], label=m)
        plot_arr[1].plot(back_data['OPEN'].index, back_data['CLOSE'][m], label=m)
    plot_arr[0].legend(loc='upper center')
    plot_arr[1].legend(loc='upper center')
    plt.show()
