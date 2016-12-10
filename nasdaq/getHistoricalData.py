import pandas as pd
import urllib
import time

def download(ticker):
    url_format = 'http://www.google.com/finance/historical?q=%s&startdate=Nov 1, 1996&enddate=Nov 30, 2016&output=csv'
    url = url_format%ticker
    file_name = 'historicalData/%s.csv'%ticker.lower()
    print 'Downloading %s data from url: %s to file: %s'%(ticker,url,file_name)
    #urllib.urlretrieve(url, file_name)

def getTickers():
    csv = pd.read_csv('nasdaq.csv')
    return csv['Symbol']

if __name__ == '__main__':
    tickers = getTickers()
    for ticker in tickers:
        if '^' not in ticker:
            download(ticker)
            time.sleep(1)
