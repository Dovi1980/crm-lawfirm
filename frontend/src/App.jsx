import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'

// Pages
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ClientsPage from './pages/ClientsPage'
import ClientDetailPage from './pages/ClientDetailPage'
import CasesPage from './pages/CasesPage'
import CaseDetailPage from './pages/CaseDetailPage'
import TasksPage from './pages/TasksPage'
import UsersPage from './pages/UsersPage'

// Create TanStack Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public Access Route */}
            <Route path="/login" element={<LoginPage />} />

            {/* Authenticated Dashboard Shell Layout */}
            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              
              <Route path="/clients" element={<ClientsPage />} />
              <Route path="/clients/:id" element={<ClientDetailPage />} />
              
              <Route path="/cases" element={<CasesPage />} />
              <Route path="/cases/:id" element={<CaseDetailPage />} />
              
              <Route path="/tasks" element={<TasksPage />} />
              
              {/* Admin Roles Restrict Route */}
              <Route path="/users" element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <UsersPage />
                </ProtectedRoute>
              } />
            </Route>

            {/* Generic Page Not Found fallback */}
            <Route path="*" element={
              <div className="flex flex-col items-center justify-center min-h-screen bg-legal-cream dark:bg-legal-charcoal-dark p-6 text-center">
                <h1 className="font-serif text-8xl font-bold text-legal-gold mb-4">404</h1>
                <p className="text-xl text-legal-navy-deep dark:text-slate-300 font-medium mb-6">Página no encontrada</p>
                <a href="/" className="premium-btn-primary">Volver al Portal</a>
              </div>
            } />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
