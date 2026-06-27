import type { NoteSuggestionStatus, NoteSuggestionType } from '../../types'

export const SUGGESTION_TYPE_LABEL: Record<NoteSuggestionType, string> = {
  updated_content: 'Conteúdo atualizado',
  new_content: 'Novo conteúdo',
  'spelling/grammar': 'Ortografia/Gramática',
  content_error: 'Erro de conteúdo',
  new_card_to_add: 'Novo cartão',
  new_tags: 'Novas tags',
  updated_tags: 'Tags atualizadas',
  delete: 'Exclusão',
  other: 'Outro',
}

export const SUGGESTION_STATUS_LABEL: Record<NoteSuggestionStatus, string> = {
  pending: 'Aguardando',
  accepted: 'Aceita',
  rejected: 'Rejeitada',
}
