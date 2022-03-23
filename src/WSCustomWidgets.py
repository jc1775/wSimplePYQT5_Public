from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QDockWidget, QListWidget, QMainWindow, QWidget, QGraphicsView, QLabel, QGraphicsTextItem, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QSize, QByteArray
from PyQt5.QtGui import QPixmap, QFont, QColor
import numpy as np
import pyqtgraph as pg
from pyqtgraph.graphicsItems import DateAxisItem
import datetime
import pytz
import itertools
import finplot as fplt
import pandas as pd


class GraphButtons():
    
    def __init__(self, text):
        buttonStyleSheet = "border-radius: 50px; border: 2px solid grey; font-size: 20px; background-color: #90A5A9"
        self.text = text
        self.button = QPushButton(text)
        self.button.setFixedSize(100, 100)
        self.button.setStyleSheet(buttonStyleSheet)

class WealthSimpleGraphs():
    def __init__(self, dates=None, prices=None, volume=None, name=None, stockgraph=False, portfoliograph=False, dataFrame=None):
        if stockgraph:
            self.stockgraphCreate(dates, prices, volume, name, dataFrame)
        elif portfoliograph:
            self.portfoliographCreate(dates,prices, name)
    
    def updateStockGraph(self, dates, prices, volume, dataFrame, name):
        self.verticalGraphLayout.removeWidget(self.graph.vb.win)
        self.verticalGraphLayout.removeWidget(self.buttonWidget)

        ##Data
        self.dates = dates
        self.prices = prices
        self.name = name
        x = [i.to_pydatetime().timestamp() for i in dates ]
        y = prices
        self.minX = min(x)
        self.maxX = max(x)
        self.minY = min(y)
        self.maxY = max(y)
        ##Styling
        graphFont = QFont()
        graphFont.setWeight(63)
        graphFont.setPointSize(16)
        graphfontColor = QColor(105,105,105)
        grad = QtGui.QLinearGradient(0, self.minY, 0, self.maxY)
        grad.setColorAt(0, pg.mkColor('#FFFFFF'))
        grad.setColorAt(1, pg.mkColor('54575A'))
        brush = QtGui.QBrush(grad)

        ##Graph
        self.graph = fplt.create_plot(init_zoom_periods=100)
        axo =self.graph.overlay()
        df = dataFrame

        g_dates = [datetime.datetime.fromtimestamp(z).strftime("%Y-%m-%d %H:%M:%S") for z in x]
        plot_frame = pd.DataFrame(g_dates, columns=["Dates"])
        plot_frame['Close'] = df['Close'].tolist()
 
        plot_frame = plot_frame.astype({'Dates':'datetime64[ns]'})
        price = df['Open Close High Low'.split()]
        volume = df['Open Close Volume'.split()]
        self.graph.set_visible(crosshair=False)
        #fplt.candlestick_ochl(price)
        dataTypeSeries = plot_frame.dtypes
        self.plot_frame = plot_frame
        fplt.volume_ocv(volume, ax=axo)
        fplt.plot(plot_frame['Dates'], plot_frame['Close'].rolling(25).mean(), ax=self.graph)
        self.priceData = plot_frame['Close'].tolist()
        self.graph.vb.setLimits(xMin=25, xMax=len(plot_frame) - 1, yMin=self.minY, yMax=self.maxY + ((self.maxY- self.minY) / 4))



        #Crosshairs
        crossHairColor = pg.mkColor(192,192,192)
        crossHairPen = pg.mkPen(crossHairColor, width=4)
        self.priceLineX = pg.InfiniteLine(movable=False, angle=90, pen=crossHairPen)
        self.priceLineY = pg.InfiniteLine(movable=False, angle=0, pen=crossHairPen)
        closeHairColor = pg.mkColor(119,136,153)
        closeHairPen = pg.mkPen(closeHairColor, width=4)
        self.previousCloseLine = pg.InfiniteLine(movable=False, angle=0, label="Previous Close", pen=closeHairPen,
                                            labelOpts={'position':0.3, 'movable': False, 'color': (105,105,105)})
        self.volumeLine = pg.InfiniteLine(movable=False, angle=90, pen=crossHairPen)

        ##HLayout
        self.horizontalButtonLayout = QtWidgets.QHBoxLayout()
        self.horizontalButtonLayout.setSpacing(50)

        ##HLayoutButtons
        self.oneDayButtonStock = GraphButtons("1D")
        self.oneWeekButtonStock = GraphButtons("1W")
        self.oneMonthbuttonStock = GraphButtons("1M")
        self.threeMonthButtonStock = GraphButtons("3M")
        self.oneYearButtonStock = GraphButtons("1Y")
        self.allButtonStock = GraphButtons("ALL")

        ##HSpacers
        horizontalSpacerLeft = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        horizontalSpacerRight = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)

        ##FrameWidgets
        self.buttonWidget = QWidget()
        self.buttonWidget.setMaximumHeight(120)


        ##Label
        self.priceLabel = pg.TextItem(anchor=(0.5,0))
        date = (datetime.datetime.fromtimestamp(x[-1])).strftime("%b %d, %Y %I:%M %p")
        self.priceLabel.setText("HELLLLOOOWORLD\nGOOODBYEWORLLLD")
        self.priceLabel.setText(str(round(y[-1],2))+"$\n"+ date)
        self.priceLabel.setFont(graphFont)
        self.priceLabel.setColor(graphfontColor)
        it = self.priceLabel.textItem
        option = it.document().defaultTextOption()
        option.setAlignment(QtCore.Qt.AlignCenter)
        it.document().setDefaultTextOption(option)
        it.setTextWidth(it.boundingRect().width() * 1.25)
        vbRange = self.graph.vb.viewRange()
        vbMidX = vbRange[0][0] + ((vbRange[0][1] - vbRange[0][0]) / 2)
        self.priceLabel.setPos(vbMidX, self.maxY + ((self.maxY - self.minY) / 4))

        #Building
        self.graph.addItem(self.priceLineX)
        self.graph.addItem(self.priceLineY)
        self.graph.addItem(self.previousCloseLine)
        self.graph.vb.addItem(self.priceLabel)

        self.horizontalButtonLayout.addSpacerItem(horizontalSpacerLeft)
        self.horizontalButtonLayout.addWidget(self.oneDayButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.oneWeekButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.oneMonthbuttonStock.button)
        self.horizontalButtonLayout.addWidget(self.threeMonthButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.oneYearButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.allButtonStock.button)
        self.horizontalButtonLayout.addSpacerItem(horizontalSpacerRight)
        self.buttonWidget.setLayout(self.horizontalButtonLayout)

        
        self.verticalGraphLayout.addWidget(self.graph.vb.win)
        self.verticalGraphLayout.addWidget(self.buttonWidget)
    def updateStockGraphOLD(self,dates, prices, volume):
        ##Data
        self.dates = dates
        self.prices = prices
        x = [i.to_pydatetime().timestamp() for i in dates ]
        y = prices
        self.minX = min(x)
        self.maxX = max(x)
        self.minY = min(y)
        self.maxY = max(y)

        ##Styling
        graphFont = QFont()
        graphFont.setWeight(63)
        graphFont.setPointSize(16)
        graphfontColor = QColor(105,105,105)
        grad = QtGui.QLinearGradient(0, self.minY, 0, self.maxY)
        grad.setColorAt(0, pg.mkColor('#FFFFFF'))
        grad.setColorAt(1, pg.mkColor('54575A'))
        brush = QtGui.QBrush(grad)

        ##Rebuild
        self.graph.plot(x, y, pen=pg.mkPen(0.5, width=3), fillLevel=0, brush=brush, clear=True)
        self.graph.plotItem.vb.setLimits(xMin=self.minX, xMax=self.maxX, yMin=self.minY, yMax=self.maxY + ((self.maxY- self.minY) / 4))
        self.graph.enableAutoRange()
        vbRange = self.graph.plotItem.vb.viewRange()
        vbMidX = vbRange[0][0] + ((vbRange[0][1] - vbRange[0][0]) / 2)
        self.priceLabel.setPos(vbMidX, self.maxY + ((self.maxY - self.minY) / 4))
        self.graph.addItem(self.priceLineX)
        self.graph.addItem(self.priceLineY)

        volumeCurve = pg.PlotCurveItem()
        volumeCurve.setData(x,[(v * 0.001) for v in volume], pen=pg.mkPen(0.5, width=3))
        self.volumeGraph.addItem(volumeCurve)
        self.volumeGraph.plotItem.vb.setLimits(xMin=self.minX, xMax=self.maxX, yMin=min(volume), yMax=max(volume))
    
    def updatePortfolioGraph(self, dates, prices, time):
    
        ##Data
        self.dates = dates
        self.prices = prices
        x = dates
        y = prices
        self.minX = min(x)
        self.maxX = max(x)
        self.minY = min(y)
        self.maxY = max(y)

        ##Styling
        graphFont = QFont()
        graphFont.setWeight(63)
        graphFont.setPointSize(16)
        graphfontColor = QColor(105,105,105)
        grad = QtGui.QLinearGradient(0, self.minY, 0, self.maxY)
        grad.setColorAt(0, pg.mkColor('#FFFFFF'))
        grad.setColorAt(1, pg.mkColor('54575A'))
        brush = QtGui.QBrush(grad)
        

        #Rebuild
        self.volumeLine.hide()
        self.graph.getPlotItem().hideAxis('bottom')
        self.graph.plot(x, y, pen=pg.mkPen(0.5, width=3), fillLevel=0, brush=brush, clear=True)
        self.graph.plotItem.vb.setLimits(xMin=self.minX, xMax=self.maxX, yMin=self.minY, yMax=self.maxY + ((self.maxY- self.minY) / 4))
        self.graph.enableAutoRange()
        vbRange = self.graph.plotItem.vb.viewRange()
        vbMidX = vbRange[0][0] + ((vbRange[0][1] - vbRange[0][0]) / 2)
        self.priceLabel.setPos(vbMidX, self.maxY + ((self.maxY - self.minY) / 4))
        self.graph.addItem(self.priceLineX)
        self.graph.addItem(self.priceLineY)

    def portfoliographCreate(self, dates, prices, name):
        ##Data
        self.dates = dates
        self.prices = prices
        self.name = name
        x = dates
        y = prices
        self.minX = min(x)
        self.maxX = max(x)
        self.minY = min(y)
        self.maxY = max(y)

        ##Styling
        graphFont = QFont()
        graphFont.setWeight(63)
        graphFont.setPointSize(16)
        graphfontColor = QColor(105,105,105)
        grad = QtGui.QLinearGradient(0, self.minY, 0, self.maxY)
        grad.setColorAt(0, pg.mkColor('#FFFFFF'))
        grad.setColorAt(1, pg.mkColor('54575A'))
        brush = QtGui.QBrush(grad)

        ##Main Graph
        self.graph = pg.PlotWidget()
        self.graph.setMinimumHeight(300)
        self.graph.setMouseEnabled(True,False)
        self.graph.setLabels(title=name)
        self.date_axis = DateAxisItem.DateAxisItem(orientation='bottom') 
        self.graph.getAxis('left').setWidth(100) 
        self.graph.setAxisItems({'bottom': self.date_axis})
        self.graph.plot(x, y, pen=pg.mkPen(0.5, width=3), fillLevel=0, brush=brush)
        self.graph.plotItem.vb.setLimits(xMin=self.minX, xMax=self.maxX, yMin=self.minY, yMax=self.maxY + ((self.maxY- self.minY) / 4))
        self.graph.enableAutoRange()
        self.graph.getPlotItem().hideAxis('bottom')
        
        ##Volume Graph
        self.volumeGraph = pg.PlotWidget()
        self.volumeGraph.getPlotItem().hideAxis('bottom')
        self.volumeGraph.hide()

        ##Label
        self.priceLabel = pg.TextItem(anchor=(0.5,0))
        date = (datetime.datetime.fromtimestamp(x[-1])).strftime("%b %d, %Y %I:%M %p")
        self.priceLabel.setText("HELLLLOOOWORLD\nGOOODBYEWORLLLD")
        self.priceLabel.setText(str(round(y[-1],2))+"$\n"+ date)
        self.priceLabel.setFont(graphFont)
        self.priceLabel.setColor(graphfontColor)
        it = self.priceLabel.textItem
        option = it.document().defaultTextOption()
        option.setAlignment(QtCore.Qt.AlignCenter)
        it.document().setDefaultTextOption(option)
        it.setTextWidth(it.boundingRect().width() * 1.25)
        vbRange = self.graph.plotItem.vb.viewRange()
        vbMidX = vbRange[0][0] + ((vbRange[0][1] - vbRange[0][0]) / 2)
        self.priceLabel.setPos(vbMidX, self.maxY + ((self.maxY - self.minY) / 4))

        #Crosshairs
        crossHairColor = pg.mkColor(192,192,192)
        crossHairPen = pg.mkPen(crossHairColor, width=4)
        self.priceLineX = pg.InfiniteLine(movable=False, angle=90, pen=crossHairPen)
        self.priceLineY = pg.InfiniteLine(movable=False, angle=0, pen=crossHairPen)
        closeHairColor = pg.mkColor(119,136,153)
        closeHairPen = pg.mkPen(closeHairColor, width=4)
        self.previousCloseLine = pg.InfiniteLine(movable=False, angle=0, label="Previous Close", pen=closeHairPen,
                                            labelOpts={'position':0.3, 'movable': False, 'color': (105,105,105)})
        self.volumeLine = pg.InfiniteLine(movable=False, angle=90, pen=crossHairPen)

        ##VLayout
        self.verticalGraphLayout = QtWidgets.QVBoxLayout()
        self.verticalGraphLayout.setSpacing(0)

        ##HLayout
        self.horizontalButtonLayout = QtWidgets.QHBoxLayout()
        self.horizontalButtonLayout.setSpacing(50)

        ##HLayoutButtons
        self.oneDayButton = GraphButtons("1D")
        self.oneWeekButton = GraphButtons("1W")
        self.oneMonthbutton = GraphButtons("1M")
        self.threeMonthButton = GraphButtons("3M")
        self.oneYearButton = GraphButtons("1Y")
        self.allButton = GraphButtons("ALL")

        ##HSpacers
        horizontalSpacerLeft = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        horizontalSpacerRight = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)

        ##FrameWidgets
        self.multiWidget = QWidget()
        self.buttonWidget = QWidget()
        self.buttonWidget.setMaximumHeight(120)

        ##Dock
        self.graphDock = QDockWidget()
        self.graphDock.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)

        #Building
        self.graph.addItem(self.priceLineX)
        self.graph.addItem(self.priceLineY)
        self.graph.plotItem.vb.addItem(self.priceLabel)

        self.horizontalButtonLayout.addSpacerItem(horizontalSpacerLeft)
        self.horizontalButtonLayout.addWidget(self.oneDayButton.button)
        self.horizontalButtonLayout.addWidget(self.oneWeekButton.button)
        self.horizontalButtonLayout.addWidget(self.oneMonthbutton.button)
        self.horizontalButtonLayout.addWidget(self.threeMonthButton.button)
        self.horizontalButtonLayout.addWidget(self.oneYearButton.button)
        self.horizontalButtonLayout.addWidget(self.allButton.button)
        self.horizontalButtonLayout.addSpacerItem(horizontalSpacerRight)
        self.buttonWidget.setLayout(self.horizontalButtonLayout)
        
        self.verticalGraphLayout.addWidget(self.graph)
        self.verticalGraphLayout.addWidget(self.volumeGraph)
        self.verticalGraphLayout.addWidget(self.buttonWidget)

        self.multiWidget.setLayout(self.verticalGraphLayout)
        self.graphDock.setWidget(self.multiWidget)

    def stockgraphCreate(self, dates, prices, volume, name, dataFrame):
        ##Data
        self.dates = dates
        self.prices = prices
        self.name = name
        x = [i.to_pydatetime().timestamp() for i in dates ]
        y = prices
        self.minX = min(x)
        self.maxX = max(x)
        self.minY = min(y)
        self.maxY = max(y)
        ##Styling
        graphFont = QFont()
        graphFont.setWeight(63)
        graphFont.setPointSize(16)
        graphfontColor = QColor(105,105,105)
        grad = QtGui.QLinearGradient(0, self.minY, 0, self.maxY)
        grad.setColorAt(0, pg.mkColor('#FFFFFF'))
        grad.setColorAt(1, pg.mkColor('54575A'))
        brush = QtGui.QBrush(grad)

        ##Graph
        self.graph = fplt.create_plot(init_zoom_periods=100)
        axo =self.graph.overlay()
        df = dataFrame

        g_dates = [datetime.datetime.fromtimestamp(z).strftime("%Y-%m-%d %H:%M:%S") for z in x]
        plot_frame = pd.DataFrame(g_dates, columns=["Dates"])
        plot_frame['Close'] = df['Close'].tolist()
 
        plot_frame = plot_frame.astype({'Dates':'datetime64[ns]'})
        price = df['Open Close High Low'.split()]
        volume = df['Open Close Volume'.split()]
        self.graph.set_visible(crosshair=False)
        #fplt.candlestick_ochl(price)
        dataTypeSeries = plot_frame.dtypes
        self.plot_frame = plot_frame
        fplt.volume_ocv(volume, ax=axo)
        fplt.plot(plot_frame['Dates'], plot_frame['Close'].rolling(25).mean(), ax=self.graph)
        self.priceData = plot_frame['Close'].tolist()
        self.graph.vb.setLimits(xMin=25, xMax=len(plot_frame) - 1, yMin=self.minY, yMax=self.maxY + ((self.maxY- self.minY) / 4))



        #Crosshairs
        crossHairColor = pg.mkColor(192,192,192)
        crossHairPen = pg.mkPen(crossHairColor, width=4)
        self.priceLineX = pg.InfiniteLine(movable=False, angle=90, pen=crossHairPen)
        self.priceLineY = pg.InfiniteLine(movable=False, angle=0, pen=crossHairPen)
        closeHairColor = pg.mkColor(119,136,153)
        closeHairPen = pg.mkPen(closeHairColor, width=4)
        self.previousCloseLine = pg.InfiniteLine(movable=False, angle=0, label="Previous Close", pen=closeHairPen,
                                            labelOpts={'position':0.3, 'movable': False, 'color': (105,105,105)})
        self.volumeLine = pg.InfiniteLine(movable=False, angle=90, pen=crossHairPen)

        ##VLayout
        self.verticalGraphLayout = QtWidgets.QVBoxLayout()
        self.verticalGraphLayout.setSpacing(0)

        ##HLayout
        self.horizontalButtonLayout = QtWidgets.QHBoxLayout()
        self.horizontalButtonLayout.setSpacing(50)

        ##HLayoutButtons
        self.oneDayButtonStock = GraphButtons("1D")
        self.oneWeekButtonStock = GraphButtons("1W")
        self.oneMonthbuttonStock = GraphButtons("1M")
        self.threeMonthButtonStock = GraphButtons("3M")
        self.oneYearButtonStock = GraphButtons("1Y")
        self.allButtonStock = GraphButtons("ALL")

        ##HSpacers
        horizontalSpacerLeft = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        horizontalSpacerRight = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)

        ##FrameWidgets
        self.multiWidget = QWidget()
        self.buttonWidget = QWidget()
        self.buttonWidget.setMaximumHeight(120)

        ##Dock
        self.graphDock = QDockWidget()
        self.graphDock.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)

        ##Label
        self.priceLabel = pg.TextItem(anchor=(0.5,0))
        date = (datetime.datetime.fromtimestamp(x[-1])).strftime("%b %d, %Y %I:%M %p")
        self.priceLabel.setText("HELLLLOOOWORLD\nGOOODBYEWORLLLD")
        self.priceLabel.setText(str(round(y[-1],2))+"$\n"+ date)
        self.priceLabel.setFont(graphFont)
        self.priceLabel.setColor(graphfontColor)
        it = self.priceLabel.textItem
        option = it.document().defaultTextOption()
        option.setAlignment(QtCore.Qt.AlignCenter)
        it.document().setDefaultTextOption(option)
        it.setTextWidth(it.boundingRect().width() * 1.25)
        vbRange = self.graph.vb.viewRange()
        vbMidX = vbRange[0][0] + ((vbRange[0][1] - vbRange[0][0]) / 2)
        self.priceLabel.setPos(vbMidX, self.maxY + ((self.maxY - self.minY) / 4))

        #Building
        self.graph.addItem(self.priceLineX)
        self.graph.addItem(self.priceLineY)
        self.graph.addItem(self.previousCloseLine)
        self.graph.vb.addItem(self.priceLabel)

        self.horizontalButtonLayout.addSpacerItem(horizontalSpacerLeft)
        self.horizontalButtonLayout.addWidget(self.oneDayButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.oneWeekButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.oneMonthbuttonStock.button)
        self.horizontalButtonLayout.addWidget(self.threeMonthButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.oneYearButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.allButtonStock.button)
        self.horizontalButtonLayout.addSpacerItem(horizontalSpacerRight)
        self.buttonWidget.setLayout(self.horizontalButtonLayout)

        
        self.verticalGraphLayout.addWidget(self.graph.vb.win)
        self.verticalGraphLayout.addWidget(self.buttonWidget)

        self.multiWidget.setLayout(self.verticalGraphLayout)
        self.graphDock.setWidget(self.multiWidget)

    def stockgraphCreateOLD(self, dates, prices, volume, name):
        ##Data
        self.dates = dates
        self.prices = prices
        self.name = name
        x = [i.to_pydatetime().timestamp() for i in dates ]
        y = prices
        self.minX = min(x)
        self.maxX = max(x)
        self.minY = min(y)
        self.maxY = max(y)

        ##Styling
        graphFont = QFont()
        graphFont.setWeight(63)
        graphFont.setPointSize(16)
        graphfontColor = QColor(105,105,105)
        grad = QtGui.QLinearGradient(0, self.minY, 0, self.maxY)
        grad.setColorAt(0, pg.mkColor('#FFFFFF'))
        grad.setColorAt(1, pg.mkColor('54575A'))
        brush = QtGui.QBrush(grad)

        ##Main Graph
        self.graph = pg.PlotWidget()
        self.graph.setMinimumHeight(300)
        self.graph.setMouseEnabled(True,False)
        self.graph.setLabels(title=name)
        self.date_axis = DateAxisItem.DateAxisItem(orientation='bottom') 
        self.graph.getAxis('left').setWidth(100) 
        self.graph.setAxisItems({'bottom': self.date_axis})
        self.graph.plot(x, y, pen=pg.mkPen(0.5, width=3), fillLevel=0, brush=brush)
        self.graph.plotItem.vb.setLimits(xMin=self.minX, xMax=self.maxX, yMin=self.minY, yMax=self.maxY + ((self.maxY- self.minY) / 4))
        self.graph.enableAutoRange()
        
        ##Volume Graph
        self.volumeGraph = pg.PlotWidget()
        self.volumeGraph.setMaximumHeight(200)
        self.volumeGraph.setMouseEnabled(False,False)
        self.date_axis = DateAxisItem.DateAxisItem(orientation='bottom')
        self.volumeGraph.getAxis('left').setWidth(100) 
        self.volumeGraph.setAxisItems({'bottom': self.date_axis})
        volumeCurve = pg.PlotCurveItem()
        volumeCurve.setData(x,[(v * 0.001) for v in volume], pen=pg.mkPen(0.5, width=3))
        self.volumeGraph.addItem(volumeCurve)
        self.volumeGraph.getPlotItem().hideAxis('bottom')
        self.volumeGraph.plotItem.vb.setLimits(xMin=self.minX, xMax=self.maxX, yMin=min(volume), yMax=max(volume))
        self.volumeGraph.showGrid(True, True)

        ##Label
        self.priceLabel = pg.TextItem(anchor=(0.5,0))
        date = (datetime.datetime.fromtimestamp(x[-1])).strftime("%b %d, %Y %I:%M %p")
        self.priceLabel.setText("HELLLLOOOWORLD\nGOOODBYEWORLLLD")
        self.priceLabel.setText(str(round(y[-1],2))+"$\n"+ date)
        self.priceLabel.setFont(graphFont)
        self.priceLabel.setColor(graphfontColor)
        it = self.priceLabel.textItem
        option = it.document().defaultTextOption()
        option.setAlignment(QtCore.Qt.AlignCenter)
        it.document().setDefaultTextOption(option)
        it.setTextWidth(it.boundingRect().width() * 1.25)
        vbRange = self.graph.plotItem.vb.viewRange()
        vbMidX = vbRange[0][0] + ((vbRange[0][1] - vbRange[0][0]) / 2)
        self.priceLabel.setPos(vbMidX, self.maxY + ((self.maxY - self.minY) / 4))

        #Crosshairs
        crossHairColor = pg.mkColor(192,192,192)
        crossHairPen = pg.mkPen(crossHairColor, width=4)
        self.priceLineX = pg.InfiniteLine(movable=False, angle=90, pen=crossHairPen)
        self.priceLineY = pg.InfiniteLine(movable=False, angle=0, pen=crossHairPen)
        closeHairColor = pg.mkColor(119,136,153)
        closeHairPen = pg.mkPen(closeHairColor, width=4)
        self.previousCloseLine = pg.InfiniteLine(movable=False, angle=0, label="Previous Close", pen=closeHairPen,
                                            labelOpts={'position':0.3, 'movable': False, 'color': (105,105,105)})
        self.volumeLine = pg.InfiniteLine(movable=False, angle=90, pen=crossHairPen)

        ##VLayout
        self.verticalGraphLayout = QtWidgets.QVBoxLayout()
        self.verticalGraphLayout.setSpacing(0)

        ##HLayout
        self.horizontalButtonLayout = QtWidgets.QHBoxLayout()
        self.horizontalButtonLayout.setSpacing(50)

        ##HLayoutButtons
        self.oneDayButtonStock = GraphButtons("1D")
        self.oneWeekButtonStock = GraphButtons("1W")
        self.oneMonthbuttonStock = GraphButtons("1M")
        self.threeMonthButtonStock = GraphButtons("3M")
        self.oneYearButtonStock = GraphButtons("1Y")
        self.allButtonStock = GraphButtons("ALL")

        ##HSpacers
        horizontalSpacerLeft = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        horizontalSpacerRight = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)

        ##FrameWidgets
        self.multiWidget = QWidget()
        self.buttonWidget = QWidget()
        self.buttonWidget.setMaximumHeight(120)

        ##Dock
        self.graphDock = QDockWidget()
        self.graphDock.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)

        #Building
        self.graph.addItem(self.priceLineX)
        self.graph.addItem(self.priceLineY)
        self.graph.addItem(self.previousCloseLine)
        self.graph.plotItem.vb.addItem(self.priceLabel)

        self.horizontalButtonLayout.addSpacerItem(horizontalSpacerLeft)
        self.horizontalButtonLayout.addWidget(self.oneDayButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.oneWeekButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.oneMonthbuttonStock.button)
        self.horizontalButtonLayout.addWidget(self.threeMonthButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.oneYearButtonStock.button)
        self.horizontalButtonLayout.addWidget(self.allButtonStock.button)
        self.horizontalButtonLayout.addSpacerItem(horizontalSpacerRight)
        self.buttonWidget.setLayout(self.horizontalButtonLayout)

        self.volumeGraph.addItem(self.volumeLine)
        self.verticalGraphLayout.addWidget(self.graph)
        self.verticalGraphLayout.addWidget(self.volumeGraph)
        self.verticalGraphLayout.addWidget(self.buttonWidget)

        self.multiWidget.setLayout(self.verticalGraphLayout)
        self.graphDock.setWidget(self.multiWidget)
