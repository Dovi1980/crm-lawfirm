import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import axiosClient from '../api/axiosClient'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import ClientForm from '../components/forms/ClientForm'
import { Plus, Search, UserCheck, AlertCircle } from 'lucide-react'

const ClientsPage = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  // Query Clients List
  const { data: clients = [], isLoading, error } = useQuery({
    queryKey: ['clients', searchTerm],
    queryFn: async () => {
      const response = await axiosClient.get(`/clients?search=${searchTerm}`)
      return response.data
    }
  })

  // Create Client Mutation
  const createMutation = useMutation({
    mutationFn: async (newClient) => {
      return await axiosClient.post('/clients', newClient)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['clients'])
      setIsModalOpen(false)
      setErrorMessage('')
    },
    onError: (err) => {
      const message = err.response?.data?.detail || 'Ocurrió un error al crear el cliente.'
      setErrorMessage(message)
    }
  })

  const columns = [
    {
      header: 'Nombre Completo',
      render: (row) => `${row.last_name}, ${row.first_name}`
    },
    {
      header: 'Tipo',
      render: (row) => (
        <span className="capitalize font-medium">
          {row.client_type === 'natural' ? 'Persona Física' : 'Persona Jurídica'}
        </span>
      )
    },
    {
      header: 'CUIT / CUIL / DNI',
      accessor: 'tax_id'
    },
    {
      header: 'Correo Electrónico',
      accessor: 'email'
    },
    {
      header: 'Teléfono',
      accessor: 'phone'
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
    }
  ]

  const handleRowClick = (row) => {
    navigate(`/clients/${row.id}`)
  }

  const handleCreateSubmit = (formData) => {
    createMutation.mutate(formData)
  }

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-bold text-legal-navy-deep dark:text-white mb-1">
            Fichero de Clientes
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Administre la información fiscal, domiciliaria y de contacto de sus patrocinados.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="premium-btn-gold"
        >
          <Plus className="w-5 h-5" />
          <span>Nuevo Cliente</span>
        </button>
      </div>

      {/* Search Filter bar */}
      <div className="relative max-w-md shadow-sm">
        <Search className="absolute left-3.5 top-3 w-5 h-5 text-slate-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="premium-input pl-11"
          placeholder="Buscar por nombre, CUIT/CUIL, DNI o email..."
        />
      </div>

      {/* Main DataTable list */}
      <DataTable
        columns={columns}
        data={clients}
        isLoading={isLoading}
        onRowClick={handleRowClick}
        emptyMessage="No se encontraron clientes registrados."
      />

      {/* Create Client Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setErrorMessage('') }}
        title="Registrar Nuevo Cliente"
        size="lg"
      >
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}
        <ClientForm
          onSubmit={handleCreateSubmit}
          onCancel={() => { setIsModalOpen(false); setErrorMessage('') }}
          isSubmitting={createMutation.isLoading}
        />
      </Modal>
    </div>
  )
}

export default ClientsPage
export { ClientsPage }
