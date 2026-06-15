import { describe, expect, it } from 'vitest'
import { cardCreateSchema, cardVersionSchema } from './card-form-schema'

const content = {
  front_text: 'Pergunta',
  back_text: 'Verso',
  answer_text: 'Resposta',
  explanation_text: 'Explicação',
}

describe('card form schemas', () => {
  it('accepts a complete initial card', () => {
    const result = cardCreateSchema.safeParse({
      canonical_key: 'direito-constitucional',
      discipline_id: '11111111-1111-4111-8111-111111111111',
      topic_id: '22222222-2222-4222-8222-222222222222',
      ...content,
      change_reason: 'Versão inicial',
    })

    expect(result.success).toBe(true)
  })

  it('requires every pedagogical content field', () => {
    const result = cardCreateSchema.safeParse({
      canonical_key: 'direito-constitucional',
      discipline_id: '11111111-1111-4111-8111-111111111111',
      topic_id: '22222222-2222-4222-8222-222222222222',
      ...content,
      answer_text: ' ',
      change_reason: 'Versão inicial',
    })

    expect(result.success).toBe(false)
  })

  it('requires a change reason for a new version', () => {
    const result = cardVersionSchema.safeParse({
      ...content,
      change_reason: '',
    })

    expect(result.success).toBe(false)
  })
})
