from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
from auquanToolbox.dataloader import data_available
import matplotlib.pyplot as plt

def metrics(daily_pnl, total_pnl, baseline_data, base_index):

    stats = {}
    daily_return = daily_pnl.sum(axis=1)
    total_return = total_pnl.sum(axis=1)

    stats['Total Pnl'] = (total_pnl.iloc[total_pnl.index.size-1].sum())
    stats['Annual Return'] = annualized_return(daily_return)
    stats['Annual Vol']=annual_vol(daily_return)
    stats['Sharpe Ratio'] = sharpe_ratio(daily_return)
    stats['Sortino Ratio'] = sortino_ratio(daily_return)
    stats['Max Drawdown']=max_drawdown(daily_return)
    stats['Profit Factor']=profit_factor(daily_return)
    stats['Profitablity (%)']=profit_percent(daily_return)
    if base_index:
        stats['Base Return(%)'] = annualized_return(baseline_data['DAILY_PNL'])
        stats['Beta'] = beta(daily_return,baseline_data['DAILY_PNL'])

    for x in stats.keys():
        if np.isnan(stats[x]):
            del stats[x]

    return stats

def annualized_return(daily_return):
    total_return = daily_return.sum()
    total_days = daily_return.index.size
    if total_return < -1:
        total_return = -1
    return ((1 + total_return)**(252 / total_days) - 1)
    

def annualized_std(daily_return):
    return np.sqrt(252)*np.std(daily_return)

def annualized_downside_std(daily_return):
    mar = 0
    downside_return = daily_return.copy()
    downside_return[downside_return > 0]= 0
    return np.sqrt(252)*np.std(downside_return)

def annual_vol(daily_return):
    return annualized_std(daily_return)

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

def alpha(daily_return, baseline_daily_return,beta):
    return annualized_return(daily_return) - beta*annualized_return(baseline_daily_return)

def profit_factor(daily_return):
    downside_return = daily_return.copy()
    downside_return[downside_return > 0]= 0
    upside_return = daily_return.copy()
    upside_return[upside_return < 0]= 0
    if downside_return.sum() == 0:
        return 0
    return -(upside_return.sum())/(downside_return.sum())

def profit_percent(daily_return):
    total_return = daily_return.copy()
    total_return[total_return != 0]= 1
    upside_return = daily_return.copy()
    upside_return[upside_return < 0]= 0
    upside_return[upside_return > 0]= 1
    if total_return.sum() == 0:
        return 0
    return upside_return.sum()/total_return.sum()

def baseline(exchange, base_index, date_range,logger):
    features = ['OPEN', 'CLOSE']
    baseline_data = {}

    assert data_available(exchange, [base_index],logger)
    csv = pd.read_csv('%s/historicalData/%s.csv'%(exchange.lower(),base_index.lower()), index_col=0)
    csv.index = pd.to_datetime(csv.index)
    csv.columns = [col.upper() for col in csv.columns]
    csv = csv.reindex(index=csv.index[::-1])
    #features = [col.upper() for col in csv.columns]

    for feature in features:
        baseline_data[feature] = pd.Series(0, index=date_range)
        baseline_data[feature][base_index] = csv[feature][date_range]
    
    baseline_data['DAILY_PNL'] = pd.Series(0, index=date_range)
    baseline_data['TOTAL_PNL'] = pd.Series(0, index=date_range)

    open_start = baseline_data['OPEN'][base_index].iloc[1]
    for end in range(1, date_range.size):
        close_curr = baseline_data['CLOSE'][base_index].iloc[end]
        close_last = baseline_data['CLOSE'][base_index].iloc[end-1]
        if end == 1:
            close_last = open_start
        pnl_curr = (close_curr - close_last) / open_start

        baseline_data['DAILY_PNL'].iloc[end] = pnl_curr
        baseline_data['TOTAL_PNL'].iloc[end] = pnl_curr + baseline_data['TOTAL_PNL'].iloc[end - 1]

    return baseline_data            

def analyze(exchange, markets, back_data):
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