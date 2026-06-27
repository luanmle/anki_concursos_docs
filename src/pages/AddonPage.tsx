import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle as CheckCircle2,
  ClipboardText as Clipboard,
  GitBranch,
  Plug as PlugZap,
  ArrowClockwise as RefreshCw,
  XCircle,
} from '@phosphor-icons/react'
import { useMemo, useState } from 'react'
import { API_URL, ApiError, apiRequest } from '../api/client'
import { useAuth } from '../auth/auth-context'
import {
  EmptyState,
  ErrorState,
  LoadingState,
  StatusBadge,
} from '../components/ui-primitives'
import { ExploreHero } from '../components/ExploreHero'
import { Input } from '../components/ui/input'
import { cn } from '../lib/utils'
import { formatDate } from '../lib/presentation'
import type {
  AnkiDeckManifest,
  AnkiDeckSync,
  DeckSubscriptionList,
  SubscribableDeck,
  SubscribableDeckList,
} from '../types'

const muriaePrimaryBtn =
  'inline-flex h-[42px] items-center gap-2 rounded-[6px] bg-[#231651] px-4 text-[13.5px] font-semibold !text-white transition-colors hover:bg-[#1a1040] disabled:cursor-not-allowed disabled:opacity-50'
const muriaeSecondaryBtn =
  'inline-flex h-[42px] items-center gap-2 rounded-[6px] border border-mu-border bg-mu-surface px-4 text-[13.5px] font-semibold text-mu-text transition-colors hover:border-mu-border-hover hover:bg-mu-surface-2 disabled:cursor-not-allowed disabled:opacity-50'
const muriaeSurface =
  'rounded-[10px] border border-mu-border bg-mu-surface shadow-[0_1px_2px_-1px_rgba(31,36,48,0.05),0_2px_6px_-2px_rgba(31,36,48,0.05)]'
const muriaeEyebrow =
  'text-[11px] font-bold uppercase tracking-[0.14em] text-mu-brand'

