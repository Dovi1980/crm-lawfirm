import React, { createContext, useState, useEffect } from 'react'
import axiosClient from '../api/axiosClient'

export const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user session already exists in local storage
    const token = localStorage.getItem('accessToken')
    const email = localStorage.getItem('userEmail')
    const role = localStorage.getItem('userRole')
    const name = localStorage.getItem('userName')

    if (token && email && role && name) {
      setUser({
        email,
        role,
        name
      })
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    try {
      const response = await axiosClient.post('/auth/login', { email, password })
      const { access_token, refresh_token, role, user_email, user_name } = response.data

      // Save to local storage
      localStorage.setItem('accessToken', access_token)
      localStorage.setItem('refreshToken', refresh_token)
      localStorage.setItem('userRole', role)
      localStorage.setItem('userEmail', user_email)
      localStorage.setItem('userName', user_name)

      // Set user state
      setUser({
        email: user_email,
        role,
        name: user_name
      })
      
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Ocurrió un error al iniciar sesión'
      return { success: false, error: message }
    }
  }

  const logout = async () => {
    const refreshToken = localStorage.getItem('refreshToken')
    if (refreshToken) {
      try {
        // Safe backend logout to revoke token
        await axiosClient.post(`/auth/logout?refresh_token=${refreshToken}`)
      } catch (e) {
        console.error("Failed to revoke token on server", e)
      }
    }
    
    // Clear local cache session anyway
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
