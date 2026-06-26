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
import { EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge } from '../components/ui-primitives'
import { formatDate } from '../lib/presentation'
import type {
  AnkiDeckManifest,
  AnkiDeckSync,
  DeckSubscriptionList,
  SubscribableDeck,
  SubscribableDeckList,
} from '../types'

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
    <div className="addon-page">
      <PageHeader
        eyebrow="Distribuicao"
        title="Preparacao do add-on Anki"
        description="Assine decks publicados, valide o manifesto e confira o pacote de sincronizacao que o add-on externo consumira."
        action={
          <button className="button button-secondary" type="button" onClick={refreshAll}>
            <RefreshCw size={17} />
            Atualizar
          </button>
        }
      />

      {error && (
        <ErrorState
          message={error.message}
          requestId={error instanceof ApiError ? error.requestId : null}
        />
      )}

      <section className="addon-flow-card">
        <div>
          <PlugZap size={24} />
          <strong>O que fica neste sistema</strong>
          <p>
            Login, assinatura de decks, manifestos e deltas por release. O add-on
            externo usara esses endpoints para escrever no Anki local.
          </p>
        </div>
        <div>
          <GitBranch size={24} />
          <strong>O que fica no add-on</strong>
          <p>
            Criar note type, mapear card_id para note_id, aplicar added, updated,
            removed e deprecated, e guardar a ultima release aplicada.
          </p>
        </div>
      </section>

      <div className="addon-layout">
        <section className="addon-panel">
          <div className="addon-section-title">
            <p className="eyebrow">Decks publicados</p>
            <h2>Assinaturas disponiveis</h2>
          </div>
          {decks.isLoading ? (
            <LoadingState />
          ) : decks.data?.items.length ? (
            <div className="addon-deck-list">
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
              title="Nenhum deck publicado"
              description="Publique uma release de deck para que ele apareca como assinavel."
            />
          )}
        </section>

        <section className="addon-panel addon-detail-panel">
          <div className="addon-section-title">
            <p className="eyebrow">Contrato do add-on</p>
            <h2>{selectedDeck?.name || 'Selecione um deck'}</h2>
          </div>
          {selectedDeckId ? (
            <>
              <EndpointList deckId={selectedDeckId} />
              <div className="sync-release-control">
                <label>
                  <span>Release local simulada</span>
                  <input
                    min="0"
                    type="number"
                    value={sinceRelease}
                    onChange={(event) => setSinceRelease(event.target.value)}
                  />
                </label>
                <button
                  className="button button-secondary"
                  type="button"
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
              title="Nenhum deck selecionado"
              description="Assine ou selecione um deck publicado para validar os endpoints que o add-on usara."
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
    <article className={`addon-deck-card ${selected ? 'addon-deck-card-selected' : ''}`}>
      <button type="button" className="addon-deck-main" onClick={onSelect}>
        <div>
          <strong>{deck.name}</strong>
          <p>{deck.description || 'Sem descricao.'}</p>
        </div>
        <StatusBadge value={deck.subscribed ? 'subscribed' : deck.status} />
      </button>
      <div className="addon-deck-meta">
        <span>{deck.active_card_count} cards</span>
        <span>Release {deck.latest_release}</span>
        <span>Atualizado {formatDate(deck.updated_at)}</span>
      </div>
      {deck.subscribed ? (
        <button
          className="button button-secondary"
          disabled={busy}
          type="button"
          onClick={onCancel}
        >
          <XCircle size={16} />
          Cancelar
        </button>
      ) : (
        <button
          className="button button-primary"
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
    <div className="addon-endpoints">
      {endpoints.map((endpoint) => (
        <button
          key={endpoint}
          type="button"
          onClick={() => navigator.clipboard?.writeText(endpoint)}
        >
          <Clipboard size={15} />
          <code>{endpoint}</code>
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
    <div className="addon-contract-grid">
      <article>
        <span>Manifesto</span>
        <strong>{manifest.note_type}</strong>
        <p>Campos: {manifest.fields.join(', ')}</p>
        <p>
          Modelos suportados:{' '}
          {Object.values(manifest.supported_note_types)
            .map((note) => note.note_type)
            .join(', ')}
        </p>
        <pre>{JSON.stringify(manifest.field_mapping, null, 2)}</pre>
      </article>
      <article>
        <span>Sync preview</span>
        <strong>
          {sync.has_changes ? `${sync.changes.length} mudancas` : 'Sem mudancas'}
        </strong>
        <p>
          Release local {sync.from_release} para release remota {sync.to_release}
        </p>
        <div className="addon-change-list">
          {sync.changes.slice(0, 8).map((change) => (
            <div key={`${change.release_id}-${change.card_id}`}>
              <StatusBadge value={change.action} />
              <code>{change.public_id}</code>
              <small>release {change.release_number}</small>
            </div>
          ))}
          {sync.changes.length > 8 && (
            <small>Mais {sync.changes.length - 8} mudancas no payload.</small>
          )}
        </div>
      </article>
    </div>
  )
}
