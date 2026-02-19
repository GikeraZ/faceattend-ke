import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../services/auth'
import api from '../services/api'

export default function InstructorDashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  
  // State
  const [loading, setLoading] = useState(true)
  const [courses, setCourses] = useState([])
  const [selectedUnit, setSelectedUnit] = useState('')
  const [yearOfStudy, setYearOfStudy] = useState('')
  const [courseProgram, setCourseProgram] = useState('')
  const [attendanceData, setAttendanceData] = useState(null)
  const [loadingAttendance, setLoadingAttendance] = useState(false)
  const [message, setMessage] = useState(null)
  
  // Load instructor dashboard on mount
  useEffect(() => {
    loadInstructorDashboard()
  }, [])
  
  const loadInstructorDashboard = async () => {
    try {
      setLoading(true)
      const response = await api.get('/attendance/instructor/dashboard')
      setCourses(response.data.courses || [])
    } catch (error) {
      console.error('Failed to load dashboard:', error)
      setMessage({ type: 'error', text: 'Failed to load dashboard' })
    } finally {
      setLoading(false)
    }
  }
  
  const loadUnitAttendance = useCallback(async () => {
    if (!selectedUnit) {
      setMessage({ type: 'error', text: 'Please select a unit code' })
      return
    }
    
    try {
      setLoadingAttendance(true)
      setMessage(null)
      
      // Build query parameters
      const params = {}
      if (yearOfStudy) params.year_of_study = yearOfStudy
      if (courseProgram) params.course_program = courseProgram
      
      const response = await api.get(`/attendance/instructor/unit/${selectedUnit}`, { params })
      setAttendanceData(response.data)
      
    } catch (error) {
      console.error('Failed to load attendance:', error)
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.error || 'Failed to load attendance' 
      })
      setAttendanceData(null)
    } finally {
      setLoadingAttendance(false)
    }
  }, [selectedUnit, yearOfStudy, courseProgram])
  
  const handleExport = async () => {
    if (!selectedUnit) return
    
    try {
      const response = await api.get(`/attendance/instructor/export/${selectedUnit}`)
      
      // Create and download CSV file
      const blob = new Blob([response.data.csv], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = response.data.filename
      link.click()
      window.URL.revokeObjectURL(url)
      
      setMessage({ type: 'success', text: 'CSV exported successfully!' })
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to export CSV' })
    }
  }
  
  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }
  
  const formatDate = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString('en-KE', {
      timeZone: 'Africa/Nairobi',
      dateStyle: 'medium',
      timeStyle: 'short'
    })
  }
  
  if (loading) {
    return (
      <div className="container" style={{ paddingTop: '4rem', textAlign: 'center' }}>
        <div className="card">
          <p className="loading">Loading instructor dashboard...</p>
        </div>
      </div>
    )
  }
  
  // Check if user is instructor or admin
  if (!user || (user.role !== 'instructor' && user.role !== 'admin')) {
    return (
      <div className="container" style={{ paddingTop: '4rem' }}>
        <div className="card">
          <h2>⚠️ Access Denied</h2>
          <p>This page is for instructors and administrators only.</p>
          <button onClick={() => navigate('/dashboard')} className="btn btn-primary mt-4">
            Go to Student Dashboard
          </button>
        </div>
      </div>
    )
  }
  
  return (
    <div>
      {/* Navigation Bar */}
      <nav className="navbar">
        <a href="/instructor" className="nav-brand">👨‍🏫 Instructor Panel</a>
        <div className="nav-user">
          <span>{user?.full_name} ({user?.role === 'admin' ? 'Admin' : 'Lecturer'})</span>
          <button onClick={handleLogout} className="btn btn-sm btn-outline">Logout</button>
        </div>
      </nav>
      
      {/* Main Content */}
      <div className="container" style={{ paddingTop: '1rem' }}>
        
        {/* Welcome Card */}
        <div className="card">
          <h2>Welcome, {user?.full_name}!</h2>
          <p style={{ color: '#666' }}>
            View and manage student attendance records for your units
          </p>
        </div>
        
        {/* Units Overview */}
        <div className="card">
          <h3>📚 Your Units</h3>
          {courses.length === 0 ? (
            <p style={{ color: '#666' }}>No units assigned yet.</p>
          ) : (
            <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))' }}>
              {courses.map(course => (
                <div 
                  key={course.id}
                  onClick={() => setSelectedUnit(course.code)}
                  className={`card ${selectedUnit === course.code ? 'selected' : ''}`}
                  style={{ 
                    cursor: 'pointer',
                    border: selectedUnit === course.code ? '2px solid #667eea' : '1px solid #e5e7eb',
                    background: selectedUnit === course.code ? '#f0f9ff' : 'white'
                  }}
                >
                  <h4 style={{ color: '#667eea', margin: '0 0 0.5rem 0' }}>{course.code}</h4>
                  <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem' }}>{course.name}</p>
                  <small style={{ color: '#666' }}>{course.department}</small>
                  <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid #e5e7eb' }}>
                    <small>📊 {course.attendance_count} records</small>
                    <br />
                    <small>👥 {course.unique_students} students</small>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Filter and View Attendance */}
        <div className="card">
          <h3>🔍 View Attendance by Unit</h3>
          
          <div className="dashboard-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
  <div className="form-group">
    <label>Unit Code *</label>
    <input
      type="text"
      value={selectedUnit}
      onChange={(e) => setSelectedUnit(e.target.value.toUpperCase())}
      placeholder="e.g., CS401, IT201"
      style={{ 
        width: '100%', 
        padding: '0.75rem', 
        border: '2px solid #e5e7eb', 
        borderRadius: '8px',
        textTransform: 'uppercase',
        fontWeight: '500'
      }}
    />
    <small style={{ color: '#666' }}>
      Enter any unit code (e.g., CS401, IT201, MATH101)
    </small>
  </div>
            
            <div className="form-group">
              <label>Year of Study</label>
              <select
                value={yearOfStudy}
                onChange={(e) => setYearOfStudy(e.target.value)}
                style={{ width: '100%', padding: '0.75rem', border: '2px solid #e5e7eb', borderRadius: '8px' }}
              >
                <option value="">All Years</option>
                <option value="1">Year 1</option>
                <option value="2">Year 2</option>
                <option value="3">Year 3</option>
                <option value="4">Year 4</option>
                <option value="5">Year 5</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Course Program</label>
              <select
                value={courseProgram}
                onChange={(e) => setCourseProgram(e.target.value)}
                style={{ width: '100%', padding: '0.75rem', border: '2px solid #e5e7eb', borderRadius: '8px' }}
              >
                <option value="">All Programs</option>
                <option value="Computer Science">Computer Science</option>
                <option value="Information Technology">Information Technology</option>
                <option value="Software Engineering">Software Engineering</option>
                <option value="Cyber Security">Cyber Security</option>
                <option value="Data Science">Data Science</option>
              </select>
            </div>
          </div>
          
          <div className="btn-group" style={{ marginTop: '1rem' }}>
            <button onClick={loadUnitAttendance} className="btn btn-primary" disabled={!selectedUnit || loadingAttendance}>
              {loadingAttendance ? '⏳ Loading...' : '🔍 View Attendance'}
            </button>
            
            {attendanceData && (
              <button onClick={handleExport} className="btn btn-success">
                📥 Export CSV
              </button>
            )}
          </div>
        </div>
        
        {/* Status Message */}
        {message && (
          <div className={`message ${message.type}`}>{message.text}</div>
        )}
        
        {/* Attendance Records Table */}
        {loadingAttendance ? (
          <div className="card">
            <p className="loading">Loading attendance records...</p>
          </div>
        ) : attendanceData ? (
          <div className="card full-width">
            <div className="flex justify-between items-center">
              <h3>
                📋 {attendanceData.unit.code} - {attendanceData.unit.name}
              </h3>
              <div style={{ textAlign: 'right' }}>
                <p style={{ margin: 0, fontSize: '0.9rem', color: '#666' }}>
                  {attendanceData.summary.unique_students} students | {attendanceData.summary.total_records} records
                </p>
              </div>
            </div>
            
            {attendanceData.students.length === 0 ? (
              <p style={{ color: '#666', padding: '2rem', textAlign: 'center' }}>
                No attendance records found for this unit.
              </p>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Reg. Number</th>
                      <th>Student Name</th>
                      <th>Year</th>
                      <th>Program</th>
                      <th>Date & Time</th>
                      <th>Confidence</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attendanceData.students.map((record, index) => (
                      <tr key={record.id || index}>
                        <td><strong>{record.student.reg_number}</strong></td>
                        <td>{record.student.full_name}</td>
                        <td>{record.attendance.year_of_study || record.student.year_of_study}</td>
                        <td>{record.attendance.course_program || record.student.course_program}</td>
                        <td>{formatDate(record.attendance.timestamp)}</td>
                        <td>
                          <span style={{ 
                            color: record.attendance.confidence > 0.8 ? '#10b981' : '#f59e0b',
                            fontWeight: '500'
                          }}>
                            {(record.attendance.confidence * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td>
                          <span className={`status-badge ${record.attendance.status}`}>
                            {record.attendance.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : null}
        
      </div>
    </div>
  )
}