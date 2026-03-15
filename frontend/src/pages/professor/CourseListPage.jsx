import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import { api } from '../../utils/api'

// ── Toast ──────────────────────────────────────────────────────────────────
function Toast({ message, type, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000)
    return () => clearTimeout(t)
  }, [onClose])

  return (
    <div className={`fixed bottom-6 right-6 z-50 ${type === 'error' ? 'bg-red-600' : 'bg-slate-800'} text-white text-sm px-5 py-3 rounded-xl shadow-lg`}>
      {message}
    </div>
  )
}

// ── CourseModal ────────────────────────────────────────────────────────────
function CourseModal({ course, onClose, onSaved }) {
  const { token } = useAuthStore()
  const isEdit = !!course

  const [form, setForm] = useState({
    course_name: course?.course_name ?? '',
    course_code: course?.course_code ?? '',
    section: course?.section ?? '',
    semester: course?.semester ?? '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (isEdit) {
        await api.patch(`/api/v1/courses/${course.id}`, form, { token })
      } else {
        await api.post('/api/v1/courses', form, { token })
      }
      onSaved(isEdit ? '과목 정보가 수정되었습니다.' : '과목이 등록되었습니다.')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40">
      <div className="card w-96">
        <h3 className="text-lg font-semibold text-slate-800 mb-5">
          {isEdit ? '과목 정보 수정' : '과목 등록'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          {[
            ['과목명', 'course_name', '운영체제'],
            ['교과코드', 'course_code', 'CS301'],
            ['분반', 'section', '01'],
            ['학기', 'semester', '2024-1'],
          ].map(([label, key, placeholder]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
              <input
                className="input"
                value={form[key]}
                onChange={set(key)}
                placeholder={placeholder}
                required={key !== 'section'}
              />
            </div>
          ))}
          {error && <p className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">{error}</p>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={onClose}>취소</button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? '저장 중...' : '저장'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── ConfirmDialog ──────────────────────────────────────────────────────────
function ConfirmDialog({ name, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40">
      <div className="card w-80">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">과목 삭제</h3>
        <p className="text-sm text-slate-600 mb-6">
          <span className="font-medium">{name}</span> 과목과 모든 성적 데이터가 삭제됩니다. 되돌릴 수 없습니다.
        </p>
        <div className="flex gap-3 justify-end">
          <button className="btn-secondary" onClick={onCancel}>취소</button>
          <button className="btn-danger" onClick={onConfirm}>삭제</button>
        </div>
      </div>
    </div>
  )
}

// ── Main ───────────────────────────────────────────────────────────────────
export default function CourseListPage() {
  const { token } = useAuthStore()
  const navigate = useNavigate()

  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [semesterFilter, setSemesterFilter] = useState('all')
  const [modal, setModal] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [toast, setToast] = useState(null)

  const showToast = (message, type = 'success') => setToast({ message, type })

  const fetchCourses = useCallback(async () => {
    try {
      const data = await api.get('/api/v1/courses', { token })
      setCourses(data)
    } catch {
      showToast('과목 목록을 불러오지 못했습니다.', 'error')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { fetchCourses() }, [fetchCourses])

  const handleSaved = (msg) => { setModal(null); showToast(msg); fetchCourses() }

  const handleDelete = async () => {
    try {
      await api.delete(`/api/v1/courses/${deleteTarget.id}`, { token })
      setDeleteTarget(null)
      showToast('과목이 삭제되었습니다.')
      fetchCourses()
    } catch {
      setDeleteTarget(null)
      showToast('삭제에 실패했습니다.', 'error')
    }
  }

  const semesters = [...new Set(courses.map((c) => c.semester))].sort().reverse()
  const filtered = semesterFilter === 'all'
    ? courses
    : courses.filter((c) => c.semester === semesterFilter)

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-slate-800">담당 과목</h2>
        <button className="btn-primary" onClick={() => setModal({})}>+ 과목 등록</button>
      </div>

      {/* 학기 필터 */}
      {semesters.length > 1 && (
        <div className="flex gap-2 mb-6">
          <button
            className={`px-3 py-1 rounded-full text-sm ${semesterFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-white border border-slate-200 text-slate-600'}`}
            onClick={() => setSemesterFilter('all')}
          >
            전체
          </button>
          {semesters.map((s) => (
            <button
              key={s}
              className={`px-3 py-1 rounded-full text-sm ${semesterFilter === s ? 'bg-blue-600 text-white' : 'bg-white border border-slate-200 text-slate-600'}`}
              onClick={() => setSemesterFilter(s)}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="card text-center py-12 text-slate-400">불러오는 중...</div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-12 text-slate-400">
          {semesterFilter === 'all' ? '등록된 과목이 없습니다.' : '해당 학기 과목이 없습니다.'}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((c) => (
            <div key={c.id} className="card">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold text-slate-800">{c.course_name}</h3>
                  <p className="text-sm text-slate-500 mt-0.5">
                    {c.course_code}{c.section ? ` — ${c.section}분반` : ''} · {c.semester}
                  </p>
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <button
                  className="btn-primary text-xs px-3 py-1.5"
                  onClick={() => navigate(`/professor/courses/${c.id}/upload`)}
                >
                  성적 업로드
                </button>
                <button
                  className="btn-secondary text-xs px-3 py-1.5"
                  onClick={() => setModal({ course: c })}
                >
                  수정
                </button>
                <button
                  className="btn-danger text-xs px-3 py-1.5"
                  onClick={() => setDeleteTarget(c)}
                >
                  삭제
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal !== null && (
        <CourseModal
          course={modal.course}
          onClose={() => setModal(null)}
          onSaved={handleSaved}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          name={deleteTarget.course_name}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
    </div>
  )
}
