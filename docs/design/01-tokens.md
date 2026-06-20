# Design System — Tokens Canônicos

> **Fonte canônica:** `admin/tailwind.config.ts`
> **Referência visual:** site.HTML (Scrimba) — accent azul, Inter, Phosphor
> **Implementação:** Caio transcreve esta tabela para `tailwind.config.ts`; a issue downstream remove o `:root` duplicado de `index.css`.

---

## 1. Contexto

O design system do `admin/` estava fragmentado em três fontes conflitantes:

| Fonte | Primário | Fonte tipográfica | Status |
|---|---|---|---|
| `tailwind.config.ts` | `#acc7ff` (Material 3) | Hanken Grotesk | **Canônica — precisa ser atualizada** |
| `index.css :root` | `#a78bfa` (violeta) | Geist, Inter | Em uso hoje — será deprecada |
| `site.HTML` (ref.) | `#3b82f6` (azul) | Inter | Referência visual — direciona o redesign |

**Decisões fixadas por Luan (não reabrir):**
1. Fonte canônica → `admin/tailwind.config.ts`
2. Accent → `#3b82f6`, hover `#2563eb`
3. Tipografia → Inter (único)
4. Ícones → Phosphor (substitui `lucide-react`)

---

## 2. Paleta de Cores

### 2.1 Primitivos

Estes são os valores brutos que formam a base da paleta. Nunca referenciar diretamente nos componentes — usar os tokens semânticos abaixo.

| Nome | Hex | Uso referencial |
|---|---|---|
| `navy-950` | `#0f1117` | Camada mais profunda |
| `navy-900` | `#141720` | Sidebar / topbar overlay |
| `navy-850` | `#181b23` | Canvas principal (bg Scrimba) |
| `navy-800` | `#1d2029` | Superfície baixa |
| `navy-750` | `#22252d` | Superfície card (bg Scrimba card) |
| `navy-700` | `#2a2e38` | Borda padrão / hover bg (Scrimba border) |
| `gray-600` | `#374151` | Borda forte / outline focus |
| `gray-400` | `#9ca3af` | Texto secundário / ícones |
| `gray-300` | `#d1d5db` | Texto corpo (Scrimba text) |
| `white` | `#ffffff` | Títulos / texto primário |
| `blue-600` | `#3b82f6` | Accent principal |
| `blue-700` | `#2563eb` | Accent hover |
| `blue-900` | `#1e3a5f` | Container accent / tint |
| `blue-200` | `#93c5fd` | Texto info sobre fundo escuro |
| `green-400` | `#34d399` | Sucesso |
| `green-950` | `#052e25` | Container sucesso |
| `amber-400` | `#fbbf24` | Aviso |
| `amber-950` | `#3a2a05` | Container aviso |
| `red-400` | `#f87171` | Perigo / erro |
| `red-950` | `#3b1111` | Container perigo |
| `violet-500` | `#8b5cf6` | Tag PRO / papel admin |
| `violet-400` | `#a855f7` | Tag UPDATED |
| `red-500` | `#ef4444` | Tag HOT |

### 2.2 Tokens Semânticos → `tailwind.config.ts`

Esta é a tabela de transcrição para o Caio. Cada linha → uma entrada em `theme.extend.colors`.

#### Backgrounds

| Token Tailwind | Valor | Uso |
|---|---|---|
| `bg` | `#181b23` | Canvas da página (main content area) |
| `sidebar` | `#141720` | Fundo do sidebar |
| `surface` | `#22252d` | Cards, painéis, primeira elevação |
| `surface-high` | `#2a2e38` | Hover de superfície, segunda elevação |
| `surface-low` | `#1d2029` | Superfícies abaixo do canvas |
| `surface-lowest` | `#0f1117` | Superfície mais profunda (overlay topbar) |

#### Bordas

| Token Tailwind | Valor | Uso |
|---|---|---|
| `border` | `#2a2e38` | Borda padrão |
| `border-strong` | `#374151` | Borda forte / foco |

#### Texto

