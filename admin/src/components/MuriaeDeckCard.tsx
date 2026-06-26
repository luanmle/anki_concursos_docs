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
    strip: 'bg-[#eeebfa] border-b-[rgba(35,22,81,0.18)]',
    text: 'text-[#231651]',
    badge: 'bg-[#eeebfa] border-[rgba(35,22,81,0.18)] text-[#231651]',
  },
  community: {
    label: 'Comunidade',
    strip: 'bg-[oklch(0.95_0.04_220)] border-b-[oklch(0.82_0.07_220)]',
    text: 'text-[oklch(0.42_0.14_220)]',
    badge: 'bg-[oklch(0.95_0.04_220)] border-[oklch(0.82_0.07_220)] text-[oklch(0.42_0.14_220)]',
  },
  ai: {
    label: 'IA',
    strip: 'bg-[oklch(0.97_0.05_60)] border-b-[oklch(0.84_0.1_56)]',
    text: 'text-[oklch(0.44_0.16_52)]',
    badge: 'bg-[oklch(0.97_0.05_60)] border-[oklch(0.84_0.1_56)] text-[oklch(0.44_0.16_52)]',
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
        'flex cursor-pointer flex-col overflow-hidden rounded-[8px] border border-[#e4e1da] bg-white text-left',
        'shadow-[0_1px_2px_-1px_rgba(31,36,48,0.06),0_3px_8px_-3px_rgba(31,36,48,0.08)]',
        'transition-[border-color,box-shadow,transform] duration-200 ease-out',
        'hover:-translate-y-[3px] hover:border-[#cdc6ba] hover:shadow-[0_6px_12px_-3px_rgba(31,36,48,0.10),0_18px_32px_-10px_rgba(35,22,81,0.18)]',
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
        <h3 className="font-dm-serif text-[18px] font-normal leading-[1.25] tracking-[-0.01em] text-[#1f2430]">
          {deck.name}
        </h3>
        <p className="text-[13.5px] leading-[1.55] text-[#667085]">
          {deck.description || 'Baralho publicado na plataforma.'}
        </p>
      </div>

      <hr className="mx-[18px] mt-[14px] border-0 border-t border-dashed border-[#e4e1da]" />

      <div className="flex flex-col gap-[7px] px-[18px] py-3">
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-[7px] text-[12.5px] text-[#667085] [&>svg]:shrink-0 [&>svg]:text-[#98a2b3]">
            <Stack size={14} />
            {deck.active_card_count.toLocaleString('pt-BR')} notas
          </span>
          {deck.subscribed && (
            <span className="inline-flex items-center gap-[5px] text-[12.5px] font-semibold text-[#231651]">
              <Check size={13} weight="bold" />
              Inscrito
            </span>
          )}
        </div>
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-[7px] text-[12.5px] text-[#667085] [&>svg]:shrink-0 [&>svg]:text-[#98a2b3]">
            <ArrowClockwise size={14} />
            Versão {deck.latest_release}
          </span>
          <span className="text-[12.5px] text-[#98a2b3]">{formatDeckDate(deck.updated_at)}</span>
        </div>
      </div>
    </article>
  )
}
