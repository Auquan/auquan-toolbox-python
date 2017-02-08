from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
import os
import csv
import json
import logging
import datetime as dt
from auquanToolbox.dataloader import load_data
from auquanToolbox.resultviewer import loadgui
from auquanToolbox.metrics import metrics, baseline
import matplotlib.pyplot as plt
import urllib2


def backtest(exchange, markets, trading_strategy, date_start, date_end, lookback, budget=1000000, verbose=False, base_index='SPX', trading_costs = True, isJson=False):

    logger = get_logger()

    if updateCheck():
        logger.warn('Your version of auquanToolbox is not the most updated.' +
            ' If you are using pip, please use \'pip install -U auquanToolbox\'.' + 
            ' If you downloaded the package, you need to go to https://github.com/Auquan/auquan-toolbox-python'+
            ' to redownload that package.')

    #Verify Settings

    try:
        assert(isinstance(lookback, int)),"Lookback is invalid"
    except AssertionError:
            logger.exception("Lookback is invalid")
            raise

    #Load data for backtest
   
    (back_data, date_range) = load_data(exchange, markets, date_start, date_end, lookback, budget, logger)
    logger.info('Initial funds: %0.2f'%budget)
    logger.info('------------------------------------')
    logger.info('Evaluating...')

    budget_curr = budget
    
    position_curr = None
    margin_curr = None
    cost_to_trade = None

    res = []
    start_index = -1

    for startDate in pd.date_range(start=date_start, end=date_end, freq='B'):
        if startDate not in date_range:
            logger.info(startDate.strftime('Trading date is a Holiday or data not present :%d %b %Y'))
            continue
        end = date_range.get_loc(startDate)
        if start_index < 0:
            start_index = end

        start = end - lookback
        if start < 0:
            start = 0

        if position_curr is None:
            position_curr = back_data['POSITION'].iloc[end-1]
            margin_curr = back_data['MARGIN'].iloc[end-1]
            cost_to_trade = position_curr*0

        # get order and verify
        lookback_data = {feature: data[start: end] for feature, data in back_data.items()}
        order = trading_strategy(lookback_data)
        try:
            assert((order['SIGNAL'].isin([-1,0,1])).all())
        except AssertionError:
            logger.info("Signal can only be -1(sell), 0(hold) or 1(buy)")
            raise
        try:
            assert((order['PRICE']>=0).all())
        except AssertionError:
            logger.info("Price cannot be negative")
            raise
        try:
            assert(order['WEIGHTS']>=0).all() 
        except AssertionError:
            logger.info("Please check weights. Weights cannot be negative and should sum to <= 1")
            raise

        if order['WEIGHTS'].sum()>1:
            order['WEIGHTS'] = order['WEIGHTS']/order['WEIGHTS'].sum()

        # evaluate new position based on order and budget
        
        try:
            price_curr = back_data['OPEN'].iloc[end].astype(float)
            open_curr = back_data['OPEN'].iloc[end].astype(float)
            close_curr = back_data['CLOSE'].iloc[end].astype(float)
            open_last = back_data['OPEN'].iloc[end-1].astype(float)
            close_last = back_data['CLOSE'].iloc[end-1].astype(float)
            high = back_data['HIGH'].iloc[end - 1].astype(float)
            low = back_data['LOW'].iloc[end - 1].astype(float)
        except ValueError:
            logger.info("Data not formatted properly")
            raise


        slippage = (high - low) * 0.05
        position_last = back_data['POSITION'].iloc[end - 1].astype(int)
        value = budget_curr + margin_curr + (position_last * open_curr).sum()
        order['QUANTITY'] = getquantity(order, price_curr, slippage,value,position_last, logger)
        (position_curr, budget_curr, margin_curr, cost_to_trade) = execute_order(order, position_last, slippage, price_curr, budget_curr,margin_curr,logger, trading_costs)

        # set info in back data
        back_data['POSITION'].iloc[end] = position_curr
        back_data['ORDER'].iloc[end] = order['QUANTITY']
        filled_order = position_curr - position_last
        back_data['FILLED_ORDER'].iloc[end] = filled_order

        # calculate pnl
        pnl_curr = (position_curr * (close_curr  - open_curr) + position_last * (open_curr - close_last)) - cost_to_trade
        back_data['DAILY_PNL'].iloc[end] = pnl_curr
        back_data['TOTAL_PNL'].iloc[end] = pnl_curr + back_data['TOTAL_PNL'].iloc[end - 1]

        # available funds
        back_data['FUNDS'].iloc[end] = budget_curr

        #funds used as margin
        back_data['MARGIN'].iloc[end] = -(position_curr[position_curr<0] * close_curr[position_curr<0]).sum()

        #portfolio value
        value_curr = budget_curr + margin_curr+ (margin_curr - back_data['MARGIN'].iloc[end]) + (position_curr[position_curr>0] * close_curr[position_curr>0]).sum()
        back_data['VALUE'].iloc[end] = value_curr

        #cost
        back_data['COST TO TRADE'].iloc[end] = cost_to_trade

        #print to STDOUT
        logger.info(date_range[end].strftime('Trading date :%d %b %Y'))
        if verbose:
            s = 'stocks         : %s'%markets+'\n'+\
            'today open     : %s'%open_curr.values+'\n'+\
            'today close    : %s'%close_curr.values+'\n'+\
            'order          : %s'%order['QUANTITY'].values+'\n'+\
            'position       : %s'%position_curr.values+'\n'+\
            'cost to trade  : %0.2f'%cost_to_trade.sum()+'\n'+\
            'Available funds: %0.2f'%budget_curr+'\n'+\
            'Margin funds   : %0.2f'%margin_curr+'\n'+\
            'pnl            : %0.2f'%pnl_curr.sum()+'\n'+\
            'Portfolio Value: %0.2f'%value_curr+'\n'+\
            '------------------------------------'
            logger.info(s)
        
        if value_curr<=0:
            logger.info('Out of funds. Exiting!')
            break
            
    logger.info('Final Portfolio Value: %0.2f'%value_curr)

    if isJson:
        if base_index:
            baseline_data = baseline(exchange, base_index, date_range, logger)
            return writejson({feature: data[start_index-1: end+1] for feature, data in back_data.items()},budget,{feature: data[start_index-1: end+1] for feature, data in baseline_data.items()}, base_index)
        else:
            return writejson({feature: data[start_index-1: end+1] for feature, data in back_data.items()},budget,{}, base_index)
    else:
        writecsv({feature: data[start_index-1: end+1] for feature, data in back_data.items()},budget)

    logger.info('Plotting Results...')

    loadgui({feature: data[start_index-1: end+1] for feature, data in back_data.items()}, exchange, base_index, budget,logger)

