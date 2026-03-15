/**
 * API 클라이언트 유틸리티
 *
 * Render 무료 플랜은 비활성 15분 후 슬립 상태로 전환됩니다.
 * 첫 요청이 느린 경우(>3초) "서버를 깨우는 중" 토스트를 표시합니다.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const SLOW_THRESHOLD_MS = 3000

let onWakingUp = null  // 슬립 알림 콜백 (App에서 등록)
let onWakeUpDone = null

export function setWakeUpCallbacks(onStart, onEnd) {
  onWakingUp = onStart
  onWakeUpDone = onEnd
}

async function request(path, options = {}) {
  const url = `${API_URL}${path}`
  const token = options.token

  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const startedAt = Date.now()
  let wakeUpTimer = null

  // 3초 이상 걸리면 슬립 알림 표시
  if (onWakingUp) {
    wakeUpTimer = setTimeout(() => {
      onWakingUp?.()
    }, SLOW_THRESHOLD_MS)
  }

  try {
    const res = await fetch(url, {
      method: options.method || 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    })

    clearTimeout(wakeUpTimer)
    if (Date.now() - startedAt >= SLOW_THRESHOLD_MS) {
      onWakeUpDone?.()
    }

    // 204 No Content 등 본문 없는 응답 처리
    const data = res.status === 204 ? null : await res.json()
    if (!res.ok) {
      throw new Error(data?.error || `HTTP ${res.status}`)
    }
    return data
  } catch (err) {
    clearTimeout(wakeUpTimer)
    onWakeUpDone?.()
    throw err
  }
}

export const api = {
  get:    (path, options) => request(path, { ...options, method: 'GET' }),
  post:   (path, body, options) => request(path, { ...options, method: 'POST', body }),
  patch:  (path, body, options) => request(path, { ...options, method: 'PATCH', body }),
  put:    (path, body, options) => request(path, { ...options, method: 'PUT', body }),
  delete: (path, options) => request(path, { ...options, method: 'DELETE' }),
}
