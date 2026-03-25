import src.stock_data as stockdata
companies=['TCS.NS','INFY.NS','WIPRO.NS','AAPL','GOOGL','MSFT','AMZN']

for ticker in companies:
    stockdata.get_stock_data(ticker)
    