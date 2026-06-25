import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, MessageSquare, FileText, Loader2, AlertCircle, X } from 'lucide-react'
import axiosClient from '../../api/axiosClient'
import ChatPanel from './ChatPanel'

/**
 * Per-case AI panel.
 * - "Resumir" generates a one-shot executive summary using a sync endpoint.
 * - "Hablar sobre el caso" opens a chat panel with the case as system context.
 */
const CaseAIPanel = ({ caseId }) => {
  const [chatOpen, setChatOpen] = useState(false)
  const [summary, setSummary] = useState(null)
  const [summaryError, setSummaryError] = useState(null)

  const summaryMutation = useMutation({
    mutationFn: async () => {
      const resp = await axiosClient.post(`/ai/cases/${caseId}/summary`)
      return resp.data.summary
    },
    onSuccess: (text) => {
      setSummary(text)
      setSummaryError(null)
    },
    onError: (err) => {
      const detail = err.response?.data?.detail || 'No se pudo generar el resumen.'
      setSummaryError(detail)
    },
  })

  return (
    <div className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
        <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-legal-gold" />
          Asistente IA del expediente
        </h3>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <button
          onClick={() => summaryMutation.mutate()}
          disabled={summaryMutation.isPending}
          className="premium-btn-secondary py-2 px-4 text-sm flex items-center gap-2 disabled:opacity-50"
        >
          {summaryMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <FileText className="w-4 h-4" />
          )}
          <span>{summaryMutation.isPending ? 'Generando…' : 'Resumir caso'}</span>
        </button>

        <button
          onClick={() => setChatOpen(true)}
          className="premium-btn-primary py-2 px-4 text-sm flex items-center gap-2"
        >
          <MessageSquare className="w-4 h-4" />
          <span>Hablar sobre el caso</span>
        </button>
      </div>

      {summaryError && (
        <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 px-3 py-2 rounded-lg flex items-start gap-2 text-sm mb-3">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{summaryError}</span>
        </div>
      )}

      {summary && (
        <div className="bg-legal-cream/30 dark:bg-legal-charcoal-dark border border-legal-gold/20 rounded-lg p-4 mt-2 relative">
          <button
            onClick={() => setSummary(null)}
            className="absolute top-2 right-2 p-1 text-slate-400 hover:text-slate-600"
            aria-label="Cerrar resumen"
          >
            <X className="w-4 h-4" />
          </button>
          <h4 className="text-xs font-bold uppercase text-legal-gold mb-2">Resumen generado por IA</h4>
          <pre className="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200 font-sans leading-relaxed">
            {summary}
          </pre>
          <p className="mt-3 pt-3 border-t border-legal-gold/10 text-[11px] text-slate-400 italic">
            Sugerencia generada por IA. Revisá antes de usarla en una comunicación oficial.
          </p>
        </div>
      )}

      {/* Slide-over chat */}
      {chatOpen && (
        <div className="fixed inset-0 z-50 bg-black/30 flex justify-end" onClick={() => setChatOpen(false)}>
          <div
            className="w-full sm:w-[440px] h-full bg-white dark:bg-legal-charcoal-medium shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <ChatPanel
              endpoint={`/api/ai/cases/${caseId}/chat`}
              title="Chat sobre el expediente"
              subtitle="El modelo ya conoce los datos del caso"
              emptyHint="Preguntá sobre los hechos, las gestiones registradas o los próximos pasos. El modelo ve el dossier completo del expediente."
              onClose={() => setChatOpen(false)}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default CaseAIPanel
