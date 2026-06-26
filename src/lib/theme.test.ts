import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { applyTheme, getStoredTheme, initTheme, setTheme } from './theme'

describe('theme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  afterEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('defaults to light when nothing is stored', () => {
    expect(getStoredTheme()).toBe('light')
  })

  it('reads a stored dark preference', () => {
    localStorage.setItem('anki-concursos-theme', 'dark')
    expect(getStoredTheme()).toBe('dark')
  })

  it('applyTheme sets the data-theme attribute', () => {
    applyTheme('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('setTheme persists and applies the choice', () => {
    setTheme('dark')
    expect(localStorage.getItem('anki-concursos-theme')).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    setTheme('light')
    expect(localStorage.getItem('anki-concursos-theme')).toBe('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('initTheme applies the stored preference', () => {
    localStorage.setItem('anki-concursos-theme', 'dark')
    expect(initTheme()).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })
})
