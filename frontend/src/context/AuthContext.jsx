import React, { createContext, useState, useEffect } from 'react'
import axiosClient, { silentRefresh } from '../api/axiosClient'
import { setAccessToken, clearAccessToken } from '../api/tokenStore'

export const AuthContext = createContext(null)

// Profile keys kept in localStorage for instant UI (NOT the access token).
const PROFILE_KEYS = ['userEmail', 'userRole', 'userName']

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // On load the access token lives only in memory (lost on reload). If we have
    // a stored profile, try a silent refresh via the HttpOnly cookie to restore
    // the session transparently — the user stays logged in across reloads.
    let cancelled = false

    const restore = async () => {
      const email = localStorage.getItem('userEmail')
      const role = localStorage.getItem('userRole')
      const name = localStorage.getItem('userName')

      if (email && role && name) {
        const token = await silentRefresh()
        if (cancelled) return
        if (token) {
          setUser({ email, role, name })
        } else {
          // Refresh cookie expired/revoked → clean up.
          localStorage.clear()
          clearAccessToken()
        }
      }
      if (!cancelled) setLoading(false)
    }

    restore()
    return () => { cancelled = true }
  }, [])

  const login = async (email, password) => {
    try {
      const response = await axiosClient.post('/auth/login', { email, password })
      const { access_token, role, user_email, user_name } = response.data

      // Access token → memory only. Refresh token → HttpOnly cookie (server-side).
      setAccessToken(access_token)
      localStorage.setItem('userRole', role)
      localStorage.setItem('userEmail', user_email)
      localStorage.setItem('userName', user_name)

      setUser({ email: user_email, role, name: user_name })

      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Ocurrió un error al iniciar sesión'
      return { success: false, error: message }
    }
  }

  const logout = async () => {
    try {
      // Server reads the refresh token from the HttpOnly cookie and revokes it.
      await axiosClient.post('/auth/logout')
    } catch (e) {
      console.error('Failed to revoke session on server', e)
    }
    clearAccessToken()
    localStorage.clear()
    setUser(null)
  }

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    isAdmin: user?.role === 'admin',
    isLawyer: user?.role === 'lawyer',
    isAssistant: user?.role === 'assistant'
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
