import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'

export default function AdminDashboard() {
  const { user, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-slate-800">관리자 대시보드</h1>
          <button className="btn-secondary" onClick={() => { clearAuth(); navigate('/login') }}>
            로그아웃
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card cursor-pointer hover:shadow-lg transition-shadow"
               onClick={() => navigate('/admin/professors')}>
            <div className="text-3xl mb-3">👥</div>
            <h2 className="text-lg font-semibold text-slate-700">교수 계정 관리</h2>
            <p className="text-sm text-slate-500 mt-1">교수 계정을 등록·수정·삭제합니다</p>
          </div>

          <div className="card cursor-pointer hover:shadow-lg transition-shadow"
               onClick={() => navigate('/professor')}>
            <div className="text-3xl mb-3">📊</div>
            <h2 className="text-lg font-semibold text-slate-700">성적 관리</h2>
            <p className="text-sm text-slate-500 mt-1">과목별 성적을 관리합니다</p>
          </div>
        </div>
      </div>
    </div>
  )
}
