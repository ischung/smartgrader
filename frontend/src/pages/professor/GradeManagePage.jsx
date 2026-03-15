import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import { api } from '../../utils/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const DEFAULT_POLICY = [
  { grade: 'A+', min_score: 95, max_score: 100 },
  { grade: 'A0', min_score: 90, max_score: 94.99 },
  { grade: 'B+', min_score: 85, max_score: 89.99 },
  { grade: 'B0', min_score: 80, max_score: 84.99 },
  { grade: 'C+', min_score: 75, max_score: 79.99 },
  { grade: 'C0', min_score: 70, max_score: 74.99 },
  { grade: 'D+', min_score: 65, max_score: 69.99 },
  { grade: 'D0', min_score: 60, max_score: 64.99 },
  { grade: 'F',  min_score: 0,  max_score: 59.99 },
]

// ── Toast ──────────────────────────────────────────────────────────────────
function Toast({ message, type, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000)
    return () => clearTimeout(t)
  }, [onClose])
  return (
    <div className={`fixed bottom-6 right-6 z-50 text-white text-sm px-5 py-3 rounded-xl shadow-lg max-w-sm
      ${type === 'error' ? 'bg-red-600' : 'bg-slate-800'}`}>
      {message}
    </div>
  )
}

// ── InlineCell ─────────────────────────────────────────────────────────────
function InlineCell({ value, onSave, disabled }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value ?? '')
  const inputRef = useRef(null)

  useEffect(() => {
    if (editing) inputRef.current?.focus()
  }, [editing])

  const commit = () => {
    setEditing(false)
    const num = draft === '' ? null : Number(draft)
    if (num !== value) onSave(num)
  }

  if (disabled) {
    return <td className="px-3 py-2 text-center text-slate-300 text-xs">—</td>
  }

  if (editing) {
    return (
      <td className="px-1 py-1">
        <input
          ref={inputRef}
          type="number"
          min="0"
          className="w-16 text-center border border-blue-400 rounded px-1 py-0.5 text-sm focus:outline-none"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => { if (e.key === 'Enter') commit() }}
        />
      </td>
    )
  }

  return (
    <td
      className="px-3 py-2 text-center cursor-pointer hover:bg-blue-50 text-slate-700 text-sm"
      onClick={() => { setDraft(value ?? ''); setEditing(true) }}
    >
      {value ?? <span className="text-slate-300">—</span>}
    </td>
  )
}

