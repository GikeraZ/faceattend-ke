import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../services/auth'

export default function ProtectedRoute({ children, roles = [] }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  
  // Show loading state
  if (loading) {
    return (
      <div className="container" style={{ paddingTop: '4rem', textAlign: 'center' }}>
        <div className="card">
          <p>Loading...</p>
        </div>
      </div>
    )
  }
  
  // Redirect to login if not authenticated
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  
  // Check role authorization
  if (roles.length > 0 && !roles.includes(user.role)) {
    return (
      <div className="container" style={{ paddingTop: '4rem' }}>
        <div className="card">
          <h2>⚠️ Access Denied</h2>
          <p>You don't have permission to access this page.</p>
          <p className="mt-4">
            <a href="/dashboard" className="btn btn-primary">Go to Dashboard</a>
          </p>
        </div>
      </div>
    )
  }
  
  return children
}