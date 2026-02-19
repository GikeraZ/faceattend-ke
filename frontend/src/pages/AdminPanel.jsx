import React, { useState, useEffect } from 'react'
import { useAuth } from '../services/auth'
import api from '../services/api'

export default function AdminPanel() {
  const { user, logout } = useAuth()
  const [students, setStudents] = useState([])
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load students
        const studentsRes = await api.get('/admin/students')
        setStudents(studentsRes.data)
        
        // Load recent audit logs
        const logsRes = await api.get('/compliance/audit-logs?per_page=10')
        setAuditLogs(logsRes.data.logs || [])
      } catch (error) {
        console.error('Admin load error:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])
  
  const handleDataRequest = async (userId, requestType) => {
    try {
      await api.post('/compliance/data-request', {
        user_id: userId,
        type: requestType
      })
      alert('Data request submitted successfully')
    } catch (error) {
      alert('Failed to submit request: ' + error.message)
    }
  }
  
  if (loading) {
    return <div className="container"><p>Loading admin panel...</p></div>
  }
  
  return (
    <div>
      <nav className="navbar">
        <a href="/admin" className="nav-brand">⚙️ Admin Panel</a>
        <div className="nav-user">
          <span>{user?.full_name} (Admin)</span>
          <button onClick={logout} className="btn btn-sm btn-outline">Logout</button>
        </div>
      </nav>
      
      <div className="container" style={{ paddingTop: '1rem' }}>
        
        {/* Student Management */}
        <div className="card">
          <h2>👥 Student Management</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Reg. Number</th>
                  <th>Face Enrolled</th>
                  <th>Consent</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {students.map(student => (
                  <tr key={student.id}>
                    <td>{student.full_name}</td>
                    <td>{student.reg_number}</td>
                    <td>{student.face_enrolled ? '✅' : '❌'}</td>
                    <td>{student.consent ? '✅' : '❌'}</td>
                    <td>
                      <div className="btn-group">
                        <button 
                          className="btn btn-sm btn-outline"
                          onClick={() => handleDataRequest(student.id, 'access')}
                        >
                          🔍 View Data
                        </button>
                        <button 
                          className="btn btn-sm btn-outline"
                          onClick={() => handleDataRequest(student.id, 'erasure')}
                        >
                          🗑️ Request Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Audit Logs */}
        <div className="card">
          <h2>🔍 Recent Audit Logs</h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Action</th>
                  <th>User</th>
                  <th>IP Address</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map(log => (
                  <tr key={log.id}>
                    <td>
                      {new Date(log.timestamp).toLocaleString('en-KE', {
                        timeZone: 'Africa/Nairobi',
                        dateStyle: 'short',
                        timeStyle: 'short'
                      })}
                    </td>
                    <td>{log.action}</td>
                    <td>{log.actor}</td>
                    <td>{log.ip}</td>
                    <td>
                      <span className={`badge ${log.status >= 400 ? 'error' : 'success'}`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="btn btn-outline mt-4">
            View All Logs →
          </button>
        </div>
        
        {/* System Status */}
        <div className="card">
          <h2>🔧 System Status</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div className="card" style={{ background: '#f0fdf4', border: '1px solid #86efac' }}>
              <strong>✅ API</strong>
              <p>Operational</p>
            </div>
            <div className="card" style={{ background: '#f0fdf4', border: '1px solid #86efac' }}>
              <strong>✅ Database</strong>
              <p>Connected</p>
            </div>
            <div className="card" style={{ background: '#f0fdf4', border: '1px solid #86efac' }}>
              <strong>✅ Face Engine</strong>
              <p>Ready</p>
            </div>
          </div>
        </div>
        
      </div>
    </div>
  )
}