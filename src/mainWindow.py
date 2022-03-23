from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QApplication, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QDockWidget, QListWidget, QMainWindow, QWidget, QGraphicsView, QLabel, QGraphicsTextItem, QPushButton, QApplication
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QSize, QByteArray
from PyQt5.QtGui import QPixmap, QFont, QColor
from guiTradeCode import WealthSimple, LoginError
from WSCustomWidgets import WealthSimpleGraphs
from wsimple.api import Wsimple, WSOTPUser, errors as WSerrors
from urllib.error import HTTPError
import firebaseStuff as fb
import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems import DateAxisItem
import shapely.geometry
import time
import csv
import datetime
import os
import pickle
import copy
import threading
import matplotlib.pyplot as plt
import pytz
import finplot as fplt

class TimeAxisItem(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [datetime.datetime.fromtimestamp(value) for value in values]

class IncorrectCredentials(Exception):
    pass

class StartingPage(QMainWindow):
    #resized = pyqtSignal()

    def __init__(self, widgetList):
        super(StartingPage, self).__init__()
        self.widget = QtWidgets.QStackedWidget()
        self.widgetList = widgetList

        for item in widgetList:
            self.widget.addWidget(item)

        self.setCentralWidget(self.widget)
        self.setStyleSheet("QMainWindow::separator {background: rgb(200, 200, 200);width: 5px;height: 2px;}")

    def addanotherpage(self, item):
        self.widget.addWidget(item)
        self.widgetList.append(item)

    def iterate_stack(self):
        self.widget.setCurrentIndex(self.widget.currentIndex() + 1)
    
    def log_out(self):
        newLoginPage = LoginPage()
        newLoginPage.hideOnStart()
        self.widget.removeWidget(self.widgetList[0])
        self.addanotherpage(newLoginPage)
        self.iterate_stack()
        self.widget.removeWidget(self.widgetList[1])
        self.widgetList = [self.widgetList[-1]]

    def closeEvent(self, event):
        print("Closing application")
        if len(widgetList) == 2:
            self.widgetList[1].send_charts()

    '''def resizeEvent(self, event):
        print("Resized")
        self.resized.emit()
        return super(StartingPage, self).resizeEvent(event)'''

class LoginPage(QDialog):
    def __init__(self):
        super(LoginPage, self).__init__()
        loadUi("./ui-files/login.ui",self)
        self.OTPLabel.setStyleSheet("color: red;")
        self.emailLabel.setStyleSheet("color: red;")
        self.passwordLabel.setStyleSheet("color: red;")
        self.incorrectLabel.setStyleSheet("color: red;")
        self.loginButton.clicked.connect(lambda: self.login(self.usernameEdit.text(), self.passwordEdit.text()))
        self.passwordEdit.returnPressed.connect(self.loginButton.click)
        self.onetimepasswordEdit.returnPressed.connect(self.loginButtonOTP.click)
        self.authLogoutButton.clicked.connect(lambda: self.logout())
        self.loginAttempted = False
    
    def authenticated_user(self, User):
        try:
            self.name =  User.get_users_name()
            self.authLabel.setText("Welcome back " + self.name[0] + " " + self.name[1])
            self.authLabel.show()
            self.authContinueButton.show()
            self.authLogoutButton.show()
            self.authContinueButton.clicked.connect(lambda: self.goToDashBoard(User))
            print("Authenticated User")
            elelist = [
                self.usernameEdit,
                self.passwordEdit,
                self.loginButton,
                self.signupButton
            ]
            for item in elelist:
                item.hide()
        except (WSerrors.InvalidAccessTokenError, LoginError, EOFError) as e:
            print("Authenticated login failed")
            raise WSOTPUser

    def logout(self):
        '''with open('./user-data/tokens.txt', 'wb') as file:
                pickle.dump([], file)'''
        self.hideOnStart()
        elelist = [
            self.usernameEdit,
            self.passwordEdit,
            self.loginButton,
            self.signupButton
        ]
        for ele in elelist:
            ele.show()

    def goToDashBoard(self, User):
        dashboard = HomeDashBoard(User)
        window.addanotherpage(dashboard)
        window.iterate_stack()
        window.showMaximized()
        
    def check_required_fields(self,fields):
        for field in fields:
            if field.text() == '':
                return False
        return True

    def login(self, username = '', password = ''):
        self.hideOnStart()
        if not self.check_required_fields([self.usernameEdit]) or not self.check_required_fields([self.passwordEdit]) :
            if not self.check_required_fields([self.usernameEdit]):
                print("Please enter your Username")
                self.emailLabel.show()
            if not self.check_required_fields([self.passwordEdit]):
                print("Please enter your password")
                self.passwordLabel.show()
            return
        if self.loginAttempted == True:
            return
        print(username, password)
        self.username = username
        self.password = password
        User = WealthSimple(username, password)
        try: 
            User.login()
            self.loginAttempted = True
            print("Logged in authenticated")
            self.authenticated_user(User)
        except WSOTPUser:
            try:
                print("WSOT")
                User.login(otp=True)
                self.loginButton.hide()
                self.loginButtonOTP.show()
                self.OTPLabel.show()
                self.onetimepasswordEdit.show()
                self.loginButtonOTP.clicked.connect(lambda: self.otp_try_log(User))
            except WSerrors.LoginError:
                print("Username or password incorrect")
                self.incorrectLabel.show()
                return
        except WSerrors.LoginError:
            print("Username or password incorrect")
            self.incorrectLabel.show()
            return

    def otp_try_log(self, User):
        User.otp_login(self.onetimepasswordEdit.text())
        self.goToDashBoard(User)

    def hideOnStart(self):
        element_list = [
            self.loginButtonOTP,
            self.OTPLabel,
            self.onetimepasswordEdit,
            self.authLabel,
            self.authContinueButton,
            self.authLogoutButton,
            self.emailLabel,
            self.passwordLabel,
            self.incorrectLabel,
        ]

        for element in element_list:
            element.hide()

    def otPasswordNeeded(self):
        self.loginButton.hide()
        self.onetimepasswordEdit.show()
        self.OTPLabel.show()
        self.loginButtonOTP.show()

class HomeDashBoard(QDialog):
    
    def __init__(self, User):
        super(HomeDashBoard, self).__init__()
        loadUi("./ui-files/dashboard.ui",self)
        self.user = User
        self.createTFSATable()
        self.createPersonalStockTable()
        self.createCryptoTable()
        self.loadDashBoard()
        
        self.watchlistTable.itemClicked.connect(lambda item: self.get_graph_data(self.watchlistTable, item))
        self.personalStockTable.itemClicked.connect(lambda item: self.get_graph_data(self.personalStockTable, item))
        self.tfsaStockTable.itemClicked.connect(lambda item: self.get_graph_data(self.tfsaStockTable, item))
        self.cryptoTable.itemClicked.connect(lambda item: self.get_graph_data(self.cryptoTable, item))

        self.watchlistTable.itemDoubleClicked.connect(lambda item: self.goToStockPage(item))
        self.personalStockTable.itemDoubleClicked.connect(lambda item: self.goToStockPage(item))
        self.tfsaStockTable.itemDoubleClicked.connect(lambda item: self.goToStockPage(item))
        self.cryptoTable.itemDoubleClicked.connect(lambda item: self.goToStockPage(item))

        self.stocklistButton.clicked.connect(lambda: self.listMinimizer(self.accountTabs, self.stocklistButton))
        self.watchlistButton.clicked.connect(lambda: self.listMinimizer(self.watchlistTable, self.watchlistButton))
        self.accountTabs.tabBarDoubleClicked.connect(lambda tab: self.account_graph_get(tab))

        self.defaultGraphLocation = None

        self.data_updater = UpdateDataThread(self.user)
        self.data_updater.start()
        self.data_updater.send_lists.connect(self.reloadDashBoard)
        self.data_updater.token_expired.connect(self.log_out_dash)

        self.graph_updater = UpdateGraphThread(self.user)
        self.graph_updater.send_data.connect(self.createGraphDock)
        self.graph_updater.send_data_portfolio.connect(lambda data:self.createGraphDock(data, portfolio=True))

        #window.resized.connect(self.whenResized)

    def goToStockPage(self, User):
        StockInfo = []
        stockview = StockView(User, StockInfo)
        window.addanotherpage(stockview)
        window.iterate_stack()
        window.showMaximized()
    
    def whenResized(self):
        print("ScreenResized")
        screenW = window.width()
        screenH = window.height()
       
        #self.newgraphDock.multiWidget.resize(screenW/3,self.newgraphDock.multiWidget.height())
        graphW = self.newgraphDock.multiWidget.width()
        graphH = self.newgraphDock.multiWidget.height()
        print(graphW, graphH)
        #self.newgraphDock.volumeGraph.setMaximumHeight(screenH/7)

        
        '''try:
            self.newGraphDock.multiWidget.setWidth(screenW/3)
        except:
            print("didn't work")'''
        try:
            chartButtonList = [
                self.newgraphDock.oneDayButtonStock,
                self.newgraphDock.oneWeekButtonStock,
                self.newgraphDock.oneMonthbuttonStock,
                self.newgraphDock.threeMonthButtonStock,
                self.newgraphDock.oneYearButtonStock,
                self.newgraphDock.allButtonStock,
            ]
        except:
            chartButtonList = [
                self.newgraphDock.oneDayButton,
                self.newgraphDock.oneWeekButton,
                self.newgraphDock.oneMonthbutton,
                self.newgraphDock.threeMonthButton,
                self.newgraphDock.oneYearButton,
                self.newgraphDock.allButton,
            ]
        
        for button in chartButtonList:
            try:
                newButtonDim = round(graphW / 11,0)
                btnBorderRad = newButtonDim / 2
                print(newButtonDim, btnBorderRad)
                button.button.setFixedSize(newButtonDim, newButtonDim)
                buttonStyleSheet = "border-radius:"+ str(btnBorderRad)  +"px; border: 2px solid grey; font-size: 20px; background-color: #90A5A9"
                button.button.setStyleSheet(buttonStyleSheet)
                self.newgraphDock.horizontalButtonLayout.setSpacing(newButtonDim/2)
                self.newgraphDock.buttonWidget.setMaximumHeight(newButtonDim + newButtonDim * 0.2)
                self.newgraphDock.buttonWidget.setMinimumHeight(newButtonDim +  newButtonDim * 0.2)
                print("Resized")
            except:
                pass

    def redrawPortfolio(self, time):
        self.graph_updater.run(updateGraph=True, newGraph=False, portfolioGraph=True, time=time, account=self.account, currentGraph= self.newgraphDock)
        xData = self.newgraphDock.graph.__dict__['plotItem'].__dict__['dataItems'][0].__dict__['xData']
        yData = self.newgraphDock.graph.__dict__['plotItem'].__dict__['dataItems'][0].__dict__['yData']
        yData = self.newgraphDock.priceData
        self.index_of_2100 = []
        if self.newgraphDock.name != 'Crypto':
            hour_looking_at = 16
            minute_look_at = 0
            for n in xData:
                if datetime.datetime.fromtimestamp(n).hour == hour_looking_at and datetime.datetime.fromtimestamp(n).minute == minute_look_at:
                    tempDate = datetime.datetime(year=2020, month=1, day=1 , hour= hour_looking_at)
                    tempDate2 = datetime.datetime(year=2020, month=1, day=1 , hour=1, minute=minute_look_at)
                    hour_looking_at = (tempDate + datetime.timedelta(hours=7)).hour
                    self.index_of_2100.append(n)
        polyData = []
        i = 0
        for point in xData:
            polyData.append([point, yData[i]])
            i += 1
        polyData.append([max(xData),0])
        polyData.insert(0,[0,0])
        polygon = shapely.geometry.Polygon(polyData)
        self.polygon = polygon.buffer(0.000000000001)

    def account_graph_get(self, tab):
        self.account = self.accountTabs.tabText(tab)
        time = '1d'
        self.graph_updater.run(newGraph=True, updateGraph=False, portfolioGraph=True, time=time, account=self.account)

    def log_out_dash(self):
        try:
            self.graphDock.close()
        except:
            pass
        self.data_updater.terminate()
        self.send_charts()
        window.log_out()
    
    def update_crosshair_text(self, x, y, xtext, ytext):
        if xtext != "":
            self.newDate = xtext
            #print(xtext)
        return "", ""

    def mouseMoved(self, evt):
        try:
            pos = evt
            mousePoint = self.newgraphDock.graph.vb.mapSceneToView(pos)
            x = mousePoint.x()
            y = mousePoint.y()
            intersectLine = shapely.geometry.LineString([[x, self.newgraphDock.maxY],[x, 0]])
            moveX = intersectLine.intersection(self.polygon).xy[1]
            moveTo = moveX[0]
            self.newgraphDock.priceLineX.setPos([x,x])
            self.newgraphDock.priceLineY.setPos([moveTo,moveTo])
            self.newgraphDock.volumeLine.setPos([x,x])
            try:
                if len(self.index_of_2100) > 1:
                    if self.index_of_2100[0] < x < self.index_of_2100[1]:
                        x = ((datetime.datetime.fromtimestamp(x)) + datetime.timedelta(hours=17,  minutes=30)).timestamp()
                    elif self.index_of_2100[1] < x < self.index_of_2100[2]:
                        x = ((datetime.datetime.fromtimestamp(x)) + datetime.timedelta(hours=34, minutes=30)).timestamp()
                    elif self.index_of_2100[2] < x:
                        x = ((datetime.datetime.fromtimestamp(x)) + datetime.timedelta(hours=51,  minutes=30)).timestamp()
            except:
                pass

            fplt.add_crosshair_info(self.update_crosshair_text, ax=self.newgraphDock.graph)
            #date = (datetime.datetime.fromtimestamp(x)).strftime("%b %d, %Y %I:%M %p")
            print(moveTo, x)
            if str(moveTo) != '1e-12':
                self.newgraphDock.priceLabel.setText(str(round(moveTo,2))+"$\n"+ self.newDate)
            else:
                self.newgraphDock.priceLabel.setText(" ")
        except (NotImplementedError, AttributeError):
            pass

    def mouseMovedOLD(self, evt):
        try:
            pos = evt
            mousePoint = self.newgraphDock.graph.vb.mapSceneToView(pos)
            x = mousePoint.x()
            y = mousePoint.y()
            intersectLine = shapely.geometry.LineString([[x, self.newgraphDock.maxY],[x, 0]])
            moveX = intersectLine.intersection(self.polygon).xy[1]
            moveTo = moveX[0]
            self.newgraphDock.priceLineX.setPos([x,x])
            self.newgraphDock.priceLineY.setPos([moveTo,moveTo])
            self.newgraphDock.volumeLine.setPos([x,x])
            try:
                if len(self.index_of_2100) > 1:
                    if self.index_of_2100[0] < x < self.index_of_2100[1]:
                        x = ((datetime.datetime.fromtimestamp(x)) + datetime.timedelta(hours=17,  minutes=30)).timestamp()
                    elif self.index_of_2100[1] < x < self.index_of_2100[2]:
                        x = ((datetime.datetime.fromtimestamp(x)) + datetime.timedelta(hours=34, minutes=30)).timestamp()
                    elif self.index_of_2100[2] < x:
                        x = ((datetime.datetime.fromtimestamp(x)) + datetime.timedelta(hours=51,  minutes=30)).timestamp()
            except:
                pass
            date = (datetime.datetime.fromtimestamp(x)).strftime("%b %d, %Y %I:%M %p")
            self.newgraphDock.priceLabel.setText(str(round(moveTo,2))+"$\n"+ date)
        except (NotImplementedError, AttributeError):
            pass
            
    def redrawStock(self, time, portfolio=False):
        self.graph_updater.run(updateGraph=True, newGraph=False, portfolioGraph=False,time=time, currentGraph= self.newgraphDock, stockGraph=True)
        self.graphDock = self.newgraphDock.graphDock
        if self.defaultGraphLocation is not None:
            if self.defaultGraphLocation == 'floating':
                window.addDockWidget(Qt.RightDockWidgetArea, self.graphDock)
                self.graphDock.setFloating(True)
            else:
                self.graphDock.setFloating(False)
                if self.defaultGraphLocation == "top":
                    window.addDockWidget(Qt.TopDockWidgetArea, self.graphDock)
                elif self.defaultGraphLocation == "bottom":
                    window.addDockWidget(Qt.BottomDockWidgetArea, self.graphDock)
                elif self.defaultGraphLocation == "right":
                    window.addDockWidget(Qt.RightDockWidgetArea, self.graphDock)
                elif self.defaultGraphLocation == "left":
                    window.addDockWidget(Qt.LeftDockWidgetArea, self.graphDock)
        else:
            window.addDockWidget(Qt.RightDockWidgetArea, self.graphDock)
        
        #self.newgraphDock.volumeGraph.enableAutoRange()
        #self.newgraphDock.graph.enableAutoRange()

        xData = self.newgraphDock.graph.__dict__['dataItems'][0].__dict__['xData']
        yData = self.newgraphDock.graph.__dict__['dataItems'][0].__dict__['yData']
        #yData = self.newgraphDock.priceData
        print(xData)
        print(yData)

        for i in range(len(yData)):
            #print(yData[i])
            if np.isnan(yData[i]):
                yData[i] = 0
                #print("WE GOT ONE")
        
        print(xData)
        print(yData)
        
        polyData = []
        i = 0
        for point in xData:
            polyData.append([point, yData[i]])
            i += 1
        polyData.append([max(xData),0])
        polyData.insert(0,[0,0])
        polygon = shapely.geometry.Polygon(polyData)
        self.polygon = polygon.buffer(0.000000000001)

        if not portfolio: 
            self.newgraphDock.previousCloseLine.setPos([self.prevClose, self.prevClose])
            #self.newgraphDock.volumeGraph.scene().sigMouseMoved.connect(lambda evt: self.mouseMoved(evt))
            self.newgraphDock.oneDayButtonStock.button.clicked.connect(lambda: self.redrawStock("1d"))
            self.newgraphDock.oneWeekButtonStock.button.clicked.connect(lambda: self.redrawStock("1w"))
            self.newgraphDock.oneMonthbuttonStock.button.clicked.connect(lambda: self.redrawStock("1m"))
            self.newgraphDock.threeMonthButtonStock.button.clicked.connect(lambda: self.redrawStock("3m"))
            self.newgraphDock.oneYearButtonStock.button.clicked.connect(lambda: self.redrawStock("1y"))
            self.newgraphDock.allButtonStock.button.clicked.connect(lambda: self.redrawStock("all"))
        else:
            self.newgraphDock.oneDayButton.button.clicked.connect(lambda: self.redrawPortfolio("1d"))
            self.newgraphDock.oneWeekButton.button.clicked.connect(lambda: self.redrawPortfolio("1w"))
            self.newgraphDock.oneMonthbutton.button.clicked.connect(lambda: self.redrawPortfolio("1m"))
            self.newgraphDock.threeMonthButton.button.clicked.connect(lambda: self.redrawPortfolio("3m"))
            self.newgraphDock.oneYearButton.button.clicked.connect(lambda: self.redrawPortfolio("1y"))
            self.newgraphDock.allButton.button.clicked.connect(lambda: self.redrawPortfolio("all"))

        self.newgraphDock.graph.scene().sigMouseMoved.connect(lambda evt: self.mouseMoved(evt))
        self.newgraphDock.graph.vb.sigRangeChanged.connect(lambda: self.graphlabelmover())
        self.graphDock.topLevelChanged.connect(lambda: self.get_graph_location(self.graphDock))
    
    def createGraphDock(self, newgraphDock, portfolio=False):
        try:
            self.graphDock.close()
            print("loading new graph")
        except AttributeError:
            pass
        self.newgraphDock = newgraphDock
        self.graphDock = self.newgraphDock.graphDock
        if self.defaultGraphLocation is not None:
            if self.defaultGraphLocation == 'floating':
                window.addDockWidget(Qt.RightDockWidgetArea, self.graphDock)
                self.graphDock.setFloating(True)
            else:
                self.graphDock.setFloating(False)
                if self.defaultGraphLocation == "top":
                    window.addDockWidget(Qt.TopDockWidgetArea, self.graphDock)
                elif self.defaultGraphLocation == "bottom":
                    window.addDockWidget(Qt.BottomDockWidgetArea, self.graphDock)
                elif self.defaultGraphLocation == "right":
                    window.addDockWidget(Qt.RightDockWidgetArea, self.graphDock)
                elif self.defaultGraphLocation == "left":
                    window.addDockWidget(Qt.LeftDockWidgetArea, self.graphDock)
        else:
            window.addDockWidget(Qt.RightDockWidgetArea, self.graphDock)
        
        #self.newgraphDock.volumeGraph.enableAutoRange()
        #self.newgraphDock.graph.enableAutoRange()

        xData = self.newgraphDock.graph.__dict__['dataItems'][0].__dict__['xData']
        yData = self.newgraphDock.graph.__dict__['dataItems'][0].__dict__['yData']
        #yData = self.newgraphDock.priceData
        print(xData)
        print(yData)

        for i in range(len(yData)):
            #print(yData[i])
            if np.isnan(yData[i]):
                yData[i] = 0
                #print("WE GOT ONE")
        
        print(xData)
        print(yData)
        
        polyData = []
        i = 0
        for point in xData:
            polyData.append([point, yData[i]])
            i += 1
        polyData.append([max(xData),0])
        polyData.insert(0,[0,0])
        polygon = shapely.geometry.Polygon(polyData)
        self.polygon = polygon.buffer(0.000000000001)

        if not portfolio: 
            self.newgraphDock.previousCloseLine.setPos([self.prevClose, self.prevClose])
            #self.newgraphDock.volumeGraph.scene().sigMouseMoved.connect(lambda evt: self.mouseMoved(evt))

            self.newgraphDock.oneDayButtonStock.button.clicked.connect(lambda: self.redrawStock("1d"))
            self.newgraphDock.oneWeekButtonStock.button.clicked.connect(lambda: self.redrawStock("1w"))
            self.newgraphDock.oneMonthbuttonStock.button.clicked.connect(lambda: self.redrawStock("1m"))
            self.newgraphDock.threeMonthButtonStock.button.clicked.connect(lambda: self.redrawStock("3m"))
            self.newgraphDock.oneYearButtonStock.button.clicked.connect(lambda: self.redrawStock("1y"))
            self.newgraphDock.allButtonStock.button.clicked.connect(lambda: self.redrawStock("all"))
        else:
            self.newgraphDock.oneDayButton.button.clicked.connect(lambda: self.redrawPortfolio("1d"))
            self.newgraphDock.oneWeekButton.button.clicked.connect(lambda: self.redrawPortfolio("1w"))
            self.newgraphDock.oneMonthbutton.button.clicked.connect(lambda: self.redrawPortfolio("1m"))
            self.newgraphDock.threeMonthButton.button.clicked.connect(lambda: self.redrawPortfolio("3m"))
            self.newgraphDock.oneYearButton.button.clicked.connect(lambda: self.redrawPortfolio("1y"))
            self.newgraphDock.allButton.button.clicked.connect(lambda: self.redrawPortfolio("all"))

        self.newgraphDock.graph.scene().sigMouseMoved.connect(lambda evt: self.mouseMoved(evt))
        self.newgraphDock.graph.vb.sigRangeChanged.connect(lambda: self.graphlabelmover())
        self.graphDock.topLevelChanged.connect(lambda: self.get_graph_location(self.graphDock))

    def graphlabelmover(self):
        vbRange = self.newgraphDock.graph.vb.viewRange()
        vbMidX = vbRange[0][0] + ((vbRange[0][1] - vbRange[0][0]) / 2)
        self.newgraphDock.priceLabel.setPos(vbMidX, vbRange[1][1])
            
    def createTFSATable(self):
        self.tfsaStockTable = QtWidgets.QTableWidget()
        self.tfsaStockTable.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tfsaStockTable.sizePolicy().hasHeightForWidth())
        self.tfsaStockTable.setSizePolicy(sizePolicy)
        self.tfsaStockTable.setMinimumSize(QtCore.QSize(0, 0))
        self.tfsaStockTable.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.tfsaStockTable.setFont(font)
        self.tfsaStockTable.setStyleSheet("gridline-color: lightgrey;\n""")
        self.tfsaStockTable.setFrameShape(QtWidgets.QFrame.VLine)
        self.tfsaStockTable.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.tfsaStockTable.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tfsaStockTable.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tfsaStockTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tfsaStockTable.setAlternatingRowColors(True)
        self.tfsaStockTable.setShowGrid(True)
        self.tfsaStockTable.setGridStyle(QtCore.Qt.SolidLine)
        self.tfsaStockTable.setWordWrap(False)
        self.tfsaStockTable.setCornerButtonEnabled(True)
        self.tfsaStockTable.setObjectName("tfsaStockTable")
        self.tfsaStockTable.setColumnCount(8)
        self.tfsaStockTable.setRowCount(9)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setVerticalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setVerticalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setVerticalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setVerticalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setVerticalHeaderItem(8, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.tfsaStockTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.tfsaStockTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.tfsaStockTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.tfsaStockTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.tfsaStockTable.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.tfsaStockTable.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.tfsaStockTable.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.tfsaStockTable.setHorizontalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.tfsaStockTable.setItem(0, 0, item)
        self.tfsaStockTable.horizontalHeader().setVisible(True)
        self.tfsaStockTable.horizontalHeader().setCascadingSectionResizes(True)
        self.tfsaStockTable.horizontalHeader().setDefaultSectionSize(200)
        self.tfsaStockTable.horizontalHeader().setMinimumSectionSize(60)
        self.tfsaStockTable.horizontalHeader().setStretchLastSection(True)
        self.tfsaStockTable.verticalHeader().setVisible(False)
        self.tfsaStockTable.verticalHeader().setCascadingSectionResizes(False)
        self.tfsaStockTable.verticalHeader().setDefaultSectionSize(60)
        self.tfsaStockTable.verticalHeader().setMinimumSectionSize(60)
        self.tfsaStockTable.verticalHeader().setStretchLastSection(True)
        item = self.tfsaStockTable.horizontalHeaderItem(0)
        item.setText("Ticker")
        item = self.tfsaStockTable.horizontalHeaderItem(1)
        item.setText("Current Price")
        item = self.tfsaStockTable.horizontalHeaderItem(2)
        item.setText("Previous Close")
        item = self.tfsaStockTable.horizontalHeaderItem(3)
        item.setText( "Price Change")
        item = self.tfsaStockTable.horizontalHeaderItem(4)
        item.setText("% Change")
        item = self.tfsaStockTable.horizontalHeaderItem(5)
        item.setText("Max Price")
        item = self.tfsaStockTable.horizontalHeaderItem(6)
        item.setText("Low Price")
        item = self.tfsaStockTable.horizontalHeaderItem(7)
        item.setText("Holdings")
    
    def createPersonalStockTable(self):
        self.personalStockTable = QtWidgets.QTableWidget()
        self.personalStockTable.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.personalStockTable.sizePolicy().hasHeightForWidth())
        self.personalStockTable.setSizePolicy(sizePolicy)
        self.personalStockTable.setMinimumSize(QtCore.QSize(0, 0))
        self.personalStockTable.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.personalStockTable.setFont(font)
        self.personalStockTable.setStyleSheet("gridline-color: lightgrey;\n""")
        self.personalStockTable.setFrameShape(QtWidgets.QFrame.VLine)
        self.personalStockTable.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.personalStockTable.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.personalStockTable.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.personalStockTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.personalStockTable.setAlternatingRowColors(True)
        self.personalStockTable.setShowGrid(True)
        self.personalStockTable.setGridStyle(QtCore.Qt.SolidLine)
        self.personalStockTable.setWordWrap(False)
        self.personalStockTable.setCornerButtonEnabled(True)
        self.personalStockTable.setObjectName("personalStockTable")
        self.personalStockTable.setColumnCount(8)
        self.personalStockTable.setRowCount(9)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setVerticalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setVerticalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setVerticalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setVerticalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setVerticalHeaderItem(8, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.personalStockTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.personalStockTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.personalStockTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.personalStockTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.personalStockTable.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.personalStockTable.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.personalStockTable.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.personalStockTable.setHorizontalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.personalStockTable.setItem(0, 0, item)
        self.personalStockTable.horizontalHeader().setVisible(True)
        self.personalStockTable.horizontalHeader().setCascadingSectionResizes(True)
        self.personalStockTable.horizontalHeader().setDefaultSectionSize(200)
        self.personalStockTable.horizontalHeader().setMinimumSectionSize(60)
        self.personalStockTable.horizontalHeader().setStretchLastSection(True)
        self.personalStockTable.verticalHeader().setVisible(False)
        self.personalStockTable.verticalHeader().setCascadingSectionResizes(False)
        self.personalStockTable.verticalHeader().setDefaultSectionSize(60)
        self.personalStockTable.verticalHeader().setMinimumSectionSize(60)
        self.personalStockTable.verticalHeader().setStretchLastSection(True) 
        item = self.personalStockTable.horizontalHeaderItem(0)
        item.setText("Ticker")
        item = self.personalStockTable.horizontalHeaderItem(1)
        item.setText("Current Price")
        item = self.personalStockTable.horizontalHeaderItem(2)
        item.setText("Previous Close")
        item = self.personalStockTable.horizontalHeaderItem(3)
        item.setText( "Price Change")
        item = self.personalStockTable.horizontalHeaderItem(4)
        item.setText("% Change")
        item = self.personalStockTable.horizontalHeaderItem(5)
        item.setText("Max Price")
        item = self.personalStockTable.horizontalHeaderItem(6)
        item.setText("Low Price")
        item = self.personalStockTable.horizontalHeaderItem(7)
        item.setText("Holdings")

    def createCryptoTable(self):
        self.cryptoTable = QtWidgets.QTableWidget()
        self.cryptoTable.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cryptoTable.sizePolicy().hasHeightForWidth())
        self.cryptoTable.setSizePolicy(sizePolicy)
        self.cryptoTable.setMinimumSize(QtCore.QSize(0, 0))
        self.cryptoTable.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.cryptoTable.setFont(font)
        self.cryptoTable.setStyleSheet("gridline-color: lightgrey;\n""")
        self.cryptoTable.setFrameShape(QtWidgets.QFrame.VLine)
        self.cryptoTable.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.cryptoTable.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.cryptoTable.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.cryptoTable.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.cryptoTable.setAlternatingRowColors(True)
        self.cryptoTable.setShowGrid(True)
        self.cryptoTable.setGridStyle(QtCore.Qt.SolidLine)
        self.cryptoTable.setWordWrap(False)
        self.cryptoTable.setCornerButtonEnabled(True)
        self.cryptoTable.setObjectName("cryptoTable")
        self.cryptoTable.setColumnCount(8)
        self.cryptoTable.setRowCount(9)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setVerticalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setVerticalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setVerticalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setVerticalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setVerticalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setVerticalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setVerticalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setVerticalHeaderItem(8, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.cryptoTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.cryptoTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.cryptoTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.cryptoTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.cryptoTable.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.cryptoTable.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.cryptoTable.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(16)
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.cryptoTable.setHorizontalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.cryptoTable.setItem(0, 0, item)
        self.cryptoTable.horizontalHeader().setVisible(True)
        self.cryptoTable.horizontalHeader().setCascadingSectionResizes(True)
        self.cryptoTable.horizontalHeader().setDefaultSectionSize(200)
        self.cryptoTable.horizontalHeader().setMinimumSectionSize(60)
        self.cryptoTable.horizontalHeader().setStretchLastSection(True)
        self.cryptoTable.verticalHeader().setVisible(False)
        self.cryptoTable.verticalHeader().setCascadingSectionResizes(False)
        self.cryptoTable.verticalHeader().setDefaultSectionSize(60)
        self.cryptoTable.verticalHeader().setMinimumSectionSize(60)

        item = self.cryptoTable.horizontalHeaderItem(0)
        item.setText("Ticker")
        item = self.cryptoTable.horizontalHeaderItem(1)
        item.setText("Current Price")
        item = self.cryptoTable.horizontalHeaderItem(2)
        item.setText("Previous Close")
        item = self.cryptoTable.horizontalHeaderItem(3)
        item.setText( "Price Change")
        item = self.cryptoTable.horizontalHeaderItem(4)
        item.setText("% Change")
        item = self.cryptoTable.horizontalHeaderItem(5)
        item.setText("Max Price")
        item = self.cryptoTable.horizontalHeaderItem(6)
        item.setText("Low Price")
        item = self.cryptoTable.horizontalHeaderItem(7)
        item.setText("Holdings")

    def get_graph_data(self, table, item):
        row = item.row()
        stock = table.item(row, 0)
        self.prevClose = table.item(row, 2).text()
        self.graph_updater.run(symbol=stock, stockGraph=True, newGraph=True)
        
    def get_graph_location(self, dock):
        print("Getting location")
        if dock.isFloating():
            new_location = 'floating'
        else:
            location = window.dockWidgetArea(dock)
            if location == 1:
                new_location='left'
            elif location == 2:
                new_location="right"
            elif location == 4:
                new_location="top"
            elif location == 8:
                new_location="bottom"
        print(new_location)
        self.defaultGraphLocation = new_location

    def reloadDashBoard(self, L):
        self.watchlistTable.setSortingEnabled(False)
        self.personalStockTable.setSortingEnabled(False)
        self.tfsaStockTable.setSortingEnabled(False)
        self.cryptoTable.setSortingEnabled(False)
        my_watchList = []
        personal_stocklist =[]
        tfsa_stocklist =[]
        crypto_stocklist =[]

        if len(L) >= 1:
            my_watchList = L[0]
            self.watchlistTable.setRowCount(len(my_watchList))
            for i in range(len(my_watchList)):
                for j in range(len(my_watchList[i])):
                    data = str(my_watchList[i][j])
                    try:
                        self.watchlistTable.item(i,j).setData(Qt.DisplayRole,data)
                    except:
                        pass

        if len(L) >= 2:
            tfsa_stocklist = L[1]
            self.personalStockTable.setRowCount(len(personal_stocklist))
            for i in range(len(tfsa_stocklist)):
                for j in range(len(tfsa_stocklist[i])):
                    data = tfsa_stocklist[i][j]
                    try:
                        self.tfsaStockTable.item(i,j).setData(Qt.DisplayRole,data)
                    except:
                        pass

        if len(L) >= 3:
            personal_stocklist = L[2]
            self.personalStockTable.setRowCount(len(personal_stocklist))
            for i in range(len(personal_stocklist)):
                for j in range(len(personal_stocklist[i])):
                    data = personal_stocklist[i][j]
                    try:
                        self.personalStockTable.item(i,j).setData(Qt.DisplayRole,data)
                    except:
                        pass

        if len(L) >= 4:
            crypto_stocklist = L[3]
            self.cryptoTable.setRowCount(len(crypto_stocklist))
            for i in range(len(crypto_stocklist)):
                for j in range(len(crypto_stocklist[i])):
                    data = crypto_stocklist[i][j]
                    try:
                        self.cryptoTable.item(i,j).setData(Qt.DisplayRole,data)
                    except:
                        pass

        self.watchlistTable.setSortingEnabled(True)
        self.personalStockTable.setSortingEnabled(True)
        self.tfsaStockTable.setSortingEnabled(True)
        self.cryptoTable.setSortingEnabled(True)


        self.table_data = {
                "watchList": my_watchList ,
                "personalList": personal_stocklist,
                "tfsaList": tfsa_stocklist,
                "cyrptoList": crypto_stocklist
            }

    def loadDashBoard(self):
        tfsa_stocklist = []
        my_watchList = []
        personal_stocklist = []
        crypto_stocklist = []
        self.tfsaStockTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.watchlistTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.personalStockTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cryptoTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        stockTables = [self.watchlistTable, self.tfsaStockTable, self.personalStockTable, self.cryptoTable]
        cleanEmail = (window.widgetList[0].username).replace('.', "")
        try:
            cleanEmail = (window.widgetList[0].username).replace('.', "")
            try:
                watchlistFB = (fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("WatchList").get()).val()
            except:
                watchlistFB = []
            try:
                tfsalistFB = (fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("TFSAList").get()).val()
            except:
                tfsalistFB = []
            try: 
                personallistFB = (fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("PersonalList").get()).val()
            except:
                personallistFB =[]
            try:
                cryptoFB = (fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("CryptoList").get()).val()
            except:
                cryptoFB = []
            myStockLists = [watchlistFB, tfsalistFB, personallistFB, cryptoFB]
            if myStockLists == [None,None,None,None]:
                raise ValueError

            k = 0
            for table in stockTables:
                currentStockList = myStockLists[k]
                k += 1
                if currentStockList is None:
                    continue
                table.setRowCount(len(currentStockList))
                for i in range(len(currentStockList)):
                    for j in range(len(currentStockList[i])):
                        data = currentStockList[i][j]
                        x = QTableWidgetItem()
                        x.setData(Qt.EditRole, data)
                        table.setItem(i,j,x)
                
                

            print("Loaded from Firebase")
        except:
            account_list = self.user.get_accounts()

            my_watchList = self.user.get_watch_list()
            self.watchlistTable.setRowCount(len(my_watchList))
            for i in range(len(my_watchList)):
                for j in range(len(my_watchList[i])):
                    data = my_watchList[i][j]
                    x = QTableWidgetItem()
                    x.setData(Qt.EditRole, data)
                    self.watchlistTable.setItem(i,j,x)

            if len(account_list) >= 1:
                tfsa_stocklist = self.user.get_my_stock_list(account_list[0])
                self.tfsaStockTable.setRowCount(len(tfsa_stocklist))
                for i in range(len(tfsa_stocklist)):
                    for j in range(len(tfsa_stocklist[i])):
                        data = tfsa_stocklist[i][j]
                        x = QTableWidgetItem()
                        x.setData(Qt.EditRole, data)
                        self.tfsaStockTable.setItem(i,j,x)

            if len(account_list) >= 2:
                personal_stocklist = self.user.get_my_stock_list(account_list[1])
                self.personalStockTable.setRowCount(len(personal_stocklist))
                for i in range(len(personal_stocklist)):
                    for j in range(len(personal_stocklist[i])):
                        data = personal_stocklist[i][j]
                        x = QTableWidgetItem()
                        x.setData(Qt.EditRole, data)
                        self.personalStockTable.setItem(i,j,x)

            if len(account_list) >= 3:
                crypto_stocklist = self.user.get_my_stock_list(account_list[2])
                self.cryptoTable.setRowCount(len(crypto_stocklist))
                for i in range(len(crypto_stocklist)):
                    for j in range(len(crypto_stocklist[i])):
                        data = crypto_stocklist[i][j]
                        x = QTableWidgetItem()
                        x.setData(Qt.EditRole, data)
                        self.cryptoTable.setItem(i,j,x)
            
            self.table_data = {
                "watchList": my_watchList ,
                "personalList": personal_stocklist,
                "tfsaList": tfsa_stocklist,
                "cyrptoList": crypto_stocklist
            }
            cleanEmail = (window.widgetList[0].username).replace('.', "")
            fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("WatchList").set(self.table_data["watchList"])
            fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("PersonalList").set(self.table_data["personalList"])
            fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("TFSAList").set(self.table_data["tfsaList"])
            fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("CryptoList").set(self.table_data["cyrptoList"])

        self.mystockTable.hide()
        self.accountTabs.removeTab(0)
        self.accountTabs.removeTab(0)
        self.accountTabs.setCurrentIndex(0)
        self.watchlistTable.setSortingEnabled(True)
        self.personalStockTable.setSortingEnabled(True)
        self.tfsaStockTable.setSortingEnabled(True)
        self.cryptoTable.setSortingEnabled(True)

        Tabs = ['TFSA', 'Personal', 'Crypto']
        i = 0
        for chart in stockTables[1:]:
                new_tab = QTabWidget()
                self.accountTabs.addTab(chart, Tabs[i])
                i += 1
    
    def listMinimizer(self, l, buttonpressed):
        mH = QByteArray(b'maximumHeight')
        self.startingHeight = window.height()
        sH = l.height()

        self.animation = QPropertyAnimation(targetObject= l, propertyName= mH)
        self.animation.setDuration(250)
        self.animation.setStartValue(sH)
        if sH == 0:
            self.animation.setEndValue(self.startingHeight)
        else:
            self.animation.setEndValue(0)
        self.animation.start()
    
    def send_charts(self):
        try:
            print("sending charts to firebase")
            cleanEmail = (window.widgetList[0].username).replace('.', "")
            fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("WatchList").set(self.table_data["watchList"])
            fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("PersonalList").set(self.table_data["personalList"])
            fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("TFSAList").set(self.table_data["tfsaList"])
            fb.db.child("Users").child("WealthSimple").child(cleanEmail).child("StockTables").child("CryptoList").set(self.table_data["cyrptoList"])
        except:
            pass

class StockView(QDialog):
    def __init__(self, User, StockInfo):
        super(StockView, self).__init__()
        loadUi("./ui-files/tradewindow.ui",self)
        self.user = User
        self.stock_info = StockInfo
        
class UpdateDataThread(QThread):
    send_lists = pyqtSignal(list)
    token_expired = pyqtSignal(bool)
    def __init__(self, User):
        super(UpdateDataThread, self).__init__()
        self.user = User

    def run(self):
        self.data_updater()
        mustend = time.time() + 10
        while time.time() < mustend:
            time.sleep(5)
            print("10 seconds is up")
            self.data_updater()
            self.run()

    def data_updater(self):
        try:
            account_list =self.user.get_accounts()
            dataList=[]
            try:
                my_watchList = self.user.get_watch_list()
                dataList.append(my_watchList)
                if len(account_list) >= 1:
                    my_tfsa_stocklist = self.user.get_my_stock_list(account_list[0])
                    dataList.append(my_tfsa_stocklist)
                if len(account_list) >= 2:
                    my_personal_stocklist = self.user.get_my_stock_list(account_list[1])
                    dataList.append(my_personal_stocklist)
                if len(account_list) >= 3:
                    my_crypto_list = self.user.get_my_stock_list(account_list[2])
                    dataList.append(my_crypto_list)
                self.send_lists.emit(dataList)
            except HTTPError:
                return
        except WSerrors.InvalidAccessTokenError:
            self.token_expired.emit(True)

class UpdateGraphThread(QThread):
    send_data = pyqtSignal(WealthSimpleGraphs)
    send_data_portfolio = pyqtSignal(WealthSimpleGraphs)
    def __init__(self, User):
        super(UpdateGraphThread, self).__init__()
        self.user = User
    
    def run(self, symbol=None, newGraph=False, updateGraph=False,currentGraph=None ,stockGraph=False, portfolioGraph=False, time=None, account=None):
        if newGraph:
            self.get_data(symbol=symbol, stockGraph=stockGraph, portfolioGraph=portfolioGraph, time=time, account=account)
        elif updateGraph and currentGraph is not None:
            self.get_data_update(symbol=symbol, stockGraph=stockGraph, portfolioGraph=portfolioGraph, time=time, account=account, currentGraph=currentGraph)

    def get_data_update(self, currentGraph: WealthSimpleGraphs, symbol=None, stockGraph=False, portfolioGraph=False, time=None, account=None, ):
        print("Getting Update data")
        if stockGraph:
            symbol = currentGraph.name
            if time == "1d":
                history = self.user.get_stock_chart(symbol,'1d','1m')
            elif time == "1w":
                history = self.user.get_stock_chart(symbol,'7d','1m')
            elif time == "1m":
                history = self.user.get_stock_chart(symbol,'1mo','5m')
            elif time == "3m":
                history = self.user.get_stock_chart(symbol,'3mo','1h')
            elif time == "1y":
                history = self.user.get_stock_chart(symbol,'1y','1h')
            elif time == "all":
                history = self.user.get_stock_chart(symbol,'max','1d')
            dates = history[0]
            prices = history[1]
            volume = history[2]
            dataFrame = history[3]
            currentGraph.updateStockGraph(dates, prices, volume, dataFrame, currentGraph.name)
        elif portfolioGraph:
            history = self.user.get_portfolio_chart(time, account)
            dates = [i[0].timestamp() for i in history ]
            prices = [i[1] for i in history]
            currentGraph.updatePortfolioGraph(dates, prices, time)
            
    def get_data(self, symbol=None, stockGraph=False, portfolioGraph=False, time=None, account=None):
        print("Getting data")
        if stockGraph:
            history = self.user.get_stock_chart(symbol.text(),'1d','1m')
            dates = history[0]
            prices = history[1]
            volume = history[2]
            dataFrame = history[3]
            self.createGraphDock(dates, prices, volume, symbol.text(),dataFrame)
        elif portfolioGraph:
            history = self.user.get_portfolio_chart(time, account)
            self.createPortfolioDock(history, account)

    def createPortfolioDock(self, portfolio, name):
        dates = [i[0].timestamp() for i in portfolio ]
        prices = [i[1] for i in portfolio]
        newPortfolioDock = WealthSimpleGraphs(dates=dates, prices=prices, portfoliograph=True, name=name)
        self.send_data_portfolio.emit(newPortfolioDock)
    def createGraphDock(self, dates, prices, volume, name, dataFrame):
        newStockDock = WealthSimpleGraphs(dates=dates, prices=prices, volume=volume, name=name, stockgraph=True, dataFrame=dataFrame)
        self.send_data.emit(newStockDock)

if __name__ == "__main__":
    import sys
    #QApplication.setAttribute(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    pg.setConfigOption('background', 'w')
    app = QtWidgets.QApplication(sys.argv)
    mainwindow = LoginPage()
    mainwindow.hideOnStart()
    widgetList = [mainwindow]
    window = StartingPage(widgetList)
    window.show()
    sys.exit(app.exec_())