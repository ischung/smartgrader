import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import CourseListPage from './CourseListPage'
import GradeUploadPage from './GradeUploadPage'
import GradeItemPage from './GradeItemPage'

export default function ProfessorDashboard() {
  const { clearAuth } = useAuthStore()
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center">
        <h1 className="text-lg font-bold text-slate-800">SmartGrader</h1>
        <button
          className="btn-secondary text-sm"
          onClick={() => { clearAuth(); navigate('/login') }}
        >
          로그아웃
        </button>
      </header>

      <main className="p-8 max-w-5xl mx-auto">
        <Routes>
          <Route index element={<Navigate to="courses" replace />} />
          <Route path="courses" element={<CourseListPage />} />
          <Route path="courses/:courseId/upload" element={<GradeUploadPage />} />
          <Route path="courses/:courseId/items" element={<GradeItemPage />} />
        </Routes>
      </main>
    </div>
  )
}
