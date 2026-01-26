import React, { useState, useEffect } from 'react';
import { stocksAPI } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function Stocks() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [quote, setQuote] = useState(null);
  const [history, setHistory] = useState(null);
  const [companyInfo, setCompanyInfo] = useState(null);
  const [period, setPeriod] = useState('1M');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);

  // Search stocks as user types
  useEffect(() => {
    const searchStocks = async () => {
      if (searchQuery.length < 1) {
        setSearchResults([]);
        return;
      }

      setSearchLoading(true);
      try {
        const response = await stocksAPI.search(searchQuery);
        setSearchResults(response.data.results || []);
      } catch (err) {
        console.error('Search error:', err);
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    };

    const timeoutId = setTimeout(searchStocks, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  // Fetch stock data when a stock is selected
  const handleSelectStock = async (symbol) => {
    setSelectedStock(symbol);
    setLoading(true);
    setError(null);
    setSearchQuery('');
    setSearchResults([]);

    try {
      // Fetch quote, history, and company info in parallel
      const [quoteRes, historyRes, companyRes] = await Promise.all([
        stocksAPI.getQuote(symbol),
        stocksAPI.getHistory(symbol, period),
        stocksAPI.getCompanyInfo(symbol)
      ]);

      setQuote(quoteRes.data);
      setHistory(historyRes.data);
      setCompanyInfo(companyRes.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch stock data');
      console.error('Error fetching stock data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch new history when period changes
  useEffect(() => {
    if (selectedStock) {
      const fetchHistory = async () => {
        try {
          const response = await stocksAPI.getHistory(selectedStock, period);
          setHistory(response.data);
        } catch (err) {
          console.error('Error fetching history:', err);
        }
      };
      fetchHistory();
    }
  }, [period, selectedStock]);

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatNumber = (value) => {
    if (!value) return 'N/A';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return value.toLocaleString();
  };

  return (
    <div className="stocks">
      <h1 className="text-3xl font-bold mb-6">Stock Market</h1>

      {/* Search Bar */}
      <div className="mb-6 relative">
        <input
          type="text"
          placeholder="Search stocks by symbol or company name..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />

        {/* Search Results Dropdown */}
        {searchResults.length > 0 && (
          <div className="absolute z-10 w-full mt-2 bg-white border border-gray-300 rounded-lg shadow-lg max-h-96 overflow-y-auto">
            {searchResults.map((result, index) => (
              <div
                key={index}
                className="p-4 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                onClick={() => handleSelectStock(result.symbol)}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-bold text-lg">{result.symbol}</div>
                    <div className="text-gray-600 text-sm">{result.name}</div>
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    <div>{result.type}</div>
                    <div>{result.region}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {searchLoading && (
          <div className="absolute right-4 top-4">
            <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      )}

      {/* Stock Details */}
      {!loading && selectedStock && quote && (
        <div className="space-y-6">
          {/* Stock Quote Card */}
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-3xl font-bold">{quote.symbol}</h2>
                <p className="text-gray-600 text-lg">{quote.name}</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold">{formatCurrency(quote.price)}</div>
                <div className={`text-lg ${quote.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {quote.change >= 0 ? '+' : ''}{quote.change?.toFixed(2)}
                  ({quote.change_percent >= 0 ? '+' : ''}{quote.change_percent?.toFixed(2)}%)
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <div>
                <div className="text-gray-500 text-sm">Open</div>
                <div className="font-semibold">{formatCurrency(quote.open)}</div>
              </div>
              <div>
                <div className="text-gray-500 text-sm">High</div>
                <div className="font-semibold">{formatCurrency(quote.day_high)}</div>
              </div>
              <div>
                <div className="text-gray-500 text-sm">Low</div>
                <div className="font-semibold">{formatCurrency(quote.day_low)}</div>
              </div>
              <div>
                <div className="text-gray-500 text-sm">Prev Close</div>
                <div className="font-semibold">{formatCurrency(quote.previous_close)}</div>
              </div>
              <div>
                <div className="text-gray-500 text-sm">Volume</div>
                <div className="font-semibold">{quote.volume?.toLocaleString() || 'N/A'}</div>
              </div>
              <div>
                <div className="text-gray-500 text-sm">Market Cap</div>
                <div className="font-semibold">{formatNumber(quote.market_cap)}</div>
              </div>
            </div>
          </div>

          {/* Historical Chart */}
          {history && history.data && (
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">Price History</h3>
                <div className="flex gap-2">
                  {['1D', '1W', '1M', '3M', '6M', '1Y', '5Y'].map((p) => (
                    <button
                      key={p}
                      onClick={() => setPeriod(p)}
                      className={`px-3 py-1 rounded ${
                        period === p
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={history.data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis
                    domain={['auto', 'auto']}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
                    formatter={(value) => formatCurrency(value)}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="close"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    name="Close Price"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Company Information */}
          {companyInfo && (
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-xl font-bold mb-4">Company Information</h3>

              {companyInfo.description && (
                <div className="mb-4">
                  <h4 className="font-semibold mb-2">About</h4>
                  <p className="text-gray-700 text-sm leading-relaxed">{companyInfo.description}</p>
                </div>
              )}

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                {companyInfo.sector && (
                  <div>
                    <div className="text-gray-500 text-sm">Sector</div>
                    <div className="font-semibold">{companyInfo.sector}</div>
                  </div>
                )}
                {companyInfo.industry && (
                  <div>
                    <div className="text-gray-500 text-sm">Industry</div>
                    <div className="font-semibold">{companyInfo.industry}</div>
                  </div>
                )}
                {companyInfo.country && (
                  <div>
                    <div className="text-gray-500 text-sm">Country</div>
                    <div className="font-semibold">{companyInfo.country}</div>
                  </div>
                )}
                {companyInfo.employees && (
                  <div>
                    <div className="text-gray-500 text-sm">Employees</div>
                    <div className="font-semibold">{companyInfo.employees.toLocaleString()}</div>
                  </div>
                )}
                {companyInfo.pe_ratio && (
                  <div>
                    <div className="text-gray-500 text-sm">P/E Ratio</div>
                    <div className="font-semibold">{companyInfo.pe_ratio.toFixed(2)}</div>
                  </div>
                )}
                {companyInfo.beta && (
                  <div>
                    <div className="text-gray-500 text-sm">Beta</div>
                    <div className="font-semibold">{companyInfo.beta.toFixed(2)}</div>
                  </div>
                )}
                {companyInfo['52_week_high'] && (
                  <div>
                    <div className="text-gray-500 text-sm">52 Week High</div>
                    <div className="font-semibold">{formatCurrency(companyInfo['52_week_high'])}</div>
                  </div>
                )}
                {companyInfo['52_week_low'] && (
                  <div>
                    <div className="text-gray-500 text-sm">52 Week Low</div>
                    <div className="font-semibold">{formatCurrency(companyInfo['52_week_low'])}</div>
                  </div>
                )}
                {companyInfo.website && (
                  <div className="col-span-2 md:col-span-3">
                    <div className="text-gray-500 text-sm">Website</div>
                    <a
                      href={companyInfo.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline font-semibold"
                    >
                      {companyInfo.website}
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && !selectedStock && (
        <div className="bg-white p-12 rounded-lg shadow text-center">
          <svg
            className="mx-auto h-24 w-24 text-gray-400 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <h2 className="text-2xl font-bold mb-2 text-gray-700">Search for Stocks</h2>
          <p className="text-gray-500">Enter a symbol or company name to view stock information, charts, and company details.</p>
        </div>
      )}
    </div>
  );
}

export default Stocks;
