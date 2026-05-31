import React, { useEffect } from 'react'
import { X } from 'lucide-react'

const Modal = ({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'md' 
}) => {

  useEffect(() => {
    // Disable background page scrolling when modal is active
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  if (!isOpen) return null

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
      {/* Dark backdrop with elegant glassmorphic blur */}
      <div 
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Modal Dialog container */}
      <div 
        className={`bg-white dark:bg-legal-charcoal-medium w-full ${sizeClasses[size]} rounded-2xl shadow-premium-lg border border-slate-100 dark:border-slate-800 z-10 transform transition-all duration-300 scale-100 flex flex-col max-h-[90vh]`}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4.5 border-b border-slate-100 dark:border-slate-800">
          <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white tracking-wide">
            {title}
          </h3>
          <button 
            onClick={onClose}
            className="p-1 rounded-full text-slate-400 hover:bg-slate-100 dark:hover:bg-legal-charcoal-dark dark:text-slate-500 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {children}
        </div>
      </div>
    </div>
  )
}

export default Modal
// note: using dynamic overflow styling for scrolling support inside body
