import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowRight,
  Book as BookOpen,
  Check,
  Clock as Clock3,
  Copy,
  Flag,
  Lightbulb,
  ChatText as MessageSquare,
  Plus,
  MagnifyingGlass as Search,
  ShareNetwork as Share2,
  ShieldCheck,
  Sparkle as Sparkles,
  ThumbsUp,
  X,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import {
  fallbackDecks,
  fallbackNotes,
  changeTypes,
  initialComments,
  type CommentKind,
  type StudentComment,
  type StudentSuggestion,
} from '../data/communityData'
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from '../components/ui'
import { useLocalStorageState } from '../hooks/useLocalStorageState'
import { formatDate } from '../lib/presentation'
import { StatusBadge } from '../components/ui'
import type {
  AnkiDeckSync,
  AnkiSyncChange,
  CardSummary,
  CardVersion,
  SubscribableDeck,
  SubscribableDeckList,
} from '../types'

type DeckFilter = 'all' | 'subscribed' | 'available'

function noteTitle(note: AnkiSyncChange) {
  return (
    note.fields?.Front ||
    note.fields?.Text ||
    note.fields?.front_text ||
    note.public_id
  )
}

function noteSummary(note: AnkiSyncChange) {
  return (
    note.fields?.Explanation ||
    note.fields?.Back ||
    note.fields?.Extra ||
    'Nota sincronizada pela plataforma.'
  )
}

function useDeckCatalog() {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['community-decks'],
    queryFn: async () => {
      const response = await apiRequest<SubscribableDeckList>(
        '/subscriptions/decks?page=1&page_size=100',
        {},
        token,
      )
      return response.items
    },
    retry: 1,
  })
}

function useDeckNotes(deckId: string, enabled = true) {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['community-deck-notes', deckId],
    enabled: Boolean(deckId) && enabled,
    queryFn: async () => {
      const response = await apiRequest<AnkiDeckSync>(
        `/addon/decks/${deckId}/sync?since_release=0&page=1&page_size=1000`,
        {},
        token,
      )
      return response.changes
    },
    retry: 1,
  })
}

export function ExplorePage() {
  const { hasRole } = useAuth()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<DeckFilter>('all')
  const decksQuery = useDeckCatalog()
  const decks = decksQuery.data?.length ? decksQuery.data : fallbackDecks
  const visibleDecks = decks.filter((deck) => {
    const matchesQuery = `${deck.name} ${deck.description || ''}`
      .toLowerCase()
      .includes(query.toLowerCase())
    const matchesFilter =
      filter === 'all' ||
      (filter === 'subscribed' && deck.subscribed) ||
      (filter === 'available' && !deck.subscribed)
    return matchesQuery && matchesFilter
  })

  return (
    <div className="ac-page">
      <header className="ac-hero ac-hero-row">
        <div>
          <span className="ac-eyebrow">Explore</span>
          <h1>Explore Baralhos</h1>
          <p>Encontre e inscreva-se nos melhores decks focados em concursos públicos.</p>
        </div>
        <SegmentedFilter value={filter} onChange={setFilter} />
      </header>

      <label className="ac-search">
        <Search size={18} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar baralhos..."
        />
      </label>

      <section className="ac-deck-grid">
        {visibleDecks.map((deck) => (
          <DeckCard key={deck.deck_id} deck={deck} />
        ))}
        {decksQuery.isLoading && <SkeletonDeckCard />}
      </section>

      {!visibleDecks.length && !decksQuery.isLoading && (
        <EmptyPanel
          title="Nenhum baralho encontrado"
          description="Ajuste a busca ou altere o filtro para ver outros baralhos."
        />
      )}

      {hasRole('admin', 'curator', 'reviewer') && (
        <section className="ac-admin-callout">
          <ShieldCheck size={22} />
          <div>
            <strong>Área administrativa disponível</strong>
            <span>Gerencie baralhos, sugestões e releases sem misturar o fluxo do estudante.</span>
          </div>
          <Link to="/admin">Abrir administração</Link>
        </section>
      )}
    </div>
  )
}

