import type { NoteSuggestionType } from '../../types'

export const CHANGE_TYPE_TO_ENUM: Record<string, NoteSuggestionType> = {
  'Novo conteúdo': 'new_content',
  'Ortografia/Gramática': 'spelling/grammar',
  'Erro de conteúdo': 'content_error',
  'Novo cartão para adicionar': 'new_card_to_add',
  'Novas tags': 'new_tags',
  'Tags atualizadas': 'updated_tags',
  'Excluir nota': 'delete',
  Outro: 'other',
}

export function mapChangeType(label: string): NoteSuggestionType {
  return CHANGE_TYPE_TO_ENUM[label] ?? 'other'
}

/**
 * Só os campos que mudaram, no formato `{old,new}` consumido pelo DiffViewer.
 */
export function buildChangedFields(
  original: Record<string, string>,
  edited: Record<string, string>,
): Record<string, { old: string; new: string }> {
  return Object.fromEntries(
    Object.entries(edited).flatMap(([name, value]) => {
      const before = original?.[name] ?? ''
      return value === before ? [] : [[name, { old: before, new: value }]]
    }),
  )
}
