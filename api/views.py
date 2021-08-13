
from __future__ import (absolute_import, division, print_function,unicode_literals)
from backtrader.indicators import EMA
from flask import Blueprint, jsonify, request
import backtrader

from . import db
from .models import Stock

from .data_context import get_chart_data, get_candle_data, general_info
import backtrader
import datetime
from flask_cors import CORS

main = Blueprint('main', __name__)


@main.route('/inputs', methods=['POST'])
@cross_origin()
def inputs():
    stock_data = request.get_json()
    new_stock = Stock(ticker=stock_data['ticker'], size=stock_data['size'])
    
    
    #delete old rows 
    db.session.query(Stock).delete()
    db.session.commit()

    #new row
    db.session.add(new_stock)
    db.session.commit()



    return 'Done', 201


@main.route('/company_info')
def company_info():
    tick = Stock.query.first().ticker
    data = general_info(tick)
    return data


@main.route('/chart_data')
def chart_data():
    tick = Stock.query.first().ticker
    sess = Stock.query.first().size
    data = get_candle_data(tick, sess)
    return jsonify(data)



@main.route('/simple_data')
def simple_data():
    simple_dict = {}

    ##### Create a Stratey


    class TestStrategy(backtrader.Strategy):

        def log(self, close, date, dt=None):
            ''' Logging function fot this strategy'''
            dt = dt or self.datas[0].datetime.date(0)
            #print('%s, %s' % (dt.isoformat(), txt))
            simple_dict[dt.isoformat()] = [close, date]

        def __init__(self):
            # Keep a reference to the "close" line in the data[0] dataseries
            self.dataclose = self.datas[0].close
            self.order = None

        def notify_order(self, order):
            if order.status in [order.Submitted, order.Accepted]:
                return

            if order.status in [order.Completed]:
                if order.isbuy():
                    self.log('BUY EXECUTED', order.executed.price)
                elif order.issell():
                    self.log('SELL EXECUTED', order.executed.price)

                self.bar_executed = len(self)
            self.order = None

        def next(self):
            # Simply log the closing price of the series from the reference
            self.log('Close', self.dataclose[0])

            if self.order:
                return

            if not self.position:

                if self.dataclose[0] < self.dataclose[-1]:
                    # current close less than previous close

                    if self.dataclose[-1] < self.dataclose[-2]:
                        # previous close less than the previous close

                        # BUY, BUY, BUY!!! (with all possible default parameters)
                        self.log('BUY CREATE', self.dataclose[0])
                        self.order = self.buy()

            else:
                if len(self) >= (self.bar_executed + 5):
                    self.log('SELL CREATED', self.dataclose[0])
                    self.order = self.sell()

    
    simple_data_dict={}
    tick=Stock.query.first().ticker
    sess = Stock.query.first().size

    simple_data_dict['ticker'] = tick
    
    df = get_chart_data(tick, sess)

    cerebro = backtrader.Cerebro()


    cerebro.broker.set_cash(1000000)
    df.to_csv('stock_data.csv', index=False)
    data = backtrader.feeds.YahooFinanceCSVData(
        dataname='stock_data.csv',
        #beginning values
        fromdate=datetime.datetime(int(df.iloc[0, 0].split(
            '-')[0]), int(df.iloc[0, 0].split('-')[1]), int(df.iloc[0, 0].split('-')[2])),
        #endddate
        todate=datetime.datetime(int(df.iloc[-1, 0].split(
            '-')[0]), int(df.iloc[-1, 0].split('-')[1]), int(df.iloc[-1, 0].split('-')[2])),
        reverse=False
    )

    cerebro.adddata(data)

    cerebro.addstrategy(TestStrategy)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(backtrader.sizers.AllInSizerInt)

    #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    simple_data_dict['starting'] = cerebro.broker.getvalue()

    cerebro.run()
    #print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    simple_data_dict['final'] = cerebro.broker.getvalue()
    #print(sma_data_dict)
    simple_data_dict['price_dict'] = simple_dict
    
    return jsonify({'simple': simple_data_dict})






