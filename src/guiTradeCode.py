from wsimple.api import Wsimple, WSOTPUser, errors
import csv
import datetime
import os
import pickle
import yfinance as yf
import pandas as pd
import firebaseStuff as fb
import pytz

class LoginError(Exception):
        pass
    
class WealthSimple():
    def __init__(self, account_email='', account_password=''):
        self.password = account_password
        self.email = account_email
        self.tokens = []
        self.firebase_token = []
        self.user = None

        self.stock_positions = []
        self.stock_positions_call_count = 0
        
    def get_users_name(self):
        meinfo = self.user.get_me(self.tokens)
        first = meinfo['first_name']
        last = meinfo['last_name']
        return [first,last]

    def get_tfsa_activity(self):
        return self.user.get_activities(self.tokens, account_id= self.__tfsa())
    
    def get_non_reg_activity(self):
        return self.user.get_activities(self.tokens, account_id= self.__non_reg_trade())
    
    def get_crypto_activity(self):
        return self.user.get_activities(self.tokens, account_id= self.__non_reg_crypto())

    def get_accounts(self):
        results = self.user.get_accounts(self.tokens)['results']
        return [i['id'] for i in results]

    def __get_token_file(self):
        with open('./user-data/tokens.txt', 'rb') as file:
            token = pickle.load(file)
            print("Pickled File Loaded")
        return token

    def __non_reg_trade(self):
        for account in self.user_accounts:
            if "crypto" not in account:
                if "non-registered" in account:
                    return account
    
    def __non_reg_crypto(self):
        for account in self.user_accounts:
            if "non-registered-crypto" in account:
                return account
    
    def __tfsa(self):
        for account in self.user_accounts:
            if "tfsa" in account:
                return account

    def authenticated_login(self, username='', password=''):
        self.tokens = self.__get_token_file()[0]
        if self.email != self.__get_token_file()[2]:
            raise LoginError
            return
        if self.tokens != []:
            try:
                FBuser = fb.auth.sign_in_with_email_and_password(username, password)
                firebase_token = FBuser['idToken']
                print("FireBase Authenticated")
            except:
                raise errors.LoginError
            ws = Wsimple.oauth_login(self.tokens)
            print("Wealth Simple Authenticated")
            token = ws.tokens
            with open('./user-data/tokens.txt', 'wb') as file:
                pickle.dump([token, firebase_token, username], file)
            print([token, firebase_token])
            self.tokens = token
            self.user = ws
            self.user_accounts = self.get_accounts()
        else:
            raise LoginError

    def otp_login(self, otpnumber):
            ws = Wsimple.otp_login(self.email, self.password, otpnumber)
            token = ws.tokens
            try:
                fb.auth.create_user_with_email_and_password(self.email, self.password)
                FBuser = fb.auth.sign_in_with_custom_token(self.firebase_token)
                firebase_token = FBuser['idToken']
            except:
                FBuser = fb.auth.sign_in_with_email_and_password(self.email,self.password)
                firebase_token = FBuser['idToken']
            with open('./user-data/tokens.txt', 'wb') as file:
                pickle.dump([token, firebase_token, self.email], file)
            print([token, firebase_token])
            self.tokens = token
            self.user = ws
            self.user_accounts = self.get_accounts()

    def login(self, otp=False):  
        if otp:
            try:
                ws = Wsimple(self.email, self.password)
            except WSOTPUser:
                pass
            except errors.LoginError:
                raise errors.LoginError
        else:
            try:
                self.authenticated_login(username=self.email, password=self.password)
            except:
                raise WSOTPUser
                print("Auth Failed")
        
    def get_watch_list(self):
        x = self.user.get_watchlist(self.tokens)['securities']
        sl = []
        for i in x:
            symbol = symbol = self.yahoo_naming(i)
            try:
                currentPrice = float(i['quote']['ask'])
                previousClose = float(i['quote']['previous_close'])
                priceChange = float(currentPrice) - float(previousClose)
                try:
                    percChange = (round(100 * (float(currentPrice) / float(previousClose) - 1), 2))
                except:
                    percChange = 0
                maxPrice = float(i['quote']['high'])
                minPrice = float(i['quote']['low'])
                sl.append([symbol, currentPrice, previousClose, round(priceChange, 2), percChange, maxPrice, minPrice])
            except:
                print(symbol)
        return sl

    def get_my_stock_list(self, account_id):
        if self.stock_positions == [] or self.stock_positions_call_count == 3:
            self.stock_positions = self.user.get_mobile_dashboard(self.tokens)['positions']['results']
            self.stock_positions_call_count = 0
        else:
            self.stock_positions_call_count += 1

        x = self.stock_positions
        sl = []
        for i in x:
            if i['account_id'] == account_id:
                if 'crypto' in account_id:
                    symbol = i['stock']['symbol'] + "-CAD"
                    stock = yf.Ticker(symbol)
                    stockinfo = stock.info
                    openprice = float(stockinfo['open'])
                    currentPrice = float(self.get_current_price(stock))
                    maxPrice = float(stockinfo['dayHigh'])
                    minPrice = float(stockinfo['dayLow'])
                    priceChange = currentPrice - openprice
                    try:
                        percChange = (round(100 * (float(currentPrice) / float(openprice) - 1), 2))
                    except:
                        percChange = 0
                    quantity = float(i['quantity'])
                    sl.append([symbol, currentPrice, openprice, round(priceChange, 2), percChange, maxPrice, minPrice, quantity])
                else:
                    symbol = self.yahoo_naming(i)
                    stock = yf.Ticker(symbol)
                    try:
                        currentPrice = float(self.get_current_price(stock))
                    except:
                        currentPrice = float(i['quote']['ask'])
                    try:
                        previousClose = float(i['quote']['previous_close'])
                    except:
                        print(symbol)
                    priceChange = float(currentPrice) - float(previousClose)
                    percChange = (round(100 * (float(currentPrice) / float(previousClose) - 1), 2))
                    maxPrice = float(i['quote']['high'])
                    minPrice = float(i['quote']['low'])
                    quantity = float(i['quantity'])
                    sl.append([symbol, currentPrice, previousClose, round(priceChange, 2), percChange, maxPrice, minPrice, quantity])
        return sl
    
    def yahoo_naming(self, stock):
        symbol = stock['stock']['symbol']
        if "." in symbol:
            symbol = symbol.split(".")
            symbol = "-".join(symbol)
        if stock['stock']['primary_exchange'] == "TSX-V":  
            symbol += ".V"
        elif stock['stock']['security_type'] == 'EXCHANGE_TRADED_FUND':
            symbol += ".TO"
        elif stock['stock']['primary_exchange'] == "TSX":
            symbol += ".TO"
        elif stock['stock']['primary_exchange'] == 'AEQUITAS NEO EXCHANGE':
            symbol += ".NE"
        elif stock['stock']['primary_exchange'] == 'CSE':
            symbol += ".CN"
        elif stock['stock']['primary_exchange'] == 'FINRA':
            symbol += ""
        elif stock['stock']['primary_exchange'] != 'NYSE' and stock['stock']['primary_exchange'] != 'NASDAQ':
            print(stock['stock']['primary_exchange'])

        return symbol

    def get_current_price(self, stock):
        cp = stock.history(period="1d", interval="1m")['Open'].iloc[-1]
        return cp

    def update_csv(
            self,
            start_date = str(datetime.datetime.now())[:10], 
            end_date = str(datetime.datetime.now())[:10], 
            file_name = 'StockReport.csv', 
            all_data = False):
        account_activity = self.user.get_activities(self.tokens, account_id= self.account_id, limit=99)['results']
        stock_history = []
        option_list = ['created_at', 'symbol', 'security_name', 'object', 'order_type', 'quantity', 'market_value','fill_fx_rate']
        stock_history.append(option_list)
        for trade in account_activity:
            trade_info = []
            if trade['object'] == 'deposit' or trade['market_value'] == None:
                        continue
            for option in option_list:
                try:
                    if option == 'market_value':
                        try:
                            trade_info.append(trade[option]['amount'])
                        except TypeError:
                            continue
                    else:
                        trade_info.append(trade[option])
                except KeyError:
                    trade_info.append(' ')
            if trade['object'] == 'dividend':
                trade_info[0] = trade['process_date']
            
            trade_date = trade_info[0][:10]
            if all_data is False:
                year = int(trade_date[:4])
                month = int(trade_date[5:7])
                day = int(trade_date[8:10])
                startyear = int(start_date[:4])
                startmonth = int(start_date[5:7])
                startday = int(start_date[8:10])
                endyear = int(end_date[:4])
                endmonth = int(end_date[5:7])
                endday = int(end_date[8:10])
                d1 = datetime.date(startyear, startmonth, startday)
                d2 = datetime.date(year, month, day)
                d3 = datetime.date(endyear, endmonth, endday)
                if not (d1 <= d2 <= d3):
                    continue
            trade_info[0] = trade_date
            stock_history.append(trade_info)

        with open(file_name, 'r', newline='') as read_file, open('temp.csv', 'w', newline='') as write_file:
                wr = csv.writer(write_file, quoting=csv.QUOTE_ALL)
                wr.writerows(stock_history)
                reader = csv.reader(read_file)
                data = list(reader)
                if data != []:
                    data.pop(0)
                wr.writerows(data)
        os.remove(file_name)
        os.rename('temp.csv', file_name)

    def get_positions_file(self):
        positions = self.user.get_positions(self.tokens)['results']
        firstitem = positions[0]['stock']
        stockList = []
        for stock in positions:
            for key,value in stock.items():
                if key == 'stock':
                    stockList.append(value) 

        keys = firstitem.keys()
        fieldsnotin = 0
        with open('StockPositions.csv', 'w', newline='')  as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            try:
                dict_writer.writerows(stockList)
            except ValueError:
                fieldsnotin += 1

    def get_stock_chart(self, ticker, period, interval):
        stock = yf.Ticker(ticker)
        try:
            history = stock.history(period= period, interval= interval).drop(columns=["Stock Splits", "Dividends", "Close", "Low", "High"])
            history.index.name = 'Date'
            prevClose = 0
            history.reset_index(inplace=True)
            dataFrame = yf.download(ticker,period=period, interval=interval)
            dataFrame.index.name = 'Date'
            return[history['Date'].tolist(), history['Open'].tolist(), history['Volume'].tolist(),dataFrame]
        except:
            return

    def get_stock_chartOLD(self, ticker, period, interval):
        stock = yf.Ticker(ticker)
        try:
            history = stock.history(period= period, interval= interval).drop(columns=["Stock Splits", "Dividends", "Close", "Low", "High"])
            history.index.name = 'Date'
            prevClose = 0
            history.reset_index(inplace=True)
            return[history['Date'].tolist(), history['Open'].tolist(), history['Volume'].tolist()]
        except:
            return

    def get_portfolio_chart(self, time, account):
        if account == 'TFSA':
            account = self.__tfsa()
        elif account == 'Personal':
            account = self.__non_reg_trade()
        elif account == 'Crypto':
            account = self.__non_reg_crypto()
        portfolio = self.user.get_historical_portfolio_data(self.tokens, time=time,account_id=account)['results']
        if account == self.__non_reg_crypto():
            try:
                graphing_data = [[(datetime.datetime.strptime(x['date'].replace("T"," ").replace("Z",""),'%Y-%m-%d %H:%M:%S.%f')).replace(tzinfo=pytz.UTC),x['value']['amount']] for x in portfolio ]
            except ValueError:
                graphing_data = [[(datetime.datetime.strptime(x['date'].replace("T"," ").replace("Z",""),'%Y-%m-%d')).replace(tzinfo=pytz.UTC),x['value']['amount']] for x in portfolio ]
            return graphing_data
        try:
            graphing_data = [[(datetime.datetime.strptime(x['date'].replace("T"," ").replace("Z",""),'%Y-%m-%d %H:%M:%S.%f')).replace(tzinfo=pytz.UTC),x['value']['amount']] for x in portfolio ]
            cleanedDates = self.portfolio_hour_cleaner(graphing_data)
            x = 0
            for i in graphing_data:
                i[0] = cleanedDates[x]
                x += 1
        except ValueError:
            graphing_data = [[(datetime.datetime.strptime(x['date'].replace("T"," ").replace("Z",""),'%Y-%m-%d')).replace(tzinfo=pytz.UTC),x['value']['amount']] for x in portfolio ]
        return graphing_data

    def portfolio_data_cleaner(self, data):
        dates = [i[0] for i in data]
        newDates = []
        startingIndex = 0
        days_to_sub = 0
        if dates[0].weekday() == 0:
            newDates.append(dates[0])
            startingIndex = 1
        for day in dates[startingIndex:]:
            if day.weekday() == 0:
                days_to_sub += 2
                newDay = day - datetime.timedelta(days= days_to_sub)   
            else:
                newDay = day - datetime.timedelta(days= days_to_sub)
            newDates.append(newDay)
        return newDates

    def portfolio_hour_cleaner(self, data):
        print("starting hour cleaner")
        dates = [i[0] for i in data]
        newDates = []
        startingIndex = 0
        hours_to_sub = 0
        min_to_sub = 0
        newDates.append(dates[0])
        for day in dates[1:]:
            if day.hour == 14 and day.minute == 30:
                hours_to_sub += 17
                min_to_sub = 30
                newDay = day - datetime.timedelta(hours= hours_to_sub, minutes=min_to_sub)   
            else:
                newDay = day - datetime.timedelta(hours= hours_to_sub, minutes=min_to_sub)   
            newDates.append(newDay)
        return newDates
            

        