| Token Tailwind | Valor | Uso |
|---|---|---|
| `text` | `#ffffff` | Títulos, texto principal |
| `text-body` | `#d1d5db` | Texto corpo |
| `text-muted` | `#9ca3af` | Texto secundário / muted |
| `text-disabled` | `#6b7280` | Placeholder, desabilitado |

#### Primary / Accent

| Token Tailwind | Valor | Uso |
|---|---|---|
| `primary` | `#3b82f6` | Accent principal (azul) |
| `primary-hover` | `#2563eb` | Hover do accent |
| `primary-dim` | `#1e3a5f` | Container / tint do accent |

#### Semântico / Status

| Token Tailwind | Valor | Uso |
|---|---|---|
| `success` | `#34d399` | Foreground sucesso |
| `success-dim` | `#052e25` | Background container sucesso |
| `warning` | `#fbbf24` | Foreground aviso |
| `warning-dim` | `#3a2a05` | Background container aviso |
| `danger` | `#f87171` | Foreground perigo / erro |
| `danger-dim` | `#3b1111` | Background container perigo |
| `info` | `#93c5fd` | Foreground info (azul claro) |
| `info-dim` | `#1e3a5f` | Background container info |

#### Tags / Badges de tipo

Reusam o padrão visual PRO/HOT/FREE da referência Scrimba, adaptados para os papéis e tipos do domínio.

| Token Tailwind | Valor | Uso / Equivalência |
|---|---|---|
| `tag-pro` | `#8b5cf6` | Admin, PRO — violeta |
| `tag-hot` | `#ef4444` | HOT, danger variants — vermelho |
| `tag-free` | `#3b82f6` | FREE = primary — azul |
| `tag-updated` | `#a855f7` | UPDATED, revised — violeta claro |

---

## 3. Tipografia

### 3.1 Font family

**Decisão:** Inter em todas as hierarquias. Remover Hanken Grotesk e Geist do projeto.

```ts
// tailwind.config.ts
fontFamily: {
  sans: [
    'Inter',
    'ui-sans-serif',
    'system-ui',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
  ],
}
```

