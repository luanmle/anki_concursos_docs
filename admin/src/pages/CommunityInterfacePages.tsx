import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  ArrowRight,
  Book as BookOpen,
  Check,
  Clock as Clock3,
  Copy,
  Info,
  Lightbulb,
  ArrowCounterClockwise,
  ArrowClockwise,
  TextAlignLeft,
  TextAlignCenter,
  TextAlignRight,
  TextAlignJustify,
  ChatText as MessageSquare,
  Plus,
  MagnifyingGlass as Search,
  ShareNetwork as Share2,
  SlidersHorizontal,
  Stack,
  Sparkle as Sparkles,
  LinkSimple,
  ListBullets,
  ListNumbers,
  TextB,
  TextH,
  TextT,
  TextItalic,
  TextUnderline,
  DotsThreeVertical,
  X,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import { changeTypes } from '../data/communityData'
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from '../components/ui-primitives'
import { ExploreHero } from '../components/ExploreHero'
import { HtmlFieldEditor, HtmlFieldView } from '../components/HtmlField'
import { htmlToText } from '../lib/html'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { Dialog, DialogContent, DialogTitle } from '../components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { ToggleGroup, ToggleGroupItem } from '../components/ui/toggle-group'
import {
  CATEGORY,
  MuriaeDeckCard,
  deckCategory,
  formatDeckDate,
} from '../components/MuriaeDeckCard'
import { cn } from '../lib/utils'
import { formatDate } from '../lib/presentation'
import type {
  AnkiDeckSync,
  AnkiSyncChange,
  NoteCommentList,
  NoteSuggestion,
  NoteSuggestionList,
  NoteSuggestionStatus,
  SubscribableDeck,
  SubscribableDeckList,
} from '../types'
import { SuggestionList } from '../components/suggestions/SuggestionList'
import { DiffViewer } from '../components/suggestions/DiffViewer'
import { SuggestionDiscussion } from '../components/suggestions/SuggestionDiscussion'
import {
  SUGGESTION_STATUS_LABEL,
  SUGGESTION_TYPE_LABEL,
} from '../components/suggestions/labels'
import {
  buildChangedFields,
  mapChangeType,
} from '../components/suggestions/payload'

type DeckFilter = 'all' | 'subscribed' | 'available'

function noteTitle(note: AnkiSyncChange) {
  return htmlToText(
    note.fields?.Front ||
      note.fields?.Text ||
      note.fields?.front_text ||
      note.public_id,
  )
}

