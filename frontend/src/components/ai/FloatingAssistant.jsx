import React, { useState } from 'react'
import { Sparkles } from 'lucide-react'
import ChatPanel from './ChatPanel'

/**
 * Persistent floating button bottom-right. Opens a chat panel tied to the
 * global assistant endpoint (no case context).
 */
const FloatingAssistant = () => {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Trigger button — visible on every authenticated route */}
      <button
        onClick={() => setOpen(o => !o)}
        className="fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full bg-legal-navy-deep dark:bg-legal-gold text-legal-gold dark:text-legal-navy-deep border-2 border-legal-gold shadow-xl flex items-center justify-center hover:scale-105 active:scale-95 transition-transform"
        aria-label={open ? 'Cerrar asistente' : 'Abrir asistente IA'}
      >
        <Sparkles className="w-6 h-6" />
      </button>

      {/* Slide-over panel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-40 w-[380px] max-w-[calc(100vw-3rem)] h-[560px] max-h-[calc(100vh-8rem)]">
          <ChatPanel
            endpoint="/api/ai/assistant"
            title="Asistente IA"
            subtitle="Consultas generales del estudio"
            emptyHint="Pedime ayuda con redacción, dudas procesales generales, o cómo organizar el día. Las respuestas son sugerencias — verificá antes de actuar."
            onClose={() => setOpen(false)}
          />
        </div>
      )}
    </>
  )
}

export default FloatingAssistant
