import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import PrivateRoute from './router/PrivateRoute'
import WakeUpToast from './components/common/WakeUpToast'
import { setWakeUpCallbacks } from './utils/api'

// Pages
import LoginPage from './pages/LoginPage'
import AdminDashboard from './pages/admin/AdminDashboard'
import ProfessorManagePage from './pages/admin/ProfessorManagePage'
import ProfessorDashboard from './pages/professor/ProfessorDashboard'
import StudentDashboard from './pages/student/StudentDashboard'

export default function App() {
  const [wakingUp, setWakingUp] = useState(false)

  useEffect(() => {
    setWakeUpCallbacks(
      () => setWakingUp(true),
      () => setWakingUp(false),
    )
  }, [])

  return (
    <BrowserRouter>
      <WakeUpToast visible={wakingUp} />
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* 관리자 전용 */}
        <Route path="/admin" element={
          <PrivateRoute allowedRoles={['admin']}>
            <AdminDashboard />
          </PrivateRoute>
        } />
        <Route path="/admin/professors" element={
          <PrivateRoute allowedRoles={['admin']}>
            <ProfessorManagePage />
          </PrivateRoute>
        } />

        {/* 교수/관리자 공용 */}
        <Route path="/professor/*" element={
          <PrivateRoute allowedRoles={['professor', 'admin']}>
            <ProfessorDashboard />
          </PrivateRoute>
        } />

        {/* 학생 전용 */}
        <Route path="/student/*" element={
          <PrivateRoute allowedRoles={['student']}>
            <StudentDashboard />
          </PrivateRoute>
        } />

        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
