import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../hooks/useAuth'
import axiosClient from '../api/axiosClient'
import Modal from '../components/Modal'
import ClientForm from '../components/forms/ClientForm'
import InteractionForm from '../components/forms/InteractionForm'
import { 
  Building2, 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  FileText,
  Calendar,
  Plus,
  Edit,
  Trash2,
  AlertCircle,
  Clock,
  Briefcase
} from 'lucide-react'

const ClientDetailPage = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAssistant } = useAuth()
  const queryClient = useQueryClient()

  // Modal States
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isInteractionModalOpen, setIsInteractionModalOpen] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  // 1. Fetch Client Profile Details
  const { data: client, isLoading: isClientLoading, error: clientError } = useQuery({
    queryKey: ['client', id],
    queryFn: async () => {
      const response = await axiosClient.get(`/clients/${id}`)
      return response.data
    }
  })

  // 2. Fetch Client's Associated Cases (Expedientes)
  const { data: cases = [], isLoading: isCasesLoading } = useQuery({
    queryKey: ['clientCases', id],
    queryFn: async () => {
      const response = await axiosClient.get(`/cases?client_id=${id}`)
      return response.data
    }
  })

  // 3. Fetch Client's Activity Timeline Interactions
  const { data: interactions = [], isLoading: isInteractionsLoading } = useQuery({
    queryKey: ['clientInteractions', id],
    queryFn: async () => {
      const response = await axiosClient.get(`/interactions?client_id=${id}`)
      return response.data
    }
  })

  // Edit Client Profile Mutation
  const updateMutation = useMutation({
    mutationFn: async (updatedData) => {
      return await axiosClient.put(`/clients/${id}`, updatedData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['client', id])
      queryClient.invalidateQueries(['clients'])
      setIsEditModalOpen(false)
      setErrorMessage('')
    },
    onError: (err) => {
      setErrorMessage(err.response?.data?.detail || 'Error al actualizar el perfil.')
    }
  })

  // Delete Client Profile Mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      return await axiosClient.delete(`/clients/${id}`)
    },
    onSuccess: (response) => {
      // Backend returns either hard-deleted or soft-deactivated message
      alert(response.data?.detail || 'Cliente removido correctamente.')
      navigate('/clients')
    },
    onError: (err) => {
      alert(err.response?.data?.detail || 'No se pudo eliminar el cliente.')
    }
  })

  // Create Append-only Interaction Log Mutation
  const addInteractionMutation = useMutation({
    mutationFn: async (newAct) => {
      return await axiosClient.post('/interactions', newAct)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['clientInteractions', id])
      queryClient.invalidateQueries(['dashboardStats'])
      setIsInteractionModalOpen(false)
      setErrorMessage('')
    },
    onError: (err) => {
      setErrorMessage(err.response?.data?.detail || 'Error al registrar la actividad.')
    }
  })

  if (isClientLoading) {
    return (
      <div className="flex justify-center items-center py-24">
        <div className="w-10 h-10 border-4 border-legal-gold border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  if (clientError) {
    return (
      <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-4 rounded-xl flex items-center gap-3">
        <AlertCircle className="w-6 h-6 flex-shrink-0" />
        <span>El cliente no existe o ha sido desvinculado del estudio.</span>
      </div>
    )
  }

  const handleEditSubmit = (formData) => {
    updateMutation.mutate(formData)
  }

  const handleDelete = () => {
    if (window.confirm('¿Está seguro de que desea eliminar permanentemente la ficha de este cliente?')) {
      deleteMutation.mutate()
    }
  }

  const handleAddInteraction = (formData) => {
    addInteractionMutation.mutate(formData)
  }

  return (
    <div className="space-y-8">
      {/* Detail Toolbar Title and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-legal-navy-deep text-white border border-legal-gold flex items-center justify-center font-serif text-xl font-bold dark:bg-legal-gold dark:text-legal-navy-deep">
            {client.client_type === 'natural' ? <User className="w-6 h-6" /> : <Building2 className="w-6 h-6" />}
          </div>
          <div>
            <h1 className="font-serif text-3xl font-bold text-legal-navy-deep dark:text-white mb-1">
              {client.last_name}, {client.first_name}
            </h1>
            <p className="text-xs text-legal-gold font-bold tracking-widest uppercase">
              Ficha del Cliente #{client.id}
            </p>
          </div>
        </div>

        {/* Action buttons (hides delete for assistants) */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsEditModalOpen(true)}
            className="premium-btn-secondary"
          >
            <Edit className="w-4 h-4" />
            <span>Editar Ficha</span>
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

      {/* Info Card blocks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Core Profile stats card */}
        <div className="lg:col-span-1 bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium h-fit space-y-6">
          <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white pb-3 border-b border-slate-100 dark:border-slate-800">
            Detalles de Contacto
          </h3>
          <div className="space-y-4.5 text-sm">
            {client.tax_id && (
              <div className="flex items-start gap-3">
                <FileText className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">CUIT / CUIL / DNI</h4>
                  <p className="text-slate-800 dark:text-slate-200 font-semibold">{client.tax_id}</p>
                </div>
              </div>
            )}
            {client.email && (
              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Correo Electrónico</h4>
                  <p className="text-slate-800 dark:text-slate-200 font-semibold truncate max-w-[200px]">{client.email}</p>
                </div>
              </div>
            )}
            {client.phone && (
              <div className="flex items-start gap-3">
                <Phone className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Teléfono</h4>
                  <p className="text-slate-800 dark:text-slate-200 font-semibold">{client.phone}</p>
                </div>
              </div>
            )}
            {(client.address || client.city || client.province) && (
              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Domicilio Legal</h4>
                  <p className="text-slate-800 dark:text-slate-200 font-semibold">
                    {client.address || ''}<br />
                    {client.city ? `${client.city}, ` : ''}{client.province || ''}
                  </p>
                </div>
              </div>
            )}
            <div className="flex items-start gap-3">
              <Calendar className="w-5 h-5 text-legal-gold flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Alta en el Sistema</h4>
                <p className="text-slate-800 dark:text-slate-200 font-semibold">
                  {new Date(client.created_at).toLocaleDateString('es-ES')}
                </p>
              </div>
            </div>
          </div>

          {client.notes && (
            <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1.5">Anotaciones del Letrado</h4>
              <p className="text-sm bg-slate-50 dark:bg-legal-charcoal-dark border border-slate-100 dark:border-slate-800 p-3 rounded-lg text-slate-600 dark:text-slate-300 font-medium">
                {client.notes}
              </p>
            </div>
          )}
        </div>

        {/* Detailed Relations Work Area */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Associated Cases Index */}
          <div className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium">
            <div className="flex items-center justify-between mb-5">
              <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-legal-gold" />
                Expedientes del Cliente
              </h3>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                {cases.length} en total
              </span>
            </div>

            {isCasesLoading ? (
              <div className="h-20 bg-slate-100 dark:bg-slate-800 rounded animate-pulse" />
            ) : cases.length === 0 ? (
              <div className="py-8 text-center text-slate-400 dark:text-slate-500 font-medium">
                El cliente no cuenta con expedientes en trámite actualmente.
              </div>
            ) : (
              <div className="space-y-3">
                {cases.map((cs) => (
                  <div
                    key={cs.id}
                    onClick={() => navigate(`/cases/${cs.id}`)}
                    className="p-4 rounded-xl border border-slate-100 hover:border-slate-200 bg-slate-50/50 hover:bg-slate-50 dark:border-slate-800 dark:bg-legal-charcoal-dark dark:hover:bg-legal-charcoal-dark/70 transition-all cursor-pointer flex justify-between items-center"
                  >
                    <div>
                      <span className="text-xs font-bold text-legal-gold tracking-wide">{cs.case_number}</span>
                      <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mt-0.5">{cs.title}</h4>
                      <p className="text-xs text-slate-400 capitalize mt-1">{cs.case_type} · Asignado a: {cs.assigned_lawyer?.first_name} {cs.assigned_lawyer?.last_name}</p>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded text-xs font-bold uppercase ${
                      cs.status === 'cerrado' ? 'bg-slate-200 text-slate-600' : 'bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400'
                    }`}>
                      {cs.status.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Interactions History logs timeline */}
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
                No se registran llamadas, audiencias o escritos cargados en la ficha.
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
                      <p className="text-sm text-slate-600 dark:text-slate-300 font-medium">
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

      {/* Edit Client Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => { setIsEditModalOpen(false); setErrorMessage('') }}
        title="Editar Ficha de Cliente"
        size="lg"
      >
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}
        <ClientForm
          initialData={client}
          onSubmit={handleEditSubmit}
          onCancel={() => { setIsEditModalOpen(false); setErrorMessage('') }}
          isSubmitting={updateMutation.isLoading}
        />
      </Modal>

      {/* Interaction Modal Log */}
      <Modal
        isOpen={isInteractionModalOpen}
        onClose={() => { setIsInteractionModalOpen(false); setErrorMessage('') }}
        title="Registrar Nueva Gestión de Trámite"
        size="md"
      >
        {errorMessage && (
          <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-3 rounded-lg flex items-start gap-2.5 text-sm mb-5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}
        <InteractionForm
          clientId={client.id}
          onSubmit={handleAddInteraction}
          onCancel={() => { setIsInteractionModalOpen(false); setErrorMessage('') }}
          isSubmitting={addInteractionMutation.isLoading}
        />
      </Modal>
    </div>
  )
}

export default ClientDetailPage
export { ClientDetailPage }
