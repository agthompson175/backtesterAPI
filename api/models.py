from . import db

class Stock(db.Model):
    ticker = db.Column(db.String(50), primary_key=True)
    size = db.Column(db.String(50))
    


#https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&outputsize=full&apikey=demo
#https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&outputsize=full&apikey=demo
