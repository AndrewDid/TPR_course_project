import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as sco

DAYS = 252


def calculate_cov_matrix(data, days):
    return data.pct_change().cov().to_numpy() * days


def calculate_mean_returns(data, days):
    return data.pct_change().mean() * days


def calculate_returns(weights, mean_return):
    return np.dot(weights, mean_return) * DAYS


def calculate_volatility(weights, cov_matrix):
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights))) * np.sqrt(DAYS)


def calculate_sharp_ratio(portfolio_return, risk_free_rate, portlofio_volatility):
    return (portfolio_return - risk_free_rate) / portlofio_volatility


def generate_random_portfolios(mean_returns, cov_matrix, risk_free_rate, num_portfolios):
    num_stocks = len(mean_returns)

    random_weights = np.zeros((num_portfolios, num_stocks))
    random_returns = np.zeros((num_portfolios,))
    random_volatilities = np.zeros((num_portfolios,))
    random_sharp_ratios = np.zeros((num_portfolios,))
    for i in range(num_portfolios):
        portfolio_weights = np.random.random(num_stocks)
        portfolio_weights /= np.sum(portfolio_weights)
        portfolio_return = calculate_returns(portfolio_weights, mean_returns)
        portfolio_volatility = calculate_volatility(portfolio_weights, cov_matrix)
        portfolio_sharp_ratio = calculate_sharp_ratio(portfolio_return, risk_free_rate, portfolio_volatility)

        random_weights[i] = portfolio_weights
        random_returns[i] = portfolio_return
        random_volatilities[i] = portfolio_volatility
        random_sharp_ratios[i] = portfolio_sharp_ratio

    return random_weights, random_returns, random_volatilities, random_sharp_ratios


def neg_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate):
    returns = calculate_returns(weights, mean_returns)
    volatility = calculate_volatility(weights, cov_matrix)
    return -1 * calculate_sharp_ratio(returns, risk_free_rate, volatility)


def max_sharpe_ratio(mean_returns, cov_matrix, risk_free_rate):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix, risk_free_rate)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bound = (0.0, 1.0)
    bounds = tuple(bound for asset in range(num_assets))
    results = sco.minimize(neg_sharpe_ratio, num_assets*[1./num_assets], args=args,
                           method='SLSQP', bounds=bounds, constraints=constraints)
    return results


def min_volatility(mean_returns, cov_matrix):
    num_assets = len(mean_returns)
    args = (cov_matrix,)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bound = (0.0, 1.0)
    bounds = tuple(bound for asset in range(num_assets))
    results = sco.minimize(calculate_volatility, num_assets * [1. / num_assets], args=args,
                           method='SLSQP', bounds=bounds, constraints=constraints)
    return results


def efficient_return(mean_returns, cov_matrix, target):
    num_assets = len(mean_returns)
    args = (cov_matrix,)

    def portfolio_return(weights):
        return calculate_returns(weights, mean_returns)

    constraints = ({'type': 'eq', 'fun': lambda x: portfolio_return(x) - target},
                   {'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for asset in range(num_assets))
    results = sco.minimize(calculate_volatility, num_assets*[1./num_assets], args=args,
                           method='SLSQP', bounds=bounds, constraints=constraints)
    return results


def calculate_efficient_frontier(mean_returns, cov_matrix, returns_range):
    efficients = []
    for ret in returns_range:
        efficients.append(efficient_return(mean_returns, cov_matrix, ret))
    return efficients


def get_data(path):
    df = pd.read_csv(path, index_col=0)
    return df


if __name__ == '__main__':
    df = pd.read_csv("../stonks.csv", index_col=0)
    mean_returns = calculate_mean_returns(df, DAYS)
    cov_matrix = calculate_cov_matrix(df, DAYS)

    weights, returns, volatilities, sharps_ratios = generate_random_portfolios(mean_returns, cov_matrix, 0.0178, 100000)

    max_sharp_ratio_index = np.argmax(sharps_ratios)
    min_volatility_index = np.argmin(volatilities)

    max_shapre_weights = max_sharpe_ratio(mean_returns, cov_matrix, 0.0178)['x']
    min_vol_weights = min_volatility(mean_returns, cov_matrix)['x']

    sdp = calculate_volatility(max_shapre_weights, cov_matrix)
    rp = calculate_returns(max_shapre_weights, mean_returns)

    sdp_min = calculate_volatility(min_vol_weights, cov_matrix)
    rp_min = calculate_returns(min_vol_weights, mean_returns)

    target = np.linspace(-80, 80, 100)
    efficient_portfolios = calculate_efficient_frontier(mean_returns, cov_matrix, target)

    plt.style.use('seaborn')
    plt.scatter(x=volatilities, y=returns, c=returns, marker='o', cmap='YlGnBu', s=10, alpha=0.3)
    plt.colorbar()
    plt.plot([p['fun'] for p in efficient_portfolios], target, linestyle='-.', color='black', label='efficient frontier')
    plt.scatter(volatilities[max_sharp_ratio_index],
                returns[max_sharp_ratio_index],
                marker='*',
                color='r',
                s=500,
                label='Maximum Sharpe ratio')
    plt.scatter(sdp,
                rp,
                marker='*',
                color='r',
                s=500,
                label='Maximum Sharpe ratio')

    plt.scatter(sdp_min,
                rp_min,
                marker='*',
                color='b',
                s=500,
                label='Minimum Volatility')
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
