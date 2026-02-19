import React, { createContext, useContext, useState, useEffect } from 'react'
import api from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  
  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const stored = localStorage.getItem('user')
        if (stored) {
          const response = await api.get('/auth/me')
          setUser(response.data)
        }
      } catch (error) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      } finally {
        setLoading(false)
      }
    }
    checkAuth()
  }, [])
  
  // Login with role-based redirect
  const login = async (credentials) => {
    const response = await api.post('/auth/login', credentials)
    const { user: userData, role } = response.data
    
    localStorage.setItem('user', JSON.stringify(userData))
    setUser(userData)
    
    // ✅ Redirect based on role
    if (role === 'instructor' || role === 'admin') {
      // Lecturers and admins go to instructor dashboard
      window.location.href = '/instructor'
    } else {
      // Students go to student dashboard
      window.location.href = '/dashboard'
    }
    
    return userData
  }
  
  // Register new user
  const register = async (userData) => {
    const response = await api.post('/auth/register', userData)
    return response.data
  }
  
  // Logout user
  const logout = async () => {
    await api.post('/auth/logout').catch(() => {})
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    window.location.href = '/login'
  }
  
  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  }
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}