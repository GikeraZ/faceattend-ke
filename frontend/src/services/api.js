/**
 * API client with auth handling
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30000 // 30 seconds for face recognition
})

// Request interceptor: add auth token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Helper for multipart/form-data uploads
export const uploadFile = (endpoint, file, additionalData = {}) => {
  const formData = new FormData()
  formData.append('photo', file)
  
  Object.entries(additionalData).forEach(([key, value]) => {
    formData.append(key, value)
  })
  
  return api.post(endpoint, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export default api