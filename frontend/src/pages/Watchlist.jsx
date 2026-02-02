import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { stocksAPI, watchlistAPI } from '../services/api';
import useAuthStore from '../store/authStore';

function Watchlist() {
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState([]);
  const [quotes, setQuotes] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [targetPrice, setTargetPrice] = useState('');
  const [addLoading, setAddLoading] = useState(false);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Fetch watchlist on mount
  useEffect(() => {
    if (isAuthenticated) {
      fetchWatchlist();
    }
  }, [isAuthenticated]);

  const fetchWatchlist = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await watchlistAPI.getAll();
      setWatchlist(response.data);
      // Fetch quotes for all watchlist items
      fetchQuotes(response.data);
    } catch (err) {
      setError('Failed to load watchlist');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchQuotes = async (items) => {
    const quotePromises = items.map(async (item) => {
      try {
        const response = await stocksAPI.getQuote(item.symbol);
        return { symbol: item.symbol, quote: response.data };
      } catch (err) {
        console.error(`Failed to fetch quote for ${item.symbol}:`, err);
        return { symbol: item.symbol, quote: null };
      }
    });

    const results = await Promise.all(quotePromises);
    const quotesMap = {};
    results.forEach(({ symbol, quote }) => {
      quotesMap[symbol] = quote;
    });
    setQuotes(quotesMap);
  };

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

  const handleSelectStock = (stock) => {
    setSelectedStock(stock);
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleAddToWatchlist = async () => {
    if (!selectedStock) {
      return;
    }

    setAddLoading(true);
    try {
      await watchlistAPI.add({
        symbol: selectedStock.symbol,
        target_price: targetPrice ? parseFloat(targetPrice) : null,
      });
      setSelectedStock(null);
      setTargetPrice('');
      fetchWatchlist();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add to watchlist');
    } finally {
      setAddLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Remove this stock from your watchlist?')) {
      return;
    }

    try {
      await watchlistAPI.delete(id);
      fetchWatchlist();
    } catch (err) {
      setError('Failed to remove from watchlist');
    }
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) {
      return 'N/A';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  return (
    <div className="watchlist">
      <h1 className="text-3xl font-bold mb-6">Watchlist</h1>

      {/* Add Stock Form */}
      <div className="bg-white p-6 rounded-lg shadow-lg mb-6">
        <h2 className="text-xl font-semibold mb-4">Add Stock to Watchlist</h2>

        <div className="flex flex-col md:flex-row gap-4">
          {/* Stock Search */}
          <div className="flex-1 relative">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Stock
            </label>
            {selectedStock ? (
              <div className="flex items-center justify-between px-4 py-3 border border-gray-300 rounded-lg bg-gray-50">
                <div>
                  <span className="font-bold">{selectedStock.symbol}</span>
                  <span className="text-gray-600 ml-2">{selectedStock.name}</span>
                </div>
                <button
                  onClick={() => setSelectedStock(null)}
                  className="text-gray-500 hover:text-red-500"
                >
                  X
                </button>
              </div>
            ) : (
              <>
                <input
                  type="text"
                  placeholder="Search by symbol or name..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                {searchResults.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {searchResults.map((result, index) => (
                      <div
                        key={index}
                        className="p-3 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                        onClick={() => handleSelectStock(result)}
                      >
                        <span className="font-bold">{result.symbol}</span>
                        <span className="text-gray-600 ml-2 text-sm">{result.name}</span>
                      </div>
                    ))}
                  </div>
                )}
                {searchLoading && (
                  <div className="absolute right-3 top-9">
                    <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Target Price */}
          <div className="w-full md:w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target Price (optional)
            </label>
            <input
              type="number"
              step="0.01"
              placeholder="$0.00"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
            />
          </div>

          {/* Add Button */}
          <div className="flex items-end">
            <button
              onClick={handleAddToWatchlist}
              disabled={!selectedStock || addLoading}
              className="w-full md:w-auto px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-blue-300 disabled:cursor-not-allowed transition"
            >
              {addLoading ? 'Adding...' : 'Add to Watchlist'}
            </button>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
          <button onClick={() => setError('')} className="float-right font-bold">X</button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin h-12 w-12 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      )}

      {/* Watchlist Items */}
      {!loading && watchlist.length > 0 && (
        <div className="space-y-3">
          {watchlist.map((item) => {
            const quote = quotes[item.symbol];
            const change = quote?.change;
            const changePercent = quote?.change_percent;
            const isPositive = change >= 0;

            return (
              <div
                key={item.id}
                className="bg-white p-4 rounded-lg shadow flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Symbol and Name */}
                <div
                  className="flex-1 cursor-pointer hover:text-blue-600 transition"
                  onClick={() => navigate(`/stocks?symbol=${item.symbol}`)}
                >
                  <div className="font-bold text-lg">{item.symbol}</div>
                  <div className="text-gray-600 text-sm">{quote?.name || 'Loading...'}</div>
                </div>

                {/* Current Price */}
                <div className="text-center md:text-right">
                  <div className="text-gray-500 text-xs">Current Price</div>
                  <div className="font-semibold text-lg">
                    {quote ? formatCurrency(quote.price) : '...'}
                  </div>
                </div>

                {/* Day's P&L */}
                <div className="text-center md:text-right min-w-[120px]">
                  <div className="text-gray-500 text-xs">Day&apos;s Change</div>
                  {quote ? (
                    <div className={`font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                      {isPositive ? '+' : ''}{change?.toFixed(2)} ({isPositive ? '+' : ''}{changePercent?.toFixed(2)}%)
                    </div>
                  ) : (
                    <div className="text-gray-400">...</div>
                  )}
                </div>

                {/* Target Price */}
                <div className="text-center md:text-right min-w-[100px]">
                  <div className="text-gray-500 text-xs">Target</div>
                  <div className="font-semibold">
                    {item.target_price ? formatCurrency(item.target_price) : '-'}
                  </div>
                </div>

                {/* Delete Button */}
                <button
                  onClick={() => handleDelete(item.id)}
                  className="text-red-500 hover:text-red-700 hover:bg-red-50 px-3 py-2 rounded transition"
                  title="Remove from watchlist"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Empty State */}
      {!loading && watchlist.length === 0 && (
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
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
          <h2 className="text-2xl font-bold mb-2 text-gray-700">Your Watchlist is Empty</h2>
          <p className="text-gray-500">Search for stocks above and add them to your watchlist to track their prices.</p>
        </div>
      )}
    </div>
  );
}

export default Watchlist;
