/**
 * Render 슬립 대응 토스트
 * API 첫 응답이 3초 이상 걸릴 때 표시
 */
export default function WakeUpToast({ visible }) {
  if (!visible) return null

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50
                    bg-slate-800 text-white text-sm px-5 py-3 rounded-full
                    shadow-lg flex items-center gap-3 animate-pulse">
      <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10"
                stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z" />
      </svg>
      서버를 깨우는 중이에요... 잠시만 기다려 주세요
    </div>
  )
}