// ── ScoreTab ──────────────────────────────────────────────────────────────
function ScoreTab({ courseId, token, showToast }) {
  const [table, setTable] = useState(null)
  const [results, setResults] = useState({})  // student_id → {total_score, grade}
  const [calculating, setCalculating] = useState(false)
  const [gradingCalc, setGradingCalc] = useState(false)

  const fetchTable = useCallback(async () => {
    try {
      const data = await api.get(`/api/v1/courses/${courseId}/scores`, { token })
      setTable(data)
    } catch {
      showToast('성적표를 불러오지 못했습니다.', 'error')
    }
  }, [courseId, token, showToast])

  useEffect(() => { fetchTable() }, [fetchTable])

  const saveScore = async (studentId, itemId, itemType, rawScore) => {
    const body = { student_id: studentId, grade_item_id: itemId }
    if (itemType === 'attendance') {
      body.absence_count = rawScore
    } else {
      body.raw_score = rawScore
    }
    try {
      await api.patch(`/api/v1/courses/${courseId}/scores`, body, { token })
    } catch (err) {
      showToast(err.message || '저장에 실패했습니다.', 'error')
    }
  }

  const calculateTotal = async () => {
    setCalculating(true)
    try {
      const data = await api.post(`/api/v1/courses/${courseId}/scores/calculate`, {}, { token })
      const map = {}
      data.forEach((r) => { map[r.student_id] = { total_score: r.total_score, grade: null } })
      setResults(map)
      showToast('총점이 계산되었습니다.')
    } catch (err) {
      showToast(err.message || '총점 계산에 실패했습니다.', 'error')
    } finally {
      setCalculating(false)
    }
  }

  const calculateGrades = async () => {
    setGradingCalc(true)
    try {
      const data = await api.post(`/api/v1/courses/${courseId}/grades/calculate`, {}, { token })
      const map = {}
      data.forEach((r) => { map[r.student_id] = { total_score: r.total_score, grade: r.grade } })
      setResults(map)
      showToast('학점이 계산되었습니다.')
    } catch (err) {
      showToast(err.message || '학점 계산에 실패했습니다. 먼저 총점 계산 및 학점 정책을 설정하세요.', 'error')
    } finally {
      setGradingCalc(false)
    }
  }

  if (!table) return <div className="text-center py-12 text-slate-400">불러오는 중...</div>

  const { items, students } = table
  const hasTotal = Object.keys(results).length > 0
  const hasGrade = hasTotal && Object.values(results).some((r) => r.grade)

  return (
    <div>
      <div className="flex gap-3 mb-4">
        <button className="btn-primary text-sm" onClick={calculateTotal} disabled={calculating}>
          {calculating ? '계산 중...' : '총점 계산'}
        </button>
        <button className="btn-secondary text-sm" onClick={calculateGrades} disabled={gradingCalc}>
          {gradingCalc ? '계산 중...' : '학점 계산'}
        </button>
      </div>

      <div className="card p-0 overflow-x-auto">
        <table className="text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-3 py-2 font-medium text-slate-600 whitespace-nowrap sticky left-0 bg-slate-50">학번</th>
              <th className="text-left px-3 py-2 font-medium text-slate-600 whitespace-nowrap">이름</th>
              {items.map((item) => (
                <th key={item.id} className="px-3 py-2 font-medium text-slate-600 whitespace-nowrap text-center">
                  {item.name}
                  <span className="block text-xs font-normal text-slate-400">{item.weight != null ? `${item.weight}%` : '그룹'}</span>
                </th>
              ))}
              {hasTotal && (
                <th className="px-3 py-2 font-medium text-blue-600 whitespace-nowrap text-center bg-blue-50">총점</th>
              )}
              {hasGrade && (
                <th className="px-3 py-2 font-medium text-blue-600 whitespace-nowrap text-center bg-blue-50">학점</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {students.length === 0 && (
              <tr>
                <td colSpan={items.length + 2} className="px-3 py-8 text-center text-slate-400">
                  수강 학생이 없습니다. 먼저 성적 파일을 업로드하세요.
                </td>
              </tr>
            )}
            {students.map((student) => (
              <tr key={student.id} className="hover:bg-slate-50">
                <td className="px-3 py-2 text-slate-600 whitespace-nowrap sticky left-0 bg-white">{student.login_id}</td>
                <td className="px-3 py-2 text-slate-800 whitespace-nowrap font-medium">{student.name}</td>
                {items.map((item) => {
                  const cell = student.scores[item.id] || {}
                  const isAttend = item.item_type === 'attendance'
                  const val = isAttend ? cell.absence_count : cell.raw_score
                  return (
                    <InlineCell
                      key={item.id}
                      value={val}
                      onSave={(v) => saveScore(
                        student.id, item.id, item.item_type,
                        isAttend ? undefined : v,
                        isAttend ? v : undefined,
                      )}
                    />
                  )
                })}
                {hasTotal && (
                  <td className="px-3 py-2 text-center font-semibold text-blue-700 bg-blue-50 whitespace-nowrap">
                    {results[student.id]?.total_score ?? '—'}
                  </td>
                )}
                {hasGrade && (
                  <td className="px-3 py-2 text-center font-semibold text-blue-700 bg-blue-50 whitespace-nowrap">
                    {results[student.id]?.grade ?? '—'}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── PolicyTab ─────────────────────────────────────────────────────────────
function PolicyTab({ courseId, token, showToast }) {
  const [entries, setEntries] = useState(DEFAULT_POLICY)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get(`/api/v1/courses/${courseId}/policy`, { token })
      .then((data) => { if (data.length > 0) setEntries(data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [courseId, token])

  const update = (i, field) => (e) => {
    setEntries((prev) => prev.map((en, idx) =>
      idx === i ? { ...en, [field]: Number(e.target.value) } : en
    ))
  }

  const save = async () => {
    setSaving(true)
    try {
      await api.put(`/api/v1/courses/${courseId}/policy`, { entries }, { token })
      showToast('학점 정책이 저장되었습니다.')
    } catch (err) {
      showToast(err.message || '저장에 실패했습니다.', 'error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="text-center py-12 text-slate-400">불러오는 중...</div>

  return (
    <div className="max-w-lg">
      <p className="text-sm text-slate-500 mb-4">각 학점의 점수 범위를 설정하세요.</p>
      <div className="card p-0 overflow-hidden mb-4">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-4 py-2 font-medium text-slate-600">학점</th>
              <th className="text-left px-4 py-2 font-medium text-slate-600">최소 점수</th>
              <th className="text-left px-4 py-2 font-medium text-slate-600">최대 점수</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {entries.map((en, i) => (
              <tr key={en.grade}>
                <td className="px-4 py-2 font-semibold text-slate-700">{en.grade}</td>
                <td className="px-2 py-1">
                  <input
                    type="number" min="0" max="100" step="0.01"
                    className="input w-24 text-sm"
                    value={en.min_score}
                    onChange={update(i, 'min_score')}
                  />
                </td>
                <td className="px-2 py-1">
                  <input
                    type="number" min="0" max="100" step="0.01"
                    className="input w-24 text-sm"
                    value={en.max_score}
                    onChange={update(i, 'max_score')}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button className="btn-primary" onClick={save} disabled={saving}>
        {saving ? '저장 중...' : '저장'}
      </button>
    </div>
  )
}

// ── FilesTab ──────────────────────────────────────────────────────────────
function FilesTab({ courseId, token, showToast }) {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(null)

  useEffect(() => {
    api.get(`/api/v1/courses/${courseId}/files`, { token })
      .then(setFiles)
      .catch(() => showToast('파일 목록을 불러오지 못했습니다.', 'error'))
      .finally(() => setLoading(false))
  }, [courseId, token, showToast])

  const download = async (fileId) => {
    setDownloading(fileId)
    try {
      const res = await fetch(`${API_URL}/api/v1/courses/${courseId}/files/${fileId}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || `HTTP ${res.status}`)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `result_${courseId}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      showToast(err.message || '다운로드에 실패했습니다.', 'error')
    } finally {
      setDownloading(null)
    }
  }

  const FILE_TYPE_LABELS = { original: { label: '원본', color: 'bg-slate-100 text-slate-600' },
                             result:   { label: '결과', color: 'bg-blue-100 text-blue-700' } }

  if (loading) return <div className="text-center py-12 text-slate-400">불러오는 중...</div>

  return (
    <div className="max-w-2xl">
      {files.length === 0 ? (
        <div className="card text-center py-12 text-slate-400">업로드된 파일이 없습니다.</div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-2 font-medium text-slate-600">유형</th>
                <th className="text-left px-4 py-2 font-medium text-slate-600">파일 경로</th>
                <th className="text-left px-4 py-2 font-medium text-slate-600">업로드일</th>
                <th className="text-right px-4 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {files.map((f) => {
                const badge = FILE_TYPE_LABELS[f.file_type] || { label: f.file_type, color: 'bg-slate-100 text-slate-600' }
                return (
                  <tr key={f.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${badge.color}`}>
                        {badge.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs truncate max-w-xs">
                      {f.storage_path.split('/').pop()}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs whitespace-nowrap">
                      {new Date(f.created_at).toLocaleDateString('ko-KR')}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        className="btn-secondary text-xs px-3 py-1"
                        onClick={() => download(f.id)}
                        disabled={downloading === f.id}
                      >
                        {downloading === f.id ? '...' : '다운로드'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────
const TABS = [
  { id: 'scores',  label: '성적표' },
  { id: 'policy',  label: '학점 정책' },
  { id: 'files',   label: '파일' },
]

export default function GradeManagePage() {
  const { courseId } = useParams()
  const { token } = useAuthStore()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('scores')
  const [toast, setToast] = useState(null)

  const showToast = useCallback((message, type = 'success') => setToast({ message, type }), [])

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <button className="text-sm text-slate-500 hover:text-slate-700"
          onClick={() => navigate('/professor/courses')}>
          ← 과목 목록
        </button>
        <h2 className="text-2xl font-bold text-slate-800">성적 관리</h2>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 border-b border-slate-200">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`px-4 py-2 text-sm font-medium transition-colors
              ${activeTab === tab.id
                ? 'text-blue-600 border-b-2 border-blue-600 -mb-px'
                : 'text-slate-500 hover:text-slate-700'}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'scores' && (
        <ScoreTab courseId={courseId} token={token} showToast={showToast} />
      )}
      {activeTab === 'policy' && (
        <PolicyTab courseId={courseId} token={token} showToast={showToast} />
      )}
      {activeTab === 'files' && (
        <FilesTab courseId={courseId} token={token} showToast={showToast} />
      )}

      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
    </div>
  )
}
