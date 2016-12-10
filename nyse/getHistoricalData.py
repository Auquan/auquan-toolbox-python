import pandas as pd
import urllib
import time

def download(ticker):
    url_format = 'http://www.google.com/finance/historical?q=%s&startdate=Nov 1, 1996&enddate=Nov 30, 2016&output=csv'
    url = url_format%ticker
    file_name = 'historicalData/%s.csv'%ticker.lower()
    print 'Downloading %s data from url: %s to file: %s'%(ticker,url,file_name)
    urllib.urlretrieve(url, file_name)

def getTickers():
    f = open('nyse.txt','r')
    lines = f.readlines()[1:]
    f.close()
    symbols = [line.split("\t", 1)[0] for line in lines]
    return symbols

if __name__ == '__main__':
    tickers = getTickers()
    for ticker in tickers:
        if ticker.isalnum():
            download(ticker)
            time.sleep(1)
