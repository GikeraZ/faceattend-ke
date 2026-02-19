import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import StudentDashboard from './pages/StudentDashboard'
import InstructorDashboard from './pages/InstructorDashboard'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Student dashboard - for students, instructors, and admins */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute roles={['student', 'instructor', 'admin']}>
            <StudentDashboard />
          </ProtectedRoute>
        } 
      />
      
      {/* Instructor/Admin dashboard - ONLY for instructors and admins */}
      <Route 
        path="/instructor" 
        element={
          <ProtectedRoute roles={['instructor', 'admin']}>
            <InstructorDashboard />
          </ProtectedRoute>
        } 
      />
      
      {/* Default redirect based on role will be handled in Login component */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}

export default App