def commission():
    return 0.1

def margin_perc():
    return 1

def getquantity(order, price, slippage,value,position,logger):
    weights = order['WEIGHTS']
    cost_to_trade = slippage+commission()
    if weights.sum()>0:
        new_portfolio_value = (weights.sum()*value)/(weights*(price+cost_to_trade)/price).sum()
        desired_position = weights*new_portfolio_value/price
        quantity = (order['SIGNAL']*desired_position) - position
    else:
        new_portfolio_value = 0
        quantity = - position
        quantity.fillna(0)
    return quantity.astype(int)

def execute_order(order, position, slippage, price, budget, margin, logger, trading_costs):

    trade_criteria = (np.sign(order['QUANTITY'])*price[order.index] <= np.sign(order['QUANTITY'])*order['PRICE'])
    trade_criteria[np.sign(order['QUANTITY'])*price[order.index] > np.sign(order['QUANTITY'])*order['PRICE']] = order['PRICE'] ==0
    
    position_curr = position.copy()
    total_commission = 0*position_curr
    adj_slippage = 0*position_curr

    position_curr[trade_criteria] += order['QUANTITY'][trade_criteria]
    margin_curr = -(position_curr[position_curr < 0] * price[position_curr < 0]).sum()
    if trading_costs:
        total_commission = np.abs(position_curr - position) * commission()
        slippage_adjusted_price = price + (np.sign(order['QUANTITY'])*slippage)
        slippage_adjusted_price[slippage_adjusted_price < 0] = 0
        adj_slippage = np.abs(position_curr - position)*np.abs(price - slippage_adjusted_price)
    margin_call = margin_curr-margin
    order_value = ((position_curr - position) * price).sum() + margin_call
    cost_to_trade = total_commission + adj_slippage
    return position_curr, budget - order_value - margin_call - cost_to_trade.sum(), margin_curr, cost_to_trade

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

