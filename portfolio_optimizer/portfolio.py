import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

DAYS = 252
#RISK_FREE_RATE = 0.0178


def calculate_returns(weights, mean_return):
    return np.dot(weights, mean_return) * DAYS


def calculate_volatility(weights, cov_matrix):
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(DAYS)


def calculate_sharp_ratio(portfolio_return, risk_free_rate, portlofio_volatility):
    return (portfolio_return - risk_free_rate) / portlofio_volatility


def generate_random_portfolios(stocks: pd.DataFrame, risk_free_rate: float, num_portfolios: int):
    mean_annual_return = stocks.pct_change().mean() * DAYS
    num_stocks = stocks.shape[1]
    cov_annual = stocks.pct_change().cov().to_numpy() * DAYS

    random_weights = np.zeros((num_portfolios, num_stocks))
    random_returns = np.zeros((num_portfolios,))
    random_volatilities = np.zeros((num_portfolios,))
    random_sharp_ratios = np.zeros((num_portfolios,))
    for i in range(num_portfolios):
        portfolio_weights = np.random.random(num_stocks)
        portfolio_weights /= np.sum(portfolio_weights)
        portfolio_return = calculate_returns(portfolio_weights, mean_annual_return)
        portfolio_volatility = calculate_volatility(portfolio_weights, cov_annual)
        portfolio_sharp_ratio = calculate_sharp_ratio(portfolio_return, risk_free_rate, portfolio_volatility)

        random_weights[i] = portfolio_weights
        random_returns[i] = portfolio_return
        random_volatilities[i] = portfolio_volatility
        random_sharp_ratios[i] = portfolio_sharp_ratio

    return random_weights, random_returns, random_volatilities, random_sharp_ratios


def get_data(path):
    df = pd.read_csv(path, index_col=0)
    return df


if __name__ == '__main__':
    df = pd.read_csv("stonks.csv", index_col=0)

    weights, returns, volatilities, sharps_ratios = generate_random_portfolios(df, 0.0178, 50000)

    max_sharp_ratio_index = np.argmax(sharps_ratios)
    min_volatility_index = np.argmin(volatilities)

    plt.style.use('seaborn')
    plt.scatter(x=volatilities, y=returns, c=returns, marker='o', cmap='YlGnBu', s=10, alpha=0.3)
    plt.colorbar()
    plt.scatter(volatilities[max_sharp_ratio_index],
                returns[max_sharp_ratio_index],
                marker='*',
                color='r',
                s=500,
                label='Maximum Sharpe ratio')
    plt.scatter(volatilities[min_volatility_index],
                returns[min_volatility_index],
                marker='*',
                color='b',
                s=500,
                label='Minimum Volatility')
    plt.xlabel('Volatility (Std. Deviation)')
    plt.ylabel('Expected Returns')
    plt.title('Efficient Frontier')
    plt.legend(labelspacing=0.8)
    plt.show()
