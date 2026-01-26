import React, { useState, useEffect } from 'react';
import { authAPI } from '../services/api';
import useAuthStore from '../store/authStore';

function Dashboard() {
  const [portfolio, setPortfolio] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [portfolioResponse, performanceResponse] = await Promise.all([
        authAPI.getPortfolio(),
        authAPI.getPerformance()
      ]);
      setPortfolio(portfolioResponse.data);
      setPerformance(performanceResponse.data);
    } catch (err) {
      setError('Failed to load portfolio data');
      console.error('Error fetching portfolio:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard flex items-center justify-center h-64">
        <p className="text-gray-500">Loading portfolio...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      </div>
    );
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value || 0);
  };

  const formatPercentage = (value) => {
    return `${parseFloat(value || 0).toFixed(2)}%`;
  };

  return (
    <div className="dashboard">
      <h1 className="text-3xl font-bold mb-6">Portfolio Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm">Total Value</h3>
          <p className="text-2xl font-bold">{formatCurrency(performance?.total_value)}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm">Cash Balance</h3>
          <p className="text-2xl font-bold">{formatCurrency(performance?.cash_balance)}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm">Holdings Value</h3>
          <p className="text-2xl font-bold">{formatCurrency(performance?.holdings_value)}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-gray-500 text-sm">Total Gain/Loss</h3>
          <p className={`text-2xl font-bold ${parseFloat(performance?.total_gain_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {parseFloat(performance?.total_gain_loss || 0) >= 0 ? '+' : ''}{formatCurrency(performance?.total_gain_loss)}
            <span className="text-sm ml-2">({formatPercentage(performance?.total_gain_loss_percentage)})</span>
          </p>
        </div>
      </div>

      {/* Holdings table */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Current Holdings</h2>
        {!portfolio?.holdings || portfolio.holdings.length === 0 ? (
          <p className="text-gray-500">No holdings yet. Add your first transaction to get started.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quantity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Cost</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Market Value</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Gain/Loss</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {portfolio.holdings.map((holding) => (
                  <tr key={holding.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {holding.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {parseFloat(holding.quantity).toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(holding.average_cost)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(holding.current_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatCurrency(holding.market_value)}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${parseFloat(holding.gain_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {parseFloat(holding.gain_loss || 0) >= 0 ? '+' : ''}{formatCurrency(holding.gain_loss)}
                      <span className="text-xs ml-1">({formatPercentage(holding.gain_loss_percentage)})</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
