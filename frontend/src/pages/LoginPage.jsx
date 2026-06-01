import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Scale, Lock, Mail, AlertCircle } from 'lucide-react'

const LoginPage = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Grab the redirected location, default to dashboard
  const from = location.state?.from?.pathname || '/dashboard'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    if (!email || !password) {
      setError('Por favor complete todos los campos.')
      setIsSubmitting(false)
      return
    }

    const result = await login(email, password)
    if (result.success) {
      navigate(from, { replace: true })
    } else {
      setError(result.error)
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 bg-cover bg-center px-4" style={{ backgroundImage: "linear-gradient(rgba(10, 17, 40, 0.9), rgba(28, 37, 65, 0.9))" }}>
      <div className="w-full max-w-md bg-white/95 dark:bg-legal-charcoal-medium/95 rounded-2xl shadow-premium-lg border border-legal-gold/10 p-10 backdrop-blur-md">
        
        {/* Brand Logo and Title */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="w-14 h-14 rounded-full bg-legal-gold/10 border border-legal-gold flex items-center justify-center mb-4">
            <Scale className="text-legal-gold w-7 h-7" />
          </div>
          <h1 className="font-serif text-2xl font-bold tracking-wide text-legal-navy-deep dark:text-white">LEX STUDIO</h1>
          <p className="text-xs text-legal-gold font-bold tracking-widest uppercase mt-1">Estudio Jurídico CRM</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-6">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Email */}
          <div>
            <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-2">Correo Electrónico</label>
            <div className="flex items-center gap-3">
              <Mail className="w-5 h-5 text-slate-400 flex-shrink-0" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="premium-input w-full"
                placeholder="abogado@estudio.com"
                required
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-2">Contraseña</label>
            <div className="flex items-center gap-3">
              <Lock className="w-5 h-5 text-slate-400 flex-shrink-0" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="premium-input w-full"
                placeholder="••••••••"
                required
                disabled={isSubmitting}
              />
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            className="w-full premium-btn-primary py-3 font-semibold shadow-gold-glow dark:bg-legal-gold dark:text-legal-navy-deep dark:hover:bg-legal-gold-light"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Iniciando Sesión...' : 'Ingresar al Portal'}
          </button>
        </form>

        {/* Legal Disclaimer Footer */}
        <p className="mt-8 text-center text-xs text-slate-400 dark:text-slate-500">
          Uso restringido a personal autorizado de Lex Studio. Todos los accesos son auditados.
        </p>
      </div>
    </div>
  )
}

export default LoginPage
export { LoginPage }
