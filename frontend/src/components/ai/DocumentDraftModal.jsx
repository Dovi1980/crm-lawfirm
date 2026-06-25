import React, { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  X, FileText, ChevronLeft, ChevronRight, Sparkles,
  Loader2, Save, StopCircle, AlertCircle, CheckCircle2,
} from 'lucide-react'
import axiosClient from '../../api/axiosClient'
import { useAIStream } from '../../hooks/useAIStream'

/**
 * Three-step modal for AI document drafting:
 *   1. Pick a template
 *   2. Fill in the template's variables
 *   3. Stream the draft, then save or discard
 *
 * Props:
 *   caseId: number
 *   isOpen: boolean
 *   onClose: () => void
 *   onSaved?: () => void   // notify parent so it can refetch the document list
 */
const DocumentDraftModal = ({ caseId, isOpen, onClose, onSaved }) => {
  const [step, setStep] = useState(1)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [values, setValues] = useState({})
  const [title, setTitle] = useState('')
  const [draftContent, setDraftContent] = useState('')
  const [saveError, setSaveError] = useState(null)
  const queryClient = useQueryClient()

  const { data: templates = [], isLoading: templatesLoading } = useQuery({
    queryKey: ['aiTemplates'],
    queryFn: async () => (await axiosClient.get('/ai/templates')).data,
    enabled: isOpen,
  })

  const { streamingText, isStreaming, error: streamError, send, abort, reset } =
    useAIStream({
      onDone: (full) => setDraftContent(full),
    })

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        template_key: selectedTemplate.key,
        title: title.trim() || selectedTemplate.default_title || selectedTemplate.name,
        content: draftContent,
      }
      return (await axiosClient.post(`/cases/${caseId}/documents/`, payload)).data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['caseDocuments', caseId] })
      onSaved?.()
      handleClose()
    },
    onError: (err) => {
      setSaveError(err.response?.data?.detail || 'No se pudo guardar el documento.')
    },
  })

  const handleClose = () => {
    abort()
    setStep(1)
    setSelectedTemplate(null)
    setValues({})
    setTitle('')
    setDraftContent('')
    setSaveError(null)
    reset()
    onClose()
  }

  const handleTemplatePick = (tpl) => {
    setSelectedTemplate(tpl)
    setTitle(tpl.default_title || tpl.name)
    // Seed variables with empty strings
    const seed = {}
    tpl.variables.forEach((v) => { seed[v.key] = '' })
    setValues(seed)
    setStep(2)
  }

  const requiredMissing =
    selectedTemplate?.variables.some((v) => v.required && !(values[v.key] || '').trim())

  const handleGenerate = () => {
    setStep(3)
    setDraftContent('')
    send(`/api/ai/cases/${caseId}/document/generate`, {
      template_key: selectedTemplate.key,
      variables: values,
    })
  }

  // Auto-finalize: when streaming finishes and we have text, expose Save button
  useEffect(() => {
    if (!isStreaming && streamingText && !draftContent) {
      setDraftContent(streamingText)
    }
  }, [isStreaming, streamingText, draftContent])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={handleClose}>
      <div
        className="bg-white dark:bg-legal-charcoal-medium rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-legal-navy-deep dark:bg-legal-gold text-legal-gold dark:text-legal-navy-deep flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-serif font-bold text-lg text-legal-navy-deep dark:text-white">
                Redacción asistida
              </h2>
              <p className="text-xs text-slate-500">
                Paso {step} de 3 — {step === 1 ? 'elegí un template' : step === 2 ? 'completá los datos' : 'revisá y guardá'}
              </p>
            </div>
          </div>
          <button onClick={handleClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {step === 1 && (
            <Step1Templates
              templates={templates}
              loading={templatesLoading}
              onPick={handleTemplatePick}
            />
          )}
          {step === 2 && selectedTemplate && (
            <Step2Variables
              template={selectedTemplate}
              values={values}
              onChange={(key, v) => setValues((prev) => ({ ...prev, [key]: v }))}
            />
          )}
          {step === 3 && (
            <Step3Preview
              streamingText={streamingText}
              draftContent={draftContent}
              isStreaming={isStreaming}
              error={streamError}
              title={title}
              onTitleChange={setTitle}
            />
          )}
        </div>

        {/* Footer / actions */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between bg-legal-cream/30 dark:bg-legal-charcoal-dark">
          {step > 1 && step < 3 && (
            <button
              onClick={() => setStep(step - 1)}
              className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
            >
              <ChevronLeft className="w-4 h-4" /> Atrás
            </button>
          )}
          {step === 3 && !isStreaming && (
            <button
              onClick={() => { setStep(2); setDraftContent(''); reset() }}
              className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
            >
              <ChevronLeft className="w-4 h-4" /> Volver y reintentar
            </button>
          )}
          <div className="flex-1" />

          {saveError && (
            <span className="text-xs text-red-600 mr-3 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5" /> {saveError}
            </span>
          )}

          {step === 2 && (
            <button
              onClick={handleGenerate}
              disabled={requiredMissing}
              className="premium-btn-primary py-2 px-4 text-sm flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Sparkles className="w-4 h-4" /> Generar borrador <ChevronRight className="w-4 h-4" />
            </button>
          )}
          {step === 3 && isStreaming && (
            <button
              onClick={abort}
              className="px-4 py-2 rounded-lg bg-red-500/10 text-red-600 border border-red-200 hover:bg-red-500/20 flex items-center gap-2 text-sm"
            >
              <StopCircle className="w-4 h-4" /> Detener
            </button>
          )}
          {step === 3 && !isStreaming && draftContent && (
            <button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending}
              className="premium-btn-primary py-2 px-4 text-sm flex items-center gap-2 disabled:opacity-50"
            >
              {saveMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Guardar documento
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/* --- Step 1: pick template --- */
const Step1Templates = ({ templates, loading, onPick }) => {
  if (loading) {
    return <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-legal-gold" /></div>
  }
  if (!templates.length) {
    return <p className="text-center text-slate-400 py-10">No hay templates disponibles.</p>
  }
  return (
    <div className="grid sm:grid-cols-2 gap-4">
      {templates.map((t) => (
        <button
          key={t.key}
          onClick={() => onPick(t)}
          className="text-left p-4 rounded-xl border-2 border-slate-100 dark:border-slate-800 hover:border-legal-gold hover:bg-legal-gold/5 transition-colors group"
        >
          <div className="flex items-center gap-2 mb-2">
            <FileText className="w-4 h-4 text-legal-gold" />
            <h4 className="font-serif font-bold text-sm text-legal-navy-deep dark:text-white">{t.name}</h4>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t.description}</p>
          <p className="text-[10px] uppercase font-bold text-slate-400 mt-2 tracking-wide">
            {t.variables.length} {t.variables.length === 1 ? 'variable' : 'variables'}
          </p>
        </button>
      ))}
    </div>
  )
}

/* --- Step 2: fill variables --- */
const Step2Variables = ({ template, values, onChange }) => (
  <div className="space-y-4">
    <div className="bg-legal-cream/40 dark:bg-legal-charcoal-dark p-3 rounded-lg border border-legal-gold/20">
      <h4 className="font-serif font-bold text-sm text-legal-navy-deep dark:text-white mb-1">{template.name}</h4>
      <p className="text-xs text-slate-500">{template.description}</p>
    </div>
    {template.variables.map((v) => (
      <div key={v.key}>
        <label className="block text-xs font-bold uppercase tracking-wide text-slate-500 mb-1">
          {v.label} {v.required && <span className="text-red-500">*</span>}
        </label>
        {v.type === 'textarea' ? (
          <textarea
            rows={3}
            value={values[v.key] || ''}
            onChange={(e) => onChange(v.key, e.target.value)}
            placeholder={v.placeholder}
            className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-legal-charcoal-dark px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-legal-gold/50"
          />
        ) : (
          <input
            type={v.type === 'money' ? 'number' : v.type === 'date' ? 'date' : 'text'}
            value={values[v.key] || ''}
            onChange={(e) => onChange(v.key, e.target.value)}
            placeholder={v.placeholder}
            className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-legal-charcoal-dark px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-legal-gold/50"
          />
        )}
        {v.help && <p className="text-xs text-slate-400 mt-1">{v.help}</p>}
      </div>
    ))}
  </div>
)

/* --- Step 3: streaming preview --- */
const Step3Preview = ({ streamingText, draftContent, isStreaming, error, title, onTitleChange }) => {
  const text = draftContent || streamingText
  return (
    <div className="space-y-3">
      {!isStreaming && draftContent && (
        <div>
          <label className="block text-xs font-bold uppercase tracking-wide text-slate-500 mb-1">
            Título para guardar
          </label>
          <input
            value={title}
            onChange={(e) => onTitleChange(e.target.value)}
            className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-legal-charcoal-dark px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-legal-gold/50"
          />
        </div>
      )}
      <div className="border border-slate-200 dark:border-slate-700 rounded-lg bg-white dark:bg-legal-charcoal-dark p-4 min-h-[300px] max-h-[420px] overflow-y-auto">
        {isStreaming && !text && (
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" /> Redactando borrador…
          </div>
        )}
        {text && (
          <pre className="whitespace-pre-wrap text-sm font-sans text-slate-800 dark:text-slate-200 leading-relaxed">
            {text}
            {isStreaming && <span className="ml-1 inline-block w-1.5 h-3 bg-current opacity-60 animate-pulse align-middle" />}
          </pre>
        )}
      </div>
      {error && (
        <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 px-3 py-2 rounded-lg flex items-start gap-2 text-sm">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {!isStreaming && draftContent && !error && (
        <div className="bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 text-emerald-700 dark:text-emerald-400 px-3 py-2 rounded-lg flex items-start gap-2 text-sm">
          <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>Borrador listo. Revisalo antes de guardar — recordá que es una sugerencia, no un documento final.</span>
        </div>
      )}
    </div>
  )
}

export default DocumentDraftModal
