import React, { useState, useEffect } from 'react'
import { Sun, Moon, Bell } from 'lucide-react'

const Navbar = () => {
  const [darkMode, setDarkMode] = useState(false)

  useEffect(() => {
    // Initial theme check
    const isDark = localStorage.getItem('theme') === 'dark' || 
                   (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
    if (isDark) {
      document.documentElement.classList.add('dark')
      setDarkMode(true)
    }
  }, [])

  const toggleDarkMode = () => {
    if (darkMode) {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
      setDarkMode(false)
    } else {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
      setDarkMode(true)
    }
  }

  return (
    <header className="h-16 bg-white dark:bg-legal-charcoal-medium border-b border-slate-100 dark:border-slate-800 flex items-center justify-between px-8 fixed top-0 right-0 left-64 z-10 transition-colors duration-200">
      {/* Topbar Welcome Context */}
      <div>
        <h2 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white tracking-wide">
          Portal de Gestión Estudio Jurídico
        </h2>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-4">
        {/* Theme Toggler */}
        <button
          onClick={toggleDarkMode}
          className="p-2 rounded-full text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-legal-charcoal-dark transition-all duration-200"
          title={darkMode ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
        >
          {darkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-legal-navy-medium" />}
        </button>

        {/* Action Notifications Mock */}
        <div className="relative">
          <button className="p-2 rounded-full text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-legal-charcoal-dark transition-all duration-200">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-legal-gold rounded-full border-2 border-white dark:border-legal-charcoal-medium"></span>
          </button>
        </div>
      </div>
    </header>
  )
}

export default Navbar
