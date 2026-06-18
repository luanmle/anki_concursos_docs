import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { AdminSuggestionsPage } from './CommunityInterfacePages'

const STORAGE_KEY = 'anki-concursos-suggestions'

describe('AdminSuggestionsPage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    cleanup()
  })

  it('marks a suggestion as converted to a new version', () => {
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

    render(<AdminSuggestionsPage />)

    fireEvent.click(screen.getByRole('button', { name: /converter em nova versão/i }))

    expect(screen.getByText('Convertido em nova versão')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /converter em nova versão/i }),
    ).toBeDisabled()
  })

  it('marks a suggestion as rejected', () => {
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

    render(<AdminSuggestionsPage />)

    fireEvent.click(screen.getByRole('button', { name: /rejeitar/i }))

    expect(screen.getByText('Rejeitado')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /rejeitar/i })).toBeDisabled()
  })
})