@main.route('/sma')
def simple():
    sma_dict = {}


    class SimpleStrategy(backtrader.Strategy):
        

        def log(self, close, date, dt=None):
            dt = dt or self.datas[0].datetime.date(0)
            sma_dict[dt.isoformat()] = [close, date]

        def __init__(self):
            self.dataclose = self.datas[0].close
            self.order = None
            self.buyprice = None
            self.buycomm = None

            self.sma = backtrader.indicators.SimpleMovingAverage(self.datas[0], period=15)
            self.rsi = backtrader.indicators.RelativeStrengthIndex()

        def notify_order(self, order):
            if order.status in [order.Submitted, order.Accepted]:
                return

            if order.status in [order.Completed]:
                if order.isbuy():
                    self.log(
                        'BUY EXECUTED', order.executed.price)

                    self.buyprice = order.executed.price
                    self.buycomm = order.executed.comm
                else:  # Sell
                    self.log('SELL EXECUTED', order.executed.price)

                self.bar_executed = len(self)

            elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                self.log('Order Canceled/Margin/Rejected', self.dataclose[0])

            # Write down: no pending order
            self.order = None

        def notify_trade(self, trade):
            if not trade.isclosed:
                return

            self.log('OPERATION PROFIT', trade.pnl)

        def next(self):
            self.log('Close', self.dataclose[0])
            #print('rsi:', self.rsi[0])
            if self.order:
                return

            if not self.position:
                if (self.rsi[0] < 30):
                    self.log('BUY CREATE', self.dataclose[0])
                    self.order = self.buy()

            else:
                if (self.rsi[0] > 70):
                    self.log('SELL CREATE', self.dataclose[0])
                    self.order = self.sell()

    sma_data_dict = {}
    tick = Stock.query.first().ticker
    sess = Stock.query.first().size

    sma_data_dict['ticker'] = tick

    df = get_chart_data(tick, sess)

    cerebro = backtrader.Cerebro()

    cerebro.broker.set_cash(1000000)
    df.to_csv('stock_data.csv', index=False)
    data = backtrader.feeds.YahooFinanceCSVData(
        dataname='stock_data.csv',
        #beginning values
        fromdate=datetime.datetime(int(df.iloc[0, 0].split(
            '-')[0]), int(df.iloc[0, 0].split('-')[1]), int(df.iloc[0, 0].split('-')[2])),
        #endddate
        todate=datetime.datetime(int(df.iloc[-1, 0].split(
            '-')[0]), int(df.iloc[-1, 0].split('-')[1]), int(df.iloc[-1, 0].split('-')[2])),
        reverse=False
    )

    cerebro.adddata(data)

    cerebro.addstrategy(SimpleStrategy)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(backtrader.sizers.AllInSizerInt)

    #print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    sma_data_dict['starting'] = cerebro.broker.getvalue()

    cerebro.run()
    #print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    sma_data_dict['final'] = cerebro.broker.getvalue()
    #print(sma_data_dict)
    sma_data_dict['price_dict'] = sma_dict

    return jsonify({'sma': sma_data_dict})


@main.route('/MACD')
def MACD():
    macd_dict = {}

    class MACD(backtrader.Strategy):
            params = (
                ('maperiod', 15),
            )
            #def log(self, close, date, dt=None):
            #''' Logging function fot this strategy'''
            #dt = dt or self.datas[0].datetime.date(0)
            #print('%s, %s' % (dt.isoformat(), txt))
            #simple_dict[dt.isoformat()] = [close, date]
            def log(self, close, date, dt=None):
                ''' Logging function fot this strategy'''
                dt = dt or self.datas[0].datetime.date(0)
                #print('%s, %s' % (dt.isoformat(), txt))
                macd_dict[dt.isoformat()] = [close, date]

            @staticmethod
            def percent(today, yesterday):
                return float(today - yesterday) / today

            def __init__(self):
                self.dataclose = self.datas[0].close
                self.volume = self.datas[0].volume

                self.order = None
                self.buyprice = None
                self.buycomm = None

                me1 = EMA(self.data, period=12)
                me2 = EMA(self.data, period=26)
                self.macd = me1 - me2
                self.signal = EMA(self.macd, period=9)

                backtrader.indicators.MACDHisto(self.data)

            def notify_order(self, order):
                if order.status in [order.Submitted, order.Accepted]:
                    return
                if order.status in [order.Completed]:
                    if order.isbuy():
                        self.log(
                            'BUY EXECUTED', order.executed.price)

                        self.buyprice = order.executed.price
                        self.buycomm = order.executed.comm
                        self.bar_executed_close = self.dataclose[0]
                    else:
                        self.log('SELL EXECUTED', order.executed.price)
                    self.bar_executed = len(self)

                elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                    self.log('Order Canceled/Margin/Rejected', self.dataclose[0])

                    self.order = None

            def notify_trade(self, trade):
                if not trade.isclosed:
                    return

                self.log('OPERATION PROFIT', trade.pnl)

            def next(self):
                self.log('Close', self.dataclose[0])
                if self.order:
                    return

                if not self.position:
                    condition1 = self.macd[-1] - self.signal[-1]
                    condition2 = self.macd[0] - self.signal[0]
                    if condition1 < 0 and condition2 > 0:
                        self.log('BUY CREATE', self.dataclose[0])
                        self.order = self.buy()

                else:
                    condition = (
                        self.dataclose[0] - self.bar_executed_close) / self.dataclose[0]
                    if condition > 0.1 or condition < -0.1:
                        self.log('SELL CREATE', self.dataclose[0])
                        self.order = self.sell()


    cerebro = backtrader.Cerebro()

    cerebro.addstrategy(MACD)
    
    macd_data_dict = {}
    tick = Stock.query.first().ticker
    sess = Stock.query.first().size

    macd_data_dict['ticker'] = tick

    df = get_chart_data(tick, sess)

    df.to_csv('stock_data.csv', index=False)
    data = backtrader.feeds.YahooFinanceCSVData(
        dataname='stock_data.csv',
        #beginning values
        fromdate=datetime.datetime(int(df.iloc[0, 0].split(
            '-')[0]), int(df.iloc[0, 0].split('-')[1]), int(df.iloc[0, 0].split('-')[2])),
        #endddate
        todate=datetime.datetime(int(df.iloc[-1, 0].split(
            '-')[0]), int(df.iloc[-1, 0].split('-')[1]), int(df.iloc[-1, 0].split('-')[2])),
        reverse=False
    )
    cerebro.adddata(data)

    cerebro.broker.setcash(1000000)

    cerebro.addsizer(backtrader.sizers.AllInSizerInt)

    macd_data_dict['starting'] = cerebro.broker.getvalue()
    

    cerebro.run()

    
    macd_data_dict['final'] = cerebro.broker.getvalue()

    
    macd_data_dict['macd_dict'] = macd_dict

    return jsonify({'macd': macd_data_dict})
