import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText, Plus, Lock, Edit, Trash2, X, Sparkles, AlertCircle,
  CheckCircle2, Loader2,
} from 'lucide-react'
import axiosClient from '../api/axiosClient'

const VARIABLE_TYPES = [
  { value: 'text', label: 'Texto corto' },
  { value: 'textarea', label: 'Texto largo' },
  { value: 'money', label: 'Monto' },
  { value: 'date', label: 'Fecha' },
]

const EMPTY_FORM = {
  key: '',
  name: '',
  description: '',
  instruction: '',
  default_title: '',
  is_active: true,
  variables: [],
}


const TemplatesPage = () => {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState(null)
  const [creating, setCreating] = useState(false)

  const { data: catalog = [], isLoading } = useQuery({
    queryKey: ['templatesCatalog'],
    queryFn: async () => (await axiosClient.get('/templates/catalog')).data,
  })

  const deleteMutation = useMutation({
    mutationFn: async (id) => axiosClient.delete(`/templates/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['templatesCatalog'] }),
  })

  const handleEdit = async (item) => {
    if (item.is_builtin) return
    const resp = await axiosClient.get(`/templates/${item.custom_id}`)
    setEditing(resp.data)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <Sparkles className="w-7 h-7 text-legal-gold" />
          <div>
            <h1 className="font-serif text-2xl font-bold text-legal-navy-deep dark:text-white">
              Templates de IA
            </h1>
            <p className="text-sm text-slate-500">
              Catálogo de plantillas para redacción asistida. Los del sistema son de solo lectura.
            </p>
          </div>
        </div>
        <button
          onClick={() => setCreating(true)}
          className="premium-btn-primary py-2 px-4 text-sm flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> Nuevo template
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-legal-gold" />
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {catalog.map((item) => (
            <TemplateCard
              key={item.key}
              item={item}
              onEdit={() => handleEdit(item)}
              onDelete={() => {
                if (window.confirm(`¿Eliminar template "${item.name}"?`)) {
                  deleteMutation.mutate(item.custom_id)
                }
              }}
            />
          ))}
        </div>
      )}

      {(creating || editing) && (
        <TemplateFormModal
          initial={editing}
          onClose={() => { setCreating(false); setEditing(null) }}
          onSaved={() => {
            queryClient.invalidateQueries({ queryKey: ['templatesCatalog'] })
            queryClient.invalidateQueries({ queryKey: ['aiTemplates'] })
            setCreating(false)
            setEditing(null)
          }}
        />
      )}
    </div>
  )
}


const TemplateCard = ({ item, onEdit, onDelete }) => (
  <div className={`rounded-2xl p-5 border ${
    item.is_builtin
      ? 'bg-legal-cream/30 dark:bg-legal-charcoal-dark border-legal-gold/20'
      : 'bg-white dark:bg-legal-charcoal-medium border-slate-100 dark:border-slate-800'
  }`}>
    <div className="flex items-start justify-between mb-2">
      <div className="flex items-center gap-2">
        <FileText className="w-4 h-4 text-legal-gold" />
        <h3 className="font-serif font-bold text-sm text-legal-navy-deep dark:text-white">{item.name}</h3>
      </div>
      {item.is_builtin ? (
        <span className="text-[10px] font-bold uppercase text-legal-gold tracking-wide flex items-center gap-1">
          <Lock className="w-3 h-3" /> Sistema
        </span>
      ) : (
        <span className={`text-[10px] font-bold uppercase tracking-wide ${
          item.is_active ? 'text-emerald-600' : 'text-slate-400'
        }`}>
          {item.is_active ? 'Activo' : 'Inactivo'}
        </span>
      )}
    </div>
    <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 min-h-[2rem]">
      {item.description || 'Sin descripción.'}
    </p>
    <p className="text-[11px] text-slate-400 mt-2 uppercase tracking-wide font-bold">
      {item.variable_count} {item.variable_count === 1 ? 'variable' : 'variables'} · clave: <code className="text-legal-gold">{item.key}</code>
    </p>
    {!item.is_builtin && (
      <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
        <button
          onClick={onEdit}
          className="flex-1 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800 flex items-center justify-center gap-1.5"
        >
          <Edit className="w-3.5 h-3.5" /> Editar
        </button>
        <button
          onClick={onDelete}
          className="py-1.5 px-3 rounded-lg text-xs font-semibold text-red-500 border border-red-200 hover:bg-red-50 dark:border-red-500/40 dark:hover:bg-red-500/10 flex items-center justify-center"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    )}
  </div>
)


const TemplateFormModal = ({ initial, onClose, onSaved }) => {
  const isEdit = Boolean(initial)
  const [form, setForm] = useState(initial || EMPTY_FORM)
  const [error, setError] = useState(null)

  const mutation = useMutation({
    mutationFn: async () => {
      if (isEdit) {
        const { key, ...patch } = form  // key is immutable post-create
        return axiosClient.put(`/templates/${initial.id}`, patch)
      }
      return axiosClient.post('/templates/', form)
    },
    onSuccess: onSaved,
    onError: (err) => {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map(d => `${d.loc?.join('.') ?? ''}: ${d.msg}`).join(' · '))
      } else {
        setError(detail || 'No se pudo guardar el template.')
      }
    },
  })

  const update = (key, value) => setForm(prev => ({ ...prev, [key]: value }))

  const addVariable = () => {
    update('variables', [
      ...form.variables,
      { key: '', label: '', type: 'text', required: true, placeholder: '', help: '' },
    ])
  }
  const updateVariable = (i, patch) => {
    const next = form.variables.map((v, idx) => idx === i ? { ...v, ...patch } : v)
    update('variables', next)
  }
  const removeVariable = (i) => {
    update('variables', form.variables.filter((_, idx) => idx !== i))
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-legal-charcoal-medium rounded-2xl shadow-2xl w-full max-w-3xl max-h-[92vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800">
          <h2 className="font-serif font-bold text-lg text-legal-navy-deep dark:text-white">
            {isEdit ? 'Editar template' : 'Nuevo template'}
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          <Field label="Clave única" required help="Identificador interno. Letras minúsculas, números o guión bajo (3-64 chars). No se puede modificar luego.">
            <input
              value={form.key || ''}
              onChange={(e) => update('key', e.target.value.toLowerCase())}
              disabled={isEdit}
              placeholder="demanda_laboral"
              className="premium-input"
            />
          </Field>

          <Field label="Nombre visible" required>
            <input
              value={form.name || ''}
              onChange={(e) => update('name', e.target.value)}
              placeholder="Demanda laboral por despido"
              className="premium-input"
            />
          </Field>

          <Field label="Descripción" help="Aparece en el picker de templates dentro del expediente.">
            <input
              value={form.description || ''}
              onChange={(e) => update('description', e.target.value)}
              placeholder="Para reclamos contra el empleador por despido sin causa…"
              className="premium-input"
            />
          </Field>

          <Field label="Título por defecto del documento generado">
            <input
              value={form.default_title || ''}
              onChange={(e) => update('default_title', e.target.value)}
              placeholder="Demanda laboral"
              className="premium-input"
            />
          </Field>

          <Field
            label="Instrucción para la IA"
            required
            help="Lo que el modelo lee como guía: estructura, tono, qué incluir/omitir. Sé específico."
          >
            <textarea
              rows={6}
              value={form.instruction || ''}
              onChange={(e) => update('instruction', e.target.value)}
              placeholder="Redactá una DEMANDA LABORAL en formato argentino. Estructura: SUMA, hechos, derecho, petitorio…"
              className="premium-input font-mono text-xs"
            />
          </Field>

          <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-serif font-bold text-sm text-legal-navy-deep dark:text-white">
                Variables del template
              </h4>
              <button
                onClick={addVariable}
                className="text-xs font-semibold text-legal-gold hover:text-legal-gold/80 flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" /> Agregar variable
              </button>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Estas son las preguntas que se le hacen al abogado cuando usa este template.
            </p>

            {form.variables.length === 0 ? (
              <p className="text-xs text-slate-400 italic text-center py-3 border border-dashed border-slate-200 dark:border-slate-700 rounded">
                Sin variables. El modelo redactará solo en base al expediente.
              </p>
            ) : (
              <div className="space-y-2">
                {form.variables.map((v, i) => (
                  <VariableRow
                    key={i}
                    variable={v}
                    onChange={(patch) => updateVariable(i, patch)}
                    onRemove={() => removeVariable(i)}
                  />
                ))}
              </div>
            )}
          </div>

          <Field>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => update('is_active', e.target.checked)}
                className="rounded border-slate-300 text-legal-gold focus:ring-legal-gold"
              />
              <span>Template activo (visible en el picker)</span>
            </label>
          </Field>

          {error && (
            <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 px-3 py-2 rounded-lg flex items-start gap-2 text-sm">
              <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        <div className="px-6 py-3 border-t border-slate-100 dark:border-slate-800 bg-legal-cream/30 dark:bg-legal-charcoal-dark flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800">
            Cancelar
          </button>
          <button
            onClick={() => { setError(null); mutation.mutate() }}
            disabled={mutation.isPending}
            className="premium-btn-primary py-2 px-4 text-sm flex items-center gap-2 disabled:opacity-50"
          >
            {mutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <CheckCircle2 className="w-4 h-4" />
            )}
            {isEdit ? 'Guardar cambios' : 'Crear template'}
          </button>
        </div>
      </div>
    </div>
  )
}


const Field = ({ label, required, help, children }) => (
  <div>
    {label && (
      <label className="block text-xs font-bold uppercase tracking-wide text-slate-500 mb-1">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
    )}
    {children}
    {help && <p className="text-xs text-slate-400 mt-1">{help}</p>}
  </div>
)


const VariableRow = ({ variable, onChange, onRemove }) => (
  <div className="bg-slate-50 dark:bg-legal-charcoal-dark border border-slate-100 dark:border-slate-800 rounded-lg p-3 space-y-2">
    <div className="grid sm:grid-cols-12 gap-2">
      <input
        value={variable.key}
        onChange={(e) => onChange({ key: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '') })}
        placeholder="clave"
        className="premium-input sm:col-span-3 text-xs font-mono"
      />
      <input
        value={variable.label}
        onChange={(e) => onChange({ label: e.target.value })}
        placeholder="Etiqueta visible"
        className="premium-input sm:col-span-5 text-sm"
      />
      <select
        value={variable.type}
        onChange={(e) => onChange({ type: e.target.value })}
        className="premium-input sm:col-span-3 text-sm"
      >
        {VARIABLE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
      </select>
      <button
        onClick={onRemove}
        className="sm:col-span-1 p-2 rounded-lg text-red-500 hover:bg-red-500/10 flex items-center justify-center"
        aria-label="Quitar"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
    <div className="grid sm:grid-cols-12 gap-2">
      <input
        value={variable.placeholder}
        onChange={(e) => onChange({ placeholder: e.target.value })}
        placeholder="Placeholder (opcional)"
        className="premium-input sm:col-span-11 text-xs"
      />
      <label className="sm:col-span-1 flex items-center justify-center gap-1 text-xs text-slate-500">
        <input
          type="checkbox"
          checked={variable.required}
          onChange={(e) => onChange({ required: e.target.checked })}
          className="rounded border-slate-300 text-legal-gold focus:ring-legal-gold"
        />
        Obl.
      </label>
    </div>
  </div>
)


export default TemplatesPage
