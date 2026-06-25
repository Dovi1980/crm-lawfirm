import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../hooks/useAuth'
import axiosClient from '../api/axiosClient'
import Modal from '../components/Modal'
import CaseForm from '../components/forms/CaseForm'
import InteractionForm from '../components/forms/InteractionForm'
import TaskForm from '../components/forms/TaskForm'
import CaseAIPanel from '../components/ai/CaseAIPanel'
import CaseDocumentsSection from '../components/ai/CaseDocumentsSection'
import { 
  Briefcase, 
  Scale, 
  User, 
  Clock, 
  CheckSquare, 
  FileText,
  Calendar,
  DollarSign,
  Plus,
  Edit,
  Trash2,
  AlertCircle,
  TrendingUp,
  AlertTriangle,
  FolderOpen
} from 'lucide-react'

const CaseDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAssistant } = useAuth()
  const queryClient = useQueryClient()

  // Modal States
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isInteractionModalOpen, setIsInteractionModalOpen] = useState(false)
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  // 1. Fetch Case Details
  const { data: caseItem, isLoading: isCaseLoading, error: caseError } = useQuery({
    queryKey: ['case', id],
    queryFn: async () => {
      const response = await axiosClient.get(`/cases/${id}`)
      return response.data
    }
  })

  // 2. Fetch Case's Interactions
  const { data: interactions = [], isLoading: isInteractionsLoading } = useQuery({
    queryKey: ['caseInteractions', id],
    queryFn: async () => {
      const response = await axiosClient.get(`/interactions?case_id=${id}`)
      return response.data
    }
  })

  // 3. Fetch Case's Tasks
  const { data: tasks = [], isLoading: isTasksLoading } = useQuery({
    queryKey: ['caseTasks', id],
    queryFn: async () => {
      const response = await axiosClient.get(`/tasks?case_id=${id}`)
      return response.data
    }
  })

  // 4. Fetch Clients & Lawyers (fetched lazily for edit dropdowns)
  const { data: clients = [] } = useQuery({
    queryKey: ['clientsListDropdown'],
    queryFn: async () => {
      const response = await axiosClient.get('/clients?limit=100')
      return response.data
    },
    enabled: isEditModalOpen
  })

  const { data: staffList = [] } = useQuery({
    queryKey: ['staffListDropdown'],
    queryFn: async () => {
      const response = await axiosClient.get('/users?limit=100')
      return response.data
    },
    enabled: isEditModalOpen || isTaskModalOpen
  })
  
  const lawyers = staffList.filter(u => u.role === 'lawyer' || u.role === 'admin')

  // Edit Case Mutation
  const updateMutation = useMutation({
    mutationFn: async (updatedData) => {
      return await axiosClient.put(`/cases/${id}`, updatedData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['case', id])
      queryClient.invalidateQueries(['cases'])
      setIsEditModalOpen(false)
      setErrorMessage('')
    },
    onError: (err) => {
      setErrorMessage(err.response?.data?.detail || 'Error al actualizar expediente.')
    }
  })

  // Delete Case Mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      return await axiosClient.delete(`/cases/${id}`)
    },
    onSuccess: () => {
      alert('Expediente eliminado correctamente.')
      navigate('/cases')
    },
    onError: (err) => {
      alert(err.response?.data?.detail || 'No se pudo eliminar el expediente.')
    }
  })

  // Add Interaction log Mutation
  const addInteractionMutation = useMutation({
    mutationFn: async (newAct) => {
      return await axiosClient.post('/interactions', newAct)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['caseInteractions', id])
      queryClient.invalidateQueries(['dashboardStats'])
      setIsInteractionModalOpen(false)
      setErrorMessage('')
    },
    onError: (err) => {
      setErrorMessage(err.response?.data?.detail || 'Error al registrar actividad.')
    }
  })

  // Add Task Mutation
  const addTaskMutation = useMutation({
    mutationFn: async (newTask) => {
      return await axiosClient.post('/tasks', newTask)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['caseTasks', id])
      queryClient.invalidateQueries(['dashboardStats'])
      setIsTaskModalOpen(false)
      setErrorMessage('')
    },
    onError: (err) => {
      setErrorMessage(err.response?.data?.detail || 'Error al crear la tarea.')
    }
  })

  // Task Status Toggle Mutation (Quick action)
  const toggleTaskStatusMutation = useMutation({
    mutationFn: async ({ taskId, status }) => {
      return await axiosClient.put(`/tasks/${taskId}`, { status })
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['caseTasks', id])
      queryClient.invalidateQueries(['dashboardStats'])
    }
  })

  if (isCaseLoading) {
    return (
      <div className="flex justify-center items-center py-24">
        <div className="w-10 h-10 border-4 border-legal-gold border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  if (caseError) {
    return (
      <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-4 rounded-xl flex items-center gap-3">
        <AlertCircle className="w-6 h-6 flex-shrink-0" />
        <span>Expediente no encontrado o carece de permisos de lectura.</span>
      </div>
    )
  }

  const handleEditSubmit = (formData) => {
    updateMutation.mutate(formData)
  }

  const handleDelete = () => {
    if (window.confirm('¿Está seguro de que desea eliminar este expediente y todos sus registros asociados?')) {
      deleteMutation.mutate()
    }
  }

  const handleAddInteraction = (formData) => {
    addInteractionMutation.mutate(formData)
  }

  const handleAddTask = (formData) => {
    addTaskMutation.mutate({
      ...formData,
      case_id: parseInt(id),
      client_id: caseItem.client_id
    })
  }

  const handleToggleTask = (task) => {
    const nextStatus = task.status === 'completada' ? 'pendiente' : 'completada'
    toggleTaskStatusMutation.mutate({ taskId: task.id, status: nextStatus })
  }

  const isOverdue = (dueDate) => {
    return new Date(dueDate) < new Date()
  }

  return (
    <div className="space-y-8">
      {/* Title & Toolbar Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-legal-navy-deep text-white border border-legal-gold flex items-center justify-center font-serif text-xl font-bold dark:bg-legal-gold dark:text-legal-navy-deep">
            <Scale className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-legal-gold tracking-wide">{caseItem.case_number}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                caseItem.status === 'cerrado' ? 'bg-slate-200 text-slate-600' : 'bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400'
              }`}>
                {caseItem.status.replace('_', ' ')}
              </span>
            </div>
            <h1 className="font-serif text-2xl font-bold text-legal-navy-deep dark:text-white mt-0.5 truncate max-w-[500px]">
              {caseItem.title}
            </h1>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsEditModalOpen(true)}
            className="premium-btn-secondary"
          >
            <Edit className="w-4 h-4" />
            <span>Editar Expediente</span>
          </button>
          {!isAssistant && (
            <button
              onClick={handleDelete}
              className="px-5 py-2.5 rounded-lg border border-red-200 text-red-500 hover:bg-red-500/10 hover:border-red-300 font-medium active:scale-95 flex items-center gap-2 transition-all"
            >
              <Trash2 className="w-4 h-4" />
              <span>Eliminar</span>
            </button>
          )}
        </div>
      </div>

      {/* Grid columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Core Case Profile Specs Card */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium space-y-6">
            <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
              <FolderOpen className="w-5 h-5 text-legal-gold" />
              Ficha Técnica
            </h3>
            
            <div className="space-y-4.5 text-sm">
              {/* Associated Client */}
              <div className="flex items-start gap-3">
                <User className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Cliente Patrocinado</h4>
                  <a href={`/clients/${caseItem.client_id}`} className="text-legal-navy-medium dark:text-legal-gold font-bold hover:underline">
                    {caseItem.client?.last_name}, {caseItem.client?.first_name}
                  </a>
                </div>
              </div>

              {/* Assigned Lawyer */}
              <div className="flex items-start gap-3">
                <Scale className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Letrado Asignado</h4>
                  <p className="text-slate-800 dark:text-slate-200 font-semibold">
                    {caseItem.assigned_lawyer?.last_name}, {caseItem.assigned_lawyer?.first_name}
                  </p>
                </div>
              </div>

              {/* Start Date */}
              <div className="flex items-start gap-3">
                <Calendar className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Fecha de Inicio</h4>
                  <p className="text-slate-800 dark:text-slate-200 font-semibold">
                    {new Date(caseItem.start_date).toLocaleDateString('es-ES')}
                  </p>
                </div>
              </div>

              {/* Estimated Close */}
              {caseItem.estimated_close_date && (
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Cierre Estimado</h4>
                    <p className="text-slate-800 dark:text-slate-200 font-semibold">
                      {new Date(caseItem.estimated_close_date).toLocaleDateString('es-ES')}
                    </p>
                  </div>
                </div>
              )}

              {/* Agreed Fees */}
              {caseItem.agreed_fees !== null && (
                <div className="flex items-start gap-3">
                  <DollarSign className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Honorarios Pactados</h4>
                    <p className="text-slate-800 dark:text-slate-200 font-bold text-lg text-emerald-600 dark:text-emerald-400">
                      $ {parseFloat(caseItem.agreed_fees).toLocaleString('es-ES', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Private Internal notes */}
            {caseItem.internal_notes && (
              <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Notas Privadas</h4>
                <p className="text-sm bg-slate-50 dark:bg-legal-charcoal-dark border border-slate-100 dark:border-slate-800 p-3 rounded-lg text-slate-600 dark:text-slate-300 font-medium whitespace-pre-line">
                  {caseItem.internal_notes}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Dynamic Timeline logs & Task Lists Area */}
        <div className="lg:col-span-2 space-y-8">

          {/* AI assistant panel — summary + chat with case context */}
          <CaseAIPanel caseId={caseItem.id} />

          {/* AI-drafted documents persisted per case */}
          <CaseDocumentsSection caseId={caseItem.id} />

          {/* Checklist Tasks related to Case */}
          <div className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium">
            <div className="flex items-center justify-between mb-5">
              <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white flex items-center gap-2">
                <CheckSquare className="w-5 h-5 text-legal-gold" />
                Planificación de Tareas
              </h3>
              <button
                onClick={() => setIsTaskModalOpen(true)}
                className="premium-btn-primary py-1.5 px-3 text-xs font-bold"
              >
                <Plus className="w-4 h-4" />
                <span>Agregar Tarea</span>
              </button>
            </div>

            {isTasksLoading ? (
              <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded animate-pulse" />
            ) : tasks.length === 0 ? (
              <div className="py-8 text-center text-slate-400 dark:text-slate-500 font-medium">
                No hay tareas pendientes asignadas a este expediente.
              </div>
            ) : (
              <div className="space-y-2.5">
                {tasks.map((tk) => {
                  const overdue = isOverdue(tk.due_date) && tk.status !== 'completada' && tk.status !== 'cancelada'
                  return (
                    <div 
                      key={tk.id}
                      className={`p-3.5 rounded-xl border flex items-center justify-between transition-colors ${
                        tk.status === 'completada' 
                          ? 'bg-slate-50/50 border-slate-100 dark:bg-legal-charcoal-dark dark:border-slate-900/50' 
                          : overdue 
                          ? 'bg-rose-50/30 border-rose-100 dark:bg-rose-500/5 dark:border-rose-900/30' 
                          : 'bg-white border-slate-100 dark:bg-legal-charcoal-dark dark:border-slate-800'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={tk.status === 'completada'}
                          onChange={() => handleToggleTask(tk)}
                          className="w-4.5 h-4.5 rounded border-slate-300 text-legal-gold focus:ring-legal-gold cursor-pointer"
                        />
                        <div>
                          <span className={`text-sm font-semibold block ${
                            tk.status === 'completada' 
                              ? 'line-through text-slate-400 dark:text-slate-500' 
                              : 'text-slate-800 dark:text-slate-200'
                          }`}>
                            {tk.title}
                          </span>
                          <span className="text-xs text-slate-400 mt-0.5 block capitalize">
                            Responsable: {tk.assigned_to?.first_name} {tk.assigned_to?.last_name} · Vence:{' '}
                            <span className={overdue ? 'text-rose-500 font-semibold' : ''}>
                              {new Date(tk.due_date).toLocaleDateString('es-ES')}
                            </span>
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {/* Priority indicator */}
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          tk.priority === 'urgente'
                            ? 'bg-rose-100 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400'
                            : tk.priority === 'alta'
                            ? 'bg-amber-100 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400'
                            : 'bg-slate-100 text-slate-500'
                        }`}>
                          {tk.priority}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Interactions append-only Judicial Timeline logs */}
          <div className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white flex items-center gap-2">
                <Clock className="w-5 h-5 text-legal-gold" />
                Historial Judicial & Actividades
              </h3>
              <button
                onClick={() => setIsInteractionModalOpen(true)}
                className="premium-btn-primary py-1.5 px-3 text-xs font-bold"
              >
                <Plus className="w-4 h-4" />
                <span>Registrar Gestión</span>
              </button>
            </div>

            {isInteractionsLoading ? (
              <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded animate-pulse" />
            ) : interactions.length === 0 ? (
              <div className="py-8 text-center text-slate-400 dark:text-slate-500 font-medium">
                No se registran actividades o novedades en la causa.
              </div>
            ) : (
              <div className="space-y-2">
                {interactions.map((act) => (
                  <div key={act.id} className="timeline-pill flex items-start gap-4">
                    <span className="timeline-dot" />
                    <div className="flex-1 pb-4">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 tracking-wide">
                            {act.interaction_type}
                          </span>
                          <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                            {act.user?.first_name} {act.user?.last_name}
                          </span>
                        </div>
                        <span className="text-xs text-slate-400">
                          {new Date(act.interaction_date).toLocaleDateString('es-ES')} a las {new Date(act.interaction_date).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })} hs
                        </span>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-300 font-medium whitespace-pre-wrap">
                        {act.description}
                      </p>
                      {act.duration_minutes > 0 && (
                        <span className="text-xs text-slate-400 mt-1 block">
                          Duración de gestión: {act.duration_minutes} min
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Edit Case Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => { setIsEditModalOpen(false); setErrorMessage('') }}
        title="Editar Expediente Judicial"
        size="lg"
      >
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}
        <CaseForm
          initialData={caseItem}
          clients={clients}
          lawyers={lawyers}
          onSubmit={handleEditSubmit}
          onCancel={() => { setIsEditModalOpen(false); setErrorMessage('') }}
          isSubmitting={updateMutation.isLoading}
        />
      </Modal>

      {/* Registrar Gestión Modal */}
      <Modal
        isOpen={isInteractionModalOpen}
        onClose={() => { setIsInteractionModalOpen(false); setErrorMessage('') }}
        title="Registrar Gestión en Causa"
        size="md"
      >
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}
        <InteractionForm
          caseId={caseItem.id}
          clientId={caseItem.client_id}
          onSubmit={handleAddInteraction}
          onCancel={() => { setIsInteractionModalOpen(false); setErrorMessage('') }}
          isSubmitting={addInteractionMutation.isLoading}
        />
      </Modal>

      {/* Agregar Tarea Modal */}
      <Modal
        isOpen={isTaskModalOpen}
        onClose={() => { setIsTaskModalOpen(false); setErrorMessage('') }}
        title="Crear Tarea para Expediente"
        size="md"
      >
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}
        <TaskForm
          users={lawyers}
          caseId={caseItem.id}
          clientId={caseItem.client_id}
          onSubmit={handleAddTask}
          onCancel={() => { setIsTaskModalOpen(false); setErrorMessage('') }}
          isSubmitting={addTaskMutation.isLoading}
        />
      </Modal>
    </div>
  )
}

export default CaseDetailPage
export { CaseDetailPage }
