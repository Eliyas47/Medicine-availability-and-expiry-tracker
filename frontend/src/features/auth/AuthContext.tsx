import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { User } from '@/types'
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from '@/api/client'
import authService from '@/api/auth'

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const logout = useCallback(async () => {
    const refresh = getRefreshToken()
    if (refresh) {
      try {
        await authService.logout(refresh)
      } catch {
        // Ignore errors — we clear locally regardless
      }
    }
    clearTokens()
    setUser(null)
  }, [])

  // Listen for forced logout from Axios interceptor (401 + failed refresh)
  useEffect(() => {
    const handler = () => {
      clearTokens()
      setUser(null)
    }
    window.addEventListener('auth:logout', handler)
    return () => window.removeEventListener('auth:logout', handler)
  }, [])

  // On mount, restore session from stored tokens
  useEffect(() => {
    const restoreSession = async () => {
      const token = getAccessToken()
      if (!token) {
        setIsLoading(false)
        return
      }
      try {
        const { data } = await authService.getProfile()
        setUser(data)
      } catch {
        clearTokens()
      } finally {
        setIsLoading(false)
      }
    }
    restoreSession()
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await authService.login({ email, password })
    setTokens(data.access, data.refresh)
    setUser(data.user)
  }, [])

  const refreshUser = useCallback(async () => {
    const { data } = await authService.getProfile()
    setUser(data)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>')
  return ctx
}
