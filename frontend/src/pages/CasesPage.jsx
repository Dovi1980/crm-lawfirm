import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import axiosClient from '../api/axiosClient'
import DataTable from '../components/DataTable'
import Modal from '../components/Modal'
import CaseForm from '../components/forms/CaseForm'
import { Plus, Briefcase, AlertCircle, Filter } from 'lucide-react'

const CasesPage = () => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  // Filter States
  const [statusFilter, setStatusFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  // 1. Query Cases List
  const { data: cases = [], isLoading: isCasesLoading } = useQuery({
    queryKey: ['cases', statusFilter, typeFilter],
    queryFn: async () => {
      let url = '/cases?'
      if (statusFilter) url += `status=${statusFilter}&`
      if (typeFilter) url += `case_type=${typeFilter}&`
      const response = await axiosClient.get(url)
      return response.data
    }
  })

  // 2. Fetch Clients list for assignment dropdown
  const { data: clients = [] } = useQuery({
    queryKey: ['clientsListDropdown'],
    queryFn: async () => {
      const response = await axiosClient.get('/clients?limit=100')
      return response.data
    },
    enabled: isModalOpen // Only fetch when creating a case
  })

  // 3. Fetch Lawyers list for assignment dropdown (all active staff)
  const { data: staffList = [] } = useQuery({
    queryKey: ['staffListDropdown'],
    queryFn: async () => {
      const response = await axiosClient.get('/users?limit=100')
      return response.data
    },
    enabled: isModalOpen // Only fetch when creating a case
  })

  // filter lawyers specifically from staff list
  const lawyers = staffList.filter(u => u.role === 'lawyer' || u.role === 'admin')

  // Create Case Mutation
  const createMutation = useMutation({
    mutationFn: async (newCase) => {
      return await axiosClient.post('/cases', newCase)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['cases'])
      queryClient.invalidateQueries(['dashboardStats'])
      setIsModalOpen(false)
      setErrorMessage('')
    },
    onError: (err) => {
      setErrorMessage(err.response?.data?.detail || 'Error al registrar expediente.')
    }
  })

  const columns = [
    {
      header: 'Código Exp.',
      accessor: 'case_number',
      render: (row) => <span className="font-bold text-legal-gold">{row.case_number}</span>
    },
    {
      header: 'Carátula / Título',
      accessor: 'title'
    },
    {
      header: 'Cliente',
      render: (row) => row.client ? `${row.client.last_name}, ${row.client.first_name}` : 'N/A'
    },
    {
      header: 'Abogado Asignado',
      render: (row) => row.assigned_lawyer ? `${row.assigned_lawyer.last_name}, ${row.assigned_lawyer.first_name}` : 'N/A'
    },
    {
      header: 'Materia',
      render: (row) => <span className="capitalize font-semibold">{row.case_type}</span>
    },
    {
      header: 'Estado',
      render: (row) => (
        <span className={`px-2.5 py-0.5 rounded text-xs font-bold uppercase ${
          row.status === 'cerrado' 
            ? 'bg-slate-100 text-slate-500' 
            : row.status === 'nuevo' 
            ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400'
            : 'bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400'
        }`}>
          {row.status.replace('_', ' ')}
        </span>
      )
    }
  ]

  const handleRowClick = (row) => {
    navigate(`/cases/${row.id}`)
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
            Control de Expedientes
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Listado completo de litigios en curso, juicios cerrados y fueros asignados.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="premium-btn-gold"
        >
          <Plus className="w-5 h-5" />
          <span>Nuevo Expediente</span>
        </button>
      </div>

      {/* Filters bar */}
      <div className="flex flex-wrap items-center gap-4 bg-white dark:bg-legal-charcoal-medium p-4 border border-slate-100 dark:border-slate-800 rounded-xl shadow-sm">
        <div className="flex items-center gap-2 text-sm text-slate-400 font-bold uppercase tracking-wider">
          <Filter className="w-4 h-4 text-legal-gold" />
          <span>Filtros:</span>
        </div>
        
        {/* Status Filter */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-slate-200 dark:border-slate-800 rounded-lg text-sm bg-white dark:bg-legal-charcoal-dark focus:outline-none focus:ring-2 focus:ring-legal-gold"
        >
          <option value="">Todos los Estados</option>
          <option value="nuevo">Nuevo / En Estudio</option>
          <option value="en_proceso">En Proceso / Litigio</option>
          <option value="en_espera">En Espera / Mediación</option>
          <option value="cerrado">Cerrado</option>
          <option value="archivado">Archivado</option>
        </select>

        {/* Type Filter */}
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 border border-slate-200 dark:border-slate-800 rounded-lg text-sm bg-white dark:bg-legal-charcoal-dark focus:outline-none focus:ring-2 focus:ring-legal-gold"
        >
          <option value="">Todas las Materias</option>
          <option value="civil">Civil</option>
          <option value="penal">Penal</option>
          <option value="laboral">Laboral</option>
          <option value="comercial">Comercial</option>
          <option value="familia">Familia</option>
          <option value="otro">Otro</option>
        </select>
      </div>

      {/* Main DataTable list */}
      <DataTable
        columns={columns}
        data={cases}
        isLoading={isCasesLoading}
        onRowClick={handleRowClick}
        emptyMessage="No se encontraron expedientes judiciales."
      />

      {/* Create Case Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setErrorMessage('') }}
        title="Registrar Nuevo Expediente Procesal"
        size="lg"
      >
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}
        <CaseForm
          clients={clients}
          lawyers={lawyers}
          onSubmit={handleCreateSubmit}
          onCancel={() => { setIsModalOpen(false); setErrorMessage('') }}
          isSubmitting={createMutation.isLoading}
        />
      </Modal>
    </div>
  )
}

export default CasesPage
export { CasesPage }
