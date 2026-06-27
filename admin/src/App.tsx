import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { useAuth } from './auth/auth-context'
import { AppShell } from './components/AppShell'
import { TooltipProvider } from './components/ui/tooltip'
import { LoadingState } from './components/ui-primitives'
import { DashboardPage } from './pages/DashboardPage'
import {
  CardsPage,
  DecksPage,
  ReportsPage,
  UsersPage,
} from './pages/ListPages'
import { LoginPage } from './pages/LoginPage'
import { CardDetailPage } from './pages/CardDetailPage'
import { NewCardPage, NewCardVersionPage } from './pages/CardFormPage'
import { CardImportPage } from './pages/CardImportPage'
import { DeckDetailPage, NewDeckPage } from './pages/DeckPages'
import { ReportDetailPage } from './pages/ReportDetailPage'
import { EditUserPage, NewUserPage } from './pages/UserPages'
import { OperationPage } from './pages/OperationPage'
import { AddonPage } from './pages/AddonPage'
import {
  AdminDashboardPage,
  AdminDecksPage,
  AdminSuggestionsPage,
  CommunityFuturePage,
  CommunitySuggestionHistoryPage,
  DeckPage,
  ExplorePage,
  MyDecksPage,
} from './pages/CommunityInterfacePages'
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
        <Route index element={<ExplorePage />} />
        <Route path="my-decks" element={<MyDecksPage />} />
        <Route path="deck/:deckId" element={<DeckPage />} />
        <Route path="deck/:deckId/suggestions" element={<CommunitySuggestionHistoryPage />} />
        <Route path="community" element={<CommunityFuturePage />} />
        <Route
          path="admin"
          element={
            <ProtectedRoute roles={['admin', 'curator', 'reviewer']}>
              <AdminDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/decks"
          element={
            <ProtectedRoute roles={['admin', 'curator']}>
              <AdminDecksPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin/suggestions"
          element={
            <ProtectedRoute roles={['admin', 'reviewer']}>
              <AdminSuggestionsPage />
            </ProtectedRoute>
          }
        />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="cards" element={<CardsPage />} />
        <Route
          path="cards/import"
          element={
            <ProtectedRoute roles={['admin', 'curator']}>
              <CardImportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="cards/new"
          element={
            <ProtectedRoute roles={['admin', 'curator']}>
              <NewCardPage />
            </ProtectedRoute>
          }
        />
        <Route path="cards/:cardId" element={<CardDetailPage />} />
        <Route
          path="cards/:cardId/versions/new"
          element={
            <ProtectedRoute roles={['admin', 'curator']}>
              <NewCardVersionPage />
            </ProtectedRoute>
          }
        />
        <Route path="decks" element={<DecksPage />} />
        <Route
          path="decks/new"
          element={
            <ProtectedRoute roles={['admin', 'curator']}>
              <NewDeckPage />
            </ProtectedRoute>
          }
        />
        <Route path="decks/:deckId" element={<DeckDetailPage />} />
        <Route path="addon" element={<AddonPage />} />
        <Route
          path="reports"
          element={
            <ProtectedRoute roles={['admin', 'reviewer']}>
              <ReportsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="reports/:reportId"
          element={
            <ProtectedRoute roles={['admin', 'reviewer']}>
              <ReportDetailPage />
            </ProtectedRoute>
          }
        />
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
              <NewUserPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="users/:userId"
          element={
            <ProtectedRoute roles={['admin']}>
              <EditUserPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="operation"
          element={
            <ProtectedRoute roles={['admin']}>
              <OperationPage />
            </ProtectedRoute>
          }
        />
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
        <TooltipProvider>
          <AppRoutes />
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
