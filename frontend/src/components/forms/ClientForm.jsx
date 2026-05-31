import React, { useState } from 'react'

const ClientForm = ({ 
  initialData = {}, 
  onSubmit, 
  onCancel,
  isSubmitting = false
}) => {
  const [formData, setFormData] = useState({
    first_name: initialData.first_name || '',
    last_name: initialData.last_name || '',
    client_type: initialData.client_type || 'natural',
    tax_id: initialData.tax_id || '',
    email: initialData.email || '',
    phone: initialData.phone || '',
    address: initialData.address || '',
    city: initialData.city || '',
    province: initialData.province || '',
    notes: initialData.notes || '',
    is_active: initialData.is_active !== undefined ? initialData.is_active : true
  })

  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const validate = () => {
    const tempErrors = {}
    if (!formData.first_name.trim()) tempErrors.first_name = 'El nombre es obligatorio.'
    if (!formData.last_name.trim()) tempErrors.last_name = 'El apellido o razón social es obligatorio.'
    if (formData.email && !/\S+@\S+\.\S+/.test(formData.email)) {
      tempErrors.email = 'El correo electrónico no es válido.'
    }
    setErrors(tempErrors)
    return Object.keys(tempErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (validate()) {
      onSubmit(formData)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* First Name */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Nombre</label>
          <input
            type="text"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
            className={`premium-input ${errors.first_name ? 'border-red-400 focus:ring-red-400' : ''}`}
            placeholder="Ej: Juan Ramón"
          />
          {errors.first_name && <p className="text-red-500 text-xs mt-1">{errors.first_name}</p>}
        </div>

        {/* Last Name */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Apellido / Razón Social</label>
          <input
            type="text"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            className={`premium-input ${errors.last_name ? 'border-red-400 focus:ring-red-400' : ''}`}
            placeholder="Ej: Pérez"
          />
          {errors.last_name && <p className="text-red-500 text-xs mt-1">{errors.last_name}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Client Type */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Tipo de Persona</label>
          <select
            name="client_type"
            value={formData.client_type}
            onChange={handleChange}
            className="premium-input select"
          >
            <option value="natural">Persona Física (Natural)</option>
            <option value="legal">Persona Jurídica (Legal)</option>
          </select>
        </div>

        {/* Tax ID (CUIT/CUIL/DNI) */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">CUIT / CUIL / DNI</label>
          <input
            type="text"
            name="tax_id"
            value={formData.tax_id}
            onChange={handleChange}
            className="premium-input"
            placeholder="Ej: 20-38472849-3 o DNI"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Email */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Correo Electrónico</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className={`premium-input ${errors.email ? 'border-red-400 focus:ring-red-400' : ''}`}
            placeholder="juan.perez@example.com"
          />
          {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
        </div>

        {/* Phone */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Teléfono</label>
          <input
            type="text"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            className="premium-input"
            placeholder="Ej: +54 9 11 5555-4444"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Address */}
        <div className="md:col-span-1">
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Dirección</label>
          <input
            type="text"
            name="address"
            value={formData.address}
            onChange={handleChange}
            className="premium-input"
            placeholder="Av. Corrientes 1234"
          />
        </div>

        {/* City */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Ciudad</label>
          <input
            type="text"
            name="city"
            value={formData.city}
            onChange={handleChange}
            className="premium-input"
            placeholder="CABA"
          />
        </div>

        {/* Province */}
        <div>
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Provincia</label>
          <input
            type="text"
            name="province"
            value={formData.province}
            onChange={handleChange}
            className="premium-input"
            placeholder="Buenos Aires"
          />
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">Notas / Comentarios</label>
        <textarea
          name="notes"
          value={formData.notes}
          onChange={handleChange}
          rows="3"
          className="premium-input text-area"
          placeholder="Anotaciones importantes sobre el cliente..."
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
          {isSubmitting ? 'Guardando...' : 'Guardar Cliente'}
        </button>
      </div>
    </form>
  )
}

export default ClientForm
