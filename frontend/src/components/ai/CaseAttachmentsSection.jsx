import React, { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Paperclip, Upload, Trash2, Download, Sparkles, Loader2, X,
  FileText, Image as ImageIcon, AlertCircle, CheckCircle2, Save,
} from 'lucide-react'
import axiosClient from '../../api/axiosClient'
import { useAuth } from '../../hooks/useAuth'
import { useAIStream } from '../../hooks/useAIStream'

const ACCEPT = '.pdf,.png,.jpg,.jpeg,.webp'
const MAX_MB = 15

const INTERACTION_TYPES = [
  { value: 'escrito', label: 'Escrito' },
  { value: 'audiencia', label: 'Audiencia' },
  { value: 'reunion', label: 'Reunión' },
  { value: 'llamada', label: 'Llamada' },
  { value: 'email', label: 'Email' },
  { value: 'otro', label: 'Otro' },
]

/**
 * Subida de documentación escaneada por caso + análisis con IA.
 * - Subir PDF/imagen → queda adjunto.
 * - "Analizar con IA" → Gemini lee el doc y streamea resumen + texto para gestión.
 * - "Cargar como gestión" → pre-llena y guarda una interacción en el historial.
 */
const CaseAttachmentsSection = ({ caseId, clientId }) => {
  const queryClient = useQueryClient()
  const { isAssistant } = useAuth()
  const fileInputRef = useRef(null)
  const [uploadError, setUploadError] = useState(null)
  const [analyzing, setAnalyzing] = useState(null)   // attachment en análisis
  const [uploading, setUploading] = useState(false)

  const { data: attachments = [], isLoading } = useQuery({
    queryKey: ['caseAttachments', caseId],
    queryFn: async () => (await axiosClient.get(`/cases/${caseId}/attachments/`)).data,
  })

  const uploadMutation = useMutation({
    mutationFn: async (file) => {
      const form = new FormData()
      form.append('file', file)
      return axiosClient.post(`/cases/${caseId}/attachments/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['caseAttachments', caseId] })
      setUploadError(null)
    },
    onError: (err) => {
      setUploadError(err.response?.data?.detail || 'No se pudo subir el archivo.')
    },
    onSettled: () => setUploading(false),
  })

  const deleteMutation = useMutation({
    mutationFn: async (id) => axiosClient.delete(`/cases/${caseId}/attachments/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['caseAttachments', caseId] }),
  })

  const handleFileSelected = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > MAX_MB * 1024 * 1024) {
      setUploadError(`El archivo supera el máximo de ${MAX_MB} MB.`)
      return
    }
    setUploading(true)
    uploadMutation.mutate(file)
    e.target.value = ''  // permitir re-subir el mismo archivo
  }

  const handleDownload = async (att) => {
    try {
      const resp = await axiosClient.get(
        `/cases/${caseId}/attachments/${att.id}/download`,
        { responseType: 'blob' }
      )
      const url = URL.createObjectURL(new Blob([resp.data], { type: att.mime_type }))
      const a = document.createElement('a')
      a.href = url
      a.download = att.filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch {
      alert('No se pudo descargar el archivo.')
    }
  }

  const isImage = (mime) => mime?.startsWith('image/')

  return (
    <div className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium">
      <div className="flex items-center justify-between mb-5">
        <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white flex items-center gap-2">
          <Paperclip className="w-5 h-5 text-legal-gold" />
          Documentación escaneada
        </h3>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="premium-btn-primary py-1.5 px-3 text-xs font-bold flex items-center gap-2 disabled:opacity-50"
        >
          {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
          <span>{uploading ? 'Subiendo…' : 'Subir documento'}</span>
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT}
          onChange={handleFileSelected}
          className="hidden"
        />
      </div>

      <p className="text-xs text-slate-400 mb-4">
        PDF o imagen (PNG/JPG/WEBP), hasta {MAX_MB} MB. La IA puede leer el documento y sugerir una gestión.
      </p>

      {uploadError && (
        <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 px-3 py-2 rounded-lg flex items-start gap-2 text-sm mb-3">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {isLoading ? (
        <div className="h-16 bg-slate-100 dark:bg-slate-800 rounded animate-pulse" />
      ) : attachments.length === 0 ? (
        <div className="py-8 text-center text-slate-400 dark:text-slate-500 font-medium text-sm">
          No hay documentos adjuntos en este expediente.
        </div>
      ) : (
        <ul className="space-y-2">
          {attachments.map((att) => (
            <li
              key={att.id}
              className="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-slate-800 bg-white dark:bg-legal-charcoal-dark"
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                {isImage(att.mime_type)
                  ? <ImageIcon className="w-5 h-5 text-slate-400 flex-shrink-0" />
                  : <FileText className="w-5 h-5 text-slate-400 flex-shrink-0" />}
                <div className="min-w-0">
                  <p className="font-semibold text-sm text-slate-800 dark:text-slate-200 truncate">{att.filename}</p>
                  <p className="text-[11px] text-slate-400 uppercase tracking-wide font-bold">
                    {(att.size_bytes / 1024).toFixed(0)} KB · {new Date(att.created_at).toLocaleDateString('es-ES')}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setAnalyzing(att)}
                  className="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-legal-navy-deep dark:text-legal-gold border border-legal-gold/40 hover:bg-legal-gold/10 flex items-center gap-1.5"
                  title="Analizar con IA"
                >
                  <Sparkles className="w-3.5 h-3.5" /> Analizar
                </button>
                <button
                  onClick={() => handleDownload(att)}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-legal-navy-deep hover:bg-slate-100 dark:hover:bg-slate-800"
                  title="Descargar"
                >
                  <Download className="w-4 h-4" />
                </button>
                {!isAssistant && (
                  <button
                    onClick={() => {
                      if (window.confirm('¿Eliminar este documento?')) deleteMutation.mutate(att.id)
                    }}
                    className="p-1.5 rounded-lg text-red-500 hover:bg-red-500/10"
                    title="Eliminar"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {analyzing && (
        <AnalyzeModal
          caseId={caseId}
          clientId={clientId}
          attachment={analyzing}
          onClose={() => setAnalyzing(null)}
        />
      )}
    </div>
  )
}


/**
 * Extrae la sección "## Texto para gestión" del markdown que devuelve la IA.
 * Si no la encuentra, devuelve todo el texto.
 */
function extractGestionText(markdown) {
  if (!markdown) return ''
  const m = markdown.match(/##\s*Texto para gesti[oó]n\s*\n([\s\S]*?)(?:\n##\s|$)/i)
  return (m ? m[1] : markdown).trim()
}


const AnalyzeModal = ({ caseId, clientId, attachment, onClose }) => {
  const queryClient = useQueryClient()
  const { streamingText, isStreaming, error, send } = useAIStream()
  const [started, setStarted] = useState(false)
  const [gestionType, setGestionType] = useState('escrito')
  const [gestionText, setGestionText] = useState('')
  const [showGestion, setShowGestion] = useState(false)
  const [saved, setSaved] = useState(false)

  // Disparar el análisis al abrir
  React.useEffect(() => {
    if (!started) {
      setStarted(true)
      send(`/api/ai/cases/${caseId}/attachments/${attachment.id}/analyze`, {})
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [started])

  const saveMutation = useMutation({
    mutationFn: async () => axiosClient.post('/interactions', {
      interaction_type: gestionType,
      description: gestionText.trim(),
      duration_minutes: 0,
      case_id: caseId,
      client_id: clientId,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['caseInteractions', String(caseId)] })
      queryClient.invalidateQueries({ queryKey: ['caseInteractions', caseId] })
      setSaved(true)
    },
  })

  const prepareGestion = () => {
    setGestionText(extractGestionText(streamingText))
    setShowGestion(true)
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-legal-charcoal-medium rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2.5 min-w-0">
            <Sparkles className="w-5 h-5 text-legal-gold flex-shrink-0" />
            <div className="min-w-0">
              <h2 className="font-serif font-bold text-base text-legal-navy-deep dark:text-white truncate">
                Análisis IA del documento
              </h2>
              <p className="text-xs text-slate-500 truncate">{attachment.filename}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <div className="border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-legal-charcoal-dark p-4 min-h-[200px]">
            {isStreaming && !streamingText && (
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <Loader2 className="w-4 h-4 animate-spin" /> Leyendo el documento…
              </div>
            )}
            {streamingText && (
              <pre className="whitespace-pre-wrap text-sm font-sans text-slate-800 dark:text-slate-200 leading-relaxed">
                {streamingText}
                {isStreaming && <span className="ml-1 inline-block w-1.5 h-3 bg-current opacity-60 animate-pulse align-middle" />}
              </pre>
            )}
            {error && (
              <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 px-3 py-2 rounded-lg flex items-start gap-2 text-sm">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>

          {showGestion && (
            <div className="border border-legal-gold/30 rounded-lg p-4 bg-legal-cream/30 dark:bg-legal-charcoal-dark space-y-3">
              <h4 className="text-xs font-bold uppercase text-legal-gold">Nueva gestión a partir del documento</h4>
              <div className="flex gap-2">
                <select
                  value={gestionType}
                  onChange={(e) => setGestionType(e.target.value)}
                  className="premium-input text-sm w-40"
                >
                  {INTERACTION_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <textarea
                rows={4}
                value={gestionText}
                onChange={(e) => setGestionText(e.target.value)}
                className="premium-input text-sm"
              />
              {saved ? (
                <div className="text-emerald-600 dark:text-emerald-400 text-sm flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> Gestión cargada en el historial.
                </div>
              ) : (
                <button
                  onClick={() => saveMutation.mutate()}
                  disabled={!gestionText.trim() || saveMutation.isPending}
                  className="premium-btn-primary py-2 px-4 text-sm flex items-center gap-2 disabled:opacity-50"
                >
                  {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Guardar gestión
                </button>
              )}
            </div>
          )}
        </div>

        <div className="px-6 py-3 border-t border-slate-100 dark:border-slate-800 bg-legal-cream/30 dark:bg-legal-charcoal-dark flex items-center justify-between gap-3">
          <p className="text-[11px] text-slate-400 italic">
            Lectura asistida por IA. Verificá el contenido contra el documento original.
          </p>
          {!showGestion && !isStreaming && streamingText && !error && (
            <button
              onClick={prepareGestion}
              className="premium-btn-secondary py-2 px-4 text-sm flex items-center gap-2 flex-shrink-0"
            >
              <FileText className="w-4 h-4" /> Cargar como gestión
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default CaseAttachmentsSection
