export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'anki-concursos-theme'

/** Tema salvo pelo usuário; padrão claro (ignora preferência do SO por escolha de produto). */
export function getStoredTheme(): Theme {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

/** Aplica o tema no documento (lido pelos tokens --mu-* escopados em .app-shell). */
export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme)
}

/** Persiste e aplica o tema escolhido. */
export function setTheme(theme: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    /* localStorage indisponível — segue só com o atributo aplicado */
  }
  applyTheme(theme)
}

/** Lê o tema salvo e aplica antes da primeira pintura (chamado no bootstrap). */
export function initTheme(): Theme {
  const theme = getStoredTheme()
  applyTheme(theme)
  return theme
}
