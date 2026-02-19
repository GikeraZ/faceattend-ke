import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../services/auth'
import api from '../services/api'

export default function Register() {
  const [form, setForm] = useState({
    reg_number: '',
    email: '',
    password: '',
    full_name: '',
    phone: '',
    year_of_study: '1',
    course_program: '',
    role: 'student',
    consent: {
      biometric_processing: false,
      data_storage: false,
      purpose_limitation: false
    }
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const navigate = useNavigate()
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    // Validate all required fields
    if (!form.full_name || !form.reg_number || !form.email || !form.password || !form.course_program) {
      setError('All required fields must be filled')
      return
    }
    
    // Validate consent
    const { consent } = form
    if (!consent.biometric_processing || !consent.data_storage) {
      setError('You must consent to biometric processing and data storage')
      return
    }
    
    // Validate password strength
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    
    setLoading(true)
    
    try {
      const response = await api.post('/auth/register', {
        reg_number: form.reg_number,
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        phone: form.phone,
        year_of_study: form.role === 'student' ? form.year_of_study : null,
        course_program: form.course_program,
        role: form.role,
        consent: form.consent
      })
      
      alert(response.data.message || 'Registration successful! Please login.')
      navigate('/login')
      
    } catch (err) {
      console.error('Registration error:', err)
      
      if (err.response) {
        const details = err.response.data?.details
        if (details) {
          const messages = Object.values(details).join('\n')
          setError(messages)
        } else {
          setError(err.response.data?.error || 'Registration failed')
        }
      } else if (err.request) {
        setError('Cannot connect to server. Please ensure backend is running.')
      } else {
        setError('Registration failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    if (name.startsWith('consent.')) {
      const field = name.split('.')[1]
      setForm(prev => ({
        ...prev,
        consent: { ...prev.consent, [field]: checked }
      }))
    } else {
      setForm(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }))
    }
  }
  
  return (
    <div className="container" style={{ paddingTop: '2rem' }}>
      <div className="card" style={{ maxWidth: '600px', margin: '0 auto' }}>
        <h1>📝 Registration</h1>
        <p style={{ color: '#666', marginBottom: '1.5rem' }}>
          Create your account to access FaceAttend-KE
        </p>
        
        <form onSubmit={handleSubmit}>
          {/* Account Type Section */}
          <div className="card" style={{ background: '#f0f9ff', border: '1px solid #bae6fd', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#0369a1' }}>👤 Account Type</h3>
            
            <div className="form-group">
              <label>Role *</label>
              <select
                name="role"
                value={form.role}
                onChange={handleChange}
                required
                disabled={loading}
                style={{ width: '100%', padding: '0.75rem', border: '2px solid #e5e7eb', borderRadius: '8px' }}
              >
                <option value="student">👨‍🎓 Student</option>
                <option value="instructor">👨‍🏫 Lecturer/Instructor</option>
                <option value="admin">⚙️ Administrator (Contact IT)</option>
              </select>
              <small style={{ color: '#666' }}>
                {form.role === 'student' && 'Select this if you are a student'}
                {form.role === 'instructor' && 'Select this if you are a lecturer or instructor'}
                {form.role === 'admin' && 'Admin accounts must be created by IT department'}
              </small>
            </div>
          </div>
          
          {/* Personal Information Section */}
          <div className="card" style={{ background: '#f9fafb', border: '1px solid #e5e7eb', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#667eea' }}>👤 Personal Information</h3>
            
            <div className="form-group">
              <label>Full Name *</label>
              <input
                type="text"
                name="full_name"
                value={form.full_name}
                onChange={handleChange}
                placeholder="e.g., John Doe"
                required
                disabled={loading}
              />
            </div>
            
            <div className="form-group">
              <label>Email *</label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="e.g., john@university.ac.ke"
                required
                disabled={loading}
              />
            </div>
            
            <div className="form-group">
              <label>Phone (Optional)</label>
              <input
                type="tel"
                name="phone"
                value={form.phone}
                onChange={handleChange}
                placeholder="+254712345678"
                pattern="\+254\d{9}"
                disabled={loading}
              />
            </div>
          </div>
          
          {/* Academic/Professional Information Section */}
          <div className="card" style={{ background: '#f9fafb', border: '1px solid #e5e7eb', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#667eea' }}>
              {form.role === 'student' ? '🎓 Academic Information' : '💼 Professional Information'}
            </h3>
            
            <div className="form-group">
              <label>
                {form.role === 'student' ? 'Registration Number' : 'Staff/Registration Number'} *
              </label>
              <input
                type="text"
                name="reg_number"
                value={form.reg_number}
                onChange={handleChange}
                placeholder={form.role === 'student' ? 'e.g., CS-2024-00123' : 'e.g., INST-001'}
                required
                disabled={loading}
              />
              <small style={{ color: '#666' }}>
                {form.role === 'student' && 'Format: XX-YYYY-NNNNN (e.g., CS-2024-00123)'}
                {form.role === 'instructor' && 'Enter your staff ID or registration number'}
              </small>
            </div>
            
            {form.role === 'student' && (
              <div className="form-group">
                <label>Year of Study *</label>
                <select
                  name="year_of_study"
                  value={form.year_of_study}
                  onChange={handleChange}
                  required={form.role === 'student'}
                  disabled={loading}
                  style={{ width: '100%', padding: '0.75rem', border: '2px solid #e5e7eb', borderRadius: '8px' }}
                >
                  <option value="1">Year 1</option>
                  <option value="2">Year 2</option>
                  <option value="3">Year 3</option>
                  <option value="4">Year 4</option>
                  <option value="5">Year 5</option>
                </select>
              </div>
            )}
            
            <div className="form-group">
              <label>Course/Program/Department *</label>
              <select
                name="course_program"
                value={form.course_program}
                onChange={handleChange}
                required
                disabled={loading}
                style={{ width: '100%', padding: '0.75rem', border: '2px solid #e5e7eb', borderRadius: '8px' }}
              >
                <option value="">Select Program/Department</option>
                <option value="Computer Science">Computer Science</option>
                <option value="Information Technology">Information Technology</option>
                <option value="Software Engineering">Software Engineering</option>
                <option value="Cyber Security">Cyber Security</option>
                <option value="Data Science">Data Science</option>
                <option value="Business IT">Business IT</option>
                <option value="Computer Engineering">Computer Engineering</option>
                <option value="Administration">Administration</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
          
          {/* Password Section */}
          <div className="form-group">
            <label>Password *</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              minLength="8"
              placeholder="Min 8 characters"
              required
              disabled={loading}
            />
            <small style={{ color: '#666' }}>
              Min 8 chars, include uppercase, lowercase, and number
            </small>
          </div>
          
          {/* Consent Section */}
          <div className="card" style={{ background: '#f0f9ff', border: '1px solid #bae6fd', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: '#0369a1' }}>🔐 Data Protection Consent</h3>
            
            <div className="checkbox-group mb-4">
              <input
                type="checkbox"
                id="consent_biometric"
                name="consent.biometric_processing"
                checked={form.consent.biometric_processing}
                onChange={handleChange}
                required
                disabled={loading}
              />
              <label htmlFor="consent_biometric">
                I consent to facial biometric processing for attendance verification
              </label>
            </div>
            
            <div className="checkbox-group mb-4">
              <input
                type="checkbox"
                id="consent_storage"
                name="consent.data_storage"
                checked={form.consent.data_storage}
                onChange={handleChange}
                required
                disabled={loading}
              />
              <label htmlFor="consent_storage">
                I consent to my data being stored on Kenya-hosted servers
              </label>
            </div>
            
            <div className="checkbox-group">
              <input
                type="checkbox"
                id="consent_purpose"
                name="consent.purpose_limitation"
                checked={form.consent.purpose_limitation}
                onChange={handleChange}
                required
                disabled={loading}
              />
              <label htmlFor="consent_purpose">
                I understand my data will only be used for attendance purposes
              </label>
            </div>
          </div>
          
          {error && <div className="message error">{error}</div>}
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', padding: '1rem', fontSize: '1.1rem' }}
            disabled={loading}
          >
            {loading ? '⏳ Registering...' : `📝 Register as ${form.role === 'student' ? 'Student' : form.role === 'instructor' ? 'Lecturer' : 'Admin'}`}
          </button>
        </form>
        
        <p className="mt-4 text-center">
          Already have an account? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  )
}