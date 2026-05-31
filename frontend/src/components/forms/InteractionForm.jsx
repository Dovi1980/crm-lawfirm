import React, { useState } from 'react'

const InteractionForm = ({ 
  caseId = null, 
  clientId = null, 
  onSubmit, 
  onCancel,
  isSubmitting = false
}) => {
  const [formData, setFormData] = useState({
    interaction_type: 'llamada',
    description: '',
    duration_minutes: 15,
    case_id: caseId || '',
    client_id: clientId || ''
  })

  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }))
  }

  const validate = () => {
    const tempErrors = {}
    if (!formData.description.trim()) tempErrors.description = 'La descripción de la actividad es obligatoria.'
    if (formData.duration_minutes < 0) tempErrors.duration_minutes = 'La duración debe ser positiva.'
    setErrors(tempErrors)
    return Object.keys(tempErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (validate()) {
      onSubmit({
        ...formData,
        duration_minutes: parseInt(formData.duration_minutes),
        case_id: formData.case_id ? parseInt(formData.case_id) : null,
        client_id: formData.client_id ? parseInt(formData.client_id) : null
      })
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Interaction Type Selection */}
      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Tipo de Actividad</label>
        <select
          name="interaction_type"
          value={formData.interaction_type}
          onChange={handleChange}
          className="premium-input select"
        >
          <option value="llamada">Llamada Telefónica</option>
          <option value="email">Correo Electrónico (Email)</option>
          <option value="reunion">Reunión Presencial / Virtual</option>
          <option value="escrito">Redacción de Escrito / Demanda</option>
          <option value="audiencia">Audiencia Judicial</option>
          <option value="otro">Otro Trámite / Gestión</option>
        </select>
      </div>

      {/* Duration Minutes */}
      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Duración Estimada (minutos)</label>
        <input
          type="number"
          name="duration_minutes"
          value={formData.duration_minutes}
          onChange={handleChange}
          className={`premium-input ${errors.duration_minutes ? 'border-red-400' : ''}`}
          placeholder="Ej: 30"
          min="0"
        />
        {errors.duration_minutes && <p className="text-red-500 text-xs mt-1">{errors.duration_minutes}</p>}
      </div>

      {/* Description Log */}
      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Detalle / Notas de la Actividad</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows="4"
          className={`premium-input text-area ${errors.description ? 'border-red-400' : ''}`}
          placeholder="Escriba los pormenores de la llamada, acuerdos de la reunión o novedades de la audiencia procesal..."
        />
        {errors.description && <p className="text-red-500 text-xs mt-1">{errors.description}</p>}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
        <button
          type="button"
          onClick={onCancel}
          className="premium-btn-secondary"
          disabled={isSubmitting}
        >
          Cancelar
        </button>
        <button
          type="submit"
          className="premium-btn-primary"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Registrando...' : 'Registrar Actividad'}
        </button>
      </div>
    </form>
  )
}

export default InteractionForm
