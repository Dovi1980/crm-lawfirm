import React, { useState } from 'react'

const CaseForm = ({ 
  initialData = {}, 
  clients = [], 
  lawyers = [], 
  onSubmit, 
  onCancel,
  isSubmitting = false
}) => {
  const [formData, setFormData] = useState({
    title: initialData.title || '',
    description: initialData.description || '',
    case_type: initialData.case_type || 'otro',
    status: initialData.status || 'nuevo',
    client_id: initialData.client_id || (clients.length > 0 ? clients[0].id : ''),
    assigned_lawyer_id: initialData.assigned_lawyer_id || (lawyers.length > 0 ? lawyers[0].id : ''),
    start_date: initialData.start_date ? initialData.start_date.split('T')[0] : new Date().toISOString().split('T')[0],
    estimated_close_date: initialData.estimated_close_date ? initialData.estimated_close_date.split('T')[0] : '',
    agreed_fees: initialData.agreed_fees || '',
    internal_notes: initialData.internal_notes || ''
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
    if (!formData.title.trim()) tempErrors.title = 'El título del expediente es obligatorio.'
    if (!formData.client_id) tempErrors.client_id = 'Debe seleccionar un cliente.'
    if (!formData.assigned_lawyer_id) tempErrors.assigned_lawyer_id = 'Debe asignar un abogado.'
    if (!formData.start_date) tempErrors.start_date = 'La fecha de inicio es obligatoria.'
    setErrors(tempErrors)
    return Object.keys(tempErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (validate()) {
      onSubmit({
        ...formData,
        client_id: parseInt(formData.client_id),
        assigned_lawyer_id: parseInt(formData.assigned_lawyer_id),
        agreed_fees: formData.agreed_fees ? parseFloat(formData.agreed_fees) : null,
        estimated_close_date: formData.estimated_close_date ? formData.estimated_close_date : null
      })
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Title */}
      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Título del Expediente</label>
        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          className={`premium-input ${errors.title ? 'border-red-400 focus:ring-red-400' : ''}`}
          placeholder="Ej: Sucesión Hereditaria - Familia Pérez"
        />
        {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title}</p>}
      </div>

      {/* Description */}
      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Descripción de la Causa</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows="3"
          className="premium-input text-area"
          placeholder="Resumen del litigio, juzgado interventor y detalles de inicio..."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Case Type */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Materia / Fuero</label>
          <select
            name="case_type"
            value={formData.case_type}
            onChange={handleChange}
            className="premium-input select"
          >
            <option value="civil">Civil</option>
            <option value="penal">Penal</option>
            <option value="laboral">Laboral</option>
            <option value="comercial">Comercial</option>
            <option value="familia">Familia</option>
            <option value="otro">Otro / Administrativo</option>
          </select>
        </div>

        {/* Case Status */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Estado Procesal</label>
          <select
            name="status"
            value={formData.status}
            onChange={handleChange}
            className="premium-input select"
          >
            <option value="nuevo">Nuevo / En Estudio</option>
            <option value="en_proceso">En Proceso / Litigio</option>
            <option value="en_espera">En Espera / Mediación</option>
            <option value="cerrado">Cerrado</option>
            <option value="archivado">Archivado</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Client Selection */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Cliente Asociado</label>
          <select
            name="client_id"
            value={formData.client_id}
            onChange={handleChange}
            className={`premium-input select ${errors.client_id ? 'border-red-400' : ''}`}
          >
            <option value="">-- Seleccionar Cliente --</option>
            {clients.map(c => (
              <option key={c.id} value={c.id}>
                {c.last_name}, {c.first_name} {c.tax_id ? `(${c.tax_id})` : ''}
              </option>
            ))}
          </select>
          {errors.client_id && <p className="text-red-500 text-xs mt-1">{errors.client_id}</p>}
        </div>

        {/* Lawyer Assigned Selection */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Abogado Asignado</label>
          <select
            name="assigned_lawyer_id"
            value={formData.assigned_lawyer_id}
            onChange={handleChange}
            className={`premium-input select ${errors.assigned_lawyer_id ? 'border-red-400' : ''}`}
          >
            <option value="">-- Seleccionar Abogado --</option>
            {lawyers.map(l => (
              <option key={l.id} value={l.id}>
                {l.last_name}, {l.first_name} ({l.role})
              </option>
            ))}
          </select>
          {errors.assigned_lawyer_id && <p className="text-red-500 text-xs mt-1">{errors.assigned_lawyer_id}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Start Date */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Fecha de Inicio</label>
          <input
            type="date"
            name="start_date"
            value={formData.start_date}
            onChange={handleChange}
            className={`premium-input ${errors.start_date ? 'border-red-400' : ''}`}
          />
          {errors.start_date && <p className="text-red-500 text-xs mt-1">{errors.start_date}</p>}
        </div>

        {/* Estimated Close Date */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Cierre Estimado</label>
          <input
            type="date"
            name="estimated_close_date"
            value={formData.estimated_close_date}
            onChange={handleChange}
            className="premium-input"
          />
        </div>

        {/* Agreed Fees */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Honorarios Pactados ($)</label>
          <input
            type="number"
            step="0.01"
            name="agreed_fees"
            value={formData.agreed_fees}
            onChange={handleChange}
            className="premium-input"
            placeholder="Ej: 150000.00"
          />
        </div>
      </div>

      {/* Internal Notes */}
      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Notas Internas (Privadas)</label>
        <textarea
          name="internal_notes"
          value={formData.internal_notes}
          onChange={handleChange}
          rows="3"
          className="premium-input text-area"
          placeholder="Estrategias judiciales, detalles de cobros u observaciones del caso..."
        />
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
          {isSubmitting ? 'Registrando...' : 'Registrar Expediente'}
        </button>
      </div>
    </form>
  )
}

export default CaseForm
