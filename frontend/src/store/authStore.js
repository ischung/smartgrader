import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: null,
  role: null,
  token: null,

  setAuth: (user, role, token) => set({ user, role, token }),
  clearAuth: () => set({ user: null, role: null, token: null }),
}))

export default useAuthStore
