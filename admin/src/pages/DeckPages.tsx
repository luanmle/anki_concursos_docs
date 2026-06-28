import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  CaretLeft as ChevronLeft,
  CaretRight as ChevronRight,
  DownloadSimple as Download,
  Package as PackagePlus,
  Plus,
  RocketLaunch as Rocket,
  Trash as Trash2,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { z } from 'zod'
import {
  ApiError,
  apiDownload,
  apiRequest,
} from '../api/client'
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
  DeckDetail,
  DeckSync,
  DisciplineList,
  Paginated,
  ReleaseList,
} from '../types'

const deckSchema = z.object({
  name: z.string().trim().min(1, 'Informe o nome do deck.').max(255),
  discipline_id: z.string(),
  description: z.string().trim().max(5_000),
})

type DeckValues = z.infer<typeof deckSchema>

export function NewDeckPage() {
  const { token } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const form = useForm<DeckValues>({
    resolver: zodResolver(deckSchema),
    defaultValues: { name: '', discipline_id: '', description: '' },
  })
  const description = useWatch({
    control: form.control,
    name: 'description',
  })
  const disciplines = useQuery({
    queryKey: ['disciplines'],
    queryFn: () => apiRequest<DisciplineList>('/disciplines', {}, token),
  })
  const mutation = useMutation({
    mutationFn: (values: DeckValues) =>
      apiRequest<DeckDetail>(
        '/decks',
        {
          method: 'POST',
          body: JSON.stringify({
            ...values,
            discipline_id: values.discipline_id || null,
            description: values.description || null,
          }),
        },
        token,
      ),
    onSuccess: (deck) => {
      queryClient.invalidateQueries({ queryKey: ['decks'] })
      navigate(`/decks/${deck.deck_id}`, { replace: true })
    },
  })

  return (
    <div className="editor-page compact-editor">
      <Link className="back-link" to="/decks">
        <ArrowLeft size={16} />
        Voltar para decks
      </Link>
      <PageHeader
        eyebrow="Distribuição"
        title="Novo deck"
        description="Crie um agrupamento para versões publicadas de cartões."
      />
      {mutation.error && <InlineError error={mutation.error} />}
      <form
        className="editor-form"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <section className="form-section">
          <div className="form-section-heading">
            <h2>Identificação do deck</h2>
            <p>A disciplina é opcional e pode restringir o escopo editorial.</p>
          </div>
          <div className="deck-form-grid">
            <label className="form-field">
              <span className="field-heading"><strong>Nome</strong></span>
              <input {...form.register('name')} />
              {form.formState.errors.name && (
                <small className="field-error">
                  {form.formState.errors.name.message}
                </small>
              )}
            </label>
            <label className="form-field">
              <span className="field-heading"><strong>Disciplina</strong></span>
              <select {...form.register('discipline_id')}>
                <option value="">Todas / não definida</option>
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
          </div>
          <label className="form-field form-field-spaced">
            <span className="field-heading">
              <strong>Descrição</strong>
              <small>{description.length} / 5.000</small>
            </span>
            <textarea
              rows={5}
              maxLength={5_000}
              {...form.register('description')}
            />
          </label>
        </section>
        <footer className="form-actions">
          <Link className="button button-secondary" to="/decks">Cancelar</Link>
          <button className="button button-primary" disabled={mutation.isPending}>
            <Plus size={17} />
            {mutation.isPending ? 'Criando…' : 'Criar deck'}
          </button>
        </footer>
      </form>
    </div>
  )
}

