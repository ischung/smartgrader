import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import { api } from '../../utils/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const ALLOWED_EXTS = ['.xlsx', '.xls', '.csv']

// ── Toast ──────────────────────────────────────────────────────────────────
function Toast({ message, type, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000)
    return () => clearTimeout(t)
  }, [onClose])

  return (
    <div className={`fixed bottom-6 right-6 z-50 ${type === 'error' ? 'bg-red-600' : 'bg-slate-800'} text-white text-sm px-5 py-3 rounded-xl shadow-lg max-w-sm`}>
      {message}
    </div>
  )
}

// ── CourseInfoModal ────────────────────────────────────────────────────────
function CourseInfoModal({ extracted, courseId, token, onClose, onConfirmed }) {
  const [form, setForm] = useState({
    course_name: extracted?.course_name ?? '',
    course_code: extracted?.course_code ?? '',
    section: extracted?.section ?? '',
    semester: extracted?.semester ?? '',
  })
  const [loading, setLoading] = useState(false)
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSave = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.patch(`/api/v1/courses/${courseId}`, form, { token })
      onConfirmed()
    } catch {
      onConfirmed() // 실패해도 업로드 결과는 보여줌
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40">
      <div className="card w-96">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">과목 정보 확인</h3>
        <p className="text-sm text-slate-500 mb-5">파일에서 추출된 정보를 확인하고 수정하세요.</p>
        <form onSubmit={handleSave} className="space-y-4">
          {[
            ['과목명', 'course_name'],
            ['교과코드', 'course_code'],
            ['분반', 'section'],
            ['학기', 'semester'],
          ].map(([label, key]) => (
            <div key={key}>
              <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
              <input
                className="input"
                value={form[key]}
                onChange={set(key)}
                required={key !== 'section'}
              />
            </div>
          ))}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-secondary" onClick={onClose}>건너뛰기</button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? '저장 중...' : '저장'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Main ───────────────────────────────────────────────────────────────────
export default function GradeUploadPage() {
  const { courseId } = useParams()
  const { token } = useAuthStore()
  const navigate = useNavigate()

  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)      // upload response
  const [showModal, setShowModal] = useState(false)
  const [toast, setToast] = useState(null)
  const fileInputRef = useRef(null)

  const showToast = (message, type = 'success') => setToast({ message, type })

  const validateExt = (filename) => {
    const ext = filename.slice(filename.lastIndexOf('.')).toLowerCase()
    return ALLOWED_EXTS.includes(ext)
  }

  const uploadFile = async (file) => {
    if (!validateExt(file.name)) {
      showToast('앗, xlsx, xls, csv 파일만 업로드할 수 있어요.', 'error')
      return
    }

    setUploading(true)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_URL}/api/v1/courses/${courseId}/files/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)

      setResult(data)
      // 추출된 과목 정보가 하나라도 있으면 모달 표시
      const hasExtracted = data.extracted && Object.values(data.extracted).some(Boolean)
      if (hasExtracted) setShowModal(true)
      else showToast('파일이 업로드되었습니다.')
    } catch (err) {
      showToast(err.message || '업로드에 실패했습니다.', 'error')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadFile(file)
  }

  const onFileChange = (e) => {
    const file = e.target.files[0]
    if (file) uploadFile(file)
    e.target.value = ''
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <button
          className="text-sm text-slate-500 hover:text-slate-700"
          onClick={() => navigate('/professor/courses')}
        >
          ← 과목 목록
        </button>
        <h2 className="text-2xl font-bold text-slate-800">성적 파일 업로드</h2>
      </div>

      {/* Drop zone */}
      <div
        className={`card border-2 border-dashed text-center py-16 cursor-pointer transition-colors
          ${dragging ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-blue-400'}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          className="hidden"
          onChange={onFileChange}
        />

        {uploading ? (
          <div className="flex flex-col items-center gap-3 text-slate-500">
            <svg className="w-8 h-8 animate-spin text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            <p className="text-sm">업로드 중...</p>
          </div>
        ) : (
          <div className="text-slate-400">
            <div className="text-4xl mb-3">📂</div>
            <p className="font-medium text-slate-600 mb-1">파일을 드래그하거나 클릭해서 업로드</p>
            <p className="text-xs">xlsx, xls, csv · 최대 10MB</p>
          </div>
        )}
      </div>

      {/* Preview table */}
      {result && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-700">
              미리보기
              <span className="ml-2 text-sm font-normal text-slate-400">(총 {result.total_rows}행)</span>
            </h3>
            <p className="text-sm text-slate-500">
              학생 {result.students?.created?.length ?? 0}명 계정 생성됨
            </p>
          </div>
          <div className="card p-0 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  {result.columns.map((col) => (
                    <th key={col} className="text-left px-4 py-2 font-medium text-slate-600 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {result.preview.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    {row.map((cell, j) => (
                      <td key={j} className="px-4 py-2 text-slate-600 whitespace-nowrap">{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Course info modal */}
      {showModal && result && (
        <CourseInfoModal
          extracted={result.extracted}
          courseId={courseId}
          token={token}
          onClose={() => { setShowModal(false); showToast('파일이 업로드되었습니다.') }}
          onConfirmed={() => { setShowModal(false); showToast('파일 업로드 및 과목 정보가 저장되었습니다.') }}
        />
      )}

      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
    </div>
  )
}
