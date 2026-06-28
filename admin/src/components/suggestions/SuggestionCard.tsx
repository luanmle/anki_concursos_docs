import { ArrowRight, Check, ThumbsDown, ThumbsUp, X } from '@phosphor-icons/react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { NoteSuggestion } from '../../types'
import { formatDate } from '../../lib/presentation'
import { cn } from '../../lib/utils'
import { DiffViewer } from './DiffViewer'
import { SUGGESTION_TYPE_LABEL } from './labels'

const muriaePrimaryBtn =
  'inline-flex h-[38px] items-center gap-2 rounded-[6px] bg-[#231651] px-4 text-[13px] font-semibold !text-white transition-colors hover:bg-[#1a1040] disabled:opacity-50'
const muriaeSecondaryBtn =
  'inline-flex h-[38px] items-center gap-2 rounded-[6px] border border-mu-border bg-mu-surface px-4 text-[13px] font-semibold text-mu-text transition-colors hover:border-mu-border-hover hover:bg-mu-surface-2 disabled:opacity-50'

function initials(email: string): string {
  const name = email.split('@')[0] ?? email
  const parts = name.split(/[.\-_]+/).filter(Boolean)
  const chars = parts.length >= 2 ? parts[0][0] + parts[1][0] : name.slice(0, 2)
  return chars.toUpperCase()
}

const STATUS_STYLE: Record<
  NoteSuggestion['status'],
  { label: string; className: string }
> = {
  pending: {
    label: 'Aguardando',
    className: 'border-mu-border bg-mu-surface-2 text-mu-muted',
  },
  accepted: {
    label: 'Aceita',
    className: 'border-mu-validated-border bg-mu-validated-bg text-mu-validated',
  },
  rejected: {
    label: 'Rejeitada',
    className: 'border-mu-danger-border bg-mu-danger-bg text-mu-danger',
  },
}

export function SuggestionCard({
  suggestion,
  onReview,
  isReviewing,
}: {
  suggestion: NoteSuggestion
  onReview: (status: 'accepted' | 'rejected', comment: string) => void
  isReviewing: boolean
}) {
  const [comment, setComment] = useState('')
  const status = STATUS_STYLE[suggestion.status]
  const refId = suggestion.public_id ?? suggestion.suggestion_id.slice(0, 8)
  const isPending = suggestion.status === 'pending'

  return (
    <article className="flex flex-col gap-4 rounded-[10px] border border-mu-border bg-mu-surface p-5 shadow-[0_1px_2px_-1px_rgba(31,36,48,0.05),0_2px_6px_-2px_rgba(31,36,48,0.05)]">
      {/* Cabeçalho: autor + meta */}
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-mu-brand-bg text-[12px] font-bold text-mu-brand">
            {initials(suggestion.submitted_by_email)}
          </span>
          <div className="flex flex-col">
            <span className="text-[13.5px] font-semibold text-mu-text">
              {suggestion.submitted_by_email}
            </span>
            <span className="text-[12px] text-mu-muted">
              {formatDate(suggestion.created_at)} · {refId}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {suggestion.card_id && (
            <Link
              to={`/cards/${suggestion.card_id}`}
              className="inline-flex items-center gap-1 text-[12px] font-semibold text-mu-brand hover:underline"
            >
              Ver cartão <ArrowRight size={13} weight="bold" />
            </Link>
          )}
          <span
            className={cn(
              'rounded-full border px-2.5 py-1 text-[11px] font-semibold',
              status.className,
            )}
          >
            {status.label}
          </span>
        </div>
      </header>

      {/* Título: tipo de mudança + votos */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-[15px] font-semibold text-mu-text">
          {SUGGESTION_TYPE_LABEL[suggestion.suggestion_type] ??
            suggestion.suggestion_type}
        </h3>
        {/* ponytail: votos são display-only — backend não tem campo de voto. */}
        <div className="flex items-center gap-1" title="Votação em breve">
          <span className="inline-flex items-center gap-1 text-[12px] text-mu-muted-2">
            <ThumbsUp size={15} /> 0
          </span>
          <span className="inline-flex items-center gap-1 text-[12px] text-mu-muted-2">
            <ThumbsDown size={15} /> 0
          </span>
        </div>
      </div>

      {/* Justificativa (rationale) */}
      {suggestion.comment && (
        <div className="rounded-[8px] border border-mu-border bg-mu-bg p-3.5">
          <span className="mb-1 block text-[11px] font-bold uppercase tracking-[0.08em] text-mu-muted-2">
            Justificativa
          </span>
          <p className="whitespace-pre-wrap text-[13.5px] leading-[1.6] text-mu-text">
            {suggestion.comment}
          </p>
        </div>
      )}

      {/* Diff */}
      <DiffViewer
        fields={suggestion.fields}
        addedTags={suggestion.added_tags}
        removedTags={suggestion.removed_tags}
      />

      {/* Ações de revisão / resultado */}
      {isPending ? (
        <div className="flex flex-col gap-2.5 border-t border-mu-border pt-4">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Comentário de revisão (opcional)"
            rows={2}
            className="w-full resize-y rounded-[6px] border border-mu-border bg-mu-bg px-3 py-2 text-[13px] text-mu-text outline-none focus:border-mu-brand"
          />
          <div className="flex flex-wrap gap-2.5">
            <button
              type="button"
              disabled={isReviewing}
              onClick={() => onReview('accepted', comment)}
              className={muriaePrimaryBtn}
            >
              <Check size={16} weight="bold" /> Aceitar
            </button>
            <button
              type="button"
              disabled={isReviewing}
              onClick={() => onReview('rejected', comment)}
              className={muriaeSecondaryBtn}
            >
              <X size={16} weight="bold" /> Rejeitar
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-2.5 border-t border-mu-border pt-3">
          <p className="text-[12.5px] text-mu-muted">
            Revisada por {suggestion.reviewed_by ?? '—'}
            {suggestion.reviewed_at ? ` em ${formatDate(suggestion.reviewed_at)}` : ''}
            {suggestion.review_comment ? ` · "${suggestion.review_comment}"` : ''}
          </p>
          {suggestion.status === 'accepted' && suggestion.resulting_card_version_id && (
            <Link to={`/cards/${suggestion.card_id}`} className={muriaePrimaryBtn}>
              Abrir cartão para aprovar e publicar
              <ArrowRight size={16} weight="bold" />
            </Link>
          )}
        </div>
      )}
    </article>
  )
}
