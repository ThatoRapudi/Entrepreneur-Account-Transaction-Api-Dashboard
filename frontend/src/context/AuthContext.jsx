import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { apiPost, getStoredToken, setStoredToken, setUnauthorizedHandler } from '../api/client'

const AuthContext = createContext(null)

/**
 * Holds the login state for the whole app. The token itself lives in
 * localStorage (via api/client.js) so a page refresh doesn't force a
 * re-login - this is a real standalone app the user runs on their own
 * machine, not an in-chat preview, so persisting it is the right call.
 */
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken())

  const logout = useCallback(() => {
    setStoredToken(null)
    setToken(null)
  }, [])

  useEffect(() => {
    // Any request that comes back 401 (expired/invalid token) drops the
    // session everywhere at once, instead of just failing that one panel.
    setUnauthorizedHandler(logout)
  }, [logout])

  const login = useCallback(async (username, password) => {
    const data = await apiPost('/api/auth/login', { username, password })
    setStoredToken(data.access_token)
    setToken(data.access_token)
  }, [])

  return (
    <AuthContext.Provider value={{ isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
