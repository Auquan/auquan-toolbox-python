from __future__ import absolute_import, division, print_function, unicode_literals
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlretrieve, urlopen
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay
import os

def download(exchange, ticker, file_name,logger):
    url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/%s/historicalData/%s.csv'%(exchange.lower(), ticker.lower())
    response = urlopen(url)
    status = response.getcode()
    if status == 200:
        logger.info('Downloading %s data to file: %s'%(ticker, file_name))
        with open(file_name, 'w') as f: f.write(response.read())
        return True
    else:
        logger.info('File not found. Please check settings!')
        return False

def data_available(exchange, markets,logger):
    dir_name = '%s/historicalData/'%exchange.lower()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    for m in markets:
        file_name = '%s%s.csv'%(dir_name, m.lower())
        if not os.path.exists(file_name):
            try:
                assert(download(exchange, m, file_name,logger)),"%s not found. Please check settings!"%file_name
            except AssertionError:
                logger.exception("%s not found. Please check settings!"%file_name)
                raise      
    return True

def download_security_list(exchange, logger):
    dir_name = '%s/'%exchange.lower()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    file_name = '%s%s.txt'%(dir_name, exchange.lower())
    if not os.path.exists(file_name):
        url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/%s'%(file_name)
        response = urlopen(url)
        status = response.getcode()
        if status == 200:
            logger.info('Downloading data to file: %s'%file_name)
            with open(file_name, 'w') as f: f.write(response.read())
            return True
        else:
            logger.info('File not found. Please check exchange settings!')
        return False
    else:
        return True

def compatibleDictKeyCheck(dict, key):
    try:
        return dict.has_key(key)
    except:
        return key in dict

