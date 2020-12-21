import sys
import datetime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QMainWindow,
                             QApplication,
                             QAction,
                             qApp,
                             QFileDialog,
                             QHBoxLayout,
                             QVBoxLayout,
                             QLineEdit,
                             QPushButton,
                             QWidget,
                             QLabel,
                             QTabWidget,
                             QTableView,
                             QHeaderView)

import portfolio
import pandas as pd
import numpy as np
import time
from DateAxisItem import DateAxisItem

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent=parent)
        self._df = df.copy()

    #def toDateFrame(self):
    #    return self._df.copy()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == QtCore.Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except IndexError:
                return QtCore.QVariant()
        elif orientation == QtCore.Qt.Vertical:
            try:
                return self._df.index.tolist()[section]
            except IndexError:
                return QtCore.QVariant

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        if not index.isValid():
            return QtCore.QVariant()
        return QtCore.QVariant(str(self._df.values[index.row()][index.column()]))

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.columns)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self._data_file_name = ""
        self._data = pd.DataFrame()
        self.initUI()

    def initUI(self):
        self.createMenu()
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)

        optionsLayout = QVBoxLayout()

        riskRateLabel = QLabel("Risk rate: ", centralWidget)
        self.riskRateLineEdit = QLineEdit(centralWidget)
        self.riskRateLineEdit.setText("0.0178")
        riskRateLayout = QHBoxLayout()
        riskRateLayout.addWidget(riskRateLabel)
        riskRateLayout.addWidget(self.riskRateLineEdit)

        portfolioNumLabel = QLabel("Portfolios: ", centralWidget)
        self.portfolioNumLineEdit = QLineEdit(centralWidget)
        self.portfolioNumLineEdit.setText("10000")
        portfolioNumLayout = QHBoxLayout()
        portfolioNumLayout.addWidget(portfolioNumLabel)
        portfolioNumLayout.addWidget(self.portfolioNumLineEdit)

        generateButton = QPushButton("Generate")
        generateButton.clicked.connect(self.onGenerateButtonClick)

        boldFont = QtGui.QFont()
        boldFont.setBold(True)
        resultsTitle = QLabel("RESULTS")
        resultsTitle.setFont(boldFont)
        sharpeAllocationTitle = QLabel("Max Sharpe Ratio Potfolio Allocation:")
        sharpeAllocationTitle.setFont(boldFont)
        self.sharpeAllocationLabel = QLabel()
        volatilityAllocationTitle = QLabel("Minimum Volatility Potfolio Allocation:")
        volatilityAllocationTitle.setFont(boldFont)
        self.volatilityAllocationLabel = QLabel()

        optionsLayout.addLayout(riskRateLayout)
        optionsLayout.addLayout(portfolioNumLayout)
        optionsLayout.addWidget(generateButton)
        optionsLayout.addWidget(resultsTitle)
        optionsLayout.addWidget(sharpeAllocationTitle)
        optionsLayout.addWidget(self.sharpeAllocationLabel)
        optionsLayout.addWidget(volatilityAllocationTitle)
        optionsLayout.addWidget(self.volatilityAllocationLabel)
        optionsLayout.addStretch(1)

        tabs = QTabWidget()
        self.tableView = QTableView()
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self._stocksPlot = self.createPlot("Stocks prices", "Date", "Price in $")
        axis = DateAxisItem(orientation='bottom')
        axis.attachToPlotItem(self._stocksPlot.getPlotItem())

        self._dailyReturnsPlot = self.createPlot("Daily returns", "Date", "Price in $")
        axis = DateAxisItem(orientation='bottom')
        axis.attachToPlotItem(self._dailyReturnsPlot.getPlotItem())

        mptWidget = QWidget()
        mptLayout = QHBoxLayout()
        self._mptPlot = self.createPlot("Bullet", "Annualized Volatility", "Annualized Returns")
        mptLayout.addLayout(optionsLayout, 20)
        mptLayout.addWidget(self._mptPlot, 80)
        mptWidget.setLayout(mptLayout)

        tabs.addTab(self.tableView, "Data")
        tabs.addTab(self._stocksPlot, "Stocks")
        tabs.addTab(self._dailyReturnsPlot, "Daily Returns")
        tabs.addTab(mptWidget, "Portfolios")

        tabsLayout = QVBoxLayout()
        tabsLayout.addWidget(tabs)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(tabsLayout)

        centralWidget.setLayout(mainLayout)

        self.setGeometry(100, 100, 500, 500)
        self.setWindowTitle('Trader helper')
        self.setWindowState(QtCore.Qt.WindowMaximized)

    def createMenu(self):
        openFileAct = QAction("Open file...", self)
        openFileAct.triggered.connect(self.onOpenFileMenuClick)

        exitAct = QAction("Exit", self)
        exitAct.triggered.connect(self.close)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu("File")
        fileMenu.addAction(openFileAct)
        fileMenu.addAction(exitAct)

    def createPlot(self, title, xlabel, ylabel):
        newPlot = pg.PlotWidget()
        newPlot.setBackground('w')
        newPlot.addLegend()
        newPlot.showGrid(x=True, y=True)
        newPlot.setTitle(title)
        newPlot.setLabel("bottom", xlabel)
        newPlot.setLabel("left", ylabel)
        return newPlot

    def onOpenFileMenuClick(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Data files (*.csv)")
        if file_dialog.exec_() == QFileDialog.Accepted:
            self._data_file_name = file_dialog.selectedFiles()[0]
            self._data = portfolio.get_data(self._data_file_name)
            self.showStockData()
            self.plotStocksData()
            self.plotDailyReturn()

    def onGenerateButtonClick(self):
        risk_rate = float(self.riskRateLineEdit.text())
        num_portfolios = int(self.portfolioNumLineEdit.text())
        weights, returns, volatilities, sharps_ratios = portfolio.generate_random_portfolios(self._data, risk_rate, num_portfolios)

        max_sharpe_ratio_index = np.argmax(sharps_ratios)
        min_volatility_index = np.argmin(volatilities)


        max_sharpe_ratio_allocation = pd.DataFrame(data=np.round(weights[max_sharpe_ratio_index, :] * 100, 2),
                                                  index=self._data.columns).T
        min_volatility_allocation = pd.DataFrame(data=np.round(weights[min_volatility_index, :] * 100, 2),
                                                 index=self._data.columns).T

        self.sharpeAllocationLabel.setText(max_sharpe_ratio_allocation.to_string(index=False))
        self.sharpeAllocationLabel.adjustSize()
        self.volatilityAllocationLabel.setText(min_volatility_allocation.to_string(index=False))
        self.volatilityAllocationLabel.adjustSize()

        self.plotBullet(volatilities, returns, min_volatility_index, max_sharpe_ratio_index)

    def showStockData(self):
        model = PandasModel(self._data)
        self.tableView.setModel(model)

    def plotStocksData(self):
        date_time_range = pd.to_datetime(self._data.index).astype(int) / 10 ** 9
        for c in self._data.columns.values:
            self._stocksPlot.plot(date_time_range, self._data[c], name=c,
                             pen=pg.mkPen(color=tuple(np.random.choice(range(256), size=3)), width=5))

    def plotDailyReturn(self):
        date_time_range = pd.to_datetime(self._data.index).astype(int) / 10 ** 9
        changes = self._data.pct_change()
        for c in self._data.columns.values:
            self._dailyReturnsPlot.plot(date_time_range, changes[c].fillna(0), name=c,
                                  pen=pg.mkPen(color=tuple(np.random.choice(range(256), size=3)), width=5))

    def plotBullet(self, volatilities, returns, min_volatility_index, max_sharp_ratio_index):
        self._mptPlot.clear()
        self._mptPlot.plot(volatilities, returns, pen=None, symbol='o', name="Random Portfolios",
                           symbolPen=pg.mkPen(color=(0, 0, 255, 100), width=0),
                           symbolBrush=pg.mkBrush(color=(0, 0, 255, 100)))
        self._mptPlot.plot([volatilities[min_volatility_index]], [returns[min_volatility_index]],
                          name="Minimum Volatility", pen=None, symbol='star', symbolPen=pg.mkPen(color=(255, 0, 0, 255), width=0),
                           symbolBrush=pg.mkBrush(color=(255, 0, 0, 255)), symbolSize=20)

        self._mptPlot.plot([volatilities[max_sharp_ratio_index]], [returns[max_sharp_ratio_index]],
                          name="Max Sharpe Ratio", pen=None, symbol='star', symbolPen=pg.mkPen(color=(0, 255, 0, 255), width=0),
                          symbolBrush=pg.mkBrush(color=(0, 255, 0, 255)), symbolSize=20)

def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
