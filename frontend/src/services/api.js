import axios from 'axios';

const API_BASE_URL = 'https://ai-research-assistant-d3z9.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
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

// Response interceptor to handle token expiry / unauthorized requests
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear storage and redirect/reload if not already on login page
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        localStorage.removeItem('token');
        localStorage.removeItem('user_role');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  register: async (email, password) => {
    const response = await api.post('/api/auth/register', { email, password });
    return response.data;
  },
  login: async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      // Immediately fetch me to get user role
      try {
        const userRes = await api.get('/api/auth/me', {
          headers: { Authorization: `Bearer ${response.data.access_token}` }
        });
        localStorage.setItem('user_role', userRes.data.role);
        return { token: response.data.access_token, user: userRes.data };
      } catch (err) {
        localStorage.setItem('user_role', 'user');
        return { token: response.data.access_token, user: { email, role: 'user' } };
      }
    }
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_role');
  },
  getMe: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

export const docService = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  list: async () => {
    const response = await api.get('/api/documents');
    return response.data;
  },
  delete: async (documentId) => {
    const response = await api.delete(`/api/documents/${documentId}`);
    return response.data;
  },
  summarize: async (documentId) => {
    const response = await api.post(`/api/documents/${documentId}/summarize`);
    return response.data;
  },
  getKeywords: async (documentId) => {
    const response = await api.post(`/api/documents/${documentId}/keywords`);
    return response.data;
  },
  getQuestions: async (documentId) => {
    const response = await api.post(`/api/documents/${documentId}/questions`);
    return response.data;
  },
};

export const chatService = {
  createSession: async (title = '') => {
    const response = await api.post('/api/chat/sessions', { title });
    return response.data;
  },
  listSessions: async () => {
    const response = await api.get('/api/chat/sessions');
    return response.data;
  },
  getSession: async (sessionId) => {
    const response = await api.get(`/api/chat/sessions/${sessionId}`);
    return response.data;
  },
  deleteSession: async (sessionId) => {
    const response = await api.delete(`/api/chat/sessions/${sessionId}`);
    return response.data;
  },
  querySync: async (sessionId, content) => {
    const response = await api.post(`/api/chat/sessions/${sessionId}/query`, { content });
    return response.data;
  },
  getStreamUrl: (sessionId, queryText) => {
    const token = localStorage.getItem('token') || '';
    return `${API_BASE_URL}/api/chat/sessions/${sessionId}/query/stream?q=${encodeURIComponent(queryText)}&token=${encodeURIComponent(token)}`;
  },
};

export const adminService = {
  getStats: async () => {
    const response = await api.get('/api/admin/stats');
    return response.data;
  },
};

export default api;
