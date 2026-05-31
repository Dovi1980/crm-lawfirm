import React, { useState } from 'react'

const TaskForm = ({ 
  initialData = {}, 
  users = [], 
  caseId = null, 
  clientId = null, 
  onSubmit, 
  onCancel,
  isSubmitting = false
}) => {
  const [formData, setFormData] = useState({
    title: initialData.title || '',
    description: initialData.description || '',
    priority: initialData.priority || 'media',
    status: initialData.status || 'pendiente',
    assigned_to_id: initialData.assigned_to_id || (users.length > 0 ? users[0].id : ''),
    due_date: initialData.due_date ? initialData.due_date.split('T')[0] : new Date().toISOString().split('T')[0],
    case_id: initialData.case_id || caseId || '',
    client_id: initialData.client_id || clientId || ''
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
    if (!formData.title.trim()) tempErrors.title = 'El título de la tarea es obligatorio.'
    if (!formData.assigned_to_id) tempErrors.assigned_to_id = 'Debe asignar un responsable.'
    if (!formData.due_date) tempErrors.due_date = 'La fecha de vencimiento es obligatoria.'
    setErrors(tempErrors)
    return Object.keys(tempErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (validate()) {
      onSubmit({
        ...formData,
        assigned_to_id: parseInt(formData.assigned_to_id),
        case_id: formData.case_id ? parseInt(formData.case_id) : null,
        client_id: formData.client_id ? parseInt(formData.client_id) : null
      })
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Title */}
      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Título de la Tarea</label>
        <input
          type="text"
          name="title"
          value={formData.title}
          onChange={handleChange}
          className={`premium-input ${errors.title ? 'border-red-400 focus:ring-red-400' : ''}`}
          placeholder="Ej: Contestar demanda en juzgado comercial N° 5"
        />
        {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title}</p>}
      </div>

      {/* Description */}
      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Instrucciones / Notas</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows="3"
          className="premium-input text-area"
          placeholder="Escriba aquí los pormenores, adjuntos a revisar o indicaciones especiales..."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Priority */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Prioridad</label>
          <select
            name="priority"
            value={formData.priority}
            onChange={handleChange}
            className="premium-input select"
          >
            <option value="baja">Baja</option>
            <option value="media">Media</option>
            <option value="alta">Alta</option>
            <option value="urgente">Urgente</option>
          </select>
        </div>

        {/* Status */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Estado</label>
          <select
            name="status"
            value={formData.status}
            onChange={handleChange}
            className="premium-input select"
          >
            <option value="pendiente">Pendiente</option>
            <option value="en_progreso">En Progreso</option>
            <option value="completada">Completada</option>
            <option value="cancelada">Cancelada</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* User Selection */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Responsable Asignado</label>
          <select
            name="assigned_to_id"
            value={formData.assigned_to_id}
            onChange={handleChange}
            className={`premium-input select ${errors.assigned_to_id ? 'border-red-400' : ''}`}
          >
            <option value="">-- Seleccionar Responsable --</option>
            {users.map(u => (
              <option key={u.id} value={u.id}>
                {u.last_name}, {u.first_name} ({u.role})
              </option>
            ))}
          </select>
          {errors.assigned_to_id && <p className="text-red-500 text-xs mt-1">{errors.assigned_to_id}</p>}
        </div>

        {/* Due Date */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Fecha Vencimiento</label>
          <input
            type="date"
            name="due_date"
            value={formData.due_date}
            onChange={handleChange}
            className={`premium-input ${errors.due_date ? 'border-red-400' : ''}`}
          />
          {errors.due_date && <p className="text-red-500 text-xs mt-1">{errors.due_date}</p>}
        </div>
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
          {isSubmitting ? 'Guardando...' : 'Guardar Tarea'}
        </button>
      </div>
    </form>
  )
}

export default TaskForm
