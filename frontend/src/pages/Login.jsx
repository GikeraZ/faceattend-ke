import React, { useState } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../services/auth'

export default function Login() {
  const [form, setForm] = useState({ reg_number: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [loginType, setLoginType] = useState('student') // 'student' or 'instructor'
  
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  
  const from = location.state?.from?.pathname || '/dashboard'
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      await login(form)
      // Redirect based on role will be handled by backend response
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }
  
  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }
  
  return (
    <div className="container" style={{ paddingTop: '3rem' }}>
      <div className="card" style={{ maxWidth: '450px', margin: '0 auto' }}>
        <h1 className="text-center">🎓 FaceAttend-KE</h1>
        <p className="subtitle text-center">Facial Recognition Attendance System</p>
        
        {/* Login Type Toggle */}
        <div className="card" style={{ 
          background: '#f0f9ff', 
          border: '1px solid #bae6fd', 
          marginBottom: '1.5rem',
          padding: '0.5rem'
        }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={() => setLoginType('student')}
              style={{
                flex: 1,
                padding: '0.75rem',
                border: 'none',
                borderRadius: '8px',
                background: loginType === 'student' ? '#667eea' : 'white',
                color: loginType === 'student' ? 'white' : '#667eea',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              👨‍🎓 Student
            </button>
            <button
              type="button"
              onClick={() => setLoginType('instructor')}
              style={{
                flex: 1,
                padding: '0.75rem',
                border: 'none',
                borderRadius: '8px',
                background: loginType === 'instructor' ? '#667eea' : 'white',
                color: loginType === 'instructor' ? 'white' : '#667eea',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              👨‍🏫 Lecturer
            </button>
          </div>
        </div>
        
        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="reg_number">
              {loginType === 'student' ? 'Registration Number' : 'Staff/Registration Number'}
            </label>
            <input
              type="text"
              id="reg_number"
              name="reg_number"
              value={form.reg_number}
              onChange={handleChange}
              placeholder={
                loginType === 'student' 
                  ? 'e.g., CS-2024-00123' 
                  : 'e.g., INST-001 or email'
              }
              // ✅ No pattern restriction - accepts any format
              required
              disabled={loading}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '1rem'
              }}
            />
            {loginType === 'student' && (
              <small style={{ color: '#666' }}>
                Enter your student registration number
              </small>
            )}
            {loginType === 'instructor' && (
              <small style={{ color: '#666' }}>
                Enter your staff ID or email address
              </small>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
              disabled={loading}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '1rem'
              }}
            />
          </div>
          
          {error && <div className="message error">{error}</div>}
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ 
              width: '100%', 
              padding: '1rem',
              fontSize: '1.1rem',
              fontWeight: '600'
            }}
            disabled={loading}
          >
            {loading 
              ? '⏳ Logging in...' 
              : loginType === 'student' 
                ? '👨‍🎓 Student Login' 
                : '👨‍🏫 Lecturer Login'
            }
          </button>
        </form>
        
        {/* Footer Links */}
        <div style={{ 
          marginTop: '1.5rem', 
          paddingTop: '1.5rem', 
          borderTop: '1px solid #e5e7eb',
          textAlign: 'center'
        }}>
          {loginType === 'student' ? (
            <>
              <p style={{ color: '#666', marginBottom: '0.5rem' }}>
                New student? 
                <Link to="/register" style={{ color: '#667eea', fontWeight: '500' }}> Register here</Link>
              </p>
              <p style={{ fontSize: '0.9rem', color: '#999' }}>
                Are you a lecturer? 
                <button 
                  onClick={() => setLoginType('instructor')}
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    color: '#667eea', 
                    fontWeight: '500',
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  Switch to Lecturer Login
                </button>
              </p>
            </>
          ) : (
            <>
              <p style={{ color: '#666', marginBottom: '0.5rem' }}>
                Need a lecturer account? 
                <span style={{ color: '#999' }}> Contact administration</span>
              </p>
              <p style={{ fontSize: '0.9rem', color: '#999' }}>
                Are you a student? 
                <button 
                  onClick={() => setLoginType('student')}
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    color: '#667eea', 
                    fontWeight: '500',
                    cursor: 'pointer',
                    textDecoration: 'underline'
                  }}
                >
                  Switch to Student Login
                </button>
              </p>
            </>
          )}
        </div>
        
        {/* Demo Credentials */}
        <div className="card" style={{ 
          background: '#fef3c7', 
          border: '1px solid #fcd34d',
          marginTop: '1.5rem',
          padding: '1rem'
        }}>
          <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.95rem', color: '#92400e' }}>
            🔑 Demo Credentials
          </h4>
          {loginType === 'student' ? (
            <div style={{ fontSize: '0.85rem', color: '#78350f' }}>
              <p style={{ margin: '0.25rem 0' }}>
                <strong>Student:</strong> CS-2024-001 / student123
              </p>
            </div>
          ) : (
            <div style={{ fontSize: '0.85rem', color: '#78350f' }}>
              <p style={{ margin: '0.25rem 0' }}>
                <strong>Lecturer:</strong> INST-001 / lecturer123
              </p>
              <p style={{ margin: '0.25rem 0' }}>
                <strong>Admin:</strong> admin@uni.ac.ke / admin123
              </p>
            </div>
          )}
        </div>
        
      </div>
    </div>
  )
}