class noop_logger:
    def info(self, str):
        print(str)
    def exception(self, str):
        print(str)
    def warn(self, str):
        print(str)

def get_noop_logger():
    return noop_logger()

def writecsv(back_data,budget):

    results = pd.DataFrame(0, index=back_data['DAILY_PNL'].index, columns=['Daily Returns'])
    results['Daily Returns'] = back_data['DAILY_PNL'].sum(axis=1)*100/budget
    results['Total Returns'] = back_data['TOTAL_PNL'].sum(axis=1)*100/budget
    results['Funds'] = back_data['FUNDS']
    results['Margin'] = back_data['MARGIN']
    results['Portfolio Value'] = back_data['VALUE']
    for stock in back_data['DAILY_PNL'].columns.tolist():
        results['%s Position'%stock]= back_data['POSITION'][stock]
        results['%s Order'%stock]=back_data['ORDER'][stock]
        results['%s Filled Order'%stock]=back_data['FILLED_ORDER'][stock]
        results['%s Trade Price'%stock]=back_data['OPEN'][stock]
        results['%s Cost to Trade'%stock]=back_data['COST TO TRADE'][stock]
        results['%s PnL'%stock]=back_data['DAILY_PNL'][stock]

    results = results.sort_index(axis=0,ascending=False)
    csv_dir = 'runLogs/'
    try:
        csv_file =  open('%srun-%s.csv'%(csv_dir, dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S')), 'wb')
        results.to_csv(csv_file)
    except:
        csv_file =  open('%srun-%s.csv'%(csv_dir, dt.datetime.now().strftime('%Y-%m-%d %H-%M-%S')), 'w')
        results.to_csv(csv_file)
    # writer = csv.writer(csv_file)
    # writer.writerow(['Dates']+back_data['DAILY_PNL'].index.format())
    # writer.writerow(['Daily Pnl']+daily_return.sum(axis=1).values.tolist())
    # writer.writerow(['Total PnL']+total_return.sum(axis=1).values.tolist())
    # writer.writerow(['Funds']+back_data['FUNDS'].values.tolist())
    # writer.writerow(['Portfolio Value']+back_data['VALUE'].values.tolist())
    # for stock in back_data['DAILY_PNL'].columns.tolist():
    #     writer.writerow(['%s Position'%stock]+back_data['POSITION'][stock].values.tolist())
    #     writer.writerow(['%s Order'%stock]+back_data['ORDER'][stock].values.tolist())
    #     writer.writerow(['%s Filled Order'%stock]+back_data['FILLED_ORDER'][stock].values.tolist())
    #     writer.writerow(['%s Slippage'%stock]+back_data['SLIPPAGE'][stock].values.tolist())
    #     writer.writerow(['%s PnL'%stock]+back_data['DAILY_PNL'][stock].values.tolist())
    csv_file.close()

def writejson(back_data,budget,baseline_data,base_index):

    daily_return = back_data['DAILY_PNL']/budget
    total_return = back_data['TOTAL_PNL']/budget
    stats = metrics(daily_return, total_return, baseline_data,base_index)
    # multiply by 100 for readability purposes
    daily_return_percent = daily_return*100
    total_return_percent = total_return*100

    d = {'dates':back_data['DAILY_PNL'].index.format(),\
         'daily_pnl':daily_return_percent.sum(axis=1).values.tolist(),\
         'total_pnl':total_return_percent.sum(axis=1).values.tolist(),\
         'stocks':back_data['DAILY_PNL'].columns.tolist(),\
         'stock_pnl':daily_return_percent.values.tolist(),\
         'stock_position':back_data['POSITION'].values.tolist(),\
         'metrics':stats.keys(),\
         'metrics_values':stats.values()}
    return d;


def updateCheck():
    ''' checks for new version of toolbox
    Returns:
        returns True if the version of the toolox on PYPI is not the same as the current version
        returns False if version is the same
    '''

    from auquanToolbox.version import __version__
    updateStr = ''
    try:
        toolboxJson = urllib2.urlopen('https://pypi.python.org/pypi/auquanToolbox/json')
    except Exception as e:
        return False

    toolboxDict = json.loads(toolboxJson.read())

    if __version__ != toolboxDict['info']['version']:
        return True
    else:
        return False