export function AddonPage() {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [selectedDeckId, setSelectedDeckId] = useState('')
  const [sinceRelease, setSinceRelease] = useState('0')
  const decks = useQuery({
    queryKey: ['subscribable-decks'],
    queryFn: () =>
      apiRequest<SubscribableDeckList>(
        '/subscriptions/decks?page=1&page_size=100',
        {},
        token,
      ),
  })
  const subscriptions = useQuery({
    queryKey: ['deck-subscriptions'],
    queryFn: () =>
      apiRequest<DeckSubscriptionList>('/subscriptions', {}, token),
  })
  const manifest = useQuery({
    queryKey: ['addon-manifest', selectedDeckId],
    enabled: Boolean(selectedDeckId),
    queryFn: () =>
      apiRequest<AnkiDeckManifest>(
        `/addon/decks/${selectedDeckId}/manifest`,
        {},
        token,
      ),
  })
  const sync = useQuery({
    queryKey: ['addon-sync', selectedDeckId, sinceRelease],
    enabled: Boolean(selectedDeckId),
    queryFn: () =>
      apiRequest<AnkiDeckSync>(
        `/addon/decks/${selectedDeckId}/sync?since_release=${Number(sinceRelease) || 0}`,
        {},
        token,
      ),
  })

  const selectedDeck = useMemo(
    () => decks.data?.items.find((deck) => deck.deck_id === selectedDeckId),
    [decks.data?.items, selectedDeckId],
  )

  const subscribe = useMutation({
    mutationFn: (deckId: string) =>
      apiRequest(`/subscriptions/${deckId}`, { method: 'POST' }, token),
    onSuccess: (_data, deckId) => {
      setSelectedDeckId(deckId)
      queryClient.invalidateQueries({ queryKey: ['subscribable-decks'] })
      queryClient.invalidateQueries({ queryKey: ['deck-subscriptions'] })
      queryClient.invalidateQueries({ queryKey: ['addon-manifest', deckId] })
      queryClient.invalidateQueries({ queryKey: ['addon-sync', deckId] })
    },
  })
  const cancel = useMutation({
    mutationFn: (deckId: string) =>
      apiRequest(`/subscriptions/${deckId}/cancel`, { method: 'POST' }, token),
    onSuccess: (_data, deckId) => {
      if (selectedDeckId === deckId) setSelectedDeckId('')
      queryClient.invalidateQueries({ queryKey: ['subscribable-decks'] })
      queryClient.invalidateQueries({ queryKey: ['deck-subscriptions'] })
    },
  })

  const error =
    decks.error ||
    subscriptions.error ||
    manifest.error ||
    sync.error ||
    subscribe.error ||
    cancel.error

  function refreshAll() {
    queryClient.invalidateQueries({ queryKey: ['subscribable-decks'] })
    queryClient.invalidateQueries({ queryKey: ['deck-subscriptions'] })
    if (selectedDeckId) {
      queryClient.invalidateQueries({ queryKey: ['addon-manifest', selectedDeckId] })
      queryClient.invalidateQueries({ queryKey: ['addon-sync', selectedDeckId] })
    }
  }

  return (
    <div className="ac-page ac-page-muriae">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <ExploreHero
          eyebrow="Distribuição"
          title="Preparação do add-on Anki"
          description="Assine baralhos publicados, valide o manifesto e confira o pacote de sincronização que o add-on externo consumirá."
        />
        <button
          type="button"
          className={cn(muriaeSecondaryBtn, 'shrink-0')}
          onClick={refreshAll}
        >
          <RefreshCw size={17} />
          Atualizar
        </button>
      </div>

      {error && (
        <div className="mt-6">
          <ErrorState
            message={error.message}
            requestId={error instanceof ApiError ? error.requestId : null}
          />
        </div>
      )}

      <section className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <article className={cn(muriaeSurface, 'flex flex-col gap-2 p-5')}>
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-mu-brand-bg text-mu-brand">
            <PlugZap size={20} />
          </span>
          <strong className="text-[15px] font-semibold text-mu-text">
            O que fica neste sistema
          </strong>
          <p className="text-[13.5px] leading-relaxed text-mu-muted">
            Login, assinatura de baralhos, manifestos e deltas por release. O add-on
            externo usará esses endpoints para escrever no Anki local.
          </p>
        </article>
        <article className={cn(muriaeSurface, 'flex flex-col gap-2 p-5')}>
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-mu-brand-bg text-mu-brand">
            <GitBranch size={20} />
          </span>
          <strong className="text-[15px] font-semibold text-mu-text">
            O que fica no add-on
          </strong>
          <p className="text-[13.5px] leading-relaxed text-mu-muted">
            Criar note type, mapear card_id para note_id, aplicar added, updated,
            removed e deprecated, e guardar a última release aplicada.
          </p>
        </article>
      </section>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        <section className={cn(muriaeSurface, 'flex flex-col gap-4 p-5')}>
          <div className="flex flex-col gap-1">
            <p className={muriaeEyebrow}>Baralhos publicados</p>
            <h2 className="text-[18px] font-semibold text-mu-text">
              Assinaturas disponíveis
            </h2>
          </div>
          {decks.isLoading ? (
            <LoadingState />
          ) : decks.data?.items.length ? (
            <div className="flex flex-col gap-3">
              {decks.data.items.map((deck) => (
                <DeckSubscriptionCard
                  key={deck.deck_id}
                  deck={deck}
                  selected={deck.deck_id === selectedDeckId}
                  busy={subscribe.isPending || cancel.isPending}
                  onSelect={() => {
                    setSelectedDeckId(deck.deck_id)
                    setSinceRelease(String(deck.latest_release || 0))
                  }}
                  onSubscribe={() => subscribe.mutate(deck.deck_id)}
                  onCancel={() => cancel.mutate(deck.deck_id)}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              title="Nenhum baralho publicado"
              description="Publique uma release de baralho para que ele apareça como assinável."
            />
          )}
        </section>

        <section className={cn(muriaeSurface, 'flex flex-col gap-4 p-5')}>
          <div className="flex flex-col gap-1">
            <p className={muriaeEyebrow}>Contrato do add-on</p>
            <h2 className="text-[18px] font-semibold text-mu-text">
              {selectedDeck?.name || 'Selecione um baralho'}
            </h2>
          </div>
          {selectedDeckId ? (
            <>
              <EndpointList deckId={selectedDeckId} />
              <div className="flex flex-wrap items-end gap-3">
                <label className="flex flex-col gap-1.5">
                  <span className="text-[12px] font-medium text-mu-muted">
                    Release local simulada
                  </span>
                  <Input
                    min="0"
                    type="number"
                    className="h-[42px] w-[160px]"
                    value={sinceRelease}
                    onChange={(event) => setSinceRelease(event.target.value)}
                  />
                </label>
                <button
                  type="button"
                  className={muriaeSecondaryBtn}
                  onClick={() => sync.refetch()}
                >
                  Testar sync
                </button>
              </div>
              {manifest.isLoading || sync.isLoading ? (
                <LoadingState />
              ) : (
                <AddonContractPreview manifest={manifest.data} sync={sync.data} />
              )}
            </>
          ) : (
            <EmptyState
              title="Nenhum baralho selecionado"
              description="Assine ou selecione um baralho publicado para validar os endpoints que o add-on usará."
            />
          )}
        </section>
      </div>
    </div>
  )
}

function DeckSubscriptionCard({
  deck,
  selected,
  busy,
  onSelect,
  onSubscribe,
  onCancel,
}: {
  deck: SubscribableDeck
  selected: boolean
  busy: boolean
  onSelect: () => void
  onSubscribe: () => void
  onCancel: () => void
}) {
  return (
    <article
      className={cn(
        'flex flex-col gap-3 rounded-[10px] border bg-mu-surface p-4 transition-colors',
        selected
          ? 'border-mu-brand ring-1 ring-mu-brand'
          : 'border-mu-border hover:border-mu-border-hover',
      )}
    >
      <button
        type="button"
        className="flex items-start justify-between gap-3 text-left"
        onClick={onSelect}
      >
        <div className="flex flex-col gap-1">
          <strong className="text-[14.5px] font-semibold text-mu-text">
            {deck.name}
          </strong>
          <p className="text-[13px] leading-snug text-mu-muted">
            {deck.description || 'Sem descrição.'}
          </p>
        </div>
        <StatusBadge value={deck.subscribed ? 'subscribed' : deck.status} />
      </button>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-mu-muted-2">
        <span>{deck.active_card_count} cards</span>
        <span>Release {deck.latest_release}</span>
        <span>Atualizado {formatDate(deck.updated_at)}</span>
      </div>
      {deck.subscribed ? (
        <button
          className={cn(muriaeSecondaryBtn, 'h-[38px] self-start')}
          disabled={busy}
          type="button"
          onClick={onCancel}
        >
          <XCircle size={16} />
          Cancelar
        </button>
      ) : (
        <button
          className={cn(muriaePrimaryBtn, 'h-[38px] self-start')}
          disabled={busy || deck.latest_release === 0}
          type="button"
          onClick={onSubscribe}
        >
          <CheckCircle2 size={16} />
          Assinar
        </button>
      )}
    </article>
  )
}

function EndpointList({ deckId }: { deckId: string }) {
  const endpoints = [
    `${API_URL}/addon/decks/${deckId}/manifest`,
    `${API_URL}/addon/decks/${deckId}/sync?since_release=0`,
    `${API_URL}/subscriptions/${deckId}`,
  ]
  return (
    <div className="flex flex-col gap-2">
      {endpoints.map((endpoint) => (
        <button
          key={endpoint}
          type="button"
          className="flex items-center gap-2 rounded-[8px] border border-mu-border bg-mu-surface-2 px-3 py-2 text-left transition-colors hover:border-mu-border-hover"
          onClick={() => navigator.clipboard?.writeText(endpoint)}
        >
          <Clipboard size={15} className="shrink-0 text-mu-muted-2" />
          <code className="truncate font-mono text-[12px] text-mu-text">
            {endpoint}
          </code>
        </button>
      ))}
    </div>
  )
}

function AddonContractPreview({
  manifest,
  sync,
}: {
  manifest?: AnkiDeckManifest
  sync?: AnkiDeckSync
}) {
  if (!manifest || !sync) return null
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <article className={cn(muriaeSurface, 'flex flex-col gap-2 bg-mu-surface-2 p-4')}>
        <span className={muriaeEyebrow}>Manifesto</span>
        <strong className="text-[14px] font-semibold text-mu-text">
          {manifest.note_type}
        </strong>
        <p className="text-[12.5px] text-mu-muted">
          Campos: {manifest.fields.join(', ')}
        </p>
        <p className="text-[12.5px] text-mu-muted">
          Modelos suportados:{' '}
          {Object.values(manifest.supported_note_types)
            .map((note) => note.note_type)
            .join(', ')}
        </p>
        <pre className="mt-1 overflow-auto rounded-[8px] border border-mu-border bg-mu-surface p-3 font-mono text-[11.5px] leading-relaxed text-mu-text">
          {JSON.stringify(manifest.field_mapping, null, 2)}
        </pre>
      </article>
      <article className={cn(muriaeSurface, 'flex flex-col gap-2 bg-mu-surface-2 p-4')}>
        <span className={muriaeEyebrow}>Sync preview</span>
        <strong className="text-[14px] font-semibold text-mu-text">
          {sync.has_changes ? `${sync.changes.length} mudanças` : 'Sem mudanças'}
        </strong>
        <p className="text-[12.5px] text-mu-muted">
          Release local {sync.from_release} para release remota {sync.to_release}
        </p>
        <div className="flex flex-col gap-2">
          {sync.changes.slice(0, 8).map((change) => (
            <div
              key={`${change.release_id}-${change.card_id}`}
              className="flex items-center gap-2"
            >
              <StatusBadge value={change.action} />
              <code className="font-mono text-[11.5px] text-mu-text">
                {change.public_id}
              </code>
              <small className="text-[11px] text-mu-muted-2">
                release {change.release_number}
              </small>
            </div>
          ))}
          {sync.changes.length > 8 && (
            <small className="text-[11px] text-mu-muted-2">
              Mais {sync.changes.length - 8} mudanças no payload.
            </small>
          )}
        </div>
      </article>
    </div>
  )
}
