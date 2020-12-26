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
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice

import portfolio
import pandas as pd
import numpy as np
import time
from DateAxisItem import DateAxisItem

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent=parent)
        self._df = df.copy()

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
        riskRateLayout.addStretch(1)
        riskRateLayout.addWidget(riskRateLabel)
        riskRateLayout.addWidget(self.riskRateLineEdit)
        riskRateLayout.addStretch(1)

        portfolioNumLabel = QLabel("Portfolios: ", centralWidget)
        self.portfolioNumLineEdit = QLineEdit(centralWidget)
        self.portfolioNumLineEdit.setText("10000")
        portfolioNumLayout = QHBoxLayout()
        portfolioNumLayout.addStretch(1)
        portfolioNumLayout.addWidget(portfolioNumLabel)
        portfolioNumLayout.addWidget(self.portfolioNumLineEdit)
        portfolioNumLayout.addStretch(1)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch(1)
        generateButton = QPushButton("Generate")
        generateButton.clicked.connect(self.onGenerateButtonClick)
        buttonLayout.addWidget(generateButton)
        buttonLayout.addStretch(1)        

        randomMaxSharpeRatioLayout, self.randomMaxSharpeRatioLabel = self.createParameterLayout("Max Sharpe Ratio (from random portfolio): ")
        randomMinVolatilityLayout, self.randomMinVolatilityLabel = self.createParameterLayout("Min Volatility (from random portfolio): ")
        optimizedMaxSharpeRatioLayout, self.optimizedMaxSharpeRatioLabel = self.createParameterLayout("Max Sharpe Ratio (optimized): ")
        optimizedMinVolatilityLayout, self.optimizedMinVolatilityLabel = self.createParameterLayout("Min Volatility (optimized): ")
        

        self.sharpeChartView = QChartView(self.createChart([], [], "Max Sharpe Ratio Potfolio Allocation"))
        self.sharpeChartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.volatilityChartView = QChartView(self.createChart([], [], "Minimum Volatility Potfolio Allocation"))
        self.volatilityChartView.setRenderHint(QtGui.QPainter.Antialiasing)

        
        optionsLayout.addLayout(riskRateLayout)
        optionsLayout.addLayout(portfolioNumLayout)
        optionsLayout.addLayout(buttonLayout)
        optionsLayout.addLayout(randomMaxSharpeRatioLayout)
        optionsLayout.addLayout(optimizedMaxSharpeRatioLayout)
        optionsLayout.addWidget(self.sharpeChartView)
        optionsLayout.addLayout(randomMinVolatilityLayout)
        optionsLayout.addLayout(optimizedMinVolatilityLayout)
        optionsLayout.addWidget(self.volatilityChartView)

        tabs = QTabWidget()
        self.tableView = QTableView()
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self._stocksPlot = self.createPlot("Stocks prices", "Date", "Price in $")
        axis = DateAxisItem(orientation='bottom')
        axis.attachToPlotItem(self._stocksPlot.getPlotItem())

        self._dailyReturnsPlot = self.createPlot("Daily returns", "Date", "Daily returns")
        axis = DateAxisItem(orientation='bottom')
        axis.attachToPlotItem(self._dailyReturnsPlot.getPlotItem())

        mptWidget = QWidget()
        mptLayout = QHBoxLayout()
        self._mptPlot = self.createPlot("Efficient Frontier", "Annualized Volatility", "Annualized Returns")
        mptLayout.addWidget(self._mptPlot, 50)
        mptLayout.addLayout(optionsLayout, 50)
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
        self.setWindowTitle('Portfolio Optimizer')
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

    def createChart(self, names, values, title):
        series = QPieSeries()
        for name, value in zip(names, values):
            series.append(name + " " + str(value) + "%", value)

        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle(title)
        chart.legend().setVisible(True)

        return chart

    def createPlot(self, title, xlabel, ylabel):
        newPlot = pg.PlotWidget()
        newPlot.setBackground('w')
        newPlot.addLegend()
        newPlot.showGrid(x=True, y=True)
        newPlot.setTitle(title)
        newPlot.setLabel("bottom", xlabel)
        newPlot.setLabel("left", ylabel)
        return newPlot

    def createParameterLayout(self, text):
        parameterText = QLabel(text)
        parameterLabel = QLabel("")
        parameterLayout = QHBoxLayout()
        parameterLayout.addStretch(1)
        parameterLayout.addWidget(parameterText)
        parameterLayout.addWidget(parameterLabel)
        parameterLayout.addStretch(1)
        return parameterLayout, parameterLabel

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

        mean_returns = portfolio.calculate_mean_returns(self._data)
        cov_matrix = portfolio.calculate_cov_matrix(self._data, portfolio.DAYS)
        weights, returns, volatilities, sharps_ratios = portfolio.generate_random_portfolios(mean_returns,
                                                                                             cov_matrix,
                                                                                             risk_rate,
                                                                                             num_portfolios)

        random_min_volatility_index = np.argmin(volatilities)
        random_min_volatility_x = volatilities[random_min_volatility_index]
        random_min_volatility_y = returns[random_min_volatility_index]
        random_min_volatility_point = (random_min_volatility_x, random_min_volatility_y)
        self.randomMinVolatilityLabel.setText("return - " + str(round(random_min_volatility_y, 2)) + ", volatility - " + str(round(random_min_volatility_x, 2)))

        
        random_max_sharpe_ratio_index = np.argmax(sharps_ratios)
        random_max_sharpe_ratio_x = volatilities[random_max_sharpe_ratio_index]
        random_max_sharpe_ratio_y = returns[random_max_sharpe_ratio_index]
        random_max_sharpe_point = (random_max_sharpe_ratio_x, random_max_sharpe_ratio_y)
        self.randomMaxSharpeRatioLabel.setText("return - " + str(round(random_max_sharpe_ratio_y, 2)) + ", volatility - " + str(round(random_max_sharpe_ratio_x, 2)))

        max_sharpe = portfolio.max_sharpe_ratio(mean_returns, cov_matrix, risk_rate)
        min_volatility = portfolio.min_volatility(mean_returns, cov_matrix)

        sharpe_vol = portfolio.calculate_volatility(max_sharpe.x, cov_matrix)
        sharpe_ret = portfolio.calculate_returns(max_sharpe.x, mean_returns)
        self.optimizedMaxSharpeRatioLabel.setText("return - " + str(round(sharpe_ret, 2)) + ", volatility - " + str(round(sharpe_vol, 2)))

        volatility_vol = portfolio.calculate_volatility(min_volatility.x, cov_matrix)
        volatility_ret = portfolio.calculate_returns(min_volatility.x, mean_returns)
        self.optimizedMinVolatilityLabel.setText("return - " + str(round(volatility_ret, 2)) + ", volatility - " + str(round(volatility_vol, 2)))

        frontier_y = np.linspace(sharpe_ret, volatility_ret, 100)
        efficient_portfolios = portfolio.calculate_efficient_frontier(mean_returns, cov_matrix, frontier_y)
        frontier_x = [p['fun'] for p in efficient_portfolios]

        max_sharpe_ratio_allocation = pd.DataFrame(data=np.round(max_sharpe.x * 100, 2),
                                                  index=self._data.columns).T
        min_volatility_allocation = pd.DataFrame(data=np.round(min_volatility.x * 100, 2),
                                                 index=self._data.columns).T


        newSharpeChart = self.createChart(max_sharpe_ratio_allocation.columns.values,
                                    max_sharpe_ratio_allocation.to_numpy()[0].tolist(),
                                    "Max Sharpe Ratio Potfolio Allocation")
        self.sharpeChartView.setChart(newSharpeChart)

        newVolatilityChart = self.createChart(min_volatility_allocation.columns.values,
                                    min_volatility_allocation.to_numpy()[0].tolist(),
                                    "Minimum Volatility Potfolio Allocation")
        self.volatilityChartView.setChart(newVolatilityChart)

        self.plotBullet(volatilities,
                        returns,
                        random_min_volatility_point,
                        random_max_sharpe_point,
                        (volatility_vol, volatility_ret),
                        (sharpe_vol, sharpe_ret),
                        (frontier_x, frontier_y))

    def showStockData(self):
        model = PandasModel(self._data)
        self.tableView.setModel(model)

    def plotStocksData(self):
        self._stocksPlot.clear()
        date_time_range = pd.to_datetime(self._data.index).astype(int) / 10 ** 9
        for c in self._data.columns.values:
            self._stocksPlot.plot(date_time_range, self._data[c], name=c,
                             pen=pg.mkPen(color=tuple(np.random.choice(range(256), size=3)), width=5))

    def plotDailyReturn(self):
        self._dailyReturnsPlot.clear()
        date_time_range = pd.to_datetime(self._data.index).astype(int) / 10 ** 9
        changes = self._data.pct_change()
        for c in self._data.columns.values:
            self._dailyReturnsPlot.plot(date_time_range, changes[c].fillna(0), name=c,
                                  pen=pg.mkPen(color=tuple(np.random.choice(range(256), size=3)), width=5))

    def plotBullet(self, volatilities, returns, random_volatility_point, random_sharpe_point, min_volatility_point, max_sharpe_ratio_point, efficient_frontier):
        self._mptPlot.clear()
        self._mptPlot.plot(volatilities, returns, pen=None, symbol='o', name="Random Portfolios",
                           symbolPen=pg.mkPen(color=(0, 0, 255, 100), width=0),
                           symbolBrush=pg.mkBrush(color=(0, 0, 255, 100)))
        self._mptPlot.plot(efficient_frontier[0], efficient_frontier[1],
                           pen=pg.mkPen(color=(0, 0, 0), width=5))
        
        self._mptPlot.plot([min_volatility_point[0]], [min_volatility_point[1]],
                          name="Minimum Volatility", pen=None, symbol='star', symbolPen=pg.mkPen(color=(255, 0, 0, 255), width=0),
                           symbolBrush=pg.mkBrush(color=(255, 0, 0, 255)), symbolSize=20)

        self._mptPlot.plot([max_sharpe_ratio_point[0]], [max_sharpe_ratio_point[1]],
                          name="Max Sharpe Ratio", pen=None, symbol='star', symbolPen=pg.mkPen(color=(0, 255, 0, 255), width=0),
                          symbolBrush=pg.mkBrush(color=(0, 255, 0, 255)), symbolSize=20)

        self._mptPlot.plot([random_volatility_point[0]], [random_volatility_point[1]],
                          name="Minimum Volatility (from random generated)", pen=None, symbol='star', symbolPen=pg.mkPen(color=(0, 0, 0, 255), width=2),
                           symbolBrush=pg.mkBrush(color=(255, 0, 0, 255)), symbolSize=20)

        self._mptPlot.plot([random_sharpe_point[0]], [random_sharpe_point[1]],
                          name="Max Sharpe Ratio (from random generated)", pen=None, symbol='star', symbolPen=pg.mkPen(color=(0, 0, 0, 255), width=2),
                          symbolBrush=pg.mkBrush(color=(0, 255, 0, 255)), symbolSize=20)


def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
