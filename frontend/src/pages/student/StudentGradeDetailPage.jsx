import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import { api } from '../../utils/api'

const TYPE_LABELS = { general: '일반', attendance: '출석', attitude: '태도' }

function ScoreBadge({ value, label }) {
  if (value == null) {
    return <span className="px-1.5 py-0.5 rounded text-xs bg-slate-100 text-slate-400">미산출</span>
  }
  return <span className="font-medium text-slate-700">{label ?? value}</span>
}

export default function StudentGradeDetailPage() {
  const { courseId } = useParams()
  const { token } = useAuthStore()
  const navigate = useNavigate()

  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get(`/api/v1/student/courses/${courseId}/scores`, { token })
      .then(setData)
      .catch((err) => setError(err.message || '성적을 불러오지 못했습니다.'))
  }, [courseId, token])

  if (error) return (
    <div>
      <button className="text-sm text-slate-500 hover:text-slate-700 mb-4"
        onClick={() => navigate('/student/courses')}>← 과목 목록</button>
      <div className="card text-center py-12 text-red-500">{error}</div>
    </div>
  )

  if (!data) return <div className="card text-center py-12 text-slate-400">불러오는 중...</div>

  const { items, total_score, grade } = data

  return (
    <div>
      <button className="text-sm text-slate-500 hover:text-slate-700 mb-4"
        onClick={() => navigate('/student/courses')}>
        ← 과목 목록
      </button>

      {/* 총점·학점 요약 카드 */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="card text-center">
          <p className="text-xs text-slate-400 mb-1">총점</p>
          {total_score != null ? (
            <p className="text-3xl font-bold text-slate-800">{total_score}<span className="text-lg font-normal text-slate-400">점</span></p>
          ) : (
            <p className="text-slate-300 mt-2">미산출</p>
          )}
        </div>
        <div className="card text-center">
          <p className="text-xs text-slate-400 mb-1">학점</p>
          {grade ? (
            <p className="text-3xl font-bold text-blue-600">{grade}</p>
          ) : (
            <p className="text-slate-300 mt-2">미산출</p>
          )}
        </div>
      </div>

      {/* 항목별 성적 테이블 */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">항목</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">유형</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">그룹</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">점수</th>
              <th className="text-center px-4 py-3 font-medium text-slate-600">기여점수</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  성적 항목이 없습니다.
                </td>
              </tr>
            )}
            {items.map((item) => {
              const isAttend = item.item_type === 'attendance'
              const scoreVal = isAttend
                ? (item.absence_count != null ? `결석 ${item.absence_count}회` : null)
                : item.raw_score

              return (
                <tr key={item.id} className={item.group_id ? 'bg-blue-50/20' : ''}>
                  <td className="px-4 py-3 font-medium text-slate-800">{item.name}</td>
                  <td className="px-4 py-3 text-slate-500">{TYPE_LABELS[item.item_type] ?? item.item_type}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {item.group_name
                      ? <span className="bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">{item.group_name}</span>
                      : <span>—</span>}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <ScoreBadge value={scoreVal} label={scoreVal} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <ScoreBadge
                      value={item.contribution}
                      label={`${item.contribution}점`}
                    />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
