import { Moon, Sun } from '@phosphor-icons/react'
import { useState } from 'react'
import { getStoredTheme, setTheme, type Theme } from '../lib/theme'
import { Button } from './ui/button'

export function ThemeToggle() {
  const [theme, setThemeState] = useState<Theme>(getStoredTheme)
  const isDark = theme === 'dark'

  function toggle() {
    const next: Theme = isDark ? 'light' : 'dark'
    setTheme(next)
    setThemeState(next)
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className="muriae-theme-toggle"
      aria-label={isDark ? 'Ativar modo claro' : 'Ativar modo noturno'}
      aria-pressed={isDark}
      onClick={toggle}
    >
      {isDark ? <Sun size={18} weight="fill" /> : <Moon size={18} />}
    </Button>
  )
}
