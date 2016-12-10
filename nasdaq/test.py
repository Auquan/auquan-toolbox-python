import pandas as pd

features = ['OPEN', 'CLOSE', 'HIGH', 'LOW', 'VOLUME']
markets = ['a','aapl']
date_range = pd.date_range(start="11-Nov-16", end="21-Nov-16", freq='B')
back_data = {}

for feature in features:
    back_data[feature] = pd.DataFrame(index=date_range, columns=markets)

for market in markets:
    csv = pd.read_csv('historicalData/%s.csv'%market, index_col=0)
    csv.index = pd.to_datetime(csv.index)
    csv.columns = [col.upper() for col in csv.columns]
    for feature in features:
        back_data[feature][market] = csv[feature]

print back_data
