import React from 'react'
import { useQuery } from '@tanstack/react-query'
import axiosClient from '../api/axiosClient'
import { useAuth } from '../hooks/useAuth'
import { 
  Users, 
  Briefcase, 
  CheckCircle, 
  CheckSquare, 
  AlertTriangle,
  Clock,
  ArrowRight,
  TrendingUp,
  AlertCircle
} from 'lucide-react'

const DashboardPage = () => {
  const { user } = useAuth()

  // Query Dashboard Statistics
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: async () => {
      const response = await axiosClient.get('/dashboard/stats')
      return response.data
    },
    refetchInterval: 30000, // Auto-refresh statistics every 30 seconds
  })

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400 p-4 rounded-xl flex items-center gap-3">
        <AlertCircle className="w-6 h-6 flex-shrink-0" />
        <span>Error al cargar las estadísticas del panel. Por favor intente recargar la página.</span>
      </div>
    )
  }

  // Loading state skeleton placeholders
  const kpis = data?.kpis || {}
  const recentActivities = data?.recent_activities || []
  const urgentTasks = data?.urgent_tasks || []

  const kpiCards = [
    { 
      label: 'Clientes Activos', 
      value: kpis.total_clients, 
      icon: Users, 
      color: 'text-indigo-600 dark:text-indigo-400',
      bg: 'bg-indigo-50 dark:bg-indigo-500/10'
    },
    { 
      label: 'Expedientes en Trámite', 
      value: kpis.total_open_cases, 
      icon: Briefcase, 
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-500/10'
    },
    { 
      label: 'Casos Resueltos (Mes)', 
      value: kpis.total_closed_cases_month, 
      icon: CheckCircle, 
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-500/10'
    },
    { 
      label: 'Mis Tareas Pendientes', 
      value: kpis.pending_tasks_user, 
      icon: CheckSquare, 
      color: 'text-sky-600 dark:text-sky-400',
      bg: 'bg-sky-50 dark:bg-sky-500/10'
    },
    { 
      label: 'Tareas Vencidas', 
      value: kpis.overdue_tasks, 
      icon: AlertTriangle, 
      color: kpis.overdue_tasks > 0 ? 'text-rose-600 dark:text-rose-400 animate-overdue' : 'text-slate-500',
      bg: kpis.overdue_tasks > 0 ? 'bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20' : 'bg-slate-50 dark:bg-slate-800'
    },
  ]

  return (
    <div className="space-y-8">
      {/* Dashboard Greeting Header */}
      <div>
        <h1 className="font-serif text-3xl font-bold text-legal-navy-deep dark:text-white mb-1.5">
          Bienvenido de nuevo, {user?.name}
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
          Resumen operativo y novedades judiciales para el {new Date().toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, idx) => (
            <div key={idx} className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800/80 p-5 rounded-2xl shadow-premium animate-pulse h-32 flex flex-col justify-between">
              <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-2/3"></div>
              <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
            </div>
          ))
        ) : (
          kpiCards.map((kpi, idx) => {
            const Icon = kpi.icon
            return (
              <div key={idx} className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800/80 p-5 rounded-2xl shadow-premium hover:shadow-premium-lg hover:-translate-y-0.5 transition-all duration-300 flex flex-col justify-between h-32">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                    {kpi.label}
                  </span>
                  <div className={`p-2 rounded-lg ${kpi.bg}`}>
                    <Icon className={`w-5 h-5 ${kpi.color}`} />
                  </div>
                </div>
                <div className="mt-4">
                  <span className="text-3xl font-bold font-serif text-legal-navy-deep dark:text-white">
                    {kpi.value}
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Core Feed Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Recent Activities Timeline (2/3 width on large screens) */}
        <div className="lg:col-span-2 bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100 dark:border-slate-800">
            <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-legal-gold" />
              Historial Reciente de Actividades
            </h3>
            <span className="text-xs font-semibold text-slate-400">Últimas 10 gestiones</span>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 4 }).map((_, idx) => (
                <div key={idx} className="flex gap-4 animate-pulse">
                  <div className="w-3 h-3 rounded-full bg-slate-200 dark:bg-slate-800 mt-2"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/3"></div>
                    <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-full"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : recentActivities.length === 0 ? (
            <div className="py-12 text-center text-slate-400">
              No se han registrado actividades recientes en el estudio.
            </div>
          ) : (
            <div className="space-y-2">
              {recentActivities.map((act) => (
                <div key={act.id} className="timeline-pill flex items-start gap-4">
                  {/* Timeline bullet dot */}
                  <span className="timeline-dot" />

                  {/* Activity Details Card */}
                  <div className="flex-1 pb-4">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-legal-navy-deep/5 text-legal-navy-deep dark:bg-legal-gold/10 dark:text-legal-gold tracking-wide">
                          {act.type}
                        </span>
                        <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{act.author}</span>
                      </div>
                      <span className="text-xs text-slate-400">
                        {new Date(act.date).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })} hs
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-300 font-medium">
                      {act.description}
                    </p>
                    {act.duration > 0 && (
                      <span className="text-xs text-slate-400 mt-1 block">
                        Duración: {act.duration} minutos
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Urgent Tasks Section (1/3 width) */}
        <div className="bg-white dark:bg-legal-charcoal-medium border border-slate-100 dark:border-slate-800 p-6 rounded-2xl shadow-premium flex flex-col">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100 dark:border-slate-800">
            <h3 className="font-serif text-lg font-bold text-legal-navy-deep dark:text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-500" />
              Tareas Urgentes
            </h3>
            <span className="text-xs font-bold text-rose-500 bg-rose-50 dark:bg-rose-500/10 px-2 py-0.5 rounded">Prioritarias</span>
          </div>

          {isLoading ? (
            <div className="space-y-4 flex-1">
              {Array.from({ length: 3 }).map((_, idx) => (
                <div key={idx} className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl animate-pulse h-16"></div>
              ))}
            </div>
          ) : urgentTasks.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center py-12 text-center text-slate-400">
              <CheckCircle className="w-10 h-10 text-emerald-500/80 mb-2" />
              <span>¡Al día! No hay tareas urgentes pendientes.</span>
            </div>
          ) : (
            <div className="space-y-4 flex-1 overflow-y-auto">
              {urgentTasks.map((task) => (
                <div 
                  key={task.id} 
                  className="p-4 rounded-xl bg-slate-50 dark:bg-legal-charcoal-dark border border-slate-100 dark:border-slate-800 hover:border-slate-200 dark:hover:border-slate-700 transition-colors flex flex-col gap-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 line-clamp-1">{task.title}</span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400 mt-1">
                    <span className="capitalize px-1.5 py-0.5 rounded bg-slate-200/50 text-slate-600 dark:bg-slate-800 dark:text-slate-400 font-medium">
                      {task.status}
                    </span>
                    <span className="font-semibold text-rose-500">
                      Vence: {new Date(task.due_date).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Shortcut Link to Tasks Page */}
          <div className="pt-6 border-t border-slate-100 dark:border-slate-800 mt-4">
            <a 
              href="/tasks" 
              className="text-sm font-bold text-legal-gold hover:text-legal-gold-dark flex items-center justify-center gap-1.5 transition-colors"
            >
              Ver todas mis tareas
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>

      </div>
    </div>
  )
}

export default DashboardPage
export { DashboardPage }
