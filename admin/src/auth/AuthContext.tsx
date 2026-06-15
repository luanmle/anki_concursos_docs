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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    sessionStorage.getItem(TOKEN_KEY),
  )
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(Boolean(token))

  const logout = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
    setLoading(false)
  }, [])

  useEffect(() => {
    if (!token) return

    apiRequest<User>('/auth/me', {}, token)
      .then(setUser)
      .catch(logout)
      .finally(() => setLoading(false))
  }, [logout, token])

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiRequest<TokenResponse>('/auth/token', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    sessionStorage.setItem(TOKEN_KEY, response.access_token)
    setToken(response.access_token)
    setUser(response.user)
  }, [])

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
