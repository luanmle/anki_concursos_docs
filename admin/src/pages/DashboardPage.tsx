import {
  ArrowRight,
  BookOpenCheck,
  ClipboardList,
  CircleCheck,
  Database,
  FileWarning,
  GitBranch,
  Library,
  UserPlus,
  Users,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import type { CardSummary, DeckSummary, Paginated, Report, User } from '../types'

export function DashboardPage() {
  const { user, token, hasRole } = useAuth()
  const firstName = user?.display_name.split(' ')[0] ?? 'Admin'
  const canReview = hasRole('admin', 'reviewer')
  const canManageUsers = hasRole('admin')
  const cards = useQuery({
    queryKey: ['dashboard-cards'],
    queryFn: () => apiRequest<Paginated<CardSummary>>('/cards?page=1&page_size=1', {}, token),
  })
  const decks = useQuery({
    queryKey: ['dashboard-decks'],
    queryFn: () => apiRequest<Paginated<DeckSummary>>('/decks?page=1&page_size=1', {}, token),
  })
  const reports = useQuery({
    queryKey: ['dashboard-reports'],
    enabled: canReview,
    queryFn: () =>
      apiRequest<Paginated<Report>>(
        '/admin/reports?page=1&page_size=1&status=open',
        {},
        token,
      ),
  })
  const users = useQuery({
    queryKey: ['dashboard-users'],
    enabled: canManageUsers,
    queryFn: () =>
      apiRequest<Paginated<User>>('/admin/users?page=1&page_size=1', {}, token),
  })
  const health = useQuery({
    queryKey: ['dashboard-health'],
    queryFn: async () => {
      const [api, ready] = await Promise.all([
        apiRequest<{ status: string }>('/health'),
        apiRequest<{ status: string; database: string }>('/ready'),
      ])
      return { api, ready }
    },
    retry: false,
  })

  return (
    <div className="dashboard-page">
      <header className="dashboard-hero">
        <p className="eyebrow">Console administrativo</p>
        <h1>Visão geral</h1>
        <p>
          Olá, {firstName}. Este é o centro de comando para curadoria, decks,
          reports e operação da plataforma.
        </p>
      </header>

      <section className="dashboard-top-grid" aria-label="Ações principais">
        <ActionCard
          to="/users/new"
          icon={<UserPlus />}
          title="Provisionar usuários"
          description={formatMetric(users.data?.total, 'usuários cadastrados')}
          disabled={!canManageUsers}
        />
        <ActionCard
          to="/reports"
          icon={<ClipboardList />}
          title="Fila de revisão"
          description={formatMetric(reports.data?.total, 'reports abertos')}
          disabled={!canReview}
        />
        <ActionCard
          to="/cards"
          icon={<Database />}
          title="Base de cartões"
          description={formatMetric(cards.data?.total, 'cartões catalogados')}
        />
        <ActionCard
          to="/decks"
          icon={<BookOpenCheck />}
          title="Exportação de decks"
          description={formatMetric(decks.data?.total, 'decks disponíveis')}
        />
        <SystemHealthCard
          apiStatus={health.data?.api.status}
          databaseStatus={health.data?.ready.database}
          isError={health.isError}
        />
      </section>

      <section className="dashboard-lower-grid" aria-label="Fluxos administrativos">
        <article className="workflow-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Processo controlado</p>
              <h2>Fluxo editorial padrão</h2>
            </div>
            <GitBranch size={21} />
          </div>
          <div className="workflow-steps">
            {[
              ['Cadastrar', 'Criar o cartão e sua versão inicial.'],
              ['Revisar', 'Conferir conteúdo, referência e explicação.'],
              ['Aprovar', 'Registrar a decisão editorial.'],
              ['Publicar', 'Promover uma versão aprovada.'],
              ['Distribuir', 'Adicionar ao deck e publicar uma release.'],
            ].map(([step, description], index) => (
              <div key={step}>
                <b>{index + 1}</b>
                <span>
                  <strong>{step}</strong>
                  <small>{description}</small>
                </span>
              </div>
            ))}
          </div>
        </article>

        <aside className="dashboard-side-stack">
          <article className="dashboard-nav-card">
            <p className="eyebrow">Navegação rápida</p>
            <QuickLink to="/decks" icon={<BookOpenCheck />} title="Gerenciar decks" />
            <QuickLink to="/cards" icon={<Library />} title="Banco de cartões" />
            {canManageUsers && <QuickLink to="/users" icon={<Users />} title="Usuários" />}
            {canReview && (
              <QuickLink to="/reports" icon={<FileWarning />} title="Reports" />
            )}
          </article>

          <article className="principle-card">
            <CircleCheck size={22} />
            <div>
              <p className="eyebrow">Integridade garantida</p>
              <strong>Versões publicadas são imutáveis</strong>
              <p>
                Toda mudança pedagógica cria uma nova versão. O histórico
                anterior permanece disponível para auditoria e sincronização.
              </p>
            </div>
          </article>
        </aside>
      </section>
    </div>
  )
}

function formatMetric(value: number | undefined, label: string) {
  if (typeof value !== 'number') return 'Sincronizando com a API.'
  return `${value.toLocaleString('pt-BR')} ${label}.`
}

function ActionCard({
  to,
  icon,
  title,
  description,
  disabled = false,
}: {
  to: string
  icon: ReactNode
  title: string
  description: string
  disabled?: boolean
}) {
  if (disabled) {
    return (
      <article className="dashboard-action-card dashboard-action-disabled" aria-disabled="true">
        <span className="dashboard-action-icon">{icon}</span>
        <strong>{title}</strong>
        <p>Acesso indisponível para o seu papel administrativo.</p>
      </article>
    )
  }

  return (
    <Link className="dashboard-action-card" to={to}>
      <span className="dashboard-action-icon">{icon}</span>
      <strong>{title}</strong>
      <p>{description}</p>
    </Link>
  )
}

function SystemHealthCard({
  apiStatus,
  databaseStatus,
  isError,
}: {
  apiStatus?: string
  databaseStatus?: string
  isError: boolean
}) {
  const apiHealthy = apiStatus === 'ok' && !isError
  const databaseHealthy = databaseStatus === 'ok' && !isError
  return (
    <article className="system-health-card">
      <div className="system-card-title">
        <p className="eyebrow">System health</p>
        <span className={isError ? 'health-dot-error' : ''} />
      </div>
      <HealthRow label="Core API" value={apiHealthy ? 'Operacional' : 'Verificar'} healthy={apiHealthy} />
      <HealthRow label="Database" value={databaseHealthy ? 'Conectado' : 'Verificar'} healthy={databaseHealthy} />
      <HealthRow label="Admin frontend" value="Online" healthy />
      <div className="system-card-footer">
        <small>Monitoramento</small>
        <Link to="/operation">Ver status</Link>
      </div>
    </article>
  )
}

function HealthRow({
  label,
  value,
  healthy,
}: {
  label: string
  value: string
  healthy: boolean
}) {
  return (
    <div className="health-row">
      <strong>{label}</strong>
      <span className={healthy ? '' : 'health-row-warning'}>{value}</span>
    </div>
  )
}

function QuickLink({
  to,
  icon,
  title,
}: {
  to: string
  icon: ReactNode
  title: string
}) {
  return (
    <Link className="dashboard-nav-link" to={to}>
      <span className="quick-icon">{icon}</span>
      <strong>{title}</strong>
      <ArrowRight size={19} />
    </Link>
  )
}
