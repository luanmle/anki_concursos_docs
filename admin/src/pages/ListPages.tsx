import { useQuery } from '@tanstack/react-query'
import { Plus, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
} from '../components/ui'
import { formatDate } from '../lib/presentation'
import type {
  CardSummary,
  DeckSummary,
  Paginated,
  Report,
  User,
} from '../types'

export function CardsPage() {
  const { token, hasRole } = useAuth()
  const query = useQuery({
    queryKey: ['cards'],
    queryFn: () => apiRequest<Paginated<CardSummary>>('/cards', {}, token),
  })
  return (
    <>
      <PageHeader
        title="Cartões"
        description="Consulte identidades estáveis, versões atuais e estados editoriais."
        action={
          hasRole('admin', 'curator') ? (
            <Link className="button button-primary" to="/cards/new">
              <Plus size={18} /> Novo cartão
            </Link>
          ) : undefined
        }
      />
      <DataRegion query={query}>
        {(data) =>
          data.items.length ? (
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Identidade</th>
                    <th>Chave canônica</th>
                    <th>Status</th>
                    <th>Versão atual</th>
                    <th>Atualização</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((card) => (
                    <tr key={card.card_id}>
                      <td>
                        <Link className="table-link" to={`/cards/${card.card_id}`}>
                          {card.public_id}
                        </Link>
                      </td>
                      <td>{card.canonical_key}</td>
                      <td><StatusBadge value={card.status} /></td>
                      <td>
                        {card.current_version
                          ? `v${card.current_version.version_number} · ${card.current_version.status}`
                          : 'Sem versão'}
                      </td>
                      <td>{formatDate(card.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <TableSummary data={data} />
            </div>
          ) : (
            <EmptyState
              title="Nenhum cartão encontrado"
              description="Cadastre o primeiro cartão para iniciar o fluxo editorial."
            />
          )
        }
      </DataRegion>
    </>
  )
}

export function DecksPage() {
  const { token, hasRole } = useAuth()
  const query = useQuery({
    queryKey: ['decks'],
    queryFn: () => apiRequest<Paginated<DeckSummary>>('/decks', {}, token),
  })
  return (
    <>
      <PageHeader
        title="Decks"
        description="Organize cartões publicados e acompanhe releases imutáveis."
        action={
          hasRole('admin', 'curator') ? (
            <Link className="button button-primary" to="/decks/new">
              <Plus size={18} /> Novo deck
            </Link>
          ) : undefined
        }
      />
      <DataRegion query={query}>
        {(data) =>
          data.items.length ? (
            <div className="card-grid">
              {data.items.map((deck) => (
                <Link className="deck-card" key={deck.deck_id} to={`/decks/${deck.deck_id}`}>
                  <div>
                    <StatusBadge value={deck.status} />
                    <strong>{deck.name}</strong>
                    <p>{deck.description || 'Sem descrição.'}</p>
                  </div>
                  <span>{deck.active_card_count} cartões ativos</span>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState
              title="Nenhum deck cadastrado"
              description="Crie um deck para organizar versões publicadas."
            />
          )
        }
      </DataRegion>
    </>
  )
}

export function ReportsPage() {
  const { token } = useAuth()
  const query = useQuery({
    queryKey: ['reports'],
    queryFn: () =>
      apiRequest<Paginated<Report>>('/admin/reports', {}, token),
  })
  return (
    <>
      <PageHeader
        title="Reports"
        description="Analise problemas reportados e registre decisões auditáveis."
      />
      <DataRegion query={query}>
        {(data) =>
          data.items.length ? (
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Cartão</th>
                    <th>Tipo</th>
                    <th>Status</th>
                    <th>Tarefa</th>
                    <th>Recebido</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((report) => (
                    <tr key={report.report_id}>
                      <td>
                        <Link className="table-link" to={`/reports/${report.report_id}`}>
                          {report.public_id} · v{report.version_number}
                        </Link>
                      </td>
                      <td>{report.report_type.replaceAll('_', ' ')}</td>
                      <td><StatusBadge value={report.status} /></td>
                      <td><StatusBadge value={report.review_task.status} /></td>
                      <td>{formatDate(report.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <TableSummary data={data} />
            </div>
          ) : (
            <EmptyState
              title="Nenhum report pendente"
              description="Novos reports aparecerão aqui para revisão."
            />
          )
        }
      </DataRegion>
    </>
  )
}

export function UsersPage() {
  const { token } = useAuth()
  const query = useQuery({
    queryKey: ['users'],
    queryFn: () =>
      apiRequest<Paginated<User>>('/admin/users', {}, token),
  })
  return (
    <>
      <PageHeader
        title="Usuários"
        description="Gerencie papéis, acesso e atividade da equipe administrativa."
        action={
          <Link className="button button-primary" to="/users/new">
            <Plus size={18} /> Novo usuário
          </Link>
        }
      />
      <DataRegion query={query}>
        {(data) =>
          data.items.length ? (
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Usuário</th>
                    <th>Papel</th>
                    <th>Status</th>
                    <th>Último login</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((user) => (
                    <tr key={user.user_id}>
                      <td>
                        <strong>{user.display_name}</strong>
                        <small className="cell-secondary">{user.email}</small>
                      </td>
                      <td><StatusBadge value={user.role} /></td>
                      <td><StatusBadge value={user.is_active ? 'active' : 'inactive'} /></td>
                      <td>{formatDate(user.last_login_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <TableSummary data={data} />
            </div>
          ) : (
            <EmptyState
              title="Nenhum usuário encontrado"
              description="Crie um usuário para ampliar a equipe."
            />
          )
        }
      </DataRegion>
    </>
  )
}

function DataRegion<T>({
  query,
  children,
}: {
  query: {
    data?: T
    isLoading: boolean
    error: Error | null
    refetch: () => unknown
  }
  children: (data: T) => React.ReactNode
}) {
  if (query.isLoading) return <LoadingState />
  if (query.error) {
    const error = query.error
    return (
      <>
        <ErrorState
          message={error.message}
          requestId={error instanceof ApiError ? error.requestId : null}
        />
        <button className="button button-secondary" onClick={() => query.refetch()}>
          <RefreshCw size={17} /> Tentar novamente
        </button>
      </>
    )
  }
  return query.data ? children(query.data) : null
}

function TableSummary({ data }: { data: Paginated<unknown> }) {
  return (
    <footer className="table-summary">
      Página {data.page} de {Math.max(data.pages, 1)} · {data.total} registros
    </footer>
  )
}