function noteSummary(note: AnkiSyncChange) {
  return htmlToText(
    note.fields?.Explanation ||
      note.fields?.Back ||
      note.fields?.Extra ||
      'Nota sincronizada pela plataforma.',
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

type DeckSort = 'recent' | 'notes' | 'alpha'

const SORT_LABELS: Record<DeckSort, string> = {
  recent: 'Mais recentes',
  notes: 'Mais notas',
  alpha: 'A–Z',
}

export function ExplorePage() {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<DeckFilter>('all')
  const [sort, setSort] = useState<DeckSort>('recent')
  const decksQuery = useDeckCatalog()
  const decks = decksQuery.data ?? []
  const visibleDecks = decks
    .filter((deck) => {
      const matchesQuery = `${deck.name} ${deck.description || ''}`
        .toLowerCase()
        .includes(query.toLowerCase())
      const matchesFilter =
        filter === 'all' ||
        (filter === 'subscribed' && deck.subscribed) ||
        (filter === 'available' && !deck.subscribed)
      return matchesQuery && matchesFilter
    })
    .sort((left, right) => {
      if (sort === 'notes') return right.active_card_count - left.active_card_count
      if (sort === 'alpha') return left.name.localeCompare(right.name, 'pt-BR')
      return right.updated_at.localeCompare(left.updated_at)
    })

  return (
    <div className="ac-page ac-page-muriae">
      <ExploreHero
        eyebrow="Explore"
        title="Explore baralhos"
        description="Encontre e inscreva-se nos melhores baralhos focados em concursos públicos, construídos e revisados em comunidade."
      />

      <div className="mt-7 flex items-stretch gap-3 max-[720px]:flex-wrap">
        <div className="relative min-w-0 flex-1 max-[720px]:basis-full">
          <Search
            size={18}
            className="pointer-events-none absolute left-[14px] top-1/2 -translate-y-1/2 text-mu-muted-2"
          />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Buscar baralhos..."
            className="h-[42px] rounded-[6px] border-mu-border bg-mu-surface pl-[40px] text-[14px] text-mu-text placeholder:text-mu-muted-2 focus-visible:ring-[#231651]/30"
          />
        </div>

        <SegmentedFilter value={filter} onChange={setFilter} />

        <DropdownMenu>
          <DropdownMenuTrigger className="inline-flex h-[42px] items-center gap-2 whitespace-nowrap rounded-[6px] border border-mu-border bg-mu-surface px-4 text-[13.5px] font-semibold text-mu-text outline-none transition-colors hover:border-mu-border-hover hover:bg-mu-surface-2">
            <SlidersHorizontal size={16} className="text-mu-muted" />
            {SORT_LABELS[sort]}
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuRadioGroup
              value={sort}
              onValueChange={(value) => setSort(value as DeckSort)}
            >
              <DropdownMenuRadioItem value="recent">Mais recentes</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="notes">Mais notas</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="alpha">A–Z</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {!decksQuery.isLoading && (
        <p className="mt-[18px] mb-4 text-[13px] font-medium text-mu-muted">
          {visibleDecks.length} {visibleDecks.length === 1 ? 'baralho' : 'baralhos'}
        </p>
      )}

      <section className="grid grid-cols-1 gap-5 min-[721px]:grid-cols-2 min-[1081px]:grid-cols-3">
        {visibleDecks.map((deck) => (
          <MuriaeDeckCard key={deck.deck_id} deck={deck} />
        ))}
        {decksQuery.isLoading && <SkeletonDeckCard />}
      </section>

      {!visibleDecks.length && !decksQuery.isLoading && (
        <EmptyPanel
          title="Nenhum baralho encontrado"
          description="Ajuste a busca ou altere o filtro para ver outros baralhos."
        />
      )}

    </div>
  )
}

export function MyDecksPage() {
  const decksQuery = useDeckCatalog()
  const decks = (decksQuery.data ?? []).filter(
    (deck) => deck.subscribed,
  )

  return (
    <div className="ac-page ac-page-muriae">
      <ExploreHero
        eyebrow="Biblioteca"
        title="Meus baralhos"
        description="Continue estudando os baralhos em que você está inscrito e prepare a sincronização no Anki."
      />

      {decks.length ? (
        <section className="mt-8 grid grid-cols-1 gap-5 min-[721px]:grid-cols-2 min-[1081px]:grid-cols-3">
          {decks.map((deck) => (
            <MuriaeDeckCard key={deck.deck_id} deck={deck} />
          ))}
        </section>
      ) : (
        <section className="mt-8 flex flex-col items-start gap-3 rounded-[10px] border border-dashed border-mu-border bg-mu-surface p-8">
          <strong className="text-[16px] font-semibold text-mu-text">
            Você ainda não está inscrito em baralhos
          </strong>
          <p className="max-w-[420px] text-[14px] leading-[1.55] text-mu-muted">
            Explore os baralhos disponíveis e inscreva-se para sincronizar pelo add-on.
          </p>
          <Button
            asChild
            className="mt-1 h-[42px] gap-2 rounded-[6px] bg-[#231651] px-4 text-[13.5px] font-semibold text-white hover:bg-[#1a1040]"
          >
            <Link to="/">Explorar baralhos</Link>
          </Button>
        </section>
      )}

      <section className="mt-6 flex items-start gap-3.5 rounded-[10px] border border-mu-border bg-mu-surface p-5">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[8px] bg-mu-brand-bg text-mu-brand">
          <BookOpen size={20} />
        </span>
        <div>
          <strong className="block text-[15px] font-semibold text-mu-text">
            Sincronização com o Anki
          </strong>
          <p className="mt-1 text-[13.5px] leading-[1.55] text-mu-muted">
            O add-on usa suas inscrições para baixar manifestos, notas e releases incrementais.
          </p>
        </div>
      </section>
    </div>
  )
}

export function DeckPage() {
  const { deckId = '' } = useParams()
  const decksQuery = useDeckCatalog()
  const decks = decksQuery.data ?? []
  const deck = decks.find((item) => item.deck_id === deckId)
  const notesQuery = useDeckNotes(deck?.deck_id || deckId, Boolean(deck?.subscribed))
  const notes = notesQuery.data ?? []
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState('')

  // URL is the source of truth for the open note (deep-linkable / shareable).
  const noteParam = searchParams.get('note')
  const selectedNote = noteParam
    ? (notes.find((note) => note.public_id === noteParam) ?? null)
    : null

  const setNoteParam = (publicId: string | null) =>
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (publicId) next.set('note', publicId)
        else next.delete('note')
        return next
      },
      { replace: true },
    )

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

  const category = deckCategory(deck)
  const secondaryButton =
    'h-[42px] gap-2 rounded-[6px] border-mu-border bg-mu-surface px-4 text-[13.5px] font-semibold text-mu-text hover:border-mu-border-hover hover:bg-mu-surface-2'

  return (
    <div className="ac-page ac-page-muriae">
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-mu-muted transition-colors hover:text-mu-text"
      >
        <ArrowLeft size={16} />
        Voltar ao Explore
      </Link>

      <section className="mt-5 flex flex-col gap-6 border-b border-mu-border pb-8 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <span className="text-[11px] font-bold uppercase tracking-[0.14em] text-mu-brand">
            Baralho
          </span>
          <h1 className="mt-2 font-dm-serif text-[34px] font-normal leading-[1.1] tracking-[-0.01em] text-mu-text">
            {deck.name}
          </h1>
          <p className="mt-3 max-w-[640px] text-[15px] leading-[1.6] text-mu-muted">
            {deck.description || 'Deck publicado na plataforma Anki Concursos.'}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-[13px] text-mu-muted">
            <Badge
              className={cn(
                'rounded-[5px] border px-2 py-0.5 text-[11px] font-bold uppercase tracking-[0.06em]',
                CATEGORY[category].badge,
              )}
            >
              {CATEGORY[category].label}
            </Badge>
            <span className="inline-flex items-center gap-1.5">
              <Stack size={14} className="text-mu-muted-2" />
              {deck.active_card_count.toLocaleString('pt-BR')} notas
            </span>
            <span className="inline-flex items-center gap-1.5">
              <ArrowClockwise size={14} className="text-mu-muted-2" />
              Versão {deck.latest_release}
            </span>
            <span>Atualizado {formatDeckDate(deck.updated_at)}</span>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2.5">
          <SubscriptionButton deck={deck} />
          <Button variant="outline" className={secondaryButton}>
            <Share2 size={16} />
            Compartilhar
          </Button>
          <Button asChild variant="outline" className={secondaryButton}>
            <Link to={`/deck/${deck.deck_id}/suggestions`}>
              <MessageSquare size={16} />
              Sugestões
            </Link>
          </Button>
          <Button
            asChild
            variant="ghost"
            className="h-[42px] px-3 text-[13.5px] font-semibold text-mu-muted hover:bg-transparent hover:text-mu-brand"
          >
            <Link to="/community">Ver na Comunidade</Link>
          </Button>
        </div>
      </section>

      <section className="mt-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-[0.14em] text-mu-brand">
              Notas
            </span>
            <h2 className="mt-1.5 font-dm-serif text-[22px] font-normal text-mu-text">
              Preview do baralho
            </h2>
          </div>
          <div className="relative w-full sm:w-[280px]">
            <Search
              size={18}
              className="pointer-events-none absolute left-[14px] top-1/2 -translate-y-1/2 text-mu-muted-2"
            />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar notas..."
              className="h-[42px] rounded-[6px] border-mu-border bg-mu-surface pl-[40px] text-[14px] text-mu-text placeholder:text-mu-muted-2 focus-visible:ring-[#231651]/30"
            />
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-2.5">
          {filteredNotes.map((note) => (
            <NoteRow key={note.card_id} note={note} onOpen={() => setNoteParam(note.public_id)} />
          ))}
          {!filteredNotes.length && (
            <EmptyPanel
              title="Nenhuma nota encontrada"
              description="Ajuste a busca para localizar notas deste baralho."
            />
          )}
        </div>
      </section>

      {selectedNote && (
        <NoteModal
          deck={deck}
          note={selectedNote}
          onClose={() => setNoteParam(null)}
        />
      )}
    </div>
  )
}