export function DeckDetailPage() {
  const { deckId = '' } = useParams()
  const { token, hasRole } = useAuth()
  const queryClient = useQueryClient()
  const [cardReference, setCardReference] = useState('')
  const [releaseDescription, setReleaseDescription] = useState('')
  const [releasePage, setReleasePage] = useState(1)
  const [sinceRelease, setSinceRelease] = useState(0)
  const [downloadError, setDownloadError] = useState<Error | null>(null)
  const deck = useQuery({
    queryKey: ['deck', deckId],
    queryFn: () => apiRequest<DeckDetail>(`/decks/${deckId}`, {}, token),
  })
  const releases = useQuery({
    queryKey: ['deck-releases', deckId, releasePage],
    queryFn: () =>
      apiRequest<ReleaseList>(
        `/decks/${deckId}/releases?page=${releasePage}&page_size=20`,
        {},
        token,
      ),
  })
  const sync = useQuery({
    queryKey: ['deck-sync', deckId, sinceRelease],
    queryFn: () =>
      apiRequest<DeckSync>(
        `/decks/${deckId}/sync?since_release=${sinceRelease}`,
        {},
        token,
      ),
  })

  const refreshDeck = () => {
    queryClient.invalidateQueries({ queryKey: ['deck', deckId] })
    queryClient.invalidateQueries({ queryKey: ['decks'] })
  }
  const addCard = useMutation({
    mutationFn: async () => {
      const reference = cardReference.trim()
      let cardId = reference
      if (!z.string().uuid().safeParse(reference).success) {
        const result = await apiRequest<Paginated<CardSummary>>(
          `/cards?public_id=${encodeURIComponent(reference)}&page_size=1`,
          {},
          token,
        )
        const match = result.items.find((card) => card.public_id === reference)
        if (!match) throw new Error('Cartão não encontrado pelo ID informado.')
        cardId = match.card_id
      }
      return apiRequest<DeckDetail>(
        `/decks/${deckId}/cards`,
        { method: 'POST', body: JSON.stringify({ card_id: cardId }) },
        token,
      )
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['deck', deckId], data)
      queryClient.invalidateQueries({ queryKey: ['decks'] })
      setCardReference('')
    },
  })
  const removeCard = useMutation({
    mutationFn: (cardId: string) =>
      apiRequest<DeckDetail>(
        `/decks/${deckId}/cards/${cardId}/remove`,
        { method: 'POST', body: JSON.stringify({ action: 'removed' }) },
        token,
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(['deck', deckId], data)
      queryClient.invalidateQueries({ queryKey: ['decks'] })
    },
  })
  // re-adiciona o card → bumpa DeckCard p/ a versão publicada atual.
  // Depois é só "Publicar release" para a nota atualizar no sync/baralho.
  const updateCard = useMutation({
    mutationFn: (cardId: string) =>
      apiRequest<DeckDetail>(
        `/decks/${deckId}/cards`,
        { method: 'POST', body: JSON.stringify({ card_id: cardId }) },
        token,
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(['deck', deckId], data)
      // refetch garante que a linha reflita a versão bumpada na hora
      refreshDeck()
    },
  })
  const publishRelease = useMutation({
    mutationFn: () =>
      apiRequest(
        `/decks/${deckId}/publish-release`,
        {
          method: 'POST',
          body: JSON.stringify({
            description: releaseDescription.trim() || null,
          }),
        },
        token,
      ),
    onSuccess: () => {
      setReleaseDescription('')
      refreshDeck()
      queryClient.invalidateQueries({ queryKey: ['deck-releases', deckId] })
      queryClient.invalidateQueries({ queryKey: ['deck-sync', deckId] })
    },
  })

  if (deck.isLoading) return <LoadingState />
  if (deck.error) {
    return (
      <ErrorState
        message={deck.error.message}
        requestId={deck.error instanceof ApiError ? deck.error.requestId : null}
      />
    )
  }
  if (!deck.data) return null

  const canCurate = hasRole('admin', 'curator')
  const canPublish = hasRole('admin', 'reviewer')
  const releaseData = releases.data
  const operationError =
    addCard.error ||
    updateCard.error ||
    removeCard.error ||
    publishRelease.error ||
    downloadError

  async function exportRelease(releaseId: string) {
    setDownloadError(null)
    try {
      const { blob, filename } = await apiDownload(
        `/decks/${deckId}/releases/${releaseId}/export.csv`,
        token,
      )
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename
      anchor.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      setDownloadError(error as Error)
    }
  }

  return (
    <div className="deck-detail-page">
      <Link className="back-link" to="/decks">
        <ArrowLeft size={16} />
        Voltar para decks
      </Link>
      <header className="detail-header">
        <div>
          <div className="detail-kicker">
            <StatusBadge value={deck.data.status} />
            <code>{deck.data.deck_id}</code>
          </div>
          <h1>{deck.data.name}</h1>
          <p>{deck.data.description || 'Deck sem descrição.'}</p>
        </div>
        <strong className="deck-card-count">
          {deck.data.cards.length} cartões
        </strong>
      </header>

      {operationError && <InlineError error={operationError} />}

      {canPublish && (
        <section className="release-panel">
          <div>
            <p className="eyebrow">Snapshot imutável</p>
            <h2>Publicar nova release</h2>
            <p>
              A composição atual será registrada. Alterações posteriores exigem
              outra release.
            </p>
          </div>
          <div className="release-action">
            <input
              value={releaseDescription}
              onChange={(event) => setReleaseDescription(event.target.value)}
              placeholder="Descrição opcional da release"
              maxLength={5_000}
            />
            <button
              className="button button-primary"
              disabled={publishRelease.isPending || !deck.data.cards.length}
              onClick={() => publishRelease.mutate()}
            >
              <Rocket size={17} />
              Publicar release
            </button>
          </div>
        </section>
      )}

      <section className="deck-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Composição ativa</p>
            <h2>Cartões no deck</h2>
          </div>
        </div>
        {canCurate && (
          <form
            className="deck-add-card"
            onSubmit={(event) => {
              event.preventDefault()
              addCard.mutate()
            }}
          >
            <input
              value={cardReference}
              onChange={(event) => setCardReference(event.target.value)}
              placeholder="Adicionar por Public ID ou Card ID"
            />
            <button
              className="button button-primary"
              disabled={addCard.isPending || !cardReference.trim()}
            >
              <PackagePlus size={17} />
              Adicionar
            </button>
          </form>
        )}
        {deck.data.cards.length ? (
          <div className="table-card">
            <table>
              <thead>
                <tr>
                  <th>Public ID</th>
                  <th>Versão</th>
                  <th>Adicionado em</th>
                  {canCurate && <th>Ações</th>}
                </tr>
              </thead>
              <tbody>
                {deck.data.cards.map((card) => (
                  <tr key={card.card_id}>
                    <td>
                      <Link className="table-link" to={`/cards/${card.card_id}`}>
                        {card.public_id}
                      </Link>
                    </td>
                    <td>v{card.version_number}</td>
                    <td>{formatDate(card.added_at)}</td>
                    {canCurate && (
                      <td>
                        <div className="form-actions">
                          <button
                            className="button button-secondary"
                            disabled={updateCard.isPending}
                            title="Re-adiciona o card na versão publicada atual (depois publique uma release)"
                            onClick={() => updateCard.mutate(card.card_id)}
                          >
                            Atualizar versão
                          </button>
                          <button
                            className="danger-action"
                            disabled={removeCard.isPending}
                            onClick={() => {
                              if (window.confirm(`Remover ${card.public_id} do deck?`)) {
                                removeCard.mutate(card.card_id)
                              }
                            }}
                          >
                            <Trash2 size={15} />
                            Remover
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="Deck sem cartões"
            description="Adicione uma versão publicada para preparar a primeira release."
          />
        )}
      </section>

      <section className="deck-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Auditabilidade</p>
            <h2>Histórico de releases</h2>
          </div>
        </div>
        {releases.isLoading ? (
          <LoadingState />
        ) : releaseData?.items.length ? (
          <div className="table-card">
            <table>
              <thead>
                <tr>
                  <th>Release</th>
                  <th>Publicação</th>
                  <th>Descrição</th>
                  <th>Itens</th>
                  <th>Ações registradas</th>
                  <th>Exportação</th>
                </tr>
              </thead>
              <tbody>
                {releaseData.items.map((release) => (
                  <tr key={release.release_id}>
                    <td><strong>#{release.release_number}</strong></td>
                    <td>{formatDate(release.published_at)}</td>
                    <td>{release.description || 'Sem descrição'}</td>
                    <td>{release.item_count}</td>
                    <td>
                      <span className="release-counts">
                        +{release.actions.added} · ~{release.actions.updated} ·
                        -{release.actions.removed} · !{release.actions.deprecated}
                      </span>
                    </td>
                    <td>
                      <button
                        className="row-button"
                        onClick={() => exportRelease(release.release_id)}
                      >
                        <Download size={15} />
                        CSV
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <ReleasePagination
              data={releaseData}
              page={releasePage}
              onPageChange={setReleasePage}
            />
          </div>
        ) : (
          <EmptyState
            title="Nenhuma release publicada"
            description="O histórico aparecerá depois da primeira publicação."
          />
        )}
      </section>

      <section className="deck-section">
        <div className="section-heading sync-heading">
          <div>
            <p className="eyebrow">Sincronização incremental</p>
            <h2>Alterações desde uma release</h2>
          </div>
          <label className="since-release-field">
            <span>Desde a release</span>
            <input
              type="number"
              min={0}
              value={sinceRelease}
              onChange={(event) =>
                setSinceRelease(Math.max(0, Number(event.target.value)))
              }
            />
          </label>
        </div>
        {sync.isLoading ? (
          <LoadingState />
        ) : sync.error ? (
          <InlineError error={sync.error} />
        ) : sync.data?.has_changes ? (
          <div className="sync-list">
            {sync.data.changes.map((change, index) => (
              <article
                key={`${change.release_id}-${change.card_id}-${change.action}-${index}`}
              >
                <StatusBadge value={change.action} />
                <div>
                  <Link className="table-link" to={`/cards/${change.card_id}`}>
                    {change.public_id}
                  </Link>
                  <small>
                    Release #{change.release_number} ·{' '}
                    {formatDate(change.published_at)}
                  </small>
                </div>
                <code>
                  {change.old_card_version_id || '∅'} →{' '}
                  {change.new_card_version_id || '∅'}
                </code>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState
            title="Nenhuma alteração incremental"
            description={`O deck não possui mudanças depois da release ${sinceRelease}.`}
          />
        )}
      </section>
    </div>
  )
}

function ReleasePagination({
  data,
  page,
  onPageChange,
}: {
  data: ReleaseList
  page: number
  onPageChange: (page: number) => void
}) {
  const pages = Math.max(data.pages, 1)
  return (
    <footer className="table-summary">
      <span>
        Página {data.page} de {pages} · release mais recente #{data.latest_release}
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

function InlineError({ error }: { error: Error }) {
  return (
    <div className="form-alert inline-form-alert" role="alert">
      <strong>Não foi possível concluir a operação.</strong>
      <span>{error.message}</span>
      {error instanceof ApiError && error.requestId && (
        <small>ID da requisição: {error.requestId}</small>
      )}
    </div>
  )
}
