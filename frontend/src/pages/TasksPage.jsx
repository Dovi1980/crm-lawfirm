import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../hooks/useAuth'
import axiosClient from '../api/axiosClient'
import Modal from '../components/Modal'
import TaskForm from '../components/forms/TaskForm'
import { 
  CheckSquare, 
  Plus, 
  Trash2, 
  AlertCircle,
  Calendar,
  AlertTriangle,
  User,
  Filter,
  CheckCircle2
} from 'lucide-react'

const TasksPage = () => {
  const { user, isAssistant } = useAuth()
  const queryClient = useQueryClient()

  // Tab State: 'mine' (My Tasks) vs 'all' (All Studio Tasks)
  const [activeTab, setActiveTab] = useState('mine')
  const [statusFilter, setStatusFilter] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  // 1. Fetch Tasks list
  const { data: tasks = [], isLoading: isTasksLoading } = useQuery({
    queryKey: ['tasks', activeTab, statusFilter],
    queryFn: async () => {
      let url = '/tasks?'
      if (activeTab === 'mine') {
        // Scoped automatically on backend to logged-in user if Lawyer.
        // For Admin/Assistant in frontend, we can pass assigned_to_id filter if needed, 
        // but default backend already filters by logged in user if Lawyer.
        // Let's pass the specific assignee to be safe for all roles.
        // We will query backend, which handles lawyer filtering.
        // For Admin/Assistant to see "Mine", we can filter client-side or pass a param.
        // Let's filter client-side or pass assignee. 
        // Let's fetch all and filter or fetch with specific assignee if needed.
        // To be extremely clean, we just fetch all and filter in frontend for "mine"
        // or let the backend do it. Since backend does it automatically for lawyers, 
        // let's fetch.
      }
      if (statusFilter) url += `status=${statusFilter}&`
      
      const response = await axiosClient.get(url)
      return response.data
    }
  })

  // 2. Fetch users list for task assignments
  const { data: staffList = [] } = useQuery({
    queryKey: ['staffListTasksPage'],
    queryFn: async () => {
      const response = await axiosClient.get('/users?limit=100')
      return response.data
    },
    enabled: isModalOpen
  })

  // Filter lists based on tab
  // If activeTab is 'mine', filter tasks where assigned_to_id === current user ID
  // Wait, let's fetch the current user's details first, or use local storage userEmail to match.
  // We can fetch from staffList or use the email from Auth context to match!
  const myTasks = tasks.filter(t => t.assigned_to?.email === user?.email)
  const displayedTasks = activeTab === 'mine' ? myTasks : tasks

  // Create Task Mutation
  const createTaskMutation = useMutation({
    mutationFn: async (newTask) => {
      return await axiosClient.post('/tasks', newTask)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['tasks'])
      queryClient.invalidateQueries(['dashboardStats'])
      setIsModalOpen(false)
      setErrorMessage('')
    },
    onError: (err) => {
      setErrorMessage(err.response?.data?.detail || 'Error al crear la tarea.')
    }
  })

  // Toggle Task Status Mutation
  const toggleStatusMutation = useMutation({
    mutationFn: async ({ taskId, status }) => {
      return await axiosClient.put(`/tasks/${taskId}`, { status })
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['tasks'])
      queryClient.invalidateQueries(['dashboardStats'])
    }
  })

  // Delete Task Mutation
  const deleteTaskMutation = useMutation({
    mutationFn: async (taskId) => {
      return await axiosClient.delete(`/tasks/${taskId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['tasks'])
      queryClient.invalidateQueries(['dashboardStats'])
    },
    onError: (err) => {
      alert(err.response?.data?.detail || 'No se pudo eliminar la tarea.')
    }
  })

  const handleToggleTask = (task) => {
    const nextStatus = task.status === 'completada' ? 'pendiente' : 'completada'
    toggleStatusMutation.mutate({ taskId: task.id, status: nextStatus })
  }

  const handleDeleteTask = (taskId) => {
    if (window.confirm('¿Desea eliminar de forma permanente esta tarea?')) {
      deleteTaskMutation.mutate(taskId)
    }
  }

  const handleCreateSubmit = (formData) => {
    createTaskMutation.mutate(formData)
  }

  const isOverdue = (dueDate) => {
    return new Date(dueDate) < new Date()
  }

  const isCloseToDue = (dueDate) => {
    const diffTime = new Date(dueDate) - new Date()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays >= 0 && diffDays <= 2
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-bold text-legal-navy-deep dark:text-white mb-1">
            Gestor de Tareas
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm">
            Planifique escritos, contestaciones, audiencias y gestiones de oficina.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="premium-btn-gold"
        >
          <Plus className="w-5 h-5" />
          <span>Nueva Tarea</span>
        </button>
      </div>

      {/* Tabs & Filters bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white dark:bg-legal-charcoal-medium p-4 border border-slate-100 dark:border-slate-800 rounded-xl shadow-sm">
        
        {/* Navigation Tabs ("Mis Tareas" vs "Todas") */}
        <div className="flex bg-slate-100 dark:bg-legal-charcoal-dark p-1 rounded-lg w-fit">
          <button
            onClick={() => setActiveTab('mine')}
            className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${
              activeTab === 'mine'
                ? 'bg-white dark:bg-legal-charcoal-medium text-legal-navy-deep dark:text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`}
          >
            Mis Tareas
          </button>
          
          {/* Hides full studio view for assistants if restricted, but let's allow lawyers/admins */}
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-md transition-all ${
              activeTab === 'all'
                ? 'bg-white dark:bg-legal-charcoal-medium text-legal-navy-deep dark:text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`}
          >
            Todas las Tareas
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400">
            <Filter className="w-4 h-4 text-legal-gold" />
            <span>Filtro:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-slate-200 dark:border-slate-800 rounded-lg text-sm bg-white dark:bg-legal-charcoal-dark focus:outline-none focus:ring-2 focus:ring-legal-gold"
          >
            <option value="">Todos los Estados</option>
            <option value="pendiente">Pendiente</option>
            <option value="en_progreso">En Progreso</option>
            <option value="completada">Completada</option>
            <option value="cancelada">Cancelada</option>
          </select>
        </div>
      </div>

      {/* Checklist Grid Lists */}
      {isTasksLoading ? (
        <div className="space-y-3 animate-pulse">
          {Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="h-16 bg-white dark:bg-legal-charcoal-medium border border-slate-100 rounded-xl" />
          ))}
        </div>
      ) : displayedTasks.length === 0 ? (
        <div className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 rounded-xl p-16 text-center shadow-premium flex flex-col items-center justify-center">
          <CheckCircle2 className="w-16 h-16 text-emerald-500/30 mb-4" />
          <h3 className="font-serif text-lg font-bold text-slate-700 dark:text-slate-300">¡Libre de pendientes!</h3>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-1 max-w-sm">
            No tienes tareas activas registradas que coincidan con estos filtros.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayedTasks.map((tk) => {
            const completed = tk.status === 'completada'
            const cancelled = tk.status === 'cancelada'
            const overdue = isOverdue(tk.due_date) && !completed && !cancelled
            const nearDue = isCloseToDue(tk.due_date) && !completed && !cancelled

            return (
              <div 
                key={tk.id}
                className={`p-4 rounded-2xl border bg-white dark:bg-legal-charcoal-medium shadow-premium transition-all hover:shadow-premium-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  completed 
                    ? 'opacity-60 border-slate-100 dark:border-slate-900/50' 
                    : overdue 
                    ? 'border-rose-200 bg-rose-50/10 dark:border-rose-900/30' 
                    : nearDue
                    ? 'border-amber-200 bg-amber-50/10 dark:border-amber-900/30 animate-pulse'
                    : 'border-slate-100 dark:border-slate-800'
                }`}
              >
                {/* Task Left Checkbox details */}
                <div className="flex items-start gap-4">
                  <input
                    type="checkbox"
                    checked={completed}
                    onChange={() => handleToggleTask(tk)}
                    disabled={cancelled}
                    className="w-5 h-5 rounded border-slate-300 text-legal-gold focus:ring-legal-gold cursor-pointer mt-1"
                  />
                  <div>
                    <h3 className={`font-semibold text-base ${
                      completed ? 'line-through text-slate-400 dark:text-slate-500' : 'text-slate-800 dark:text-white'
                    }`}>
                      {tk.title}
                    </h3>
                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 font-medium">
                      <span className="flex items-center gap-1">
                        <User className="w-3.5 h-3.5 text-legal-gold" />
                        Asignada a: {tk.assigned_to?.first_name} {tk.assigned_to?.last_name}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-legal-gold" />
                        Vence:{' '}
                        <span className={overdue ? 'text-rose-500 font-bold' : nearDue ? 'text-amber-500 font-bold' : ''}>
                          {new Date(tk.due_date).toLocaleDateString('es-ES')}
                        </span>
                      </span>
                    </p>
                    {tk.description && (
                      <p className="text-sm text-slate-500 dark:text-slate-400 font-medium mt-2 bg-slate-50/50 dark:bg-legal-charcoal-dark/50 p-2.5 rounded-lg border border-slate-100/50 dark:border-slate-800/50 max-w-2xl">
                        {tk.description}
                      </p>
                    )}
                  </div>
                </div>

                {/* Right controls */}
                <div className="flex items-center gap-3 self-end sm:self-center">
                  {/* Indicators alerts */}
                  {overdue && (
                    <span className="flex items-center gap-1 text-xs font-bold text-rose-500 bg-rose-50 dark:bg-rose-500/10 px-2 py-0.5 rounded animate-overdue">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Vencida
                    </span>
                  )}
                  {nearDue && (
                    <span className="flex items-center gap-1 text-xs font-bold text-amber-500 bg-amber-50 dark:bg-amber-500/10 px-2 py-0.5 rounded">
                      <AlertCircle className="w-3.5 h-3.5" />
                      Próxima
                    </span>
                  )}

                  {/* Priority Label */}
                  <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded tracking-wide ${
                    tk.priority === 'urgente'
                      ? 'bg-rose-100 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400'
                      : tk.priority === 'alta'
                      ? 'bg-amber-100 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400'
                      : 'bg-slate-100 text-slate-500'
                  }`}>
                    {tk.priority}
                  </span>

                  {/* Delete (hidden from assistants) */}
                  {!isAssistant && (
                    <button
                      onClick={() => handleDeleteTask(tk.id)}
                      className="p-2 rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-500 active:scale-95 transition-all"
                    >
                      <Trash2 className="w-4.5 h-4.5" />
                    </button>
                  )}
                </div>

              </div>
            )
          })}
        </div>
      )}

      {/* Create Task Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setErrorMessage('') }}
        title="Crear Nueva Tarea de Oficina"
        size="md"
      >
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}
        <TaskForm
          users={staffList}
          onSubmit={handleCreateSubmit}
          onCancel={() => { setIsModalOpen(false); setErrorMessage('') }}
          isSubmitting={createTaskMutation.isLoading}
        />
      </Modal>
    </div>
  )
}

export default TasksPage
export { TasksPage }