export function MyDecksPage() {
  const decksQuery = useDeckCatalog()
  const decks = (decksQuery.data?.length ? decksQuery.data : fallbackDecks).filter(
    (deck) => deck.subscribed,
  )

  return (
    <div className="ac-page">
      <header className="ac-hero">
        <span className="ac-eyebrow">Biblioteca</span>
        <h1>Meus Baralhos</h1>
        <p>Continue estudando os decks em que você está inscrito e prepare a sincronização no Anki.</p>
      </header>
      {decks.length ? (
        <section className="ac-deck-grid">
          {decks.map((deck) => (
            <DeckCard key={deck.deck_id} deck={deck} />
          ))}
        </section>
      ) : (
        <EmptyPanel
          title="Você ainda não está inscrito em baralhos"
          description="Explore os decks disponíveis e inscreva-se para sincronizar pelo add-on."
          action={<Link className="ac-button ac-button-primary" to="/">Explorar baralhos</Link>}
        />
      )}
      <section className="ac-sync-card">
        <BookOpen size={24} />
        <div>
          <strong>Sincronização com o Anki</strong>
          <p>O add-on usa suas inscrições para baixar manifestos, notas e releases incrementais.</p>
        </div>
      </section>
    </div>
  )
}

export function DeckPage() {
  const { deckId = '' } = useParams()
  const decksQuery = useDeckCatalog()
  const decks = decksQuery.data?.length ? decksQuery.data : fallbackDecks
  const deck = decks.find((item) => item.deck_id === deckId) || decks[0]
  const notesQuery = useDeckNotes(deck?.deck_id || deckId, Boolean(deck?.subscribed))
  const notes = notesQuery.data?.length ? notesQuery.data : fallbackNotes
  const [selectedNote, setSelectedNote] = useState<AnkiSyncChange | null>(null)
  const [query, setQuery] = useState('')
  const filteredNotes = notes.filter((note) =>
    `${note.public_id} ${noteTitle(note)} ${noteSummary(note)}`
      .toLowerCase()
      .includes(query.toLowerCase()),
  )

  if (!deck) {
    return (
      <EmptyPanel
        title="Baralho não encontrado"
        description="Volte para Explore e escolha um baralho disponível."
      />
    )
  }

  return (
    <div className="ac-page">
      <section className="ac-deck-hero">
        <div>
          <span className="ac-eyebrow">Baralho</span>
          <h1>{deck.name}</h1>
          <p>{deck.description || 'Deck publicado na plataforma Anki Concursos.'}</p>
          <div className="ac-meta-row">
            <span>{deck.active_card_count} notas</span>
            <span>Release {deck.latest_release}</span>
            <span>Atualizado {formatDate(deck.updated_at)}</span>
          </div>
        </div>
        <div className="ac-deck-actions">
          <SubscriptionButton deck={deck} />
          <button className="ac-button ac-button-secondary" type="button">
            <Share2 size={17} />
            Compartilhar
          </button>
          <Link className="ac-button ac-button-secondary" to={`/deck/${deck.deck_id}/suggestions`}>
            <MessageSquare size={17} />
            Sugestões
          </Link>
          <Link className="ac-button ac-button-ghost" to="/community">
            Abrir na Community
          </Link>
        </div>
      </section>

      <section className="ac-notes-section">
        <div className="ac-section-heading">
          <div>
            <span className="ac-eyebrow">Notas</span>
            <h2>Preview do baralho</h2>
          </div>
          <label className="ac-search">
            <Search size={18} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar notas..."
            />
          </label>
        </div>
        <div className="ac-note-list">
          {filteredNotes.map((note) => (
            <button
              key={note.card_id}
              className="ac-note-row"
              type="button"
              onClick={() => setSelectedNote(note)}
            >
              <span className="ac-note-kind">{note.card_kind || 'basic'}</span>
              <div>
                <strong>{noteTitle(note)}</strong>
                <p>{noteSummary(note)}</p>
              </div>
              <code>{note.public_id}</code>
              <ArrowRight size={18} />
            </button>
          ))}
        </div>
      </section>

      {selectedNote && (
        <NoteModal
          deckId={deck.deck_id}
          note={selectedNote}
          onClose={() => setSelectedNote(null)}
        />
      )}
    </div>
  )
}

