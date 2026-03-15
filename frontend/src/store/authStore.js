import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      role: null,
      token: null,

      setAuth: (user, role, token) => set({ user, role, token }),
      clearAuth: () => set({ user: null, role: null, token: null }),
    }),
    {
      name: 'smartgrader-auth',  // localStorage key
      partialize: (state) => ({ user: state.user, role: state.role, token: state.token }),
    }
  )
)

export default useAuthStore