function NoteRow({ note, onOpen }: { note: AnkiSyncChange; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="group flex items-center gap-4 rounded-[8px] border border-mu-border bg-mu-surface px-4 py-3.5 text-left shadow-[0_1px_2px_-1px_rgba(31,36,48,0.05),0_2px_6px_-2px_rgba(31,36,48,0.06)] transition-[border-color,box-shadow,transform] duration-200 ease-out hover:-translate-y-[2px] hover:border-mu-border-hover hover:shadow-[0_5px_10px_-3px_rgba(31,36,48,0.10),0_14px_26px_-8px_rgba(35,22,81,0.16)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#231651]"
    >
      <Badge className="shrink-0 rounded-[5px] border-mu-border bg-mu-surface-2 px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em] text-mu-muted">
        {note.card_kind || 'basic'}
      </Badge>
      <div className="min-w-0 flex-1">
        <strong className="block truncate text-[14px] font-semibold text-mu-text">
          {noteTitle(note)}
        </strong>
        <p className="mt-0.5 truncate text-[13px] text-mu-muted">{noteSummary(note)}</p>
      </div>
      {/* "Validado" é apresentação: notas de baralho publicado são tidas como validadas. */}
      <Badge className="hidden shrink-0 items-center gap-1 rounded-[5px] border-mu-validated-border bg-mu-validated-bg px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-mu-validated sm:inline-flex">
        <Check size={11} weight="bold" />
        Validado
      </Badge>
      <code className="hidden shrink-0 font-mono text-[12px] text-mu-muted-2 md:block">
        {note.public_id}
      </code>
      <ArrowRight
        size={18}
        className="shrink-0 text-mu-muted-2 transition-colors group-hover:text-mu-brand"
      />
    </button>
  )
}

const modalTab =
  'h-11 flex-none rounded-none border-0 border-b-2 border-b-transparent bg-transparent px-0 text-[14px] font-semibold text-mu-muted shadow-none transition-colors hover:text-mu-text focus-visible:outline-none focus-visible:ring-0 data-[state=active]:border-b-mu-brand data-[state=active]:text-mu-text'

const muriaePrimaryBtn =
  'inline-flex h-[42px] items-center gap-2 rounded-[6px] bg-[#231651] px-4 text-[13.5px] font-semibold !text-white transition-colors hover:bg-[#1a1040]'
const muriaeSecondaryBtn =
  'inline-flex h-[42px] items-center gap-2 rounded-[6px] border border-mu-border bg-mu-surface px-4 text-[13.5px] font-semibold text-mu-text transition-colors hover:border-mu-border-hover hover:bg-mu-surface-2'
const muriaeSurface =
  'rounded-[10px] border border-mu-border bg-mu-surface shadow-[0_1px_2px_-1px_rgba(31,36,48,0.05),0_2px_6px_-2px_rgba(31,36,48,0.05)]'
const muriaeEyebrow =
  'text-[11px] font-bold uppercase tracking-[0.14em] text-mu-brand'

function NoteModal({
  deck,
  note,
  onClose,
}: {
  deck: SubscribableDeck
  note: AnkiSyncChange
  onClose: () => void
}) {
  const [showComments, setShowComments] = useState(false)
  const { token } = useAuth()
  const commentsQuery = useQuery({
    queryKey: ['note-comments', note.card_id],
    queryFn: () =>
      apiRequest<NoteCommentList>(
        `/cards/${note.card_id}/note-comments`,
        {},
        token,
      ),
  })
  const commentCount = commentsQuery.data?.total ?? 0
  const fields = note.fields || {}
  const category = CATEGORY[deckCategory(deck)]

  return (
    <Dialog open onOpenChange={(next) => !next && onClose()}>
      <DialogContent
        showCloseButton={false}
        className={cn(
          'grid-cols-[minmax(0,1fr)] gap-0 overflow-hidden rounded-[14px] border-mu-border bg-mu-surface p-0 text-mu-text sm:max-w-[720px]',
          showComments && 'sm:max-w-[1160px]',
        )}
      >
        <DialogTitle className="sr-only">{note.public_id}</DialogTitle>

        <div className="flex items-start justify-between gap-4 px-6 pt-5">
          <div className="min-w-0">
            <span className="text-[11px] font-bold uppercase tracking-[0.1em] text-mu-muted">
              {note.card_kind || 'basic'}
            </span>
            <h2 className="mt-0.5 truncate font-mono text-[20px] font-semibold text-mu-text">
              {note.public_id}
            </h2>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Badge
              className={cn(
                'rounded-[5px] border px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.06em]',
                category.badge,
              )}
            >
              {category.label}
            </Badge>
            <Badge className="inline-flex items-center gap-1 rounded-[5px] border-mu-validated-border bg-mu-validated-bg px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-mu-validated">
              <Check size={10} weight="bold" />
              Validado
            </Badge>
            {note.card_id && (
              <Link
                to={`/cards/${note.card_id}`}
                aria-label="Ver histórico de versões"
                title="Ver histórico de versões"
                className="flex h-8 w-8 items-center justify-center rounded-[6px] text-mu-muted transition-colors hover:bg-mu-surface-2 hover:text-mu-text"
              >
                <Clock3 size={16} />
              </Link>
            )}
            <button
              type="button"
              onClick={() => navigator.clipboard?.writeText(window.location.href)}
              aria-label="Copiar link da nota"
              title="Copiar link da nota"
              className="flex h-8 w-8 items-center justify-center rounded-[6px] text-mu-muted transition-colors hover:bg-mu-surface-2 hover:text-mu-text"
            >
              <LinkSimple size={16} />
            </button>
            <button
              type="button"
              onClick={() => navigator.clipboard?.writeText(note.public_id)}
              aria-label="Copiar identificador"
              className="flex h-8 w-8 items-center justify-center rounded-[6px] text-mu-muted transition-colors hover:bg-mu-surface-2 hover:text-mu-text"
            >
              <Copy size={16} />
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label="Fechar"
              className="flex h-8 w-8 items-center justify-center rounded-[6px] text-mu-muted transition-colors hover:bg-mu-surface-2 hover:text-mu-text"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        <Tabs defaultValue="content" className="mt-3 gap-0">
          <div className="flex flex-col gap-2 border-b border-mu-border px-6 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
            <TabsList variant="line" className="h-auto gap-6 rounded-none bg-transparent p-0">
              <TabsTrigger value="content" className={modalTab}>
                Conteúdo
              </TabsTrigger>
              <TabsTrigger value="suggest" className={modalTab}>
                Sugerir mudanças
              </TabsTrigger>
            </TabsList>
            <button
              type="button"
              onClick={() => setShowComments((current) => !current)}
              aria-pressed={showComments}
              className={cn(
                'inline-flex shrink-0 items-center gap-1.5 rounded-[6px] px-3 py-1.5 text-[13px] font-semibold transition-colors',
                showComments
                  ? 'bg-[#231651] text-white'
                  : 'text-mu-muted hover:text-mu-brand',
              )}
            >
              <MessageSquare size={15} />
              Comentários
              {commentCount > 0 && (
                <span
                  className={cn(
                    'inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full px-1 text-[10px] font-bold',
                    showComments ? 'bg-mu-surface/20 text-white' : 'bg-mu-brand-bg text-mu-brand',
                  )}
                >
                  {commentCount}
                </span>
              )}
            </button>
          </div>

          <div className="flex max-h-[70vh] min-h-0 flex-col md:flex-row">
            <div className="min-w-0 flex-1 overflow-y-auto px-6 py-5">
              <TabsContent value="content" className="mt-0">
                <div className="flex flex-col gap-4">
                  {Object.entries(fields).map(([label, value]) => (
                    <HtmlFieldView key={label} label={label} value={value} />
                  ))}
                </div>
                {note.tags.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {note.tags.map((tag) => (
                      <Badge
                        key={tag}
                        className="rounded-[5px] border-mu-border bg-mu-surface-2 px-2 py-0.5 text-[11px] font-medium text-mu-muted"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </TabsContent>
              <TabsContent value="suggest" className="mt-0">
                <SuggestChangePanel deckId={deck.deck_id} note={note} />
              </TabsContent>
            </div>

            {showComments && (
              <aside className="w-full shrink-0 overflow-y-auto border-t border-mu-border bg-mu-bg px-6 py-6 md:w-[448px] md:border-l md:border-t-0">
                <NoteCommentsPanel cardId={note.card_id} />
              </aside>
            )}
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}

function SuggestChangePanel({
  deckId,
  note,
}: {
  deckId: string
  note: AnkiSyncChange
}) {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [changeType, setChangeType] = useState(changeTypes[0])
  const [message, setMessage] = useState('')
  const [fields, setFields] = useState<Record<string, string>>(note.fields || {})
  const [sent, setSent] = useState(false)

  const changedFields = buildChangedFields(note.fields || {}, fields)
  const suggestionType = mapChangeType(changeType)
  const hasPayload =
    suggestionType === 'delete' || Object.keys(changedFields).length > 0
  const canSubmit = Boolean(message.trim()) && hasPayload

  const submit = useMutation({
    mutationFn: () =>
      apiRequest(
        `/addon/cards/${note.card_id}/suggestions`,
        {
          method: 'POST',
          body: JSON.stringify({
            suggestion_type: suggestionType,
            fields: changedFields,
            comment: message.trim(),
            source: 'web',
          }),
        },
        token,
      ),
    onSuccess: () => {
      setSent(true)
      queryClient.invalidateQueries({ queryKey: ['deck-note-suggestions', deckId] })
      queryClient.invalidateQueries({ queryKey: ['note-suggestions'] })
    },
  })

  const htmlToolbar = [
    { icon: <ArrowCounterClockwise size={15} />, label: 'Desfazer', cmd: 'undo' },
    { icon: <ArrowClockwise size={15} />, label: 'Refazer', cmd: 'redo' },
    { icon: <TextB size={15} />, label: 'Negrito', cmd: 'bold' },
    { icon: <TextItalic size={15} />, label: 'Itálico', cmd: 'italic' },
    { icon: <TextUnderline size={15} />, label: 'Sublinhado', cmd: 'underline' },
    { icon: <TextT size={15} />, label: 'Tachado', cmd: 'strikeThrough' },
    { icon: <TextH size={15} />, label: 'Título', cmd: 'formatBlock', arg: 'h3' },
    { icon: <LinkSimple size={15} />, label: 'Link', cmd: 'createLink' },
    { icon: <ListBullets size={15} />, label: 'Lista com marcadores', cmd: 'insertUnorderedList' },
    { icon: <ListNumbers size={15} />, label: 'Lista numerada', cmd: 'insertOrderedList' },
    { icon: <DotsThreeVertical size={15} />, label: 'Citação', cmd: 'formatBlock', arg: 'blockquote' },
    { icon: <span className="text-[14px] leading-none">—</span>, label: 'Linha horizontal', cmd: 'insertHorizontalRule' },
    { icon: <TextAlignLeft size={15} />, label: 'Alinhar à esquerda', cmd: 'justifyLeft' },
    { icon: <TextAlignCenter size={15} />, label: 'Centralizar', cmd: 'justifyCenter' },
    { icon: <TextAlignRight size={15} />, label: 'Alinhar à direita', cmd: 'justifyRight' },
    { icon: <TextAlignJustify size={15} />, label: 'Justificar', cmd: 'justifyFull' },
  ]
  const messageTextarea =
    'min-h-[112px] w-full rounded-[6px] border border-mu-border bg-mu-surface px-3.5 py-2.5 text-[15px] leading-[1.6] text-mu-text outline-none transition-colors placeholder:text-mu-muted-2 focus:border-mu-brand'

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-2 rounded-[8px] border border-mu-brand/25 bg-mu-brand-bg px-3.5 py-2.5 text-[13px] leading-[1.5] text-mu-brand">
        <Info size={17} className="mt-px shrink-0" />
        Sua sugestão será enviada para revisão da comunidade. Ela não altera automaticamente a
        nota publicada.
      </div>

      <div className="flex flex-col gap-1.5">
        <span className="text-[13px] font-semibold text-mu-text">Tipo de mudança</span>
        <Select value={changeType} onValueChange={setChangeType}>
          <SelectTrigger className="h-[42px] w-full rounded-[6px] border-mu-border bg-mu-surface text-[14px] text-mu-text focus-visible:ring-[#231651]/30">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {changeTypes.map((type) => (
              <SelectItem key={type} value={type}>
                {type}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex flex-col gap-5">
        {Object.entries(fields).map(([label, value]) => (
          <HtmlFieldEditor
            key={label}
            label={label}
            value={value}
            toolbar={htmlToolbar}
            cloze={note.card_kind === 'cloze'}
            onChange={(next) => setFields((current) => ({ ...current, [label]: next }))}
          />
        ))}
      </div>

      <label className="flex flex-col gap-1.5">
        <span className="text-[13px] font-semibold text-mu-text">Comentário para o revisor</span>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Explique o motivo da sugestão."
          className={messageTextarea}
        />
      </label>

      <div>
        <Button
          type="button"
          onClick={() => submit.mutate()}
          disabled={!canSubmit || submit.isPending}
          className="h-[42px] gap-2 rounded-[6px] bg-[#231651] px-4 text-[13.5px] font-semibold text-white hover:bg-[#1a1040] disabled:opacity-50"
        >
          {submit.isPending ? 'Enviando...' : 'Enviar sugestão'}
        </Button>
        {!canSubmit && (
          <p className="mt-1.5 text-[12px] text-mu-muted-2">
            {message.trim()
              ? 'Edite ao menos um campo para enviar.'
              : 'Escreva um comentário para o revisor.'}
          </p>
        )}
      </div>

      {submit.error && (
        <div className="flex items-center gap-2 rounded-[8px] border border-mu-danger-border bg-mu-danger-bg px-3.5 py-2.5 text-[13px] font-medium text-mu-danger">
          {submit.error instanceof Error
            ? submit.error.message
            : 'Falha ao enviar a sugestão.'}
        </div>
      )}

      {sent && (
        <div className="flex items-center gap-2 rounded-[8px] border border-mu-validated-border bg-mu-validated-bg px-3.5 py-2.5 text-[13px] font-medium text-mu-validated">
          <Check size={16} weight="bold" />
          Sugestão enviada para revisão.
        </div>
      )}
    </div>
  )
}

function NoteCommentsPanel({ cardId }: { cardId: string }) {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [body, setBody] = useState('')

  const commentsQuery = useQuery({
    queryKey: ['note-comments', cardId],
    queryFn: () =>
      apiRequest<NoteCommentList>(`/cards/${cardId}/note-comments`, {}, token),
  })
  const noteComments = commentsQuery.data?.items ?? []

  const addComment = useMutation({
    mutationFn: (text: string) =>
      apiRequest(
        `/cards/${cardId}/note-comments`,
        { method: 'POST', body: JSON.stringify({ body: text }) },
        token,
      ),
    onSuccess: () => {
      setBody('')
      queryClient.invalidateQueries({ queryKey: ['note-comments', cardId] })
    },
  })

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex items-center gap-2 text-[15px] font-semibold text-mu-text">
          <MessageSquare size={17} className="text-mu-brand" />
          Comentários
          <span className="ml-0.5 inline-flex h-[20px] min-w-[20px] items-center justify-center rounded-full bg-mu-brand-bg px-1.5 text-[11px] font-bold text-mu-brand">
            {noteComments.length}
          </span>
        </div>
        <p className="mt-1.5 text-[12.5px] leading-[1.5] text-mu-muted">
          Compartilhe dicas, mnemônicos e dúvidas para ajudar outros estudantes.
        </p>
      </div>

      <div className="flex flex-col gap-3 rounded-[10px] border border-mu-border bg-mu-surface p-3.5 shadow-[0_1px_2px_-1px_rgba(31,36,48,0.05),0_2px_6px_-2px_rgba(31,36,48,0.05)]">
        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder="Escreva um comentário sobre esta nota..."
          className="min-h-[96px] w-full resize-none rounded-[8px] border border-mu-border bg-mu-bg px-3.5 py-2.5 text-[14.5px] leading-[1.6] text-mu-text outline-none transition-colors placeholder:text-mu-muted-2 focus:border-mu-brand focus:bg-mu-surface"
        />
        <Button
          type="button"
          disabled={!body.trim() || addComment.isPending}
          onClick={() => addComment.mutate(body.trim())}
          className="h-[40px] gap-2 self-end rounded-[8px] bg-[#231651] px-5 text-[13.5px] font-semibold text-white hover:bg-[#1a1040]"
        >
          <MessageSquare size={15} />
          Publicar
        </Button>
        {addComment.error && (
          <p className="text-[12.5px] text-mu-danger">
            {addComment.error instanceof Error
              ? addComment.error.message
              : 'Falha ao publicar comentário.'}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-5 border-t border-mu-border pt-7">
        {noteComments
          .slice()
          .sort((left, right) => right.created_at.localeCompare(left.created_at))
          .map((comment) => {
            return (
              <div key={comment.comment_id} className="flex gap-3">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-mu-brand-bg text-[12px] font-bold uppercase text-mu-brand">
                  {comment.author_email.slice(0, 2)}
                </span>
                <article className="min-w-0 flex-1 rounded-[12px] border border-mu-border bg-mu-surface p-5 shadow-[0_1px_2px_-1px_rgba(31,36,48,0.06),0_4px_10px_-4px_rgba(31,36,48,0.08)]">
                  <header className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <strong className="text-[14.5px] font-semibold text-mu-text">
                      {comment.author_email}
                    </strong>
                    <small className="ml-auto text-[11px] text-mu-muted-2">
                      {formatDate(comment.created_at)}
                    </small>
                  </header>
                  <p className="mt-3 whitespace-pre-wrap text-[14.5px] leading-[1.7] text-mu-text-soft">
                    {comment.body}
                  </p>
                </article>
              </div>
            )
          })}
        {commentsQuery.isLoading && (
          <p className="text-[13px] text-mu-muted">Carregando comentários...</p>
        )}
        {!commentsQuery.isLoading && !noteComments.length && (
          <div className="flex flex-col items-center gap-2 rounded-[12px] border border-dashed border-mu-border-hover bg-mu-surface px-4 py-10 text-center">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-mu-brand-bg text-mu-brand">
              <MessageSquare size={20} />
            </span>
            <strong className="text-[13.5px] font-semibold text-mu-text">
              Ainda não há comentários
            </strong>
            <p className="max-w-[240px] text-[12.5px] leading-[1.5] text-mu-muted-2">
              Seja o primeiro a contribuir com uma dica ou observação sobre esta nota.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export function AdminDashboardPage() {
  const { token } = useAuth()
  const pendingQuery = useQuery({
    queryKey: ['note-suggestions-count', 'pending'],
    queryFn: () =>
      apiRequest<NoteSuggestionList>(
        '/admin/note-suggestions?status=pending&page_size=1',
        {},
        token,
      ),
  })
  const pendingCount = pendingQuery.data?.total ?? 0
  const actions = [
    { to: '/admin/decks', label: 'Gerenciar baralhos' },
    { to: '/admin/suggestions', label: 'Revisar sugestões' },
    { to: '/reports', label: 'Reports formais' },
    { to: '/users', label: 'Usuários' },
  ]
  return (
    <div className="ac-page ac-page-muriae">
      <ExploreHero
        eyebrow="Administração"
        title="Dashboard administrativo"
        description="Funções de curadoria para aprovar, revisar e publicar baralhos."
      />
      <section className="mt-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard label="Baralhos publicados" value="12" />
        <MetricCard label="Sugestões pendentes" value={String(pendingCount)} />
        <MetricCard label="Versões em revisão" value="25" />
        <MetricCard label="Releases pendentes" value="3" />
      </section>
      <section className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {actions.map((action) => (
          <Link
            key={action.to}
            to={action.to}
            className={cn(
              muriaeSurface,
              'group flex items-center justify-between gap-4 p-5 transition-[border-color,box-shadow,transform] duration-200 hover:-translate-y-px hover:border-mu-border-hover',
            )}
          >
            <strong className="text-[15px] font-semibold text-mu-text">{action.label}</strong>
            <ArrowRight
              size={18}
              className="shrink-0 text-mu-muted-2 transition-colors group-hover:text-mu-brand"
            />
          </Link>
        ))}
      </section>
    </div>
  )
}

export function AdminDecksPage() {
  const decksQuery = useDeckCatalog()
  const decks = decksQuery.data ?? []
  return (
    <div className="ac-page ac-page-muriae">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <ExploreHero
          eyebrow="Administração"
          title="Gerenciar baralhos"
          description="Controle publicações, releases e composição editorial."
        />
        <Link to="/decks/new" className={cn(muriaePrimaryBtn, 'shrink-0')}>
          <Plus size={16} />
          Novo baralho
        </Link>
      </div>

      <div className="mt-8 flex flex-col gap-2.5">
        {decks.map((deck) => (
          <article
            key={deck.deck_id}
            className={cn(muriaeSurface, 'flex flex-wrap items-center gap-x-5 gap-y-2 p-4')}
          >
            <div className="min-w-0 flex-1">
              <strong className="block text-[15px] font-semibold text-mu-text">
                {deck.name}
              </strong>
              <p className="mt-0.5 truncate text-[13px] text-mu-muted">
                {deck.description || 'Sem descrição.'}
              </p>
            </div>
            <Badge className="shrink-0 rounded-[5px] border-mu-border bg-mu-surface-2 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.04em] text-mu-muted">
              {deck.status}
            </Badge>
            <span className="shrink-0 text-[13px] text-mu-muted">
              {deck.active_card_count} notas
            </span>
            <span className="shrink-0 text-[13px] text-mu-muted">
              Release {deck.latest_release}
            </span>
            <Link
              to={`/deck/${deck.deck_id}`}
              className={cn(muriaeSecondaryBtn, 'h-[36px] shrink-0 px-3.5')}
            >
              Ver
            </Link>
            <Link
              to={`/decks/${deck.deck_id}`}
              className={cn(muriaePrimaryBtn, 'h-[36px] shrink-0 px-3.5')}
            >
              Gerenciar
            </Link>
          </article>
        ))}
      </div>
    </div>
  )
}

export function AdminSuggestionsPage() {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [activeStatus, setActiveStatus] = useState<NoteSuggestionStatus>('pending')

  function useStatusQuery(status: NoteSuggestionStatus) {
    return useQuery({
      queryKey: ['note-suggestions', status],
      queryFn: () =>
        apiRequest<NoteSuggestionList>(
          `/admin/note-suggestions?status=${status}&page_size=100`,
          {},
          token,
        ),
    })
  }

  const pendingQuery = useStatusQuery('pending')
  const acceptedQuery = useStatusQuery('accepted')
  const rejectedQuery = useStatusQuery('rejected')

  const queryByStatus: Record<NoteSuggestionStatus, typeof pendingQuery> = {
    pending: pendingQuery,
    accepted: acceptedQuery,
    rejected: rejectedQuery,
  }
  const activeQuery = queryByStatus[activeStatus]

  const counts = {
    pending: pendingQuery.data?.total ?? 0,
    accepted: acceptedQuery.data?.total ?? 0,
    rejected: rejectedQuery.data?.total ?? 0,
  }

  const review = useMutation({
    mutationFn: ({
      id,
      status,
      comment,
    }: {
      id: string
      status: 'accepted' | 'rejected'
      comment: string
    }) =>
      apiRequest<NoteSuggestion>(
        `/admin/note-suggestions/${id}/review`,
        {
          method: 'POST',
          body: JSON.stringify({
            status,
            review_comment: comment.trim() ? comment.trim() : null,
          }),
        },
        token,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['note-suggestions'] })
    },
  })

  return (
    <div className="ac-page ac-page-muriae">
      <ExploreHero
        eyebrow="Curadoria"
        title="Sugestões de mudanças"
        description="Revise propostas de edição enviadas pela comunidade a partir das notas, com comparação entre o conteúdo atual e o sugerido."
      />

      <div className="mt-8">
        <SuggestionList
          activeStatus={activeStatus}
          counts={counts}
          items={activeQuery.data?.items ?? []}
          loading={activeQuery.isLoading}
          error={
            activeQuery.error instanceof Error ? activeQuery.error.message : null
          }
          onStatusChange={setActiveStatus}
          reviewingId={review.isPending ? (review.variables?.id ?? null) : null}
          onReview={(id, status, comment) =>
            review.mutate({ id, status, comment })
          }
        />
      </div>
    </div>
  )
}

export function CommunityFuturePage() {
  const features = [
    {
      icon: <MessageSquare size={20} />,
      title: 'Discussões por nota',
      desc: 'Comentários colaborativos conectados ao public_id da nota.',
    },
    {
      icon: <Lightbulb size={20} />,
      title: 'Dicas e mnemônicos',
      desc: 'Conteúdo social separado do cartão oficial e moderado pela plataforma.',
    },
    {
      icon: <Sparkles size={20} />,
      title: 'Sugestões para curadoria',
      desc: 'Correções relevantes podem virar reports e novas versões.',
    },
  ]
  return (
    <div className="ac-page ac-page-muriae">
      <ExploreHero
        eyebrow="Comunidade futura"
        title="Comunidade Anki Concursos"
        description="Espaço planejado para comentários, dicas, mnemônicos e sugestões públicas por baralho e por nota."
      />
      <section className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => (
          <article key={feature.title} className={cn(muriaeSurface, 'flex flex-col gap-3 p-5')}>
            <span className="flex h-10 w-10 items-center justify-center rounded-[8px] bg-mu-brand-bg text-mu-brand">
              {feature.icon}
            </span>
            <strong className="text-[15px] font-semibold text-mu-text">{feature.title}</strong>
            <p className="text-[13.5px] leading-[1.55] text-mu-muted">{feature.desc}</p>
          </article>
        ))}
      </section>
    </div>
  )
}

const STATUS_CHIP: Record<string, string> = {
  pending: 'border-mu-border bg-mu-surface-2 text-mu-muted',
  accepted: 'border-mu-validated-border bg-mu-validated-bg text-mu-validated',
  rejected: 'border-mu-danger-border bg-mu-danger-bg text-mu-danger',
}

export function CommunitySuggestionHistoryPage() {
  const { deckId = '' } = useParams()
  const { token } = useAuth()
  const decksQuery = useDeckCatalog()
  const decks = decksQuery.data ?? []
  const deck = decks.find((item) => item.deck_id === deckId)

  const suggestionsQuery = useQuery({
    queryKey: ['deck-note-suggestions', deckId],
    queryFn: () =>
      apiRequest<NoteSuggestionList>(
        `/decks/${deckId}/note-suggestions?page_size=100`,
        {},
        token,
      ),
    enabled: Boolean(deckId),
  })

  const suggestions = suggestionsQuery.data?.items ?? []
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected =
    suggestions.find((item) => item.suggestion_id === selectedId) ||
    suggestions[0] ||
    null

  const deckName = deck?.name ?? 'Baralho'

  return (
    <div className="ac-page ac-page-muriae">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <ExploreHero
          eyebrow="Comunidade do baralho"
          title="Sugestões de mudanças"
          description={`${deckName} · acompanhe as propostas da comunidade, compare o conteúdo atual com o sugerido e participe da discussão.`}
        />
        <Link to={`/deck/${deckId}`} className={cn(muriaeSecondaryBtn, 'shrink-0')}>
          <ArrowLeft size={16} />
          Voltar ao baralho
        </Link>
      </div>

      {suggestionsQuery.isLoading ? (
        <div className="mt-8">
          <LoadingState />
        </div>
      ) : suggestionsQuery.error ? (
        <div className="mt-8">
          <ErrorState
            message={
              suggestionsQuery.error instanceof Error
                ? suggestionsQuery.error.message
                : 'Não foi possível carregar as sugestões.'
            }
            requestId={
              suggestionsQuery.error instanceof ApiError
                ? suggestionsQuery.error.requestId
                : null
            }
          />
        </div>
      ) : suggestions.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            title="Nenhuma sugestão registrada"
            description="As mudanças propostas pela comunidade aparecerão aqui assim que forem enviadas pelo add-on."
          />
        </div>
      ) : (
        <section className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-[300px_minmax(0,1fr)]">
          <aside className="flex flex-col gap-2" aria-label="Lista de sugestões">
            {suggestions.map((item) => {
              const active = item.suggestion_id === selected?.suggestion_id
              return (
                <button
                  key={item.suggestion_id}
                  type="button"
                  onClick={() => setSelectedId(item.suggestion_id)}
                  className={cn(
                    'flex flex-col gap-1 rounded-[8px] border px-4 py-3 text-left transition-colors',
                    active
                      ? 'border-mu-brand bg-mu-brand-bg'
                      : 'border-mu-border bg-mu-surface hover:border-mu-border-hover',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[13px] font-semibold text-mu-text">
                      {SUGGESTION_TYPE_LABEL[item.suggestion_type] ??
                        item.suggestion_type}
                    </span>
                    <span
                      className={cn(
                        'shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold',
                        STATUS_CHIP[item.status] ?? STATUS_CHIP.pending,
                      )}
                    >
                      {SUGGESTION_STATUS_LABEL[item.status] ?? item.status}
                    </span>
                  </div>
                  <small className="truncate text-[12px] text-mu-muted">
                    {item.submitted_by_email}
                  </small>
                  <small className="text-[11px] text-mu-muted-2">
                    {formatDate(item.created_at)}
                  </small>
                </button>
              )
            })}
          </aside>

          {selected && (
            <main className="flex min-w-0 flex-col gap-5">
              <section className={cn(muriaeSurface, 'p-5')}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <span className={muriaeEyebrow}>Sugestão selecionada</span>
                    <h2 className="mt-1.5 font-dm-serif text-[20px] font-normal text-mu-text">
                      {SUGGESTION_TYPE_LABEL[selected.suggestion_type] ??
                        selected.suggestion_type}
                    </h2>
                    <p className="mt-1 text-[12.5px] text-mu-muted">
                      Por {selected.submitted_by_email} ·{' '}
                      {formatDate(selected.created_at)}
                      {selected.public_id ? ` · ${selected.public_id}` : ''}
                    </p>
                  </div>
                  <span
                    className={cn(
                      'rounded-full border px-2.5 py-1 text-[11px] font-semibold',
                      STATUS_CHIP[selected.status] ?? STATUS_CHIP.pending,
                    )}
                  >
                    {SUGGESTION_STATUS_LABEL[selected.status] ?? selected.status}
                  </span>
                </div>

                {selected.comment && (
                  <div className="mt-4 rounded-[8px] border border-mu-border bg-mu-bg p-3.5">
                    <span className="mb-1 block text-[11px] font-bold uppercase tracking-[0.08em] text-mu-muted-2">
                      Justificativa
                    </span>
                    <p className="whitespace-pre-wrap text-[13.5px] leading-[1.6] text-mu-text">
                      {selected.comment}
                    </p>
                  </div>
                )}

                <div className="mt-4">
                  <DiffViewer
                    fields={selected.fields}
                    addedTags={selected.added_tags}
                    removedTags={selected.removed_tags}
                  />
                </div>

                {selected.status !== 'pending' && (
                  <div className="mt-4 border-t border-mu-border pt-3 text-[12.5px] text-mu-muted">
                    Revisada por {selected.reviewed_by ?? '—'}
                    {selected.reviewed_at
                      ? ` em ${formatDate(selected.reviewed_at)}`
                      : ''}
                    {selected.review_comment
                      ? ` · "${selected.review_comment}"`
                      : ''}
                  </div>
                )}
              </section>

              <SuggestionDiscussion suggestionId={selected.suggestion_id} />
            </main>
          )}
        </section>
      )}
    </div>
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
    mutationFn: () =>
      apiRequest(`/subscriptions/${deck.deck_id}/cancel`, { method: 'POST' }, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['community-decks'] })
      queryClient.invalidateQueries({ queryKey: ['deck-subscriptions'] })
    },
  })

  if (deck.subscribed) {
    return (
      <Button
        type="button"
        variant="outline"
        disabled={unsubscribeMutation.isPending}
        onClick={() => unsubscribeMutation.mutate()}
        className="h-[42px] gap-2 rounded-[6px] border-mu-validated-border bg-mu-validated-bg px-4 text-[13.5px] font-semibold text-mu-validated hover:bg-mu-validated-bg"
      >
        <X size={16} weight="bold" />
        Desinscrever
      </Button>
    )
  }

  return (
    <Button
      type="button"
      disabled={subscribeMutation.isPending}
      onClick={() => subscribeMutation.mutate()}
      className="h-[42px] gap-2 rounded-[6px] bg-[#231651] px-4 text-[13.5px] font-semibold text-white hover:bg-[#1a1040]"
    >
      <Plus size={16} />
      Inscrever-se
    </Button>
  )
}

function SegmentedFilter({
  value,
  onChange,
}: {
  value: DeckFilter
  onChange: (value: DeckFilter) => void
}) {
  const options: Array<[DeckFilter, string]> = [
    ['all', 'Todos'],
    ['subscribed', 'Inscritos'],
    ['available', 'Disponíveis'],
  ]
  return (
    <ToggleGroup
      type="single"
      value={value}
      onValueChange={(next) => next && onChange(next as DeckFilter)}
      className="h-[42px] items-center gap-0.5 rounded-[6px] border border-mu-border bg-mu-surface px-[5px]"
    >
      {options.map(([key, label]) => (
        <ToggleGroupItem
          key={key}
          value={key}
          className="h-[31px] rounded-[4px] px-4 text-[13.5px] font-semibold text-mu-muted hover:bg-transparent hover:text-mu-text data-[state=on]:bg-[#231651] data-[state=on]:text-white"
        >
          {label}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <article className={cn(muriaeSurface, 'flex flex-col gap-1 p-5')}>
      <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-mu-muted-2">
        {label}
      </span>
      <strong className="font-dm-serif text-[30px] font-normal leading-none tabular-nums text-mu-text">
        {value}
      </strong>
      <small className="mt-1 inline-flex items-center gap-1.5 text-[11px] text-mu-muted-2">
        <Clock3 size={13} />
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
