import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { 
  LayoutDashboard, 
  Users, 
  Briefcase, 
  CheckSquare, 
  UserCog, 
  LogOut, 
  Scale
} from 'lucide-react'

const Sidebar = () => {
  const { user, logout, isAdmin } = useAuth()

  const links = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/clients', label: 'Clientes', icon: Users },
    { to: '/cases', label: 'Expedientes', icon: Briefcase },
    { to: '/tasks', label: 'Tareas', icon: CheckSquare },
  ]

  if (isAdmin) {
    links.push({ to: '/users', label: 'Abogados & Personal', icon: UserCog })
  }

  return (
    <aside className="w-64 bg-legal-navy-deep text-slate-300 flex flex-col h-screen fixed left-0 top-0 border-r border-legal-gold/10 z-20">
      {/* Brand Header */}
      <div className="p-6 border-b border-legal-gold/10 flex items-center gap-3">
        <Scale className="text-legal-gold w-8 h-8" />
        <div>
          <h1 className="font-serif text-xl font-bold tracking-wide text-white">LEX STUDIO</h1>
          <p className="text-xs text-legal-gold font-medium tracking-widest uppercase">Estudio Jurídico</p>
        </div>
      </div>

      {/* Nav Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {links.map((link) => {
          const Icon = link.icon
          return (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-legal-gold/10 text-legal-gold border-l-4 border-legal-gold font-semibold shadow-gold-glow'
                    : 'hover:bg-slate-800/50 hover:text-white'
                }`
              }
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span>{link.label}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* Profile & Logout Footer */}
      <div className="p-4 border-t border-legal-gold/10 bg-slate-950/20">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-legal-gold/10 border border-legal-gold flex items-center justify-center font-bold text-legal-gold">
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="overflow-hidden">
            <h4 className="text-sm font-semibold text-white truncate">{user?.name}</h4>
            <p className="text-xs text-legal-gold font-medium capitalize truncate">
              {user?.role === 'admin' ? 'Administrador' : user?.role === 'lawyer' ? 'Abogado' : 'Asistente'}
            </p>
          </div>
        </div>
        
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-400 font-medium transition-all duration-200 active:scale-95"
        >
          <LogOut className="w-5 h-5" />
          <span>Cerrar Sesión</span>
        </button>
      </div>
    </aside>
  )
}

export default Sidebar
