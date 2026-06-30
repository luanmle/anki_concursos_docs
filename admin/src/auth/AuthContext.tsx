import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { apiRequest } from '../api/client'
import type { TokenResponse, User } from '../types'
import { AuthContext, type AuthContextValue } from './auth-context'

const TOKEN_KEY = 'anki-concursos-admin-token'
const REFRESH_TOKEN_KEY = 'anki-concursos-admin-refresh-token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY),
  )
  const [refreshToken, setRefreshToken] = useState<string | null>(() =>
    localStorage.getItem(REFRESH_TOKEN_KEY),
  )
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(Boolean(token || refreshToken))

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    setToken(null)
    setRefreshToken(null)
    setUser(null)
    setLoading(false)
  }, [])

  const persistSession = useCallback((response: TokenResponse) => {
    localStorage.setItem(TOKEN_KEY, response.access_token)
    if (response.refresh_token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token)
      setRefreshToken(response.refresh_token)
    }
    setToken(response.access_token)
    setUser(response.user)
  }, [])

  useEffect(() => {
    if (!token && !refreshToken) return

    async function validateSession() {
      try {
        if (token) {
          const currentUser = await apiRequest<User>('/auth/me', {}, token)
          setUser(currentUser)
          return
        }
        throw new Error('missing access token')
      } catch {
        if (!refreshToken) {
          logout()
          return
        }
        try {
          const refreshed = await apiRequest<TokenResponse>('/auth/refresh', {
            method: 'POST',
            body: JSON.stringify({ refresh_token: refreshToken }),
          })
          persistSession(refreshed)
        } catch {
          logout()
        }
      } finally {
        setLoading(false)
      }
    }

    validateSession()
  }, [logout, persistSession, refreshToken, token])

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiRequest<TokenResponse>('/auth/token', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    persistSession(response)
  }, [persistSession])

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      loading,
      login,
      logout,
      hasRole: (...roles) => Boolean(user && roles.includes(user.role)),
    }),
    [loading, login, logout, token, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
