import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import StudentCoursePage from './StudentCoursePage'
import StudentGradeDetailPage from './StudentGradeDetailPage'

export default function StudentDashboard() {
  const { clearAuth, user } = useAuthStore()
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-lg font-bold text-slate-800">SmartGrader</h1>
          {user?.login_id && (
            <p className="text-xs text-slate-400">{user.login_id}</p>
          )}
        </div>
        <button
          className="btn-secondary text-sm"
          onClick={() => { clearAuth(); navigate('/login') }}
        >
          로그아웃
        </button>
      </header>

      <main className="p-8 max-w-4xl mx-auto">
        <Routes>
          <Route index element={<Navigate to="courses" replace />} />
          <Route path="courses" element={<StudentCoursePage />} />
          <Route path="courses/:courseId" element={<StudentGradeDetailPage />} />
        </Routes>
      </main>
    </div>
  )
}
