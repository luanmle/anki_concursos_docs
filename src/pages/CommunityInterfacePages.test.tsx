import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminSuggestionsPage, DeckPage } from './CommunityInterfacePages'
import { fallbackDecks, fallbackNotes } from '../data/communityData'

const STORAGE_KEY = 'anki-concursos-suggestions'
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(async (path: string) => {
    if (path.includes('/subscriptions/decks')) {
      return { items: fallbackDecks }
    }
    if (path.includes('/addon/decks/')) {
      return { changes: fallbackNotes }
    }
    throw new Error(`Unexpected request: ${path}`)
  }),
}))

vi.mock('../auth/auth-context', () => ({
  useAuth: () => ({
    token: null,
    user: null,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    hasRole: vi.fn(() => true),
  }),
}))

describe('AdminSuggestionsPage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    cleanup()
  })

  function renderPage() {
    return render(
      <QueryClientProvider client={createTestQueryClient()}>
        <AdminSuggestionsPage />
      </QueryClientProvider>,
    )
  }

  it('marks a suggestion as converted to a new version', async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify([
        {
          id: 'suggestion-1',
          deckId: 'deck-1',
          publicId: 'AC-001',
          changeType: 'Erro de conteudo',
          message: 'Ajustar a explicacao',
          proposedFields: {},
          status: 'pending',
          createdAt: '2026-06-17T10:00:00Z',
        },
      ]),
    )

    renderPage()

    fireEvent.click(screen.getByRole('button', { name: /converter/i }))

    await waitFor(() =>
      expect(screen.getByTitle('converted_to_new_version')).toBeInTheDocument(),
    )
    expect(screen.getByRole('button', { name: /converter/i })).toBeDisabled()
  })

  it('marks a suggestion as rejected', async () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify([
        {
          id: 'suggestion-2',
          deckId: 'deck-1',
          publicId: 'AC-002',
          changeType: 'Ortografia/Gramatica',
          message: 'Corrigir acento',
          proposedFields: {},
          status: 'pending',
          createdAt: '2026-06-17T10:00:00Z',
        },
      ]),
    )

    renderPage()

    fireEvent.click(screen.getByRole('button', { name: /rejeitar/i }))

    await waitFor(() => expect(screen.getByTitle('rejected')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /rejeitar/i })).toBeDisabled()
  })
})

describe('DeckPage comments panel', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    cleanup()
  })

  it('shows a unified comment entry and chronological feed without filters', async () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter initialEntries={['/deck/demo-constitucional']}>
          <Routes>
            <Route path="/deck/:deckId" element={<DeckPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    fireEvent.click(await screen.findByRole('button', { name: /Qual rem/i }))
    fireEvent.click(screen.getByRole('button', { name: /coment/i }))

    expect(screen.getByPlaceholderText(/escreva um comentário sobre esta nota/i)).toBeInTheDocument()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /todos/i })).not.toBeInTheDocument()
    expect(screen.getByText(/Mariana S\./i)).toBeInTheDocument()
    expect(screen.getByText(/Joao P\./i)).toBeInTheDocument()
  })
})

