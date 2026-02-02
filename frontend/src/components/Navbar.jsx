import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';

function Navbar() {
  const navigate = useNavigate();
  const { isAuthenticated, user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-xl font-bold">
            Portfolio Tracker
          </Link>
          <div className="flex items-center space-x-6">
            {isAuthenticated ? (
              <>
                <Link to="/" className="hover:text-blue-200 transition">Dashboard</Link>
                <Link to="/stocks" className="hover:text-blue-200 transition">Stocks</Link>
                <Link to="/watchlist" className="hover:text-blue-200 transition">Watchlist</Link>
                <Link to="/transactions" className="hover:text-blue-200 transition">Transactions</Link>
                <span className="text-blue-200">Welcome, {user?.username || user?.email}</span>
                <button
                  onClick={handleLogout}
                  className="bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded transition"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="hover:text-blue-200 transition">Login</Link>
                <Link to="/register" className="bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded transition">Register</Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
