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

  const colors = type === 'error'
    ? 'bg-red-600'
    : 'bg-slate-800'

  return (
    <div className={`fixed bottom-6 right-6 z-50 ${colors} text-white text-sm px-5 py-3 rounded-xl shadow-lg`}>
      {message}
    </div>
  )
}

// ── ConfirmDialog ──────────────────────────────────────────────────────────
function ConfirmDialog({ name, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40">
      <div className="card w-80">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">교수 삭제</h3>
        <p className="text-sm text-slate-600 mb-6">
          <span className="font-medium text-slate-800">{name}</span> 계정을 삭제하시겠습니까?<br />
          이 작업은 되돌릴 수 없습니다.
        </p>
        <div className="flex gap-3 justify-end">
          <button className="btn-secondary" onClick={onCancel}>취소</button>
          <button className="btn-danger" onClick={onConfirm}>삭제</button>
        </div>
      </div>
    </div>
  )
}

// ── ProfessorModal ─────────────────────────────────────────────────────────
function ProfessorModal({ professor, onClose, onSaved }) {
  const { token } = useAuthStore()
  const isEdit = !!professor

  const [name, setName] = useState(professor?.name ?? '')
  const [loginId, setLoginId] = useState(professor?.login_id ?? '')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (isEdit) {
        const body = { name }
        if (password) body.password = password
        await api.patch(`/api/v1/users/professors/${professor.id}`, body, { token })
      } else {
        await api.post('/api/v1/users/professors', { name, login_id: loginId, password }, { token })
      }
      onSaved(isEdit ? '교수 정보가 수정되었습니다.' : '교수 계정이 등록되었습니다.')
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
          {isEdit ? '교수 정보 수정' : '교수 계정 등록'}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">이름</label>
            <input
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="홍길동"
              required
            />
          </div>

          {!isEdit && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">아이디</label>
              <input
                className="input"
                value={loginId}
                onChange={(e) => setLoginId(e.target.value)}
                placeholder="prof001"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              비밀번호{isEdit && ' (변경 시에만 입력)'}
            </label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isEdit ? '변경하지 않으려면 비워두세요' : '초기 비밀번호'}
              required={!isEdit}
            />
          </div>

          {error && (
            <p className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">{error}</p>
          )}

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

// ── Main Page ──────────────────────────────────────────────────────────────
export default function ProfessorManagePage() {
  const { token, clearAuth } = useAuthStore()
  const navigate = useNavigate()

  const [professors, setProfessors] = useState([])
  const [loading, setLoading] = useState(true)

  const [modal, setModal] = useState(null)         // null | { professor?: obj }
  const [deleteTarget, setDeleteTarget] = useState(null)  // professor obj
  const [toast, setToast] = useState(null)         // { message, type }

  const showToast = (message, type = 'success') => setToast({ message, type })

  const fetchProfessors = useCallback(async () => {
    try {
      const data = await api.get('/api/v1/users/professors', { token })
      setProfessors(data)
    } catch {
      showToast('목록을 불러오지 못했습니다.', 'error')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { fetchProfessors() }, [fetchProfessors])

  const handleSaved = (message) => {
    setModal(null)
    showToast(message)
    fetchProfessors()
  }

  const handleDelete = async () => {
    try {
      await api.delete(`/api/v1/users/professors/${deleteTarget.id}`, { token })
      setDeleteTarget(null)
      showToast('교수 계정이 삭제되었습니다.')
      fetchProfessors()
    } catch {
      setDeleteTarget(null)
      showToast('삭제에 실패했습니다.', 'error')
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <button
              className="text-sm text-slate-500 hover:text-slate-700 mb-1"
              onClick={() => navigate('/admin')}
            >
              ← 대시보드
            </button>
            <h1 className="text-2xl font-bold text-slate-800">교수 계정 관리</h1>
          </div>
          <div className="flex gap-3">
            <button className="btn-primary" onClick={() => setModal({})}>
              + 교수 등록
            </button>
            <button
              className="btn-secondary"
              onClick={() => { clearAuth(); navigate('/login') }}
            >
              로그아웃
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="card p-0 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-slate-400">목록을 불러오는 중...</div>
          ) : professors.length === 0 ? (
            <div className="p-12 text-center text-slate-400">등록된 교수가 없습니다.</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left px-6 py-3 font-medium text-slate-600">이름</th>
                  <th className="text-left px-6 py-3 font-medium text-slate-600">아이디</th>
                  <th className="px-6 py-3 text-right font-medium text-slate-600">작업</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {professors.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-medium text-slate-800">{p.name}</td>
                    <td className="px-6 py-4 text-slate-500">{p.login_id}</td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        className="btn-secondary text-xs px-3 py-1"
                        onClick={() => setModal({ professor: p })}
                      >
                        수정
                      </button>
                      <button
                        className="btn-danger text-xs px-3 py-1"
                        onClick={() => setDeleteTarget(p)}
                      >
                        삭제
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modal */}
      {modal !== null && (
        <ProfessorModal
          professor={modal.professor}
          onClose={() => setModal(null)}
          onSaved={handleSaved}
        />
      )}

      {/* Confirm Delete */}
      {deleteTarget && (
        <ConfirmDialog
          name={deleteTarget.name}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}
