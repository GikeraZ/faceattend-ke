import React, { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../services/auth'
import api from '../services/api'
import FaceScanner from '../components/FaceScanner'

export default function StudentDashboard() {
  const { user, logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  
  // State for attendance
  const [unitCode, setUnitCode] = useState('CS301')
  const [yearOfStudy, setYearOfStudy] = useState('1')
  const [courseProgram, setCourseProgram] = useState('')
  const [attendMessage, setAttendMessage] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [isEnrolled, setIsEnrolled] = useState(false)
  const [studentInfo, setStudentInfo] = useState(null)
  
  // Check if user has enrolled face and load student info
  useEffect(() => {
    if (user) {
      setIsEnrolled(!!user.face_enrolled)
      setYearOfStudy(user.year_of_study || '1')
      setCourseProgram(user.course_program || '')
    }
    loadStudentInfo()
    loadAttendanceHistory()
  }, [user])
  
  const loadStudentInfo = async () => {
    try {
      const response = await api.get('/auth/me')
      setStudentInfo(response.data)
      if (response.data) {
        setYearOfStudy(response.data.year_of_study || '1')
        setCourseProgram(response.data.course_program || '')
      }
    } catch (error) {
      console.error('Failed to load student info:', error)
    }
  }
  
  const loadAttendanceHistory = async () => {
    try {
      setLoadingHistory(true)
      const response = await api.get('/attendance/history')
      setHistory(response.data.records || [])
    } catch (error) {
      console.error('Failed to load history:', error)
      setHistory([])
    } finally {
      setLoadingHistory(false)
    }
  }
  
  // Handle face enrollment
  const handleEnroll = useCallback(async (photoBlob) => {
    try {
      setAttendMessage({ type: 'info', text: 'Processing face...' })
      
      const imageFile = new File([photoBlob], 'enrollment.jpg', { type: 'image/jpeg' })
      const formData = new FormData()
      formData.append('photo', imageFile)
      
      const response = await api.post('/face/enroll', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      setAttendMessage({ type: 'success', text: response.data.message })
      setIsEnrolled(true)
      
      // Update localStorage
      const stored = localStorage.getItem('user')
      if (stored) {
        const userData = JSON.parse(stored)
        userData.face_enrolled = true
        localStorage.setItem('user', JSON.stringify(userData))
      }
      
      setTimeout(() => setAttendMessage(null), 3000)
      
    } catch (error) {
      console.error('Enrollment error:', error)
      const errorMsg = error.response?.data?.error || 'Enrollment failed. Please try again.'
      setAttendMessage({ type: 'error', text: errorMsg })
      setTimeout(() => setAttendMessage(null), 5000)
    }
  }, [])
  
  // Handle attendance marking
  const handleAttend = useCallback(async (photoBlob) => {
    if (!unitCode.trim()) {
      setAttendMessage({ type: 'error', text: 'Please enter a unit code' })
      return
    }
    
    try {
      setAttendMessage({ type: 'info', text: 'Recognizing face...' })
      
      const imageFile = new File([photoBlob], 'attendance.jpg', { type: 'image/jpeg' })
      const formData = new FormData()
      formData.append('photo', imageFile)
      formData.append('unit_code', unitCode)
      formData.append('year_of_study', yearOfStudy)
      formData.append('course_program', courseProgram || '')
      
      const response = await api.post('/face/recognize', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      if (response.data.status === 'success') {
        setAttendMessage({ type: 'success', text: response.data.message })
        await loadAttendanceHistory()
      } else if (response.data.status === 'already_marked') {
        setAttendMessage({ type: 'info', text: response.data.message })
        await loadAttendanceHistory()
      } else {
        setAttendMessage({ type: 'error', text: response.data.message || 'Face not recognized' })
      }
      
      setTimeout(() => setAttendMessage(null), 4000)
      
    } catch (error) {
      console.error('Attendance error:', error)
      let errorMsg = 'Recognition failed. Please try again.'
      
      if (error.response) {
        errorMsg = error.response.data?.message || error.response.data?.error || errorMsg
      } else if (error.request) {
        errorMsg = 'Cannot connect to server. Please ensure backend is running.'
      }
      
      setAttendMessage({ type: 'error', text: errorMsg })
      setTimeout(() => setAttendMessage(null), 5000)
    }
  }, [unitCode, yearOfStudy, courseProgram])
  
  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout error:', error)
      navigate('/login')
    }
  }
  
  const formatDate = (timestamp) => {
    if (!timestamp) return 'N/A'
    return new Date(timestamp).toLocaleString('en-KE', {
      timeZone: 'Africa/Nairobi',
      dateStyle: 'medium',
      timeStyle: 'short'
    })
  }
  
  if (!isAuthenticated) {
    return (
      <div className="container" style={{ paddingTop: '4rem', textAlign: 'center' }}>
        <div className="card"><p className="loading">Loading...</p></div>
      </div>
    )
  }
  
  return (
    <div>
      {/* Navigation Bar */}
      <nav className="navbar">
        <a href="/dashboard" className="nav-brand">🎓 FaceAttend-KE</a>
        <div className="nav-user">
          <span>{user?.full_name || 'User'}</span>
          <button onClick={handleLogout} className="btn btn-sm btn-outline">Logout</button>
        </div>
      </nav>
      
      {/* Main Content */}
      <div className="container" style={{ paddingTop: '1rem' }}>
        <div className="dashboard-grid">
          
          {/* Face Enrollment Card */}
          <div className="card">
            <h2>📷 Face Enrollment</h2>
            <p className="hint">
              {isEnrolled 
                ? '✅ Your face is enrolled. You can now mark attendance.' 
                : 'Capture your face to enable attendance marking'}
            </p>
            
            {!isEnrolled && (
              <FaceScanner onCapture={handleEnroll} disabled={isEnrolled} label="Enroll Face" />
            )}
            
            {isEnrolled && (
              <div className="message success">✅ Face enrolled successfully!</div>
            )}
          </div>
          
          {/* Attendance Marking Card */}
          <div className="card">
            <h2>✅ Mark Attendance</h2>
            
            {/* Student Info Display */}
            {studentInfo && (
              <div className="card" style={{ background: '#f0f9ff', border: '1px solid #bae6fd', marginBottom: '1rem' }}>
                <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem' }}>
                  <div>
                    <small style={{ color: '#666' }}>Student</small>
                    <p style={{ fontWeight: '500', margin: 0 }}>{studentInfo.full_name}</p>
                  </div>
                  <div>
                    <small style={{ color: '#666' }}>Reg. Number</small>
                    <p style={{ fontWeight: '500', margin: 0 }}>{studentInfo.reg_number}</p>
                  </div>
                  <div>
                    <small style={{ color: '#666' }}>Program</small>
                    <p style={{ fontWeight: '500', margin: 0 }}>{studentInfo.course_program || 'N/A'}</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Year of Study */}
            <div className="form-group">
              <label>Year of Study</label>
              <select
                value={yearOfStudy}
                onChange={(e) => setYearOfStudy(e.target.value)}
                style={{ width: '100%', padding: '0.75rem', border: '2px solid #e5e7eb', borderRadius: '8px' }}
              >
                <option value="1">Year 1</option>
                <option value="2">Year 2</option>
                <option value="3">Year 3</option>
                <option value="4">Year 4</option>
                <option value="5">Year 5</option>
              </select>
            </div>
            
            {/* Course Program */}
            <div className="form-group">
              <label>Course/Program</label>
              <input
                type="text"
                value={courseProgram}
                onChange={(e) => setCourseProgram(e.target.value)}
                placeholder="e.g., Computer Science"
                style={{ width: '100%', padding: '0.75rem', border: '2px solid #e5e7eb', borderRadius: '8px', background: '#f9fafb' }}
              />
            </div>
            
            {/* Unit Code */}
            <div className="form-group">
              <label>Unit Code *</label>
              <input
                type="text"
                value={unitCode}
                onChange={(e) => setUnitCode(e.target.value.toUpperCase())}
                placeholder="e.g., CS304"
                pattern="[A-Z0-9]+"
                maxLength={20}
                style={{ width: '100%', padding: '0.75rem', border: '2px solid #e5e7eb', borderRadius: '8px' }}
              />
              <small style={{ color: '#666' }}>Enter the unit code for today's class (e.g., CS304, IT201)</small>
            </div>
            
            <FaceScanner onCapture={handleAttend} label="Mark Attendance" />
          </div>
          
          {/* Status Message */}
          {attendMessage && (
            <div className={`message ${attendMessage.type}`}>{attendMessage.text}</div>
          )}
          
          {/* Attendance History */}
          <div className="card full-width">
            <div className="flex justify-between items-center">
              <h2>📋 Attendance History</h2>
              <button onClick={loadAttendanceHistory} className="btn btn-sm btn-outline" disabled={loadingHistory}>
                {loadingHistory ? '⏳' : '🔄'} Refresh
              </button>
            </div>
            
            {loadingHistory ? (
              <p className="text-center loading">Loading attendance records...</p>
            ) : history.length === 0 ? (
              <p className="text-center" style={{ color: '#666', padding: '2rem' }}>
                No attendance records yet. Mark your first attendance above! 👆
              </p>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Unit Code</th>
                      <th>Year</th>
                      <th>Program</th>
                      <th>Date & Time</th>
                      <th>Confidence</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((record, index) => (
                      <tr key={record.id || index}>
                        <td><strong>{record.unit_code || record.course?.code || 'N/A'}</strong></td>
                        <td>{record.year_of_study || 'N/A'}</td>
                        <td>{record.course_program || record.course?.department || 'N/A'}</td>
                        <td>{formatDate(record.timestamp)}</td>
                        <td>
                          {record.confidence ? 
                            <span style={{ color: record.confidence > 0.8 ? '#10b981' : '#f59e0b', fontWeight: '500' }}>
                              {(record.confidence * 100).toFixed(1)}%
                            </span> : 'N/A'}
                        </td>
                        <td>
                          <span className={`status-badge ${record.status || 'present'}`}>{record.status || 'present'}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          
        </div>
      </div>
    </div>
  )
}