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
  ThumbsUp,
  Code,
  LinkSimple,
  ListBullets,
  ListNumbers,
  TextB,
  TextH,
  TextT,
  TextItalic,
  DotsThreeVertical,
  X,
} from '@phosphor-icons/react'
import { useCallback, useRef, useState } from 'react'
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
} from '../components/ui-primitives'
import { ExploreHero } from '../components/ExploreHero'
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
import { useLocalStorageState } from '../hooks/useLocalStorageState'
import { formatDate } from '../lib/presentation'
import { StatusBadge } from '../components/ui-primitives'
import type {
  AnkiDeckSync,
  AnkiSyncChange,
  CardSummary,
  CardVersion,
  SubscribableDeck,
  SubscribableDeckList,
} from '../types'

/* eslint-disable react-hooks/refs */

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
  const decks = decksQuery.data?.length ? decksQuery.data : fallbackDecks
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
            className="pointer-events-none absolute left-[14px] top-1/2 -translate-y-1/2 text-[#98a2b3]"
          />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Buscar baralhos..."
            className="h-[42px] rounded-[6px] border-[#e4e1da] bg-white pl-[40px] text-[14px] text-[#1f2430] placeholder:text-[#98a2b3] focus-visible:ring-[#231651]/30"
          />
        </div>

        <SegmentedFilter value={filter} onChange={setFilter} />

        <DropdownMenu>
          <DropdownMenuTrigger className="inline-flex h-[42px] items-center gap-2 whitespace-nowrap rounded-[6px] border border-[#e4e1da] bg-white px-4 text-[13.5px] font-semibold text-[#1f2430] outline-none transition-colors hover:border-[#d4d0c7] hover:bg-[#fbfaf8]">
            <SlidersHorizontal size={16} className="text-[#667085]" />
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
        <p className="mt-[18px] mb-4 text-[13px] font-medium text-[#667085]">
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
  const decks = (decksQuery.data?.length ? decksQuery.data : fallbackDecks).filter(
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
        <section className="mt-8 flex flex-col items-start gap-3 rounded-[10px] border border-dashed border-[#e4e1da] bg-white p-8">
          <strong className="text-[16px] font-semibold text-[#1f2430]">
            Você ainda não está inscrito em baralhos
          </strong>
          <p className="max-w-[420px] text-[14px] leading-[1.55] text-[#667085]">
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

      <section className="mt-6 flex items-start gap-3.5 rounded-[10px] border border-[#e4e1da] bg-white p-5">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[8px] bg-[#eeebfa] text-[#231651]">
          <BookOpen size={20} />
        </span>
        <div>
          <strong className="block text-[15px] font-semibold text-[#1f2430]">
            Sincronização com o Anki
          </strong>
          <p className="mt-1 text-[13.5px] leading-[1.55] text-[#667085]">
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

  const category = deckCategory(deck)
  const secondaryButton =
    'h-[42px] gap-2 rounded-[6px] border-[#e4e1da] bg-white px-4 text-[13.5px] font-semibold text-[#1f2430] hover:border-[#d4d0c7] hover:bg-[#fbfaf8]'

  return (
    <div className="ac-page ac-page-muriae">
      <Link
        to="/"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-[#667085] transition-colors hover:text-[#1f2430]"
      >
        <ArrowLeft size={16} />
        Voltar ao Explore
      </Link>

      <section className="mt-5 flex flex-col gap-6 border-b border-[#e4e1da] pb-8 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <span className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#231651]">
            Baralho
          </span>
          <h1 className="mt-2 font-dm-serif text-[34px] font-normal leading-[1.1] tracking-[-0.01em] text-[#1f2430]">
            {deck.name}
          </h1>
          <p className="mt-3 max-w-[640px] text-[15px] leading-[1.6] text-[#667085]">
            {deck.description || 'Deck publicado na plataforma Anki Concursos.'}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-[13px] text-[#667085]">
            <Badge
              className={cn(
                'rounded-[5px] border px-2 py-0.5 text-[11px] font-bold uppercase tracking-[0.06em]',
                CATEGORY[category].badge,
              )}
            >
              {CATEGORY[category].label}
            </Badge>
            <span className="inline-flex items-center gap-1.5">
              <Stack size={14} className="text-[#98a2b3]" />
              {deck.active_card_count.toLocaleString('pt-BR')} notas
            </span>
            <span className="inline-flex items-center gap-1.5">
              <ArrowClockwise size={14} className="text-[#98a2b3]" />
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
            className="h-[42px] px-3 text-[13.5px] font-semibold text-[#667085] hover:bg-transparent hover:text-[#231651]"
          >
            <Link to="/community">Ver na Comunidade</Link>
          </Button>
        </div>
      </section>

      <section className="mt-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#231651]">
              Notas
            </span>
            <h2 className="mt-1.5 font-dm-serif text-[22px] font-normal text-[#1f2430]">
              Preview do baralho
            </h2>
          </div>
          <div className="relative w-full sm:w-[280px]">
            <Search
              size={18}
              className="pointer-events-none absolute left-[14px] top-1/2 -translate-y-1/2 text-[#98a2b3]"
            />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar notas..."
              className="h-[42px] rounded-[6px] border-[#e4e1da] bg-white pl-[40px] text-[14px] text-[#1f2430] placeholder:text-[#98a2b3] focus-visible:ring-[#231651]/30"
            />
          </div>
        </div>

        <div className="mt-5 flex flex-col gap-2.5">
          {filteredNotes.map((note) => (
            <NoteRow key={note.card_id} note={note} onOpen={() => setSelectedNote(note)} />
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
          onClose={() => setSelectedNote(null)}
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
      className="group flex items-center gap-4 rounded-[8px] border border-[#e4e1da] bg-white px-4 py-3.5 text-left shadow-[0_1px_2px_-1px_rgba(31,36,48,0.05),0_2px_6px_-2px_rgba(31,36,48,0.06)] transition-[border-color,box-shadow,transform] duration-200 ease-out hover:-translate-y-[2px] hover:border-[#cdbfae] hover:shadow-[0_5px_10px_-3px_rgba(31,36,48,0.10),0_14px_26px_-8px_rgba(35,22,81,0.16)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#231651]"
    >
      <Badge className="shrink-0 rounded-[5px] border-[#e4e1da] bg-[#f6f5f2] px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.08em] text-[#667085]">
        {note.card_kind || 'basic'}
      </Badge>
      <div className="min-w-0 flex-1">
        <strong className="block truncate text-[14px] font-semibold text-[#1f2430]">
          {noteTitle(note)}
        </strong>
        <p className="mt-0.5 truncate text-[13px] text-[#667085]">{noteSummary(note)}</p>
      </div>
      {/* "Validado" é apresentação: notas de baralho publicado são tidas como validadas. */}
      <Badge className="hidden shrink-0 items-center gap-1 rounded-[5px] border-[#abefc6] bg-[#ecfdf3] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[#15803d] sm:inline-flex">
        <Check size={11} weight="bold" />
        Validado
      </Badge>
      <code className="hidden shrink-0 font-mono text-[12px] text-[#98a2b3] md:block">
        {note.public_id}
      </code>
      <ArrowRight
        size={18}
        className="shrink-0 text-[#98a2b3] transition-colors group-hover:text-[#231651]"
      />
    </button>
  )
}

const modalTab =
  'h-11 flex-none rounded-none border-0 border-b-2 border-b-transparent bg-transparent px-0 text-[14px] font-semibold text-[#667085] shadow-none transition-colors hover:text-[#1f2430] focus-visible:outline-none focus-visible:ring-0 data-[state=active]:border-b-[#231651] data-[state=active]:text-[#1f2430]'

const muriaePrimaryBtn =
  'inline-flex h-[42px] items-center gap-2 rounded-[6px] bg-[#231651] px-4 text-[13.5px] font-semibold !text-white transition-colors hover:bg-[#1a1040]'
const muriaeSecondaryBtn =
  'inline-flex h-[42px] items-center gap-2 rounded-[6px] border border-[#e4e1da] bg-white px-4 text-[13.5px] font-semibold text-[#1f2430] transition-colors hover:border-[#d4d0c7] hover:bg-[#fbfaf8]'
const muriaeSurface =
  'rounded-[10px] border border-[#e4e1da] bg-white shadow-[0_1px_2px_-1px_rgba(31,36,48,0.05),0_2px_6px_-2px_rgba(31,36,48,0.05)]'
const muriaeEyebrow =
  'text-[11px] font-bold uppercase tracking-[0.14em] text-[#231651]'

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
  const [allComments] = useLocalStorageState<StudentComment[]>(
    'anki-concursos-comments',
    initialComments,
  )
  const commentCount = allComments.filter((c) => c.publicId === note.public_id).length
  const fields = note.fields || {}
  const category = CATEGORY[deckCategory(deck)]

  return (
    <Dialog open onOpenChange={(next) => !next && onClose()}>
      <DialogContent
        showCloseButton={false}
        className={cn(
          'grid-cols-[minmax(0,1fr)] gap-0 overflow-hidden rounded-[14px] border-[#e4e1da] bg-white p-0 text-[#1f2430] sm:max-w-[720px]',
          showComments && 'sm:max-w-[1160px]',
        )}
      >
        <DialogTitle className="sr-only">{note.public_id}</DialogTitle>

        <div className="flex items-start justify-between gap-4 px-6 pt-5">
          <div className="min-w-0">
            <span className="text-[11px] font-bold uppercase tracking-[0.1em] text-[#667085]">
              {note.card_kind || 'basic'}
            </span>
            <h2 className="mt-0.5 truncate font-mono text-[20px] font-semibold text-[#1f2430]">
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
            <Badge className="inline-flex items-center gap-1 rounded-[5px] border-[#abefc6] bg-[#ecfdf3] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.04em] text-[#15803d]">
              <Check size={10} weight="bold" />
              Validado
            </Badge>
            <button
              type="button"
              onClick={() => navigator.clipboard?.writeText(note.public_id)}
              aria-label="Copiar identificador"
              className="flex h-8 w-8 items-center justify-center rounded-[6px] text-[#667085] transition-colors hover:bg-[#f1f0ec] hover:text-[#1f2430]"
            >
              <Copy size={16} />
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label="Fechar"
              className="flex h-8 w-8 items-center justify-center rounded-[6px] text-[#667085] transition-colors hover:bg-[#f1f0ec] hover:text-[#1f2430]"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        <Tabs defaultValue="content" className="mt-3 gap-0">
          <div className="flex flex-col gap-2 border-b border-[#e4e1da] px-6 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
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
                  : 'text-[#667085] hover:text-[#231651]',
              )}
            >
              <MessageSquare size={15} />
              Comentários
              {commentCount > 0 && (
                <span
                  className={cn(
                    'inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-full px-1 text-[10px] font-bold',
                    showComments ? 'bg-white/20 text-white' : 'bg-[#eeebfa] text-[#231651]',
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
                <div className="grid gap-3 sm:grid-cols-2">
                  {Object.entries(fields).map(([label, value]) => (
                    <article
                      key={label}
                      className="rounded-[8px] border border-[#e4e1da] bg-[#fafaf8] p-4"
                    >
                      <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#98a2b3]">
                        {label}
                      </span>
                      <p className="mt-1.5 text-[14px] leading-[1.55] text-[#1f2430]">{value}</p>
                    </article>
                  ))}
                </div>
                {note.tags.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {note.tags.map((tag) => (
                      <Badge
                        key={tag}
                        className="rounded-[5px] border-[#e4e1da] bg-[#f6f5f2] px-2 py-0.5 text-[11px] font-medium text-[#667085]"
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
              <aside className="w-full shrink-0 overflow-y-auto border-t border-[#e4e1da] bg-[#fafaf8] px-6 py-6 md:w-[448px] md:border-l md:border-t-0">
                <NoteCommentsPanel publicId={note.public_id} />
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
  const [suggestions, setSuggestions] = useLocalStorageState<StudentSuggestion[]>(
    'anki-concursos-suggestions',
    [],
  )
  const [changeType, setChangeType] = useState(changeTypes[0])
  const [message, setMessage] = useState('')
  const [fields, setFields] = useState<Record<string, string>>(note.fields || {})
  const [sent, setSent] = useState(false)
  const fieldRefs = useRef<Record<string, HTMLTextAreaElement | null>>({})
  const [activeField, setActiveField] = useState<string | null>(null)
  const registerFieldRef = useCallback(
    (fieldName: string) => (node: HTMLTextAreaElement | null) => {
      fieldRefs.current[fieldName] = node
    },
    [],
  )

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

  function insertMarkdown(fieldName: string, before: string, after = before, placeholder = '') {
    const textarea = fieldRefs.current[fieldName]
    if (!textarea) return

    const currentValue = fields[fieldName] ?? ''
    const start = textarea.selectionStart ?? currentValue.length
    const end = textarea.selectionEnd ?? currentValue.length
    const selectedText = currentValue.slice(start, end) || placeholder
    const nextValue =
      currentValue.slice(0, start) +
      before +
      selectedText +
      after +
      currentValue.slice(end)

    setFields((current) => ({ ...current, [fieldName]: nextValue }))
    setActiveField(fieldName)

    window.requestAnimationFrame(() => {
      const selectionStart = start + before.length
      const selectionEnd = selectionStart + selectedText.length
      textarea.focus()
      textarea.setSelectionRange(selectionStart, selectionEnd)
    })
  }

  const toolbarItems = (label: string): Array<{
    icon: React.ReactNode
    label: string
    onClick?: () => void
  }> => [
    { icon: <ArrowCounterClockwise size={15} />, label: 'Desfazer' },
    { icon: <ArrowClockwise size={15} />, label: 'Refazer' },
    { icon: <TextB size={15} />, label: 'Negrito', onClick: () => insertMarkdown(label, '**', '**', 'texto em negrito') },
    { icon: <TextItalic size={15} />, label: 'Itálico', onClick: () => insertMarkdown(label, '*', '*', 'texto em itálico') },
    { icon: <TextH size={15} />, label: 'Título', onClick: () => insertMarkdown(label, '### ', '', 'título') },
    { icon: <TextT size={15} />, label: 'Tachado', onClick: () => insertMarkdown(label, '~~', '~~', 'texto tachado') },
    { icon: <LinkSimple size={15} />, label: 'Link', onClick: () => insertMarkdown(label, '[', '](https://)', 'link') },
    { icon: <ListBullets size={15} />, label: 'Lista com marcadores', onClick: () => insertMarkdown(label, '- ', '', 'item de lista') },
    { icon: <ListNumbers size={15} />, label: 'Lista numerada', onClick: () => insertMarkdown(label, '1. ', '', 'item numerado') },
    { icon: <Code size={15} />, label: 'Bloco de código', onClick: () => insertMarkdown(label, '```\n', '\n```', 'codigo') },
    { icon: <DotsThreeVertical size={15} />, label: 'Citação', onClick: () => insertMarkdown(label, '> ', '', 'citação') },
    { icon: <span className="text-[14px] leading-none">—</span>, label: 'Linha horizontal', onClick: () => insertMarkdown(label, '\n---\n', '', '') },
    { icon: <TextAlignLeft size={15} />, label: 'Alinhar à esquerda' },
    { icon: <TextAlignCenter size={15} />, label: 'Centralizar' },
    { icon: <TextAlignRight size={15} />, label: 'Alinhar à direita' },
    { icon: <TextAlignJustify size={15} />, label: 'Justificar' },
  ]
  const toolbarButton =
    'inline-flex h-7 min-w-7 items-center justify-center rounded-[4px] px-1 text-[#667085] transition-colors hover:bg-[#eceae4] hover:text-[#1f2430]'
  const fieldTextarea =
    'min-h-[88px] w-full rounded-[6px] border border-[#e4e1da] bg-white px-3 py-2 text-[14px] leading-[1.5] text-[#1f2430] outline-none transition-colors placeholder:text-[#98a2b3] focus:border-[#231651]'

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-2 rounded-[8px] border border-[rgba(35,22,81,0.16)] bg-[#f3f1fb] px-3.5 py-2.5 text-[13px] leading-[1.5] text-[#3b2f6b]">
        <Info size={17} className="mt-px shrink-0" />
        Sua sugestão será enviada para revisão da comunidade. Ela não altera automaticamente a
        nota publicada.
      </div>

      <div className="flex flex-col gap-1.5">
        <span className="text-[13px] font-semibold text-[#1f2430]">Tipo de mudança</span>
        <Select value={changeType} onValueChange={setChangeType}>
          <SelectTrigger className="h-[42px] w-full rounded-[6px] border-[#e4e1da] bg-white text-[14px] text-[#1f2430] focus-visible:ring-[#231651]/30">
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

      <div className="grid gap-4 sm:grid-cols-2">
        {Object.entries(fields).map(([label, value]) => (
          <div className="flex flex-col gap-1.5" key={label}>
            <span className="text-[13px] font-semibold text-[#1f2430]">{label}</span>
            {activeField === label && (
              <div
                className="flex flex-wrap items-center gap-0.5 rounded-[6px] border border-[#e4e1da] bg-[#fafaf8] p-1"
                aria-label={`Barra de formatação de ${label}`}
              >
                {toolbarItems(label).map((item, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={item.onClick}
                    aria-label={item.label}
                    className={toolbarButton}
                  >
                    {item.icon}
                  </button>
                ))}
              </div>
            )}
            <textarea
              ref={registerFieldRef(label)}
              value={value}
              onFocus={() => setActiveField(label)}
              onChange={(event) =>
                setFields((current) => ({ ...current, [label]: event.target.value }))
              }
              className={fieldTextarea}
            />
            {activeField === label && (
              <p className="text-[12px] text-[#98a2b3]">A barra acima edita este campo da nota.</p>
            )}
          </div>
        ))}
      </div>

      <label className="flex flex-col gap-1.5">
        <span className="text-[13px] font-semibold text-[#1f2430]">Comentário para o revisor</span>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Explique o motivo da sugestão."
          className={fieldTextarea}
        />
      </label>

      <div>
        <Button
          type="button"
          onClick={submitSuggestion}
          className="h-[42px] gap-2 rounded-[6px] bg-[#231651] px-4 text-[13.5px] font-semibold text-white hover:bg-[#1a1040]"
        >
          Enviar sugestão
        </Button>
      </div>

      {sent && (
        <div className="flex items-center gap-2 rounded-[8px] border border-[#abefc6] bg-[#ecfdf3] px-3.5 py-2.5 text-[13px] font-medium text-[#15803d]">
          <Check size={16} weight="bold" />
          Sugestão enviada para revisão.
        </div>
      )}
    </div>
  )
}

const COMMENT_KIND_LABELS: Record<CommentKind, string> = {
  comment: 'Comentário',
  tip: 'Dica',
  mnemonic: 'Mnemônico',
  question: 'Dúvida',
  correction: 'Correção',
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

  return (
    <div className="flex flex-col gap-6">
      <div>
        <div className="flex items-center gap-2 text-[15px] font-semibold text-[#1f2430]">
          <MessageSquare size={17} className="text-[#231651]" />
          Comentários
          <span className="ml-0.5 inline-flex h-[20px] min-w-[20px] items-center justify-center rounded-full bg-[#eeebfa] px-1.5 text-[11px] font-bold text-[#231651]">
            {noteComments.length}
          </span>
        </div>
        <p className="mt-1.5 text-[12.5px] leading-[1.5] text-[#667085]">
          Compartilhe dicas, mnemônicos e dúvidas para ajudar outros estudantes.
        </p>
      </div>

      <div className="flex flex-col gap-3 rounded-[10px] border border-[#e4e1da] bg-white p-3.5 shadow-[0_1px_2px_-1px_rgba(31,36,48,0.05),0_2px_6px_-2px_rgba(31,36,48,0.05)]">
        <textarea
          value={body}
          onChange={(event) => setBody(event.target.value)}
          placeholder="Escreva um comentário sobre esta nota..."
          className="min-h-[84px] w-full resize-none rounded-[8px] border border-[#e4e1da] bg-[#fafaf8] px-3.5 py-2.5 text-[14px] leading-[1.55] text-[#1f2430] outline-none transition-colors placeholder:text-[#98a2b3] focus:border-[#231651] focus:bg-white"
        />
        <Button
          type="button"
          onClick={addComment}
          className="h-[40px] gap-2 self-end rounded-[8px] bg-[#231651] px-5 text-[13.5px] font-semibold text-white hover:bg-[#1a1040]"
        >
          <MessageSquare size={15} />
          Publicar
        </Button>
      </div>

      <div className="flex flex-col gap-4 border-t border-[#e4e1da] pt-6">
        {noteComments
          .slice()
          .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
          .map((comment) => {
            return (
              <div key={comment.id} className="flex gap-3">
                <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#eeebfa] text-[12px] font-bold uppercase text-[#231651]">
                  {comment.author.slice(0, 2)}
                </span>
                <article className="min-w-0 flex-1 rounded-[12px] border border-[#e4e1da] bg-white p-4 shadow-[0_1px_2px_-1px_rgba(31,36,48,0.06),0_4px_10px_-4px_rgba(31,36,48,0.08)]">
                  <header className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <strong className="text-[13.5px] font-semibold text-[#1f2430]">
                      {comment.author}
                    </strong>
                    <Badge className="rounded-full border-[#e4e1da] bg-[#f6f5f2] px-2 py-0.5 text-[9.5px] font-bold uppercase tracking-[0.06em] text-[#667085]">
                      {COMMENT_KIND_LABELS[comment.kind]}
                    </Badge>
                    <small className="ml-auto text-[11px] text-[#98a2b3]">
                      {formatDate(comment.createdAt)}
                    </small>
                  </header>
                  <p className="mt-2.5 text-[13.5px] leading-[1.65] text-[#3f4754]">
                    {comment.body}
                  </p>
                  <footer className="mt-3.5 flex items-center gap-2 border-t border-[#f1efe9] pt-3">
                    <button
                      type="button"
                      onClick={() => handleUpvote(comment.id)}
                      className="inline-flex items-center gap-1.5 rounded-full border border-[#e4e1da] bg-white px-3 py-1 text-[12px] font-semibold text-[#475467] transition-colors hover:border-[#231651] hover:bg-[#f3f1fb] hover:text-[#231651]"
                    >
                      <ThumbsUp size={13} weight="fill" className="text-[#98a2b3]" />
                      Útil
                      <span className="tabular-nums">{comment.score}</span>
                    </button>
                    <button
                      type="button"
                      className="ml-auto text-[12px] font-medium text-[#98a2b3] transition-colors hover:text-[#1f2430]"
                    >
                      Denunciar
                    </button>
                  </footer>
                </article>
              </div>
            )
          })}
        {!noteComments.length && (
          <div className="flex flex-col items-center gap-2 rounded-[12px] border border-dashed border-[#d8d3c8] bg-white px-4 py-10 text-center">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#eeebfa] text-[#231651]">
              <MessageSquare size={20} />
            </span>
            <strong className="text-[13.5px] font-semibold text-[#1f2430]">
              Ainda não há comentários
            </strong>
            <p className="max-w-[240px] text-[12.5px] leading-[1.5] text-[#98a2b3]">
              Seja o primeiro a contribuir com uma dica ou observação sobre esta nota.
            </p>
          </div>
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
        <MetricCard label="Sugestões pendentes" value={String(pendingSuggestions.length)} />
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
              'group flex items-center justify-between gap-4 p-5 transition-[border-color,box-shadow,transform] duration-200 hover:-translate-y-px hover:border-[#d4d0c7]',
            )}
          >
            <strong className="text-[15px] font-semibold text-[#1f2430]">{action.label}</strong>
            <ArrowRight
              size={18}
              className="shrink-0 text-[#98a2b3] transition-colors group-hover:text-[#231651]"
            />
          </Link>
        ))}
      </section>
    </div>
  )
}

export function AdminDecksPage() {
  const decksQuery = useDeckCatalog()
  const decks = decksQuery.data?.length ? decksQuery.data : fallbackDecks
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
              <strong className="block text-[15px] font-semibold text-[#1f2430]">
                {deck.name}
              </strong>
              <p className="mt-0.5 truncate text-[13px] text-[#667085]">
                {deck.description || 'Sem descrição.'}
              </p>
            </div>
            <Badge className="shrink-0 rounded-[5px] border-[#e4e1da] bg-[#f6f5f2] px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.04em] text-[#667085]">
              {deck.status}
            </Badge>
            <span className="shrink-0 text-[13px] text-[#667085]">
              {deck.active_card_count} notas
            </span>
            <span className="shrink-0 text-[13px] text-[#667085]">
              Release {deck.latest_release}
            </span>
            <Link
              to={`/deck/${deck.deck_id}`}
              className={cn(muriaeSecondaryBtn, 'h-[36px] shrink-0 px-3.5')}
            >
              Abrir
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
    <div className="ac-page ac-page-muriae">
      <ExploreHero
        eyebrow="Curadoria"
        title="Sugestões dos estudantes"
        description="Revise propostas enviadas a partir das notas sem editar conteúdo publicado diretamente."
      />

      <div className="mt-8 flex flex-col gap-2.5">
        {error && (
          <div className="flex items-center gap-2 rounded-[8px] border border-[#fecaca] bg-[#fef2f2] px-3.5 py-2.5 text-[13px] font-medium text-[#b42318]">
            {error}
          </div>
        )}
        {success && (
          <div className="flex items-center gap-2 rounded-[8px] border border-[#abefc6] bg-[#ecfdf3] px-3.5 py-2.5 text-[13px] font-medium text-[#15803d]">
            <Check size={16} weight="bold" />
            {success}
          </div>
        )}

        {suggestions.map((suggestion) => (
          <article key={suggestion.id} className={cn(muriaeSurface, 'flex flex-col gap-2.5 p-4')}>
            <header className="flex flex-wrap items-center gap-2">
              <strong className="font-mono text-[14px] font-semibold text-[#1f2430]">
                {suggestion.publicId}
              </strong>
              <Badge className="rounded-[5px] border-[#e4e1da] bg-[#f6f5f2] px-2 py-0.5 text-[11px] font-medium text-[#667085]">
                {suggestion.changeType}
              </Badge>
              <StatusBadge value={suggestion.status} />
              {suggestion.resultingCardVersionId && (
                <span className="text-[12px] text-[#98a2b3]">
                  v {suggestion.resultingCardVersionId.slice(0, 8)}
                </span>
              )}
            </header>
            <p className="text-[13.5px] leading-[1.55] text-[#667085]">
              {suggestion.message || 'Sem comentário adicional.'}
            </p>
            <footer className="flex flex-wrap items-center gap-3">
              <small className="text-[12px] text-[#98a2b3]">
                {formatDate(suggestion.createdAt)}
              </small>
              <div className="ml-auto flex gap-2">
                <button
                  type="button"
                  disabled={suggestion.status !== 'pending'}
                  onClick={() => convertSuggestion.mutate(suggestion)}
                  className="inline-flex h-[34px] items-center rounded-[6px] bg-[#231651] px-3 text-[12.5px] font-semibold text-white transition-colors hover:bg-[#1a1040] disabled:cursor-not-allowed disabled:opacity-45"
                >
                  Converter em nova versão
                </button>
                <button
                  type="button"
                  disabled={suggestion.status !== 'pending'}
                  onClick={() => rejectSuggestion.mutate(suggestion)}
                  className="inline-flex h-[34px] items-center rounded-[6px] border border-[#e4e1da] bg-white px-3 text-[12.5px] font-semibold text-[#1f2430] transition-colors hover:bg-[#fbfaf8] disabled:cursor-not-allowed disabled:opacity-45"
                >
                  Rejeitar
                </button>
              </div>
            </footer>
          </article>
        ))}
        {!suggestions.length && (
          <section className="flex flex-col items-start gap-2 rounded-[10px] border border-dashed border-[#e4e1da] bg-white p-8">
            <strong className="text-[16px] font-semibold text-[#1f2430]">
              Nenhuma sugestão pendente
            </strong>
            <p className="text-[14px] text-[#667085]">
              As sugestões criadas no modal da nota aparecerão aqui.
            </p>
          </section>
        )}
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
            <span className="flex h-10 w-10 items-center justify-center rounded-[8px] bg-[#eeebfa] text-[#231651]">
              {feature.icon}
            </span>
            <strong className="text-[15px] font-semibold text-[#1f2430]">{feature.title}</strong>
            <p className="text-[13.5px] leading-[1.55] text-[#667085]">{feature.desc}</p>
          </article>
        ))}
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
    <div className="ac-page ac-page-muriae">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <ExploreHero
          eyebrow="Comunidade do deck"
          title="Histórico de mudanças e discussão"
          description={`${deck.name} · acompanhe a nota original, a proposta do usuário, o ID da nota e a conversa editorial sem perder o contexto da sugestão.`}
        />
        <Link to={`/deck/${deck.deck_id}`} className={cn(muriaeSecondaryBtn, 'shrink-0')}>
          <ArrowLeft size={16} />
          Voltar ao deck
        </Link>
      </div>

      {!visibleHistory.length ? (
        <div className="mt-8">
          <EmptyState
            title="Nenhuma sugestão registrada"
            description="As mudanças da comunidade aparecerão aqui assim que forem criadas."
          />
        </div>
      ) : (
        <section className="mt-8 grid grid-cols-1 gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="flex flex-col gap-2" aria-label="Histórico de sugestões">
            {visibleHistory.map((item) => {
              const active = item.id === selectedSuggestion?.id
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedSuggestionId(item.id)}
                  className={cn(
                    'flex flex-col gap-0.5 rounded-[8px] border px-4 py-3 text-left transition-colors',
                    active
                      ? 'border-[#231651] bg-[#f3f1fb]'
                      : 'border-[#e4e1da] bg-white hover:border-[#d4d0c7]',
                  )}
                >
                  <span className="text-[11px] text-[#98a2b3]">Nota {item.noteId}</span>
                  <strong className="font-mono text-[13px] font-semibold text-[#1f2430]">
                    {item.publicId}
                  </strong>
                  <small className="text-[12px] text-[#667085]">Por {item.userName}</small>
                </button>
              )
            })}
          </aside>

          {selectedSuggestion && (
            <main className="flex min-w-0 flex-col gap-5">
              <section className={cn(muriaeSurface, 'p-5')}>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <span className={muriaeEyebrow}>Sugestão selecionada</span>
                    <h2 className="mt-1.5 font-dm-serif text-[20px] font-normal text-[#1f2430]">
                      {selectedSuggestion.publicId}
                    </h2>
                  </div>
                  <StatusBadge value="published" />
                </div>
                <dl className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <div>
                    <dt className="text-[11px] uppercase tracking-[0.06em] text-[#98a2b3]">
                      ID da nota
                    </dt>
                    <dd className="mt-0.5 text-[13.5px] text-[#1f2430]">
                      {selectedSuggestion.noteId}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[11px] uppercase tracking-[0.06em] text-[#98a2b3]">
                      Usuário
                    </dt>
                    <dd className="mt-0.5 text-[13.5px] text-[#1f2430]">
                      {selectedSuggestion.userName}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[11px] uppercase tracking-[0.06em] text-[#98a2b3]">
                      Criada em
                    </dt>
                    <dd className="mt-0.5 text-[13.5px] text-[#1f2430]">
                      {formatDate(selectedSuggestion.createdAt)}
                    </dd>
                  </div>
                </dl>
                <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <article className="rounded-[8px] border border-[#e4e1da] bg-[#fafaf8] p-4">
                    <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#98a2b3]">
                      Campo original
                    </span>
                    <p className="mt-1.5 text-[14px] leading-[1.55] text-[#1f2430]">
                      {selectedSuggestion.originalField}
                    </p>
                  </article>
                  <article className="rounded-[8px] border border-[#abefc6] bg-[#ecfdf3] p-4">
                    <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-[#15803d]">
                      Novo campo sugerido
                    </span>
                    <p className="mt-1.5 text-[14px] leading-[1.55] text-[#1f2430]">
                      {selectedSuggestion.suggestedField}
                    </p>
                  </article>
                </div>
              </section>

              <section className={cn(muriaeSurface, 'p-5')}>
                <div>
                  <span className={muriaeEyebrow}>Discussão</span>
                  <h2 className="mt-1.5 font-dm-serif text-[20px] font-normal text-[#1f2430]">
                    Conversa editorial
                  </h2>
                </div>
                <div className="mt-4 flex flex-col gap-2.5">
                  {selectedSuggestion.discussion.map((comment) => (
                    <article
                      key={comment.id}
                      className="rounded-[8px] border border-[#e4e1da] bg-[#fafaf8] p-3.5"
                    >
                      <header className="flex items-center justify-between gap-2">
                        <strong className="text-[13px] font-semibold text-[#1f2430]">
                          {comment.author}
                        </strong>
                        <small className="text-[11px] text-[#98a2b3]">
                          {formatDate(comment.createdAt)}
                        </small>
                      </header>
                      <p className="mt-1.5 text-[13px] leading-[1.55] text-[#475467]">
                        {comment.body}
                      </p>
                    </article>
                  ))}
                </div>
                <label className="mt-4 flex flex-col gap-1.5">
                  <span className="text-[13px] font-semibold text-[#1f2430]">
                    Adicionar comentário
                  </span>
                  <textarea
                    rows={4}
                    value={draftComment}
                    onChange={(event) => setDraftComment(event.target.value)}
                    placeholder="Registre uma observação sobre esta sugestão."
                    className="w-full rounded-[6px] border border-[#e4e1da] bg-white px-3 py-2 text-[14px] leading-[1.5] text-[#1f2430] outline-none transition-colors placeholder:text-[#98a2b3] focus:border-[#231651]"
                  />
                </label>
                <button type="button" onClick={addComment} className={cn(muriaePrimaryBtn, 'mt-3')}>
                  <MessageSquare size={16} />
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
      <Button
        type="button"
        variant="outline"
        disabled={unsubscribeMutation.isPending}
        onClick={() => unsubscribeMutation.mutate()}
        className="h-[42px] gap-2 rounded-[6px] border-[#abefc6] bg-[#ecfdf3] px-4 text-[13.5px] font-semibold text-[#15803d] hover:bg-[#d7f7e3]"
      >
        <Check size={16} weight="bold" />
        Inscrito
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
      className="h-[42px] items-center gap-0.5 rounded-[6px] border border-[#e4e1da] bg-white px-[5px]"
    >
      {options.map(([key, label]) => (
        <ToggleGroupItem
          key={key}
          value={key}
          className="h-[31px] rounded-[4px] px-4 text-[13.5px] font-semibold text-[#667085] hover:bg-transparent hover:text-[#1f2430] data-[state=on]:bg-[#231651] data-[state=on]:text-white"
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
      <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#98a2b3]">
        {label}
      </span>
      <strong className="font-dm-serif text-[30px] font-normal leading-none tabular-nums text-[#1f2430]">
        {value}
      </strong>
      <small className="mt-1 inline-flex items-center gap-1.5 text-[11px] text-[#98a2b3]">
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

