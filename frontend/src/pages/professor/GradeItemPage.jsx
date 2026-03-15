import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import { api } from '../../utils/api'

// ── Toast ──────────────────────────────────────────────────────────────────
function Toast({ message, type, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000)
    return () => clearTimeout(t)
  }, [onClose])
  return (
    <div className={`fixed bottom-6 right-6 z-50 text-white text-sm px-5 py-3 rounded-xl shadow-lg
      ${type === 'error' ? 'bg-red-600' : 'bg-slate-800'}`}>
      {message}
    </div>
  )
}

// ── WeightBar ─────────────────────────────────────────────────────────────
function WeightBar({ total }) {
  const pct = Math.min(total, 100)
  const color = total > 100 ? 'bg-red-500' : total === 100 ? 'bg-green-500' : 'bg-yellow-400'
  const textColor = total > 100 ? 'text-red-600' : total === 100 ? 'text-green-600' : 'text-yellow-600'
  const label = total > 100
    ? `가중치 합계: ${total}% (100% 초과)`
    : total === 100
    ? '가중치 합계: 100% ✓'
    : `가중치 합계: ${total}% (${100 - total}% 남음)`

  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-1">
        <span className={`text-sm font-medium ${textColor}`}>{label}</span>
      </div>
      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all duration-300`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

// ── GroupModal ────────────────────────────────────────────────────────────
function GroupModal({ group, courseId, token, onClose, onSaved }) {
  const isEdit = !!group
  const [name, setName] = useState(group?.name ?? '')
  const [weight, setWeight] = useState(group?.weight ?? '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (isEdit) {
        await api.patch(`/api/v1/courses/${courseId}/groups/${group.id}`,
          { name, weight: Number(weight) }, { token })
      } else {
        await api.post(`/api/v1/courses/${courseId}/groups`,
          { name, weight: Number(weight) }, { token })
      }
      onSaved(isEdit ? '그룹이 수정되었습니다.' : '그룹이 추가되었습니다.')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40">
      <div className="card w-80">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">
          {isEdit ? '그룹 수정' : '그룹 추가'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">그룹 이름</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="과제 그룹" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">가중치 (%)</label>
            <input className="input" type="number" min="1" max="100" value={weight}
              onChange={(e) => setWeight(e.target.value)} placeholder="20" required />
          </div>
          {error && <p className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">{error}</p>}
          <div className="flex gap-3 justify-end">
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

// ── ItemModal ─────────────────────────────────────────────────────────────
function ItemModal({ item, groups, courseId, token, onClose, onSaved }) {
  const isEdit = !!item
  const [form, setForm] = useState({
    name: item?.name ?? '',
    item_type: item?.item_type ?? 'general',
    weight: item?.weight ?? '',
    group_id: item?.group_id ?? '',
    deduction_per_absence: item?.deduction_per_absence ?? 0.5,
    display_order: item?.display_order ?? 0,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const inGroup = !!form.group_id

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const body = {
        name: form.name,
        item_type: form.item_type,
        display_order: Number(form.display_order),
      }
      if (!inGroup) body.weight = Number(form.weight)
      if (form.item_type === 'attendance') {
        body.deduction_per_absence = Number(form.deduction_per_absence)
      }

      let saved
      if (isEdit) {
        saved = await api.patch(
          `/api/v1/courses/${courseId}/items/${item.id}`, body, { token })
        // 그룹 변경이 있으면 별도 엔드포인트
        if (form.group_id !== (item.group_id ?? '')) {
          await api.patch(
            `/api/v1/courses/${courseId}/items/${item.id}/group`,
            { group_id: form.group_id || null }, { token })
        }
      } else {
        if (form.group_id) body.group_id = form.group_id
        saved = await api.post(`/api/v1/courses/${courseId}/items`, body, { token })
      }
      onSaved(isEdit ? '항목이 수정되었습니다.' : '항목이 추가되었습니다.', saved)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const TYPE_LABELS = { general: '일반', attendance: '출석', attitude: '태도' }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40">
      <div className="card w-96">
        <h3 className="text-lg font-semibold text-slate-800 mb-4">
          {isEdit ? '항목 수정' : '항목 추가'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">항목 이름</label>
            <input className="input" value={form.name} onChange={set('name')}
              placeholder="중간고사" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">유형</label>
            <select className="input" value={form.item_type} onChange={set('item_type')}>
              {Object.entries(TYPE_LABELS).map(([v, l]) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>
          {form.item_type === 'attendance' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">결석 1회당 감점</label>
              <input className="input" type="number" min="0" step="0.1"
                value={form.deduction_per_absence}
                onChange={set('deduction_per_absence')} />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">그룹 (선택)</label>
            <select className="input" value={form.group_id} onChange={set('group_id')}>
              <option value="">그룹 없음</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>{g.name} ({g.weight}%)</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              가중치 (%) {inGroup && <span className="text-slate-400 font-normal">— 그룹 가중치 적용</span>}
            </label>
            <input
              className={`input ${inGroup ? 'bg-slate-100 cursor-not-allowed' : ''}`}
              type="number" min="0" max="100" value={inGroup ? '' : form.weight}
              onChange={set('weight')}
              placeholder={inGroup ? '그룹 가중치 적용' : '25'}
              disabled={inGroup}
              required={!inGroup}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">표시 순서</label>
            <input className="input" type="number" min="0" value={form.display_order}
              onChange={set('display_order')} />
          </div>
          {error && <p className="text-sm text-red-500 bg-red-50 p-3 rounded-lg">{error}</p>}
          <div className="flex gap-3 justify-end">
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

// ── Main Page ─────────────────────────────────────────────────────────────
export default function GradeItemPage() {
  const { courseId } = useParams()
  const { token } = useAuthStore()
  const navigate = useNavigate()

  const [items, setItems] = useState([])
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)
  const [groupModal, setGroupModal] = useState(null)   // null | {} | { group }
  const [itemModal, setItemModal] = useState(null)     // null | {} | { item }
  const [deleting, setDeleting] = useState(null)       // { type: 'item'|'group', id, name }

  const showToast = (message, type = 'success') => setToast({ message, type })

  const fetchAll = useCallback(async () => {
    try {
      const [itemsData, groupsData] = await Promise.all([
        api.get(`/api/v1/courses/${courseId}/items`, { token }),
        api.get(`/api/v1/courses/${courseId}/groups`, { token }),
      ])
      setItems(itemsData)
      setGroups(groupsData)
    } catch {
      showToast('데이터를 불러오지 못했습니다.', 'error')
    } finally {
      setLoading(false)
    }
  }, [courseId, token])

  useEffect(() => { fetchAll() }, [fetchAll])

  // 가중치 합계: 비그룹 항목 + 그룹
  const totalWeight = (() => {
    const itemsSum = items
      .filter((i) => !i.group_id && i.weight != null)
      .reduce((s, i) => s + Number(i.weight), 0)
    const groupsSum = groups.reduce((s, g) => s + Number(g.weight), 0)
    return Math.round((itemsSum + groupsSum) * 100) / 100
  })()

  const handleGroupSaved = (msg) => { setGroupModal(null); showToast(msg); fetchAll() }
  const handleItemSaved = (msg) => { setItemModal(null); showToast(msg); fetchAll() }

  const handleDelete = async () => {
    const { type, id } = deleting
    setDeleting(null)
    try {
      if (type === 'group') {
        await api.delete(`/api/v1/courses/${courseId}/groups/${id}`, { token })
        showToast('그룹이 삭제되었습니다.')
      } else {
        await api.delete(`/api/v1/courses/${courseId}/items/${id}`, { token })
        showToast('항목이 삭제되었습니다.')
      }
      fetchAll()
    } catch {
      showToast('삭제에 실패했습니다.', 'error')
    }
  }

  const groupMap = Object.fromEntries(groups.map((g) => [g.id, g]))
  const TYPE_LABELS = { general: '일반', attendance: '출석', attitude: '태도' }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <button className="text-sm text-slate-500 hover:text-slate-700"
          onClick={() => navigate('/professor/courses')}>
          ← 과목 목록
        </button>
        <h2 className="text-2xl font-bold text-slate-800">성적 항목 설정</h2>
      </div>

      {/* Weight bar */}
      <WeightBar total={totalWeight} />

      {loading ? (
        <div className="card text-center py-12 text-slate-400">불러오는 중...</div>
      ) : (
        <div className="space-y-6">
          {/* ── Groups ── */}
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-slate-700">그룹</h3>
              <button className="btn-primary text-xs px-3 py-1.5"
                onClick={() => setGroupModal({})}>+ 그룹 추가</button>
            </div>
            {groups.length === 0 ? (
              <p className="text-sm text-slate-400">그룹이 없습니다.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left py-2 font-medium text-slate-600">이름</th>
                    <th className="text-left py-2 font-medium text-slate-600">가중치</th>
                    <th className="text-left py-2 font-medium text-slate-600">항목 수</th>
                    <th className="text-right py-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {groups.map((g) => (
                    <tr key={g.id}>
                      <td className="py-2 font-medium text-slate-800">{g.name}</td>
                      <td className="py-2 text-slate-600">{g.weight}%</td>
                      <td className="py-2 text-slate-500">
                        {items.filter((i) => i.group_id === g.id).length}개
                      </td>
                      <td className="py-2 text-right space-x-1">
                        <button className="btn-secondary text-xs px-2 py-1"
                          onClick={() => setGroupModal({ group: g })}>수정</button>
                        <button className="btn-danger text-xs px-2 py-1"
                          onClick={() => setDeleting({ type: 'group', id: g.id, name: g.name })}>삭제</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* ── Items ── */}
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-slate-700">성적 항목</h3>
              <button className="btn-primary text-xs px-3 py-1.5"
                onClick={() => setItemModal({})}>+ 항목 추가</button>
            </div>
            {items.length === 0 ? (
              <p className="text-sm text-slate-400">항목이 없습니다.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left py-2 font-medium text-slate-600">이름</th>
                    <th className="text-left py-2 font-medium text-slate-600">유형</th>
                    <th className="text-left py-2 font-medium text-slate-600">가중치</th>
                    <th className="text-left py-2 font-medium text-slate-600">그룹</th>
                    <th className="text-right py-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {items.map((item) => {
                    const grp = item.group_id ? groupMap[item.group_id] : null
                    return (
                      <tr key={item.id} className={grp ? 'bg-blue-50/30' : ''}>
                        <td className="py-2 font-medium text-slate-800">{item.name}</td>
                        <td className="py-2 text-slate-500">{TYPE_LABELS[item.item_type] ?? item.item_type}</td>
                        <td className="py-2 text-slate-500">
                          {grp
                            ? <span className="text-blue-400 italic">그룹({grp.weight}%)</span>
                            : `${item.weight ?? '—'}%`}
                        </td>
                        <td className="py-2 text-slate-500">{grp ? grp.name : '—'}</td>
                        <td className="py-2 text-right space-x-1">
                          <button className="btn-secondary text-xs px-2 py-1"
                            onClick={() => setItemModal({ item })}>수정</button>
                          <button className="btn-danger text-xs px-2 py-1"
                            onClick={() => setDeleting({ type: 'item', id: item.id, name: item.name })}>삭제</button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Modals */}
      {groupModal !== null && (
        <GroupModal
          group={groupModal.group}
          courseId={courseId}
          token={token}
          onClose={() => setGroupModal(null)}
          onSaved={handleGroupSaved}
        />
      )}

      {itemModal !== null && (
        <ItemModal
          item={itemModal.item}
          groups={groups}
          courseId={courseId}
          token={token}
          onClose={() => setItemModal(null)}
          onSaved={handleItemSaved}
        />
      )}

      {/* Confirm delete */}
      {deleting && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40">
          <div className="card w-80">
            <h3 className="text-lg font-semibold text-slate-800 mb-2">
              {deleting.type === 'group' ? '그룹 삭제' : '항목 삭제'}
            </h3>
            <p className="text-sm text-slate-600 mb-6">
              <span className="font-medium">{deleting.name}</span>을(를) 삭제하시겠습니까?
              {deleting.type === 'group' && ' 소속 항목들은 그룹 없음으로 변경됩니다.'}
            </p>
            <div className="flex gap-3 justify-end">
              <button className="btn-secondary" onClick={() => setDeleting(null)}>취소</button>
              <button className="btn-danger" onClick={handleDelete}>삭제</button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
    </div>
  )
}
