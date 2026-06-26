import { ArrowClockwise, Check, Clock, Stack } from '@phosphor-icons/react'
import { useNavigate } from 'react-router-dom'
import { cn } from '../lib/utils'
import type { SubscribableDeck } from '../types'

export type DeckCategory = 'official' | 'community' | 'ai'

export const CATEGORY: Record<
  DeckCategory,
  { label: string; strip: string; text: string; badge: string }
> = {
  official: {
    label: 'Oficial',
    strip: 'bg-mu-brand-bg border-b-mu-official-border',
    text: 'text-mu-brand',
    badge: 'bg-mu-brand-bg border-mu-official-border text-mu-brand',
  },
  community: {
    label: 'Comunidade',
    strip: 'bg-mu-cat-comm-bg border-b-mu-cat-comm-border',
    text: 'text-mu-cat-comm',
    badge: 'bg-mu-cat-comm-bg border-mu-cat-comm-border text-mu-cat-comm',
  },
  ai: {
    label: 'IA',
    strip: 'bg-mu-cat-ai-bg border-b-mu-cat-ai-border',
    text: 'text-mu-cat-ai',
    badge: 'bg-mu-cat-ai-bg border-mu-cat-ai-border text-mu-cat-ai',
  },
}

// Categoria e validação não existem no modelo de dados — são atributos de
// apresentação. Os baralhos demo recebem categoria explícita para reproduzir a
// vitrine da referência; baralhos reais caem no default 'community'.
const DEMO_CATEGORY: Record<string, DeckCategory> = {
  'demo-constitucional': 'official',
  'demo-logico': 'community',
  'demo-portugues': 'official',
}

export function deckCategory(deck: SubscribableDeck): DeckCategory {
  return DEMO_CATEGORY[deck.deck_id] ?? 'community'
}

export function deckValidated(deck: SubscribableDeck): boolean {
  return deck.status === 'published' || deck.status === 'validated'
}

export function formatDeckDate(value: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  const month = new Intl.DateTimeFormat('pt-BR', { month: 'short' })
    .format(date)
    .replace('.', '')
  return `${date.getDate()} ${month} ${date.getFullYear()}`
}

export function MuriaeDeckCard({ deck }: { deck: SubscribableDeck }) {
  const navigate = useNavigate()
  const category = CATEGORY[deckCategory(deck)]
  const validated = deckValidated(deck)

  function open() {
    navigate(`/deck/${deck.deck_id}`)
  }

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={open}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          open()
        }
      }}
      className={cn(
        'flex cursor-pointer flex-col overflow-hidden rounded-[8px] border border-mu-border bg-mu-surface text-left',
        'shadow-[0_1px_2px_-1px_rgba(31,36,48,0.06),0_3px_8px_-3px_rgba(31,36,48,0.08)]',
        'transition-[border-color,box-shadow,transform] duration-200 ease-out',
        'hover:-translate-y-[3px] hover:border-mu-border-hover hover:shadow-[0_6px_12px_-3px_rgba(31,36,48,0.10),0_18px_32px_-10px_rgba(35,22,81,0.18)]',
        'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#231651]',
      )}
    >
      <div
        className={cn(
          'flex items-center justify-between border-b px-[18px] py-[10px]',
          category.strip,
        )}
      >
        <span className={cn('text-[11px] font-bold uppercase tracking-[0.06em]', category.text)}>
          {category.label}
        </span>
        <span
          className={cn(
            'inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-[0.04em] opacity-75',
            category.text,
          )}
        >
          {validated ? <Check size={11} weight="bold" /> : <Clock size={11} />}
          {validated ? 'Validado' : 'Em análise'}
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-2 px-[18px] pt-[18px]">
        <h3 className="font-dm-serif text-[18px] font-normal leading-[1.25] tracking-[-0.01em] text-mu-text">
          {deck.name}
        </h3>
        <p className="text-[13.5px] leading-[1.55] text-mu-muted">
          {deck.description || 'Baralho publicado na plataforma.'}
        </p>
      </div>

      <hr className="mx-[18px] mt-[14px] border-0 border-t border-dashed border-mu-border" />

      <div className="flex flex-col gap-[7px] px-[18px] py-3">
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-[7px] text-[12.5px] text-mu-muted [&>svg]:shrink-0 [&>svg]:text-mu-muted-2">
            <Stack size={14} />
            {deck.active_card_count.toLocaleString('pt-BR')} notas
          </span>
          {deck.subscribed && (
            <span className="inline-flex items-center gap-[5px] text-[12.5px] font-semibold text-mu-brand">
              <Check size={13} weight="bold" />
              Inscrito
            </span>
          )}
        </div>
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-[7px] text-[12.5px] text-mu-muted [&>svg]:shrink-0 [&>svg]:text-mu-muted-2">
            <ArrowClockwise size={14} />
            Versão {deck.latest_release}
          </span>
          <span className="text-[12.5px] text-mu-muted-2">{formatDeckDate(deck.updated_at)}</span>
        </div>
      </div>
    </article>
  )
}