O carregamento da fonte no `index.html` (ou CSS) deve usar Google Fonts ou self-hosted:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```

### 3.2 Escala tipográfica

| Nível | Tamanho | Line-height | Tracking | Peso | Uso |
|---|---|---|---|---|---|
| **Display** | 36px | 44px | -0.02em | 700 | Títulos de hero / dashboard |
| **Heading-L** | 28px | 36px | -0.01em | 700 | Títulos de página principais |
| **Heading-M** | 24px | 32px | -0.01em | 600 | Seções principais |
| **Heading-S** | 20px | 28px | 0 | 600 | Subseções, card titles |
| **Body-L** | 16px | 24px | 0 | 400 | Texto corpo principal |
| **Body-M** | 14px | 20px | 0 | 400 | Texto corpo secundário |
| **Body-S** | 13px | 20px | 0 | 400 | Texto compacto (sidebar) |
| **Label** | 12px | 16px | +0.04em | 600 | Labels de campo, nomes em tabelas |
| **Caption** | 11px | 16px | +0.08em | 600 | Cabeçalhos de tabela, metadados |
| **Micro** | 9px | 12px | +0.12em | 800 | Eyebrow / tag text (UPPERCASE) |

---

## 4. Espaçamento

Base unit: **4px**. Usar escala Tailwind padrão (1 = 4px, 2 = 8px, etc.).

Valores customizados para adicionar ao `tailwind.config.ts`:

| Token Tailwind | Valor | Uso |
|---|---|---|
| `sidebar` | `256px` | Largura do sidebar (desktop) |
| `topbar` | `62px` | Altura do topbar |

---

## 5. Raios de borda

Substituir os raios atuais (Material 3) pelos seguintes:

```ts
// tailwind.config.ts
borderRadius: {
  'sm':    '6px',    // inputs small, badges, row-actions
  DEFAULT: '8px',    // botões, campos de formulário, cards compactos
  'lg':    '12px',   // cards médios, painéis
  'xl':    '16px',   // cards maiores, deck cards
  '2xl':   '20px',   // modal, deck hero
  'full':  '9999px', // pills, tags redondas, avatares
}
```

---

## 6. Sombras

```ts
// tailwind.config.ts (boxShadow)
boxShadow: {
  'sm':  '0 1px 3px rgba(0, 0, 0, 0.30)',
  DEFAULT: '0 4px 12px rgba(0, 0, 0, 0.35)',
  'lg':  '0 8px 24px rgba(0, 0, 0, 0.40)',
  'xl':  '0 16px 40px rgba(0, 0, 0, 0.45)',
  'glow-primary': '0 0 14px rgba(59, 130, 246, 0.35)',
  'glow-success': '0 0 10px rgba(52, 211, 153, 0.45)',
}
```

---

## 7. `tailwind.config.ts` completo após migração

```ts
import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Backgrounds
        'bg':             '#181b23',
        'sidebar':        '#141720',
        'surface':        '#22252d',
        'surface-high':   '#2a2e38',
        'surface-low':    '#1d2029',
        'surface-lowest': '#0f1117',
        // Borders
        'border':         '#2a2e38',
        'border-strong':  '#374151',
        // Text
        'text':           '#ffffff',
        'text-body':      '#d1d5db',
        'text-muted':     '#9ca3af',
        'text-disabled':  '#6b7280',
        // Accent
        'primary':        '#3b82f6',
        'primary-hover':  '#2563eb',
        'primary-dim':    '#1e3a5f',
        // Semantic
        'success':        '#34d399',
        'success-dim':    '#052e25',
        'warning':        '#fbbf24',
        'warning-dim':    '#3a2a05',
        'danger':         '#f87171',
        'danger-dim':     '#3b1111',
        'info':           '#93c5fd',
        'info-dim':       '#1e3a5f',
        // Tags
        'tag-pro':        '#8b5cf6',
        'tag-hot':        '#ef4444',
        'tag-free':       '#3b82f6',
        'tag-updated':    '#a855f7',
      },
      fontFamily: {
        sans: [
          'Inter', 'ui-sans-serif', 'system-ui', '-apple-system',
          'BlinkMacSystemFont', '"Segoe UI"', 'Roboto',
          '"Helvetica Neue"', 'Arial', 'sans-serif',
        ],
      },
      borderRadius: {
        'sm':    '6px',
        DEFAULT: '8px',
        'lg':    '12px',
        'xl':    '16px',
        '2xl':   '20px',
        'full':  '9999px',
      },
      boxShadow: {
        'sm':           '0 1px 3px rgba(0,0,0,0.30)',
        DEFAULT:        '0 4px 12px rgba(0,0,0,0.35)',
        'lg':           '0 8px 24px rgba(0,0,0,0.40)',
        'xl':           '0 16px 40px rgba(0,0,0,0.45)',
        'glow-primary': '0 0 14px rgba(59,130,246,0.35)',
        'glow-success': '0 0 10px rgba(52,211,153,0.45)',
      },
      spacing: {
        'sidebar': '256px',
        'topbar':  '62px',
      },
      maxWidth: {
        container: '1280px',
      },
    },
  },
} satisfies Config
```

---

## 8. Tokens eliminados

Os seguintes tokens do `tailwind.config.ts` atual são **Material 3** e devem ser removidos:

- Todos os `surface-container-*`, `on-surface`, `on-surface-variant`, `on-background`
- `inverse-surface`, `inverse-on-surface`, `inverse-primary`
- `primary-fixed`, `primary-fixed-dim`, `on-primary-fixed`, `on-primary-fixed-variant`
- `secondary-*` (Material 3), `tertiary-*`
- `on-primary`, `on-secondary`, `on-tertiary`, `on-error`
- `error-container`, `on-error-container`
- `secondary-fixed-*`, `tertiary-fixed-*`
- `surface-tint`, `surface-variant`
- `surface-dim`, `surface-bright`

Os valores de tipografia Material 3 (`headline-*`, `label-*`, `body-*` como font families e como fontSize entries com nomes compostos) são também eliminados — substituídos pela escala Inter simples.
