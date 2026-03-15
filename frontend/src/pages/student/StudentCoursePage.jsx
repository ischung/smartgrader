import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import { api } from '../../utils/api'

const GRADE_COLORS = {
  'A+': 'bg-green-100 text-green-700',
  'A0': 'bg-green-100 text-green-600',
  'B+': 'bg-blue-100 text-blue-700',
  'B0': 'bg-blue-100 text-blue-600',
  'C+': 'bg-yellow-100 text-yellow-700',
  'C0': 'bg-yellow-100 text-yellow-600',
  'D+': 'bg-orange-100 text-orange-700',
  'D0': 'bg-orange-100 text-orange-600',
  'F':  'bg-red-100 text-red-600',
}

export default function StudentCoursePage() {
  const { token } = useAuthStore()
  const navigate = useNavigate()
  const [grouped, setGrouped] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/v1/student/courses', { token })
      .then(setGrouped)
      .catch(() => setError('수강 과목을 불러오지 못했습니다.'))
  }, [token])

  if (error) return <div className="card text-center py-12 text-red-500">{error}</div>
  if (!grouped) return <div className="card text-center py-12 text-slate-400">불러오는 중...</div>

  const semesters = Object.keys(grouped).sort().reverse()

  if (semesters.length === 0) {
    return (
      <div className="card text-center py-16 text-slate-400">
        <div className="text-4xl mb-3">📚</div>
        <p>수강 중인 과목이 없습니다.</p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-slate-800">내 수강 과목</h2>

      {semesters.map((sem) => (
        <section key={sem}>
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
            {sem}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {grouped[sem].map((course) => {
              const gradeColor = course.grade ? (GRADE_COLORS[course.grade] || 'bg-slate-100 text-slate-600') : ''
              return (
                <div
                  key={course.id}
                  className="card cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => navigate(`/student/courses/${course.id}`)}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-semibold text-slate-800">{course.course_name}</h4>
                      <p className="text-sm text-slate-500 mt-0.5">
                        {course.course_code}
                        {course.section ? ` — ${course.section}분반` : ''}
                      </p>
                    </div>
                    {course.grade ? (
                      <span className={`px-2.5 py-0.5 rounded-full text-sm font-bold ${gradeColor}`}>
                        {course.grade}
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-400">미산출</span>
                    )}
                  </div>
                  <div className="mt-4 flex items-center gap-2 text-sm text-slate-500">
                    <span>총점</span>
                    {course.total_score != null ? (
                      <span className="font-semibold text-slate-700">{course.total_score}점</span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      ))}
    </div>
  )
}
