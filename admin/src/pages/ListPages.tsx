import { useQuery } from '@tanstack/react-query'
import {
  CaretLeft as ChevronLeft,
  CaretRight as ChevronRight,
  Funnel as Filter,
  Plus,
  ArrowClockwise as RefreshCw,
  MagnifyingGlass as Search,
  UploadSimple as Upload,
} from '@phosphor-icons/react'
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
} from '../components/ui-primitives'
import { formatDate } from '../lib/presentation'
import type {
  CardSummary,
  DeckSummary,
  DisciplineList,
  Paginated,
  Report,
  TopicList,
  User,
} from '../types'

export function CardsPage() {
  const { token, hasRole } = useAuth()
  const [page, setPage] = useState(1)
  const [publicIdInput, setPublicIdInput] = useState('')
  const [publicId, setPublicId] = useState('')
  const [status, setStatus] = useState('')
  const [disciplineId, setDisciplineId] = useState('')
  const [topicId, setTopicId] = useState('')
  const disciplines = useQuery({
    queryKey: ['disciplines'],
    queryFn: () => apiRequest<DisciplineList>('/disciplines', {}, token),
  })
  const topics = useQuery({
    queryKey: ['topics', disciplineId],
    enabled: Boolean(disciplineId),
    queryFn: () =>
      apiRequest<TopicList>(
        `/disciplines/${disciplineId}/topics`,
        {},
        token,
      ),
  })
  const query = useQuery({
    queryKey: ['cards', page, publicId, status, disciplineId, topicId],
    queryFn: () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '20',
      })
      if (publicId) params.set('public_id', publicId)
      if (status) params.set('status', status)
      if (disciplineId) params.set('discipline_id', disciplineId)
      if (topicId) params.set('topic_id', topicId)
      return apiRequest<Paginated<CardSummary>>(
        `/cards?${params.toString()}`,
        {},
        token,
      )
    },
  })
  const publishedCards = useCardCount('published', token)
  const reviewCards = useCardCount('needs_review', token)
  const reportedCards = useCardCount('reported', token)

  function applyFilters(event: FormEvent) {
    event.preventDefault()
    setPage(1)
    setPublicId(publicIdInput.trim())
  }

  return (
    <div className="cards-master-page">
      <header className="master-list-header">
        <div>
          <p className="eyebrow">Base editorial</p>
          <h1>Lista mestre de cartões</h1>
          <p>
            Gerencie e audite o repositório global de flashcards do Anki
            Concursos.
          </p>
        </div>
        {hasRole('admin', 'curator') && (
          <div className="action-group">
            <Link className="button button-secondary" to="/cards/import">
              <Upload size={18} /> Importar CSV
            </Link>
            <Link className="button button-primary" to="/cards/new">
            <Plus size={18} /> Novo cartão
            </Link>
          </div>
        )}
      </header>

      <form className="filter-panel cards-filter-panel" onSubmit={applyFilters}>
        <label>
          <span>Disciplina</span>
          <select
            value={disciplineId}
            onChange={(event) => {
              setDisciplineId(event.target.value)
              setTopicId('')
              setPage(1)
            }}
          >
            <option value="">Todas as disciplinas</option>
            {disciplines.data?.items.map((discipline) => (
              <option
                key={discipline.discipline_id}
                value={discipline.discipline_id}
              >
                {discipline.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Assunto</span>
          <select
            value={topicId}
            disabled={!disciplineId || topics.isLoading}
            onChange={(event) => {
              setTopicId(event.target.value)
              setPage(1)
            }}
          >
            <option value="">Todos os assuntos</option>
            {topics.data?.items.map((topic) => (
              <option key={topic.topic_id} value={topic.topic_id}>
                {topic.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Status</span>
          <select
            value={status}
            onChange={(event) => {
              setStatus(event.target.value)
              setPage(1)
            }}
          >
            <option value="">Todos os estados</option>
            <option value="draft">Rascunho</option>
            <option value="needs_review">Precisa de revisão</option>
            <option value="approved">Aprovado</option>
            <option value="published">Publicado</option>
            <option value="reported">Reportado</option>
            <option value="deprecated">Depreciado</option>
          </select>
        </label>
        <label className="search-field">
          <Search size={17} />
          <span className="sr-only">Buscar por ID público</span>
          <input
            value={publicIdInput}
            onChange={(event) => setPublicIdInput(event.target.value)}
            placeholder="Buscar por ID público, ex.: AC-..."
          />
        </label>
        <button className="button button-secondary" type="submit">
          <Filter size={16} />
          Aplicar filtros
        </button>
      </form>
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
                    <th aria-label="Ações" />
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
                          ? (
                              <span className="version-cell">
                                v{card.current_version.version_number}
                                <StatusBadge value={card.current_version.status} />
                              </span>
                            )
                          : 'Sem versão'}
                      </td>
                      <td>{formatDate(card.updated_at)}</td>
                      <td>
                        <Link
                          className="row-action"
                          to={`/cards/${card.card_id}`}
                          aria-label={`Abrir ${card.public_id}`}
                        >
                          <ChevronRight size={17} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <Pagination data={data} page={page} onPageChange={setPage} />
            </div>
          ) : (
            <EmptyState
              title="Nenhum cartão encontrado"
              description="Cadastre o primeiro cartão para iniciar o fluxo editorial."
            />
          )
        }
      </DataRegion>
      <section className="cards-summary-grid" aria-label="Resumo de cartões">
        <SummaryMetric
          label="Total de cartões"
          value={query.data?.total}
          detail="resultado do filtro atual"
        />
        <SummaryMetric
          label="Cartões publicados"
          value={publishedCards.data?.total}
          detail="prontos para distribuição"
        />
        <SummaryMetric
          label="Pendentes de revisão"
          value={reviewCards.data?.total}
          detail="aguardando decisão editorial"
        />
        <SummaryMetric
          label="Reportados"
          value={reportedCards.data?.total}
          detail="exigem triagem"
        />
      </section>
    </div>
  )
}

function useCardCount(status: string, token: string | null) {
  return useQuery({
    queryKey: ['card-count', status],
    queryFn: () =>
      apiRequest<Paginated<CardSummary>>(
        `/cards?page=1&page_size=1&status=${status}`,
        {},
        token,
      ),
  })
}

function SummaryMetric({
  label,
  value,
  detail,
}: {
  label: string
  value?: number
  detail: string
}) {
  return (
    <article className="summary-metric-card">
      <small>{detail}</small>
      <span>{label}</span>
      <strong>{typeof value === 'number' ? value.toLocaleString('pt-BR') : '…'}</strong>
    </article>
  )
}

export function DecksPage() {
  const { token, hasRole } = useAuth()
  const [page, setPage] = useState(1)
  const query = useQuery({
    queryKey: ['decks', page],
    queryFn: () =>
      apiRequest<Paginated<DeckSummary>>(
        `/decks?page=${page}&page_size=20`,
        {},
        token,
      ),
  })
  return (
    <>
      <PageHeader
        eyebrow="Distribuição"
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
            <div className="table-card">
              <table>
                <thead>
                  <tr>
                    <th>Deck</th>
                    <th>Status</th>
                    <th>Cartões ativos</th>
                    <th>Atualização</th>
                    <th aria-label="Ações" />
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((deck) => (
                    <tr key={deck.deck_id}>
                      <td>
                        <Link className="table-link" to={`/decks/${deck.deck_id}`}>
                          {deck.name}
                        </Link>
                        <small className="cell-secondary">
                          {deck.description || 'Sem descrição.'}
                        </small>
                      </td>
                      <td><StatusBadge value={deck.status} /></td>
                      <td><strong>{deck.active_card_count}</strong></td>
                      <td>{formatDate(deck.updated_at)}</td>
                      <td>
                        <Link
                          className="row-action"
                          to={`/decks/${deck.deck_id}`}
                          aria-label={`Abrir ${deck.name}`}
                        >
                          <ChevronRight size={17} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <Pagination data={data} page={page} onPageChange={setPage} />
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
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState('')
  const [reportType, setReportType] = useState('')
  const query = useQuery({
    queryKey: ['reports', page, status, reportType],
    queryFn: () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '20',
      })
      if (status) params.set('status', status)
      if (reportType) params.set('report_type', reportType)
      return apiRequest<Paginated<Report>>(
        `/admin/reports?${params.toString()}`,
        {},
        token,
      )
    },
  })
  return (
    <>
      <PageHeader
        eyebrow="Curadoria"
        title="Reports"
        description="Analise problemas reportados e registre decisões auditáveis."
      />
      <div className="filter-panel report-filters">
        <label>
          <span>Status</span>
          <select
            value={status}
            onChange={(event) => {
              setStatus(event.target.value)
              setPage(1)
            }}
          >
            <option value="">Todos</option>
            <option value="open">Aberto</option>
            <option value="in_review">Em revisão</option>
            <option value="resolved">Resolvido</option>
            <option value="rejected">Rejeitado</option>
            <option value="duplicate">Duplicado</option>
          </select>
        </label>
        <label>
          <span>Tipo</span>
          <select
            value={reportType}
            onChange={(event) => {
              setReportType(event.target.value)
              setPage(1)
            }}
          >
            <option value="">Todos os tipos</option>
            <option value="wrong_answer">Resposta incorreta</option>
            <option value="bad_explanation">Explicação inadequada</option>
            <option value="outdated_law">Legislação desatualizada</option>
            <option value="typo">Erro de digitação</option>
            <option value="classification_error">Erro de classificação</option>
            <option value="duplicate_card">Cartão duplicado</option>
            <option value="suggestion">Sugestão</option>
          </select>
        </label>
      </div>
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
              <Pagination data={data} page={page} onPageChange={setPage} />
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
  const [page, setPage] = useState(1)
  const query = useQuery({
    queryKey: ['users', page],
    queryFn: () =>
      apiRequest<Paginated<User>>(
        `/admin/users?page=${page}&page_size=20`,
        {},
        token,
      ),
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
                    <th aria-label="Ações" />
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((user) => (
                    <tr key={user.user_id}>
                      <td>
                        <Link className="table-link" to={`/users/${user.user_id}`}>
                          {user.display_name}
                        </Link>
                        <small className="cell-secondary">{user.email}</small>
                      </td>
                      <td><StatusBadge value={user.role} /></td>
                      <td><StatusBadge value={user.is_active ? 'active' : 'inactive'} /></td>
                      <td>{formatDate(user.last_login_at)}</td>
                      <td>
                        <Link
                          className="row-action"
                          to={`/users/${user.user_id}`}
                          aria-label={`Editar ${user.display_name}`}
                        >
                          <ChevronRight size={17} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <Pagination data={data} page={page} onPageChange={setPage} />
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

function Pagination({
  data,
  page,
  onPageChange,
}: {
  data: Paginated<unknown>
  page: number
  onPageChange: (page: number) => void
}) {
  const pages = Math.max(data.pages, 1)
  return (
    <footer className="table-summary">
      <span>
        Página {data.page} de {pages} · {data.total} registros
      </span>
      <div className="pagination-actions">
        <button
          type="button"
          aria-label="Página anterior"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft size={16} />
        </button>
        <strong>{page}</strong>
        <button
          type="button"
          aria-label="Próxima página"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </footer>
  )
}
