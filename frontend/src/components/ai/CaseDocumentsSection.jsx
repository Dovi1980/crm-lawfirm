import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText, Plus, Trash2, X, Loader2, Sparkles, Eye, AlertCircle,
  Download, FileType, FileDown,
} from 'lucide-react'
import axiosClient from '../../api/axiosClient'
import { useAuth } from '../../hooks/useAuth'
import DocumentDraftModal from './DocumentDraftModal'

/**
 * Card with the list of AI-drafted documents persisted for a case, plus
 * a button to open the drafting modal.
 */
const CaseDocumentsSection = ({ caseId }) => {
  const queryClient = useQueryClient()
  const { isAssistant } = useAuth()
  const [draftOpen, setDraftOpen] = useState(false)
  const [viewing, setViewing] = useState(null)

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['caseDocuments', caseId],
    queryFn: async () =>
      (await axiosClient.get(`/cases/${caseId}/documents/`)).data,
  })

  const archiveMutation = useMutation({
    mutationFn: async (id) => axiosClient.delete(`/cases/${caseId}/documents/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['caseDocuments', caseId] }),
  })

  const handleView = async (doc) => {
    try {
      const resp = await axiosClient.get(`/cases/${caseId}/documents/${doc.id}`)
      setViewing(resp.data)
    } catch {
      setViewing({ ...doc, content: '[No se pudo cargar el contenido]' })
    }
  }

  const handleDownload = async (doc, format) => {
    try {
      const resp = await axiosClient.get(
        `/cases/${caseId}/documents/${doc.id}/export`,
        { params: { format }, responseType: 'blob' }
      )
      const blob = new Blob([resp.data], {
        type: format === 'docx'
          ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
          : 'application/pdf',
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${doc.title.replace(/[^A-Za-z0-9_\-]+/g, '_').slice(0, 80) || 'documento'}.${format}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('No se pudo descargar el documento.')
    }
  }

  return (
    <div className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium">
      <div className="flex items-center justify-between mb-5">
        <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white flex items-center gap-2">
          <FileText className="w-5 h-5 text-legal-gold" />
          Documentos redactados
        </h3>
        <button
          onClick={() => setDraftOpen(true)}
          className="premium-btn-primary py-1.5 px-3 text-xs font-bold flex items-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          <span>Nueva redacción</span>
        </button>
      </div>

      {isLoading ? (
        <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded animate-pulse" />
      ) : documents.length === 0 ? (
        <div className="py-8 text-center text-slate-400 dark:text-slate-500 font-medium text-sm">
          Aún no hay documentos generados para este expediente.
        </div>
      ) : (
        <ul className="space-y-2">
          {documents.map((d) => (
            <li
              key={d.id}
              className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-legal-charcoal-dark"
            >
              <div className="min-w-0 flex-1">
                <p className="font-semibold text-sm text-slate-800 dark:text-slate-200 truncate">
                  {d.title}
                </p>
                <p className="text-[11px] text-slate-400 uppercase tracking-wide font-bold">
                  {d.template_key.replace('_', ' ')} ·{' '}
                  {new Date(d.created_at).toLocaleDateString('es-ES')}{' '}
                  {new Date(d.created_at).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => handleView(d)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-legal-navy-deep hover:bg-slate-100 dark:hover:bg-slate-800"
                  aria-label="Ver"
                  title="Ver"
                >
                  <Eye className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDownload(d, 'docx')}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-500/10"
                  aria-label="Descargar Word"
                  title="Descargar .docx"
                >
                  <FileType className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDownload(d, 'pdf')}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10"
                  aria-label="Descargar PDF"
                  title="Descargar PDF"
                >
                  <FileDown className="w-4 h-4" />
                </button>
                {!isAssistant && (
                  <button
                    onClick={() => {
                      if (window.confirm('¿Archivar este documento?')) {
                        archiveMutation.mutate(d.id)
                      }
                    }}
                    className="p-1.5 rounded-lg text-red-500 hover:bg-red-500/10"
                    aria-label="Archivar"
                    title="Archivar"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <DocumentDraftModal
        caseId={caseId}
        isOpen={draftOpen}
        onClose={() => setDraftOpen(false)}
      />

      {/* Viewer modal */}
      {viewing && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={() => setViewing(null)}>
          <div
            className="bg-white dark:bg-legal-charcoal-medium rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800">
              <h2 className="font-serif font-bold text-lg text-legal-navy-deep dark:text-white truncate">
                {viewing.title}
              </h2>
              <button onClick={() => setViewing(null)} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <pre className="whitespace-pre-wrap text-sm font-sans text-slate-800 dark:text-slate-200 leading-relaxed">
                {viewing.content}
              </pre>
            </div>
            <div className="px-6 py-3 border-t border-slate-100 dark:border-slate-800 bg-legal-cream/30 dark:bg-legal-charcoal-dark flex items-center justify-between gap-3">
              <p className="text-xs text-slate-500 flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5" />
                Borrador generado por IA. Validá su contenido antes de firmar o presentar.
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDownload(viewing, 'docx')}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-blue-600 border border-blue-200 hover:bg-blue-50 dark:border-blue-500/40 dark:hover:bg-blue-500/10 flex items-center gap-1.5"
                >
                  <FileType className="w-3.5 h-3.5" /> Word
                </button>
                <button
                  onClick={() => handleDownload(viewing, 'pdf')}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold text-red-600 border border-red-200 hover:bg-red-50 dark:border-red-500/40 dark:hover:bg-red-500/10 flex items-center gap-1.5"
                >
                  <FileDown className="w-3.5 h-3.5" /> PDF
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CaseDocumentsSection
