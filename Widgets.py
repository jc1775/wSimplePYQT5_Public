def createStockTable():
     self.cryptoTable = QtWidgets.QTableWidget()
        self.cryptoTable.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cryptoTable.sizePolicy().hasHeightForWidth())
        self.cryptoTable.setSizePolicy(sizePolicy)
        self.cryptoTable.setMinimumSize(QtCore.QSize(1000, 0))
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
        self.cryptoTable.verticalHeader().setStretchLastSection(True)