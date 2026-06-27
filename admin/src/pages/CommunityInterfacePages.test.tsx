import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { apiRequest } from '../api/client'
import { AdminSuggestionsPage, DeckPage } from './CommunityInterfacePages'
import { fallbackDecks, fallbackNotes } from '../data/communityData'

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

const pendingSuggestion = {
  suggestion_id: 'sug-1',
  deck_id: 'deck-1',
  card_id: 'card-1',
  public_id: 'AC-001',
  card_version_id: 'ver-1',
  version_number: 3,
  submitted_by_user_id: 'user-1',
  submitted_by_email: 'maria.silva@example.com',
  suggestion_type: 'spelling/grammar',
  status: 'pending',
  fields: { Front: { old: 'glicose', new: '<b>glicose</b>' } },
  added_tags: ['novo'],
  removed_tags: [],
  comment: 'Corrigir destaque',
  source: 'addon',
  reviewed_by: null,
  review_comment: null,
  reviewed_at: null,
  resulting_card_version_id: null,
  created_at: '2026-06-27T10:00:00Z',
  updated_at: '2026-06-27T10:00:00Z',
}

const emptyList = { items: [], page: 1, page_size: 100, total: 0, pages: 0 }

vi.mock('../api/client', () => ({
  apiRequest: vi.fn(async (path: string, options?: RequestInit) => {
    if (path.includes('/admin/note-suggestions/') && options?.method === 'POST') {
      return { ...pendingSuggestion, status: 'accepted' }
    }
    if (path.includes('/admin/note-suggestions?status=pending')) {
      return { items: [pendingSuggestion], page: 1, page_size: 100, total: 1, pages: 1 }
    }
    if (path.includes('/admin/note-suggestions')) {
      return emptyList
    }
    if (path.includes('/subscriptions/decks')) {
      return { items: fallbackDecks }
    }
    if (path.includes('/subscriptions/') && options?.method === 'POST') {
      return {
        subscription_id: 'sub-1',
        deck_id: 'demo-constitucional',
        deck_name: 'Direito Constitucional',
        latest_release: 18,
        active_card_count: 1200,
        subscribed_at: '2026-06-01T12:00:00Z',
        unsubscribed_at: path.endsWith('/cancel')
          ? '2026-06-26T12:00:00Z'
          : null,
      }
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

  it('lists pending suggestions from the backend with a diff', async () => {
    renderPage()

    expect(
      await screen.findByText('maria.silva@example.com'),
    ).toBeInTheDocument()
    expect(screen.getByText('Ortografia/Gramática')).toBeInTheDocument()
    expect(screen.getByText('Corrigir destaque')).toBeInTheDocument()
    // diff renders both sides
    expect(screen.getByText('Atual')).toBeInTheDocument()
    expect(screen.getByText('Sugerido')).toBeInTheDocument()
  })

  it('accepts a suggestion through the review endpoint', async () => {
    const apiRequestMock = vi.mocked(apiRequest)
    apiRequestMock.mockClear()

    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: /aceitar/i }))

    await waitFor(() =>
      expect(apiRequestMock).toHaveBeenCalledWith(
        '/admin/note-suggestions/sug-1/review',
        expect.objectContaining({ method: 'POST' }),
        null,
      ),
    )
  })

  it('rejects a suggestion through the review endpoint', async () => {
    const apiRequestMock = vi.mocked(apiRequest)
    apiRequestMock.mockClear()

    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: /rejeitar/i }))

    await waitFor(() => {
      const call = apiRequestMock.mock.calls.find(
        ([path]) => path === '/admin/note-suggestions/sug-1/review',
      )
      expect(call).toBeTruthy()
      expect(JSON.parse((call![1] as RequestInit).body as string).status).toBe(
        'rejected',
      )
    })
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

  it('cancels a subscription through the backend cancel endpoint', async () => {
    const apiRequestMock = vi.mocked(apiRequest)
    apiRequestMock.mockClear()

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <MemoryRouter initialEntries={['/deck/demo-constitucional']}>
          <Routes>
            <Route path="/deck/:deckId" element={<DeckPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )

    fireEvent.click(await screen.findByRole('button', { name: /desinscrever/i }))

    await waitFor(() =>
      expect(apiRequestMock).toHaveBeenCalledWith(
        '/subscriptions/demo-constitucional/cancel',
        { method: 'POST' },
        null,
      ),
    )
  })
})