function NoteModal({
  deckId,
  note,
  onClose,
}: {
  deckId: string
  note: AnkiSyncChange
  onClose: () => void
}) {
  const [mode, setMode] = useState<'view' | 'suggest' | 'comments'>('view')
  const [showComments, setShowComments] = useState(false)
  const fields = note.fields || {}

  return (
    <div className="ac-modal-backdrop" role="presentation">
      <section className="ac-note-modal" role="dialog" aria-modal="true">
        <header className="ac-modal-header">
          <div>
            <span className="ac-eyebrow">{note.card_kind || 'basic'}</span>
            <h2>{note.public_id}</h2>
          </div>
          <div className="ac-modal-actions">
            <button type="button" onClick={() => navigator.clipboard?.writeText(note.public_id)}>
              <Copy size={17} />
            </button>
            <button type="button" onClick={onClose} aria-label="Fechar">
              <X size={20} />
            </button>
          </div>
        </header>

        <nav className="ac-modal-tabs" aria-label="Nota">
          <button className={mode === 'view' ? 'active' : ''} onClick={() => setMode('view')}>
            Conteúdo
          </button>
          <button className={mode === 'suggest' ? 'active' : ''} onClick={() => setMode('suggest')}>
            Sugerir mudanças
          </button>
          <button className={mode === 'comments' ? 'active' : ''} onClick={() => setMode('comments')}>
            Comentários
          </button>
        </nav>

        {mode === 'view' && (
          <div className="ac-note-fields">
            {Object.entries(fields).map(([label, value]) => (
              <article key={label}>
                <span>{label}</span>
                <p>{value}</p>
              </article>
            ))}
            <div className="ac-note-comments-toggle">
              <button
                className="ac-button ac-button-secondary"
                type="button"
                aria-expanded={showComments}
                aria-controls="note-comments-panel"
                onClick={() => setShowComments((current) => !current)}
              >
                {showComments ? 'Ocultar comentários' : 'Mostrar comentários'}
              </button>
            </div>
            {showComments && (
              <div id="note-comments-panel" className="ac-note-comments-inline">
                <NoteCommentsPanel publicId={note.public_id} />
              </div>
            )}
            <footer className="ac-tag-row">
              {note.tags.map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </footer>
          </div>
        )}
        {mode === 'suggest' && <SuggestChangePanel deckId={deckId} note={note} />}
        {mode === 'comments' && <NoteCommentsPanel publicId={note.public_id} />}
      </section>
    </div>
  )
}

function SuggestChangePanel({
  deckId,
  note,
}: {
  deckId: string
  note: AnkiSyncChange
}) {
  const [suggestions, setSuggestions] = useLocalStorageState<StudentSuggestion[]>(
    'anki-concursos-suggestions',
    [],
  )
  const [changeType, setChangeType] = useState(changeTypes[0])
  const [message, setMessage] = useState('')
  const [fields, setFields] = useState<Record<string, string>>(note.fields || {})
  const [sent, setSent] = useState(false)

  function submitSuggestion() {
      const suggestion: StudentSuggestion = {
        id: crypto.randomUUID(),
        deckId,
        cardId: note.card_id,
        publicId: note.public_id,
        changeType,
        message,
      proposedFields: fields,
      status: 'pending',
      createdAt: new Date().toISOString(),
    }
    setSuggestions([suggestion, ...suggestions])
    setSent(true)
  }

  return (
    <div className="ac-suggestion-panel">
      <div className="ac-warning-box">
        <Flag size={18} />
        Sua sugestão será enviada para revisão. Ela não altera automaticamente a nota publicada.
      </div>
      <label className="ac-field">
        <span>Tipo de mudança</span>
        <select value={changeType} onChange={(event) => setChangeType(event.target.value)}>
          {changeTypes.map((type) => (
            <option key={type}>{type}</option>
          ))}
        </select>
      </label>
      <div className="ac-markdown-toolbar" aria-label="Barra de formatação">
        {['B', 'I', 'Lista', 'Citação', 'Código', 'Link', 'Preview'].map((item) => (
          <button key={item} type="button">{item}</button>
        ))}
      </div>
      <div className="ac-suggestion-fields">
        {Object.entries(fields).map(([label, value]) => (
          <label className="ac-field" key={label}>
            <span>{label}</span>
            <textarea
              value={value}
              onChange={(event) =>
                setFields((current) => ({ ...current, [label]: event.target.value }))
              }
            />
          </label>
        ))}
      </div>
      <label className="ac-field">
        <span>Comentário para o revisor</span>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Explique o motivo da sugestão."
        />
      </label>
      <button className="ac-button ac-button-primary" type="button" onClick={submitSuggestion}>
        Enviar sugestão
      </button>
      {sent && (
        <div className="ac-success-box">
          <Check size={18} />
          Sugestão enviada para revisão.
        </div>
      )}
    </div>
  )
}

function NoteCommentsPanel({ publicId }: { publicId: string }) {
  const [comments, setComments] = useLocalStorageState<StudentComment[]>(
    'anki-concursos-comments',
    initialComments,
  )
  const [body, setBody] = useState('')
  const noteComments = comments.filter((comment) => comment.publicId === publicId)

  function addComment() {
    if (!body.trim()) return
    setComments([
      {
        id: crypto.randomUUID(),
        publicId,
        author: 'Você',
        kind: 'comment',
        body,
        score: 0,
        createdAt: new Date().toISOString(),
      },
      ...comments,
    ])
    setBody('')
  }

  function handleUpvote(commentId: string) {
    setComments((prev) => prev.map((c) => (c.id === commentId ? { ...c, score: c.score + 1 } : c)))
  }

  const kindLabels: Record<CommentKind, string> = {
    comment: 'Comentário',
    tip: 'Dica',
    mnemonic: 'Mnemônico',
    question: 'Dúvida',
    correction: 'Correção',
  }

  return (
    <div className="ac-comments-panel">
      <div className="ac-new-comment">
        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder="Escreva um comentário sobre esta nota..."
        />
        <button className="ac-button ac-button-primary" type="button" onClick={addComment}>
          Publicar
        </button>
      </div>
      <div className="ac-comment-list">
        {noteComments
          .slice()
          .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
          .map((comment) => (
            <article key={comment.id}>
              <header>
                <strong>{comment.author}</strong>
                <span className="ac-comment-kind-badge">{kindLabels[comment.kind]}</span>
                <small>{formatDate(comment.createdAt)}</small>
              </header>
              <p>{comment.body}</p>
              <footer>
                <button type="button" onClick={() => handleUpvote(comment.id)}>
                  <ThumbsUp size={15} />
                  Útil ({comment.score})
                </button>
                <button type="button">Denunciar</button>
              </footer>
            </article>
          ))}
        {!noteComments.length && (
          <EmptyPanel
            title="Sem comentários ainda"
            description="Publique a primeira observação para iniciar o feed cronológico desta nota."
          />
        )}
      </div>
    </div>
  )
}

export function AdminDashboardPage() {
  const [suggestions] = useLocalStorageState<StudentSuggestion[]>(
    'anki-concursos-suggestions',
    [],
  )
  const pendingSuggestions = suggestions.filter((item) => item.status === 'pending')
  return (
    <div className="ac-page ac-admin-page">
      <header className="ac-hero">
        <span className="ac-eyebrow">Administração</span>
        <h1>Dashboard Administrativo</h1>
        <p>Funções de curadoria para aprovar, revisar e publicar baralhos.</p>
      </header>
      <section className="ac-admin-metrics">
        <MetricCard label="Baralhos publicados" value="12" />
        <MetricCard label="Sugestões pendentes" value={String(pendingSuggestions.length)} />
        <MetricCard label="Versões em revisão" value="25" />
        <MetricCard label="Releases pendentes" value="3" />
      </section>
      <section className="ac-admin-actions">
        <Link to="/admin/decks">Gerenciar baralhos</Link>
        <Link to="/admin/suggestions">Revisar sugestões</Link>
        <Link to="/reports">Reports formais</Link>
        <Link to="/users">Usuários</Link>
      </section>
    </div>
  )
}

export function AdminDecksPage() {
  const decksQuery = useDeckCatalog()
  const decks = decksQuery.data?.length ? decksQuery.data : fallbackDecks
  return (
    <div className="ac-page ac-admin-page">
      <header className="ac-hero ac-hero-row">
        <div>
          <span className="ac-eyebrow">Administração</span>
          <h1>Gerenciar Baralhos</h1>
          <p>Controle publicações, releases e composição editorial.</p>
        </div>
        <Link className="ac-button ac-button-primary" to="/decks/new">
          <Plus size={17} />
          Novo baralho
        </Link>
      </header>
      <div className="ac-admin-table">
        {decks.map((deck) => (
          <article key={deck.deck_id}>
            <div>
              <strong>{deck.name}</strong>
              <p>{deck.description || 'Sem descrição.'}</p>
            </div>
            <span>{deck.status}</span>
            <span>{deck.active_card_count} notas</span>
            <span>Release {deck.latest_release}</span>
            <Link to={`/deck/${deck.deck_id}`}>Abrir</Link>
          </article>
        ))}
      </div>
    </div>
  )
}

export function AdminSuggestionsPage() {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [suggestions, setSuggestions] = useLocalStorageState<StudentSuggestion[]>(
    'anki-concursos-suggestions',
    [],
  )
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  function updateSuggestionStatus(
    suggestionId: string,
    status: StudentSuggestion['status'],
    extra?: Partial<StudentSuggestion>,
  ) {
    setSuggestions((current) =>
      current.map((item) =>
        item.id === suggestionId ? { ...item, status, ...extra } : item,
      ),
    )
  }

  const convertSuggestion = useMutation({
    mutationFn: async (suggestion: StudentSuggestion) => {
      setError(null)
      setSuccess(null)

      if (!token) {
        updateSuggestionStatus(suggestion.id, 'converted_to_new_version')
        return { cardId: suggestion.cardId ?? null, versionId: null, deckId: suggestion.deckId }
      }

      const cardId = await resolveSuggestionCardId(suggestion, token)
      const payload = buildVersionPayload(suggestion)
      const created = await apiRequest<CardVersion>(
        `/cards/${cardId}/versions`,
        {
          method: 'POST',
          body: JSON.stringify(payload),
        },
        token,
      )

      await apiRequest(
        `/cards/${cardId}/versions/${created.card_version_id}/approve`,
        { method: 'POST' },
        token,
      )
      await apiRequest(
        `/cards/${cardId}/versions/${created.card_version_id}/publish`,
        { method: 'POST' },
        token,
      )

      await apiRequest(
        `/decks/${suggestion.deckId}/cards`,
        {
          method: 'POST',
          body: JSON.stringify({ card_id: cardId }),
        },
        token,
      )
      await apiRequest(
        `/decks/${suggestion.deckId}/publish-release`,
        {
          method: 'POST',
          body: JSON.stringify({
            description: `Sugestão aceita: ${suggestion.changeType}`,
          }),
        },
        token,
      )

      return { cardId, versionId: created.card_version_id, deckId: suggestion.deckId }
    },
    onSuccess: ({ cardId, versionId, deckId }, suggestion) => {
      updateSuggestionStatus(suggestion.id, 'converted_to_new_version', {
        resultingCardVersionId: versionId,
      })
      queryClient.invalidateQueries({ queryKey: ['cards'] })
      if (cardId) {
        queryClient.invalidateQueries({ queryKey: ['card', cardId] })
      }
      queryClient.invalidateQueries({ queryKey: ['decks'] })
      if (deckId) {
        queryClient.invalidateQueries({ queryKey: ['deck', deckId] })
      }
      setSuccess('Sugestão convertida e publicada.')
    },
    onError: (mutationError) => {
      setError(
        mutationError instanceof Error
          ? mutationError.message
          : 'Falha ao processar a sugestão.',
      )
    },
  })

  const rejectSuggestion = useMutation({
    mutationFn: async (suggestion: StudentSuggestion) => {
      setError(null)
      setSuccess(null)
      updateSuggestionStatus(suggestion.id, 'rejected')
      return suggestion.id
    },
    onSuccess: () => {
      setSuccess('Sugestão rejeitada.')
    },
    onError: (mutationError) => {
      setError(
        mutationError instanceof Error
          ? mutationError.message
          : 'Falha ao rejeitar a sugestão.',
      )
    },
  })

  return (
    <div className="ac-page ac-admin-page">
      <header className="ac-hero">
        <span className="ac-eyebrow">Curadoria</span>
        <h1>Sugestões dos Estudantes</h1>
        <p>Revise propostas enviadas a partir das notas sem editar conteúdo publicado diretamente.</p>
      </header>
      {error && <div className="ac-warning-box">{error}</div>}
      {success && <div className="ac-success-box">{success}</div>}
      <div className="ac-suggestion-list">
        {suggestions.map((suggestion) => (
          <article key={suggestion.id}>
            <header>
              <strong>{suggestion.publicId}</strong>
              <span>{suggestion.changeType}</span>
              <StatusBadge value={suggestion.status} />
              {suggestion.resultingCardVersionId && (
                <span>v {suggestion.resultingCardVersionId.slice(0, 8)}</span>
              )}
            </header>
            <p>{suggestion.message || 'Sem comentário adicional.'}</p>
            <footer>
              <small>{formatDate(suggestion.createdAt)}</small>
              <button
                type="button"
                disabled={suggestion.status !== 'pending'}
                onClick={() => convertSuggestion.mutate(suggestion)}
              >
                Converter em nova versão
              </button>
              <button
                type="button"
                disabled={suggestion.status !== 'pending'}
                onClick={() => rejectSuggestion.mutate(suggestion)}
              >
                Rejeitar
              </button>
            </footer>
          </article>
        ))}
        {!suggestions.length && (
          <EmptyPanel
            title="Nenhuma sugestão pendente"
            description="As sugestões criadas no modal da nota aparecerão aqui."
          />
        )}
      </div>
    </div>
  )
}

export function CommunityFuturePage() {
  return (
    <div className="ac-page">
      <section className="ac-community-hero">
        <span className="ac-eyebrow">Community futura</span>
        <h1>Comunidade Anki Concursos</h1>
        <p>
          Espaço planejado para comentários, dicas, mnemônicos e sugestões públicas por
          baralho e por nota.
        </p>
      </section>
      <section className="ac-community-grid">
        <article>
          <MessageSquare size={24} />
          <strong>Discussões por nota</strong>
          <p>Comentários colaborativos conectados ao public_id da nota.</p>
        </article>
        <article>
          <Lightbulb size={24} />
          <strong>Dicas e mnemônicos</strong>
          <p>Conteúdo social separado do cartão oficial e moderado pela plataforma.</p>
        </article>
        <article>
          <Sparkles size={24} />
          <strong>Sugestões para curadoria</strong>
          <p>Correções relevantes podem virar reports e novas versões.</p>
        </article>
      </section>
    </div>
  )
}

type DeckSuggestionHistory = {
  id: string
  noteId: string
  publicId: string
  userName: string
  originalField: string
  suggestedField: string
  createdAt: string
  discussion: Array<{
    id: string
    author: string
    body: string
    createdAt: string
  }>
}

const suggestionHistorySeed: DeckSuggestionHistory[] = [
  {
    id: 'suggestion-history-1',
    noteId: 'note-1',
    publicId: 'AC-CONST-0001',
    userName: 'Camila Ribeiro',
    originalField: 'Habeas corpus protege a liberdade de locomoção.',
    suggestedField:
      'Habeas corpus protege a liberdade de locomoção contra coação ilegal.',
    createdAt: '2026-06-16T10:15:00Z',
    discussion: [
      {
        id: 'comment-1',
        author: 'Equipe editorial',
        body: 'Boa precisão. Mantém o sentido sem confundir o enunciado original da nota.',
        createdAt: '2026-06-16T11:02:00Z',
      },
      {
        id: 'comment-2',
        author: 'Mariana S.',
        body: 'A formulação ficou mais fiel ao texto legal e continua legível no preview.',
        createdAt: '2026-06-16T11:26:00Z',
      },
    ],
  },
  {
    id: 'suggestion-history-2',
    noteId: 'note-2',
    publicId: 'AC-CONST-0002',
    userName: 'Paulo Nogueira',
    originalField: 'A Constituição admite habeas corpus.',
    suggestedField: 'A Constituição admite habeas corpus para proteger a locomoção.',
    createdAt: '2026-06-15T16:40:00Z',
    discussion: [
      {
        id: 'comment-3',
        author: 'Revisor',
        body: 'A sugestão está correta, mas não deve substituir o campo original sem contexto adicional.',
        createdAt: '2026-06-15T17:05:00Z',
      },
    ],
  },
]

export function CommunitySuggestionHistoryPage() {
  const { deckId = '' } = useParams()
  const decksQuery = useDeckCatalog()
  const decks = decksQuery.data?.length ? decksQuery.data : fallbackDecks
  const deck = decks.find((item) => item.deck_id === deckId)
  const [selectedSuggestionId, setSelectedSuggestionId] = useState(
    suggestionHistorySeed[0]?.id || '',
  )
  const [draftComment, setDraftComment] = useState('')
  const [history, setHistory] = useLocalStorageState<DeckSuggestionHistory[]>(
    `anki-concursos-suggestion-history-${deckId}`,
    suggestionHistorySeed,
  )

  const visibleHistory = history.filter((item) => !deck || item.publicId.startsWith('AC'))
  const selectedSuggestion =
    visibleHistory.find((item) => item.id === selectedSuggestionId) || visibleHistory[0] || null

  function addComment() {
    if (!selectedSuggestion || !draftComment.trim()) return
    const next = history.map((item) => {
      if (item.id !== selectedSuggestion.id) return item
      return {
        ...item,
        discussion: [
          ...item.discussion,
          {
            id: crypto.randomUUID(),
            author: 'Você',
            body: draftComment.trim(),
            createdAt: new Date().toISOString(),
          },
        ],
      }
    })
    setHistory(next)
    setDraftComment('')
  }

  if (decksQuery.isLoading) return <LoadingState />
  if (decksQuery.error) {
    return (
      <ErrorState
        message={decksQuery.error.message}
        requestId={decksQuery.error instanceof ApiError ? decksQuery.error.requestId : null}
      />
    )
  }

  if (!deck) {
    return (
      <EmptyState
        title="Deck não encontrado"
        description="Volte para a lista de decks e abra novamente a área de sugestões."
      />
    )
  }

  return (
    <div className="ac-page ac-suggestion-history-page">
      <header className="ac-suggestion-history-hero">
        <div>
          <span className="ac-eyebrow">Comunidade do deck</span>
          <h1>Histórico de mudanças e discussão</h1>
          <p>
            {deck.name} · acompanhe a nota original, a proposta do usuário, o ID da nota e a conversa editorial
            sem perder o contexto da sugestão.
          </p>
        </div>
        <Link className="ac-button ac-button-secondary" to={`/deck/${deck.deck_id}`}>
          <ArrowRight size={17} />
          Voltar ao deck
        </Link>
      </header>

      {!visibleHistory.length ? (
        <EmptyState
          title="Nenhuma sugestão registrada"
          description="As mudanças da comunidade aparecerão aqui assim que forem criadas."
        />
      ) : (
        <section className="ac-suggestion-history-layout">
          <aside className="ac-suggestion-history-list" aria-label="Histórico de sugestões">
            {visibleHistory.map((item) => {
              const active = item.id === selectedSuggestion?.id
              return (
                <button
                  key={item.id}
                  type="button"
                  className={active ? 'active' : ''}
                  onClick={() => setSelectedSuggestionId(item.id)}
                >
                  <span>Nota {item.noteId}</span>
                  <strong>{item.publicId}</strong>
                  <small>Por {item.userName}</small>
                </button>
              )
            })}
          </aside>

          {selectedSuggestion && (
            <main className="ac-suggestion-history-detail">
              <section className="ac-suggestion-history-card">
                <div className="ac-suggestion-history-card-header">
                  <div>
                    <span className="ac-eyebrow">Sugestão selecionada</span>
                    <h2>{selectedSuggestion.publicId}</h2>
                  </div>
                  <StatusBadge value="published" />
                </div>
                <dl className="ac-suggestion-metadata">
                  <div>
                    <dt>ID da nota</dt>
                    <dd>{selectedSuggestion.noteId}</dd>
                  </div>
                  <div>
                    <dt>Usuário</dt>
                    <dd>{selectedSuggestion.userName}</dd>
                  </div>
                  <div>
                    <dt>Criada em</dt>
                    <dd>{formatDate(selectedSuggestion.createdAt)}</dd>
                  </div>
                </dl>
                <div className="ac-suggestion-comparison">
                  <article>
                    <span>Campo original</span>
                    <p>{selectedSuggestion.originalField}</p>
                  </article>
                  <article>
                    <span>Novo campo sugerido</span>
                    <p>{selectedSuggestion.suggestedField}</p>
                  </article>
                </div>
              </section>

              <section className="ac-discussion-panel">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Discussão</p>
                    <h2>Conversa editorial</h2>
                  </div>
                </div>
                <div className="ac-discussion-list">
                  {selectedSuggestion.discussion.map((comment) => (
                    <article key={comment.id}>
                      <header>
                        <strong>{comment.author}</strong>
                        <small>{formatDate(comment.createdAt)}</small>
                      </header>
                      <p>{comment.body}</p>
                    </article>
                  ))}
                </div>
                <label className="ac-discussion-form">
                  <span>Adicionar comentário</span>
                  <textarea
                    rows={4}
                    value={draftComment}
                    onChange={(event) => setDraftComment(event.target.value)}
                    placeholder="Registre uma observação sobre esta sugestão."
                  />
                </label>
                <button className="ac-button ac-button-primary" type="button" onClick={addComment}>
                  <MessageSquare size={17} />
                  Publicar comentário
                </button>
              </section>
            </main>
          )}
        </section>
      )}
    </div>
  )
}

async function resolveSuggestionCardId(
  suggestion: StudentSuggestion,
  token: string,
) {
  if (suggestion.cardId) return suggestion.cardId
  const card = await apiRequest<CardSummary>(
    `/cards/public/${encodeURIComponent(suggestion.publicId)}`,
    {},
    token,
  )
  return card.card_id
}

function buildVersionPayload(suggestion: StudentSuggestion) {
  const fields = suggestion.proposedFields
  const front_text =
    fields.Front || fields.Text || fields.front_text || fields.question || ''
  const back_text =
    fields.Back || fields.Extra || fields.back_text || fields.extra || fields.answer || ''
  const answer_text =
    fields.Answer || fields.answer_text || back_text || front_text
  const explanation_text =
    fields.Explanation || fields.explanation_text || fields.Extra || back_text
  const change_reason = suggestion.message.trim()
    ? `${suggestion.changeType}: ${suggestion.message.trim()}`
    : suggestion.changeType

  if (!front_text || !back_text || !answer_text || !explanation_text) {
    throw new Error(
      'A sugestão não contém campos suficientes para criar uma nova versão.',
    )
  }

  return {
    front_text,
    back_text,
    answer_text,
    explanation_text,
    change_reason,
  }
}

function DeckCard({ deck }: { deck: SubscribableDeck }) {
  return (
    <article className={`ac-deck-card ${deck.subscribed ? 'ac-deck-card-active' : ''}`}>
      <div className="ac-deck-card-header">
        <BookOpen size={24} />
        <h2>{deck.name}</h2>
        {deck.subscribed && <span>Inscrito</span>}
      </div>
      <p>{deck.description || 'Baralho publicado na plataforma.'}</p>
      <div className="ac-deck-meta">
        <span>{deck.active_card_count} notas</span>
        <span>Última atualização: {formatDate(deck.updated_at)}</span>
      </div>
      {deck.subscribed ? (
        <Link className="ac-button ac-button-primary" to={`/deck/${deck.deck_id}`}>
          Abrir baralho
          <ArrowRight size={18} />
        </Link>
      ) : (
        <SubscriptionButton deck={deck} />
      )}
    </article>
  )
}

function SubscriptionButton({ deck }: { deck: SubscribableDeck }) {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const subscribeMutation = useMutation({
    mutationFn: () => apiRequest(`/subscriptions/${deck.deck_id}`, { method: 'POST' }, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['community-decks'] })
      queryClient.invalidateQueries({ queryKey: ['deck-subscriptions'] })
      navigate(`/deck/${deck.deck_id}`)
    },
  })

  const unsubscribeMutation = useMutation({
    mutationFn: () => apiRequest(`/subscriptions/${deck.deck_id}`, { method: 'DELETE' }, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['community-decks'] })
      queryClient.invalidateQueries({ queryKey: ['deck-subscriptions'] })
    },
  })

  if (deck.subscribed) {
    return (
      <button
        className="ac-button ac-button-secondary"
        type="button"
        disabled={unsubscribeMutation.isPending}
        onClick={() => unsubscribeMutation.mutate()}
      >
        <Check size={18} className="text-secondary" />
        Desinscrever
      </button>
    )
  }

  return (
    <button
      className="ac-button ac-button-primary"
      type="button"
      disabled={subscribeMutation.isPending}
      onClick={() => subscribeMutation.mutate()}
    >
      <Plus size={18} />
      Inscrever-se
    </button>
  )
}

function SegmentedFilter({
  value,
  onChange,
}: {
  value: DeckFilter
  onChange: (value: DeckFilter) => void
}) {
  return (
    <div className="ac-segmented">
      {[
        ['all', 'Todos'],
        ['subscribed', 'Inscritos'],
        ['available', 'Disponíveis'],
      ].map(([key, label]) => (
        <button
          key={key}
          className={value === key ? 'active' : ''}
          type="button"
          onClick={() => onChange(key as DeckFilter)}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>
        <Clock3 size={14} />
        Atualizado agora
      </small>
    </article>
  )
}

function SkeletonDeckCard() {
  return (
    <article className="ac-deck-card ac-skeleton-card" aria-label="Carregando baralho">
      <i />
      <b />
      <b />
      <b />
      <strong />
    </article>
  )
}

function EmptyPanel({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: React.ReactNode
}) {
  return (
    <section className="ac-empty-panel">
      <strong>{title}</strong>
      <p>{description}</p>
      {action}
    </section>
  )
}
