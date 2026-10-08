import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('heartguard_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('heartguard_token')
      const path = window.location.pathname
      if (!path.startsWith('/login') && !path.startsWith('/register')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export const api = {
  auth: {
    login: (email, password) => apiClient.post('/auth/login', { email, password }),
    register: (data) => apiClient.post('/auth/register', data),
    getMe: () => apiClient.get('/auth/me'),
  },

  assessments: {
    create: (data) => apiClient.post('/assessments', data),
    getAll: (params) => apiClient.get('/assessments', { params }),
    getById: (id) => apiClient.get(`/assessments/${id}`),
    getLatest: () => apiClient.get('/assessments/latest'),
  },

  dashboard: {
    getDashboard: () => apiClient.get('/dashboard'),
  },

  reviews: {
    getQueue: (params) => apiClient.get('/reviews/queue', { params }),
    getPending: () => apiClient.get('/reviews/pending'),
    create: (assessmentId, data) => apiClient.post(`/reviews/${assessmentId}`, data),
    update: (id, data) => apiClient.put(`/reviews/${id}`, data),
    getStats: () => apiClient.get('/reviews/stats'),
  },

  admin: {
    getAnalytics: () => apiClient.get('/admin/analytics'),
    getModelStatus: () => apiClient.get('/admin/model/status'),
    getDrift: () => apiClient.get('/admin/model/drift'),
    getDataQuality: () => apiClient.get('/admin/data-quality'),
    getPerformance: () => apiClient.get('/admin/model/performance'),
    getHealth: () => apiClient.get('/admin/health'),
    getAuditLogs: (params) => apiClient.get('/admin/audit-logs', { params }),
    getAuditStats: () => apiClient.get('/admin/audit-stats'),
    getUsers: (params) => apiClient.get('/admin/users', { params }),
  },

  recommendations: {
    getByAssessment: (assessmentId) => apiClient.get(`/recommendations/assessment/${assessmentId}`),
    getAll: () => apiClient.get('/recommendations'),
  },

  reports: {
    getAll: () => apiClient.get('/reports'),
    generate: (assessmentId) => apiClient.post(`/reports/generate/${assessmentId}`),
    download: (reportId) => apiClient.get(`/reports/${reportId}/download`, { responseType: 'blob' }),
  },

  security: {
    getAuditLogs: (params) => apiClient.get('/security/audit-logs', { params }),
  },

  health: {
    check: () => apiClient.get('/health'),
  },

  lifestyle: {
    analyze: (data) => apiClient.post('/lifestyle/analyze', typeof data === 'string' ? { text: data } : data),
  },
}

export default api
