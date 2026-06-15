import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { useAuth } from './auth/auth-context'
import { AppShell } from './components/AppShell'
import { LoadingState } from './components/ui'
import { DashboardPage } from './pages/DashboardPage'
import {
  CardsPage,
  DecksPage,
  ReportsPage,
  UsersPage,
} from './pages/ListPages'
import { LoginPage } from './pages/LoginPage'
import { OperationPage } from './pages/OperationPage'
import type { UserRole } from './types'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function ProtectedRoute({
  roles,
  children,
}: {
  roles?: UserRole[]
  children: React.ReactNode
}) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <LoadingState />
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/forbidden" replace />
  }
  return children
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="placeholder-page">
      <p className="eyebrow">Próxima etapa</p>
      <h1>{title}</h1>
      <p>
        O contrato da API já está mapeado. Esta tela será implementada após a
        validação do design base no Stitch.
      </p>
    </div>
  )
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="cards" element={<CardsPage />} />
        <Route path="cards/new" element={<PlaceholderPage title="Novo cartão" />} />
        <Route path="cards/:cardId" element={<PlaceholderPage title="Detalhe do cartão" />} />
        <Route path="decks" element={<DecksPage />} />
        <Route path="decks/new" element={<PlaceholderPage title="Novo deck" />} />
        <Route path="decks/:deckId" element={<PlaceholderPage title="Detalhe do deck" />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="reports/:reportId" element={<PlaceholderPage title="Revisão de report" />} />
        <Route
          path="users"
          element={
            <ProtectedRoute roles={['admin']}>
              <UsersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="users/new"
          element={
            <ProtectedRoute roles={['admin']}>
              <PlaceholderPage title="Novo usuário" />
            </ProtectedRoute>
          }
        />
        <Route path="operation" element={<OperationPage />} />
        <Route path="forbidden" element={<PlaceholderPage title="Acesso não autorizado" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </QueryClientProvider>
  )
}
