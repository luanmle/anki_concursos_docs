import { z } from 'zod'

const contentFields = {
  front_text: z.string().trim().min(1, 'Informe a frente do cartão.').max(20_000),
  back_text: z.string().trim().min(1, 'Informe o verso do cartão.').max(20_000),
  answer_text: z.string().trim().min(1, 'Informe a resposta.').max(20_000),
  explanation_text: z
    .string()
    .trim()
    .min(1, 'Informe a explicação.')
    .max(20_000),
}

export const cardCreateSchema = z.object({
  canonical_key: z
    .string()
    .trim()
    .min(1, 'Informe a chave canônica.')
    .max(255),
  discipline_id: z.string().uuid('Selecione uma disciplina.'),
  topic_id: z.string().uuid('Selecione um assunto.'),
  ...contentFields,
  change_reason: z.string().trim().min(1).max(2_000),
})

export const cardVersionSchema = z.object({
  ...contentFields,
  change_reason: z
    .string()
    .trim()
    .min(1, 'Informe o motivo da alteração.')
    .max(2_000),
})

export type CardCreateValues = z.infer<typeof cardCreateSchema>
export type CardVersionValues = z.infer<typeof cardVersionSchema>
