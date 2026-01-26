import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth API endpoints
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  register: (userData) => api.post('/api/auth/register', userData),
  getProfile: () => api.get('/api/auth/me'),
  getPortfolio: () => api.get('/api/auth/portfolio'),
  getPerformance: () => api.get('/api/auth/performance'),
};

// Stocks API endpoints
export const stocksAPI = {
  search: (query) => api.get(`/api/stocks/search?query=${query}`),
  getQuote: (symbol) => api.get(`/api/stocks/${symbol}/quote`),
  getHistory: (symbol, period = '1M') => api.get(`/api/stocks/${symbol}/history?period=${period}`),
  getCompanyInfo: (symbol) => api.get(`/api/stocks/${symbol}/company`),
};

// Transactions API endpoints
export const transactionsAPI = {
  getAll: () => api.get('/api/transactions/'),
  create: (data) => api.post('/api/transactions/', data),
  delete: (id) => api.delete(`/api/transactions/${id}`),
};

export default api;
