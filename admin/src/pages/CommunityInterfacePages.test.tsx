import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AdminSuggestionsPage } from './CommunityInterfacePages'

const STORAGE_KEY = 'anki-concursos-suggestions'
const queryClient = new QueryClient()

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
      <QueryClientProvider client={queryClient}>
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

    fireEvent.click(screen.getByRole('button', { name: /converter em nova versão/i }))

    await waitFor(() =>
      expect(screen.getByTitle('converted_to_new_version')).toBeInTheDocument(),
    )
    expect(screen.getByRole('button', { name: /converter em nova versão/i })).toBeDisabled()
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