def load_data(exchange, markets, start, end, lookback, budget, logger, random=False):

    logger.info("Loading Data from %s to %s...."%(start,end))

    # because there are some holidays adding some cushion to lookback
    try:
        dates = [pd.to_datetime(start)-BDay((lookback* 1.10)+10), pd.to_datetime(end)]
    except ValueError:
        logger.exception("%s or %s is not valid date. Please check settings!"%(start, end))
        raise ValueError("%s or %s is not valid date. Please check settings!"%(start, end))

    try:
        assert(dates[1]>dates[0]),"Start Date is after End Date"
    except AssertionError:
        logger.exception("Start Date is after End Date")
        raise

    #Download list of securities
    assert(download_security_list(exchange, logger))
    if len(markets)==0:
        file_name = '%s/%s.txt'%(exchange.lower(), exchange.lower())
        
        markets = [line.strip() for line in open(file_name)]
 

    markets = [m.upper() for m in markets]
    features = ['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME']
    date_range = pd.date_range(start=dates[0], end=dates[1], freq='B')
    back_data = {}
    if random:
        for feature in features:
            back_data[feature] = pd.DataFrame(np.random.randint(10, 50, size=(date_range.size,len(markets))),
                                              index=date_range,
                                              columns=markets)
    else:
        for feature in features:
            back_data[feature] = pd.DataFrame(index=date_range, columns=markets)
        assert data_available(exchange, markets, logger)
        market_to_drop = []
        for market in markets:
            logger.info('Reading %s.csv'%market)
            csv = pd.read_csv('%s/historicalData/%s.csv'%(exchange.lower(), market.lower()), index_col=0)
            csv.index = pd.to_datetime(csv.index)
            csv.columns = [col.upper() for col in csv.columns]
            csv = csv.reindex(index=csv.index[::-1])
            features = [col.upper() for col in csv.columns]
            market_first_date = csv.index[0]
            if (market_first_date > (dates[0]-BDay(1)+BDay(1))):
                market_to_drop.append(market)
                logger.info('Dropping %s. This stock did not start trading before (start date -lookback days)'%market)
                continue
            market_last_date = csv.index[-1]
            if (market_last_date < (dates[0] - BDay(1) + BDay(1))):
                market_to_drop.append(market)
                logger.info('Dropping %s. This stock terminated before (start date -lookback days)'%market)
                continue

            back_fill_data = False
            if market_last_date in date_range:
                back_fill_data = True
                logger.info('The market %s doesnt have data for the whole duration. Subsituting missing dates with the last known data'%market)

            for feature in features:
                if not compatibleDictKeyCheck(back_data, feature):
                    back_data[feature] = pd.DataFrame(index=date_range, columns=markets)
                back_data[feature][market] = csv[feature][date_range]
                if back_fill_data:
                    back_data[feature].loc[market_last_date:date_range[-1], market] = back_data[feature].at[market_last_date, market]

        for m in market_to_drop: 
            logger.info('Dropping %s. Not Enough Data'%m)
            markets.remove(m) 

        for feature in features:
            back_data[feature].drop(market_to_drop, axis=1, inplace=True)
        dates_to_drop = pd.Series(False, index=date_range)
        for feature in features:
            dates_to_drop |= pd.isnull(back_data[feature]).any(axis=1)

        dropped_dates = date_range[dates_to_drop]
        date_range = date_range[~dates_to_drop]
        for feature in features:
            back_data[feature] = back_data[feature].drop(dropped_dates)

    back_data['COST TO TRADE'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['POSITION'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['FILLED_ORDER'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['DAILY_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['TOTAL_PNL'] = pd.DataFrame(0, index=date_range, columns=markets)
    back_data['FUNDS'] = pd.Series(budget, index=date_range)
    back_data['VALUE'] = pd.Series(budget, index=date_range)
    back_data['MARGIN'] = pd.Series(0, index=date_range)

    return back_data, date_range

# TODO: Refactor this
def load_data_nologs(exchange, markets, start, end, lookback=2):

    # because there are some holidays adding some cushion to lookback
    try:
        dates = [pd.to_datetime(start)-BDay(lookback* 1.10), pd.to_datetime(end)]
    except ValueError:
        raise ValueError("%s or %s is not valid date. Please check settings!"%(start, end))

    assert(dates[1]>dates[0]),"Start Date is after End Date"

    dir_name = '%s/'%exchange.lower()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    file_name = '%s%s.txt'%(dir_name, exchange.lower())
    if not os.path.exists(file_name):
        url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/%s'%(file_name)
        response = urlopen(url)
        status = response.getcode()
        if status == 200:
            with open(file_name, 'w') as f: f.write(response.read())
        else:
            print('File not found. Please check exchange name!')

    if len(markets)==0:
        file_name = '%s/%s.txt'%(exchange.lower(), exchange.lower())
        
        markets = [line.strip() for line in open(file_name)]
 

    markets = [m.upper() for m in markets]
    features = ['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME']
    date_range = pd.date_range(start=dates[0], end=dates[1], freq='B')
    back_data = {}
    for feature in features:
        back_data[feature] = pd.DataFrame(index=date_range, columns=markets)
    dir_name = '%s/historicalData/'%exchange.lower()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    for m in markets:
        file_name = '%s%s.csv'%(dir_name, m.lower())
        if not os.path.exists(file_name):
            url = 'https://raw.githubusercontent.com/Auquan/auquan-historical-data/master/%s/historicalData/%s.csv'%(exchange.lower(), m.lower())
            response = urlopen(url)
            status = response.getcode()
            if status == 200:
                with open(file_name, 'w') as f: f.write(response.read())
            else:
                print('File not found. Please check settings!')
    
    market_to_drop = []
    for market in markets:
        csv = pd.read_csv('%s/historicalData/%s.csv'%(exchange.lower(), market.lower()), index_col=0)
        csv.index = pd.to_datetime(csv.index)
        csv.columns = [col.upper() for col in csv.columns]
        csv = csv.reindex(index=csv.index[::-1])
        features = [col.upper() for col in csv.columns]
        market_first_date = csv.index[0]
        if (market_first_date > (dates[0]-BDay(1)+BDay(1))):
            market_to_drop.append(market)
            continue
        market_last_date = csv.index[-1]
        if (market_last_date < (dates[0] - BDay(1) + BDay(1))):
            market_to_drop.append(market)
            continue

        back_fill_data = False
        if market_last_date in date_range:
            back_fill_data = True

        for feature in features:
            if not compatibleDictKeyCheck(back_data, feature):
                back_data[feature] = pd.DataFrame(index=date_range, columns=markets)
            back_data[feature][market] = csv[feature][date_range]
            if back_fill_data:
                back_data[feature].loc[market_last_date:date_range[-1], market] = back_data[feature].at[market_last_date, market]

    for m in market_to_drop: 
        markets.remove(m) 

    for feature in features:
        back_data[feature].drop(market_to_drop, axis=1, inplace=True)
    dates_to_drop = pd.Series(False, index=date_range)
    for feature in features:
        dates_to_drop |= pd.isnull(back_data[feature]).any(axis=1)

    dropped_dates = date_range[dates_to_drop]
    date_range = date_range[~dates_to_drop]
    for feature in features:
        back_data[feature] = back_data[feature].drop(dropped_dates)

    return back_data
