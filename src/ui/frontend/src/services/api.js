import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  // Get token from Amplify Auth
  try {
    const { getCurrentUser, fetchAuthSession } = await import('aws-amplify/auth');
    const user = await getCurrentUser();
    if (user) {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
  } catch (error) {
    console.warn('Auth token not available:', error);
  }
  return config;
});

// API methods
export default {
  // Rules
  getRules: () => api.get('/api/rules'),
  getRule: (id) => api.get(`/api/rules/${id}`),
  createRule: (data) => api.post('/api/rules', data),
  updateRule: (id, data) => api.put(`/api/rules/${id}`, data),
  deleteRule: (id) => api.delete(`/api/rules/${id}`),

  // Assignments
  getAssignments: () => api.get('/api/assignments'),
  createAssignment: (data) => api.post('/api/assignments', data),
  updateAssignment: (id, data) => api.put(`/api/assignments/${id}`, data),
  deleteAssignment: (id) => api.delete(`/api/assignments/${id}`),

  // Results
  getResults: (params) => api.get('/api/results', { params }),
  getResult: (id) => api.get(`/api/results/${id}`),

  // Data Sources
  getSources: () => api.get('/api/sources'),
  createSource: (data) => api.post('/api/sources', data),
  testSource: (id) => api.post(`/api/sources/${id}/test`),

  // Execution
  executeValidation: (data) => api.post('/api/execute', data),

  // Batch Import
  batchImport: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/batch-import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Dashboard
  getStats: () => api.get('/api/dashboard/stats'),
};
