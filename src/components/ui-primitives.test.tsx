import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { translateStatus } from '../lib/presentation'
import { StatusBadge } from './ui-primitives'

describe('status presentation', () => {
  it('translates known API states', () => {
    expect(translateStatus('needs_review')).toBe('Precisa de revisão')
  })

  it('keeps the technical value available as a title', () => {
    render(<StatusBadge value="published" />)
    expect(screen.getByText('Publicado')).toHaveAttribute('title', 'published')
  })
})
