import type { NoteSuggestion, NoteSuggestionStatus } from '../../types'
import { cn } from '../../lib/utils'
import { EmptyState, ErrorState, LoadingState } from '../ui-primitives'
import { SuggestionCard } from './SuggestionCard'

export type StatusCounts = Record<NoteSuggestionStatus, number>

const TABS: { status: NoteSuggestionStatus; label: string }[] = [
  { status: 'pending', label: 'Aguardando' },
  { status: 'accepted', label: 'Aceitas' },
  { status: 'rejected', label: 'Rejeitadas' },
]

export function SuggestionList({
  activeStatus,
  counts,
  items,
  loading,
  error,
  onStatusChange,
  onReview,
  reviewingId,
}: {
  activeStatus: NoteSuggestionStatus
  counts: StatusCounts
  items: NoteSuggestion[]
  loading: boolean
  error: string | null
  onStatusChange: (status: NoteSuggestionStatus) => void
  onReview: (id: string, status: 'accepted' | 'rejected', comment: string) => void
  reviewingId: string | null
}) {
  return (
    <div className="flex flex-col gap-5">
      {/* Filtros de status + contagem */}
      <div className="flex flex-wrap gap-1 border-b border-mu-border">
        {TABS.map((tab) => (
          <button
            key={tab.status}
            type="button"
            onClick={() => onStatusChange(tab.status)}
            className={cn(
              'flex h-11 items-center gap-2 border-b-2 px-3 text-[14px] font-semibold transition-colors',
              activeStatus === tab.status
                ? 'border-b-mu-brand text-mu-text'
                : 'border-b-transparent text-mu-muted hover:text-mu-text',
            )}
          >
            {tab.label}
            <span
              className={cn(
                'rounded-full px-1.5 py-0.5 text-[11px] font-bold',
                activeStatus === tab.status
                  ? 'bg-mu-brand-bg text-mu-brand'
                  : 'bg-mu-surface-2 text-mu-muted',
              )}
            >
              {counts[tab.status]}
            </span>
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} />
      ) : items.length === 0 ? (
        <EmptyState
          title="Nenhuma sugestão"
          description="Não há sugestões com este status no momento."
        />
      ) : (
        <div className="flex flex-col gap-4">
          {items.map((suggestion) => (
            <SuggestionCard
              key={suggestion.suggestion_id}
              suggestion={suggestion}
              isReviewing={reviewingId === suggestion.suggestion_id}
              onReview={(status, comment) =>
                onReview(suggestion.suggestion_id, status, comment)
              }
            />
          ))}
        </div>
      )}
    </div>
  )
}
