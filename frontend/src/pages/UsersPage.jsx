import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axiosClient from '../api/axiosClient'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import { Plus, Edit, Trash2, Shield, AlertCircle, Check } from 'lucide-react'

const UsersPage = () => {
  const queryClient = useQueryClient()

  // Modal and Form states
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [errorMessage, setErrorMessage] = useState('')

  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    role: 'lawyer',
    is_active: true,
    password: ''
  })

  // 1. Fetch Users List (admin only)
  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await axiosClient.get('/users')
      return response.data
    }
  })

  // 2. Create User Mutation
  const createMutation = useMutation({
    mutationFn: async (newUser) => {
      return await axiosClient.post('/users', newUser)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['users'])
      closeModal()
    },
    onError: (err) => {
      setErrorMessage(err.response?.data?.detail || 'Error al crear el usuario.')
    }
  })

  // 3. Edit User Mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      return await axiosClient.put(`/users/${id}`, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['users'])
      closeModal()
    },
    onError: (err) => {
      setErrorMessage(err.response?.data?.detail || 'Error al actualizar el usuario.')
    }
  })

  // 4. Delete/Disable User Mutation
  const deleteMutation = useMutation({
    mutationFn: async (userId) => {
      return await axiosClient.delete(`/users/${userId}`)
    },
    onSuccess: (response) => {
      alert(response.data?.detail || 'Usuario eliminado correctamente.')
      queryClient.invalidateQueries(['users'])
    },
    onError: (err) => {
      alert(err.response?.data?.detail || 'No se pudo eliminar el usuario.')
    }
  })

  const openCreateModal = () => {
    setEditingUser(null)
    setFormData({
      first_name: '',
      last_name: '',
      email: '',
      role: 'lawyer',
      is_active: true,
      password: ''
    })
    setIsModalOpen(true)
  }

  const openEditModal = (user) => {
    setEditingUser(user)
    setFormData({
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      role: user.role,
      is_active: user.is_active,
      password: '' // Kept empty unless changing password
    })
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingUser(null)
    setErrorMessage('')
  }

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setErrorMessage('')

    if (!formData.first_name.trim() || !formData.last_name.trim() || !formData.email.trim()) {
      setErrorMessage('Los campos Nombre, Apellido y Email son obligatorios.')
      return
    }

    if (!editingUser && !formData.password) {
      setErrorMessage('La contraseña es obligatoria para nuevos usuarios.')
      return
    }

    if (editingUser) {
      const payload = { ...formData }
      if (!payload.password) delete payload.password // Don't send empty password
      updateMutation.mutate({ id: editingUser.id, data: payload })
    } else {
      createMutation.mutate(formData)
    }
  }

  const handleDelete = (userId) => {
    if (window.confirm('¿Está seguro de que desea eliminar o deshabilitar este usuario del estudio?')) {
      deleteMutation.mutate(userId)
    }
  }

  const columns = [
    {
      header: 'Nombre Completo',
      render: (row) => `${row.last_name}, ${row.first_name}`
    },
    {
      header: 'Email',
      accessor: 'email'
    },
    {
      header: 'Rol',
      render: (row) => (
        <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wider ${
          row.role === 'admin' 
            ? 'bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400' 
            : row.role === 'lawyer' 
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400' 
            : 'bg-slate-100 text-slate-600'
        }`}>
          {row.role}
        </span>
      )
    },
    {
      header: 'Estado',
      render: (row) => (
        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
          row.is_active 
            ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400' 
            : 'bg-slate-100 text-slate-500'
        }`}>
          {row.is_active ? 'Activo' : 'Inactivo'}
        </span>
      )
    },
    {
      header: 'Acciones',
      render: (row) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => openEditModal(row)}
            className="p-1 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-legal-charcoal-dark dark:hover:text-slate-200"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleDelete(row.id)}
            className="p-1 rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-500"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      )
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-bold text-legal-navy-deep dark:text-white mb-1 flex items-center gap-2">
            <Shield className="w-8 h-8 text-legal-gold" />
            Abogados & Personal
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Panel de control administrativo para registrar usuarios del estudio, asignar roles y gestionar credenciales.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="premium-btn-gold"
        >
          <Plus className="w-5 h-5" />
          <span>Agregar Personal</span>
        </button>
      </div>

      {/* Main DataTable list */}
      <DataTable
        columns={columns}
        data={users}
        isLoading={isLoading}
        emptyMessage="No hay personal registrado en el estudio."
      />

      {/* User Form Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingUser ? "Modificar Ficha de Personal" : "Agregar Nuevo Personal de Estudio"}
        size="md"
      >
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* First Name */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5">Nombre</label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleInputChange}
                className="premium-input"
                required
              />
            </div>
            {/* Last Name */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5">Apellido</label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleInputChange}
                className="premium-input"
                required
              />
            </div>
          </div>

          {/* Email */}
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5">Email / Usuario</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="premium-input"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Role selection */}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5">Rol Corporativo</label>
              <select
                name="role"
                value={formData.role}
                onChange={handleInputChange}
                className="premium-input select"
              >
                <option value="admin">Administrador</option>
                <option value="lawyer">Abogado Asociado</option>
                <option value="assistant">Asistente de Oficina</option>
              </select>
            </div>

            {/* Active Switch */}
            <div className="flex flex-col justify-end pb-1.5">
              <label className="flex items-center gap-2 cursor-pointer py-2">
                <input
                  type="checkbox"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                  className="w-4.5 h-4.5 text-legal-gold border-slate-300 rounded focus:ring-legal-gold"
                />
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wide">Usuario Activo</span>
              </label>
            </div>
          </div>

          {/* Password (optional if editing) */}
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5">
              Contraseña {editingUser ? "(Dejar en blanco para conservar)" : ""}
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className="premium-input"
              minLength="8"
              required={!editingUser}
              placeholder={editingUser ? "••••••••" : ""}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-5 border-t border-slate-100 dark:border-slate-800 mt-6">
            <button
              type="button"
              onClick={closeModal}
              className="premium-btn-secondary"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="premium-btn-primary"
            >
              {editingUser ? 'Guardar Cambios' : 'Registrar Personal'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default UsersPage
export { UsersPage }
