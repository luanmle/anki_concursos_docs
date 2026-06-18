import type { AnkiSyncChange, SubscribableDeck } from '../types'

export type CommentKind = 'comment' | 'tip' | 'mnemonic' | 'question' | 'correction'

export interface StudentComment {
  id: string
  publicId: string
  author: string
  kind: CommentKind
  body: string
  score: number
  createdAt: string
}

export interface StudentSuggestion {
  id: string
  deckId: string
  cardId?: string
  publicId: string
  changeType: string
  message: string
  proposedFields: Record<string, string>
  status: 'pending' | 'converted_to_new_version' | 'rejected'
  resultingCardVersionId?: string | null
  createdAt: string
}

export const fallbackDecks: SubscribableDeck[] = [
  {
    deck_id: 'demo-constitucional',
    name: 'Direito Constitucional',
    description:
      'Artigo 5o, direitos e garantias fundamentais, organizacao do Estado e poderes da Uniao.',
    discipline_id: null,
    status: 'published',
    active_card_count: 1200,
    latest_release: 18,
    subscribed: true,
    created_at: '2026-06-01T12:00:00Z',
    updated_at: '2026-06-16T12:00:00Z',
  },
  {
    deck_id: 'demo-logico',
    name: 'Raciocinio Logico',
    description:
      'Proposicoes logicas, tabelas-verdade, equivalencias e diagramas logicos complexos.',
    discipline_id: null,
    status: 'published',
    active_card_count: 850,
    latest_release: 7,
    subscribed: false,
    created_at: '2026-06-02T12:00:00Z',
    updated_at: '2026-06-12T12:00:00Z',
  },
  {
    deck_id: 'demo-portugues',
    name: 'Lingua Portuguesa',
    description:
      'Sintaxe, morfologia, crase, concordancia verbal e interpretacao de texto.',
    discipline_id: null,
    status: 'published',
    active_card_count: 2100,
    latest_release: 11,
    subscribed: false,
    created_at: '2026-06-03T12:00:00Z',
    updated_at: '2026-06-15T12:00:00Z',
  },
]

export const fallbackNotes: AnkiSyncChange[] = [
  {
    release_id: 'demo-release',
    release_number: 18,
    published_at: '2026-06-16T12:00:00Z',
    action: 'added',
    card_id: 'demo-card-1',
    public_id: 'AC-CONST-0001',
    old_card_version_id: null,
    new_card_version_id: 'demo-version-1',
    card_kind: 'basic',
    note_type: 'Anki Concursos Basic',
    fields: {
      Front: 'Qual remédio constitucional protege a liberdade de locomoção?',
      Back: 'Habeas corpus.',
      Answer: 'Habeas corpus.',
      Explanation:
        'O habeas corpus protege a liberdade de locomoção quando alguém sofre ou se acha ameaçado de sofrer violência ou coação ilegal.',
    },
    tags: ['deck::demo-constitucional', 'card::AC-CONST-0001'],
  },
  {
    release_id: 'demo-release',
    release_number: 18,
    published_at: '2026-06-16T12:00:00Z',
    action: 'added',
    card_id: 'demo-card-2',
    public_id: 'AC-CONST-0002',
    old_card_version_id: null,
    new_card_version_id: 'demo-version-2',
    card_kind: 'cloze',
    note_type: 'Anki Concursos Cloze',
    fields: {
      Text: 'A Constituição admite {{c1::habeas corpus}} para proteger a liberdade de locomoção.',
      Extra: 'Art. 5o, LXVIII, CF.',
      Answer: 'Habeas corpus.',
      Explanation: 'O cloze preserva a memorização ativa do instituto jurídico.',
    },
    tags: ['deck::demo-constitucional', 'card::AC-CONST-0002'],
  },
]

export const initialComments: StudentComment[] = [
  {
    id: 'comment-1',
    publicId: 'AC-CONST-0001',
    author: 'Mariana S.',
    kind: 'mnemonic',
    body: 'Macete: HC = Habeas Corpus = Caminhar. Sempre associe com liberdade de ir e vir.',
    score: 24,
    createdAt: '2026-06-15T13:30:00Z',
  },
  {
    id: 'comment-2',
    publicId: 'AC-CONST-0001',
    author: 'Joao P.',
    kind: 'tip',
    body: 'A banca costuma cobrar a diferença entre habeas corpus preventivo e repressivo.',
    score: 17,
    createdAt: '2026-06-15T14:10:00Z',
  },
]

export const changeTypes = [
  'Novo conteudo',
  'Ortografia/Gramatica',
  'Erro de conteudo',
  'Novo cartao para adicionar',
  'Novas tags',
  'Tags atualizadas',
  'Excluir nota',
  'Outro',
]
