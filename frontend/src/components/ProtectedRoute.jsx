import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    // Premium loading spinner
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-legal-cream dark:bg-legal-charcoal-dark">
        <div className="w-12 h-12 border-4 border-legal-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 font-serif text-lg text-legal-navy-deep dark:text-slate-300 tracking-wide animate-pulse">Cargando Lex Studio...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    // Safe redirect to login and preserve path
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // Unauthorized access: redirect to dashboard
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default ProtectedRoute
