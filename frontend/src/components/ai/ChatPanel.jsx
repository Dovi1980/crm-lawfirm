import React, { useEffect, useRef, useState } from 'react'
import { Sparkles, X, Send, StopCircle, Loader2, AlertCircle } from 'lucide-react'
import { useAIStream } from '../../hooks/useAIStream'

/**
 * Generic chat panel powered by an SSE backend endpoint.
 *
 * Props:
 *   endpoint   string  — e.g. "/api/ai/assistant" or "/api/ai/cases/42/chat"
 *   title      string
 *   subtitle?  string
 *   emptyHint? string
 *   onClose?   () => void
 */
const ChatPanel = ({ endpoint, title, subtitle, emptyHint, onClose }) => {
  const [messages, setMessages] = useState([])  // {role, content}[]
  const [input, setInput] = useState('')
  const scrollRef = useRef(null)
  const textareaRef = useRef(null)

  const { streamingText, isStreaming, error, send, abort } = useAIStream()

  // Autoscroll on new content
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, streamingText])

  // When stream finishes, commit the assembled assistant message into history
  useEffect(() => {
    if (!isStreaming && streamingText) {
      setMessages(prev => [...prev, { role: 'assistant', content: streamingText }])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isStreaming])

  const handleSubmit = (e) => {
    e?.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isStreaming) return

    const next = [...messages, { role: 'user', content: trimmed }]
    setMessages(next)
    setInput('')
    // Send full history so the model has context
    send(endpoint, { messages: next })
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-legal-charcoal-medium border border-slate-200 dark:border-slate-800 shadow-premium rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-800 bg-legal-cream/40 dark:bg-legal-charcoal-dark">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full bg-legal-navy-deep dark:bg-legal-gold text-legal-gold dark:text-legal-navy-deep flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-serif font-bold text-legal-navy-deep dark:text-white text-sm leading-tight">{title}</h3>
            {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>}
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500"
            aria-label="Cerrar"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center text-sm text-slate-400 dark:text-slate-500 py-8 px-2">
            {emptyHint || 'Empezá la conversación. Las respuestas son sugerencias generadas por IA; verificá antes de actuar.'}
          </div>
        )}

        {messages.map((m, i) => (
          <Message key={i} role={m.role} content={m.content} />
        ))}

        {isStreaming && streamingText && (
          <Message role="assistant" content={streamingText} streaming />
        )}
        {isStreaming && !streamingText && (
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Pensando…</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 px-3 py-2 rounded-lg flex items-start gap-2 text-xs">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-slate-100 dark:border-slate-800 p-3 flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribí tu consulta…"
          rows={1}
          className="flex-1 resize-none rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-legal-charcoal-dark px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-legal-gold/50 max-h-32"
        />
        {isStreaming ? (
          <button
            type="button"
            onClick={abort}
            className="px-3 py-2 rounded-lg bg-red-500/10 text-red-600 border border-red-200 hover:bg-red-500/20 flex items-center gap-1 text-sm font-medium"
          >
            <StopCircle className="w-4 h-4" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="px-3 py-2 rounded-lg bg-legal-navy-deep text-legal-gold border border-legal-gold disabled:opacity-40 disabled:cursor-not-allowed hover:bg-legal-navy-medium flex items-center gap-1 text-sm font-medium"
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </form>
    </div>
  )
}

const Message = ({ role, content, streaming }) => {
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-sm whitespace-pre-wrap leading-relaxed ${
          isUser
            ? 'bg-legal-navy-deep text-legal-cream rounded-br-sm'
            : 'bg-slate-100 dark:bg-legal-charcoal-dark text-slate-800 dark:text-slate-200 rounded-bl-sm'
        }`}
      >
        {content}
        {streaming && <span className="ml-1 inline-block w-1.5 h-3 bg-current opacity-60 animate-pulse align-middle" />}
      </div>
    </div>
  )
}

export default ChatPanel
