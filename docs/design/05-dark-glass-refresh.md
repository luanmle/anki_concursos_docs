# Spec Visual — Dark Glassmorphism Refresh

> **Issue:** ANK-10 / ANK-8
> **Responsável pela spec:** Sofia
> **Responsável pela implementação:** Caio
> **Branch de spec:** `feat/ui-spec-dark-glass`
> **Base canônica:** `docs/design/01-tokens.md`, `docs/design/03-primitives.md`

---

## 1. Contexto e objetivo

Esta spec estende o sistema visual dark já existente (`01-tokens.md`) com uma camada de glassmorphism **sutil** para o console administrativo. O objetivo não é decoração — é criar hierarquia visual perceptível: sidebar e topbar flutuam sobre o conteúdo, modais pousam sobre a interface toda.

**O que muda:**
- Sidebar, topbar e modais ganham fundo semi-transparente com `backdrop-filter: blur`
- Sidebar passa a suportar estado colapsado (64px, ícones apenas) e expandido (256px)
- Superfícies elevadas ganham borda de luz sutil (`rgba(255,255,255,0.08)`)

**O que não muda:**
- Paleta, tipografia, espaçamento, raios — tudo permanece igual ao `01-tokens.md`
- Componentes internos (Button, StatusBadge, Tabs) — sem alteração
- Nenhuma mudança em backend ou API

**Princípio central: o glassmorphism é funcional, não decorativo.** Se remover o blur não romper a hierarquia visual percebida, está sendo usado de forma errada.

---

## 2. Glass surface tokens — adições ao sistema

### 2.1 CSS custom properties (adicionar ao `:root` em `index.css`)

```css
/* Glass surfaces — dark glassmorphism */
--glass-sidebar:       rgba(20, 23, 32, 0.85);
--glass-topbar:        rgba(24, 27, 35, 0.80);
--glass-elevated:      rgba(34, 37, 45, 0.75);
--glass-modal:         rgba(20, 23, 32, 0.92);
--glass-tooltip:       rgba(24, 27, 35, 0.95);
--glass-overlay:       rgba(0, 0, 0, 0.68);
--glass-border:        rgba(255, 255, 255, 0.07);
--glass-border-strong: rgba(255, 255, 255, 0.12);
```

### 2.2 `tailwind.config.ts` — additions

Adicionar dentro de `theme.extend.colors`:

```ts
// Glass — dark glassmorphism
'glass-sidebar':        'var(--glass-sidebar)',
'glass-topbar':         'var(--glass-topbar)',
'glass-elevated':       'var(--glass-elevated)',
'glass-modal':          'var(--glass-modal)',
'glass-tooltip':        'var(--glass-tooltip)',
'glass-overlay':        'var(--glass-overlay)',
'glass-border':         'var(--glass-border)',
'glass-border-strong':  'var(--glass-border-strong)',
```

Adicionar dentro de `theme.extend` (backdrop-blur customizado):

```ts
backdropBlur: {
  'xs':  '4px',
  'sm':  '8px',
  'md':  '14px',
  'lg':  '20px',
  'xl':  '28px',
  '2xl': '40px',
},
```

Adicionar dentro de `theme.extend` (transição da sidebar):

```ts
transitionProperty: {
  'sidebar': 'width, min-width',
},
transitionDuration: {
  '250': '250ms',
},
transitionTimingFunction: {
  'sidebar': 'cubic-bezier(0.4, 0, 0.2, 1)',
},
```

### 2.3 Razões de contraste — WCAG AA

Todos calculados considerando o fundo efetivo após composição (glass sobre `#181b23`).

| Texto | Superfície | Razão calculada | Status |
|---|---|---|---|
| `#ffffff` (text) | glass-sidebar (~`#141720`) | 19.2:1 | ✓ AAA |
| `#ffffff` (text) | glass-topbar (~`#181b23`) | 17.3:1 | ✓ AAA |
| `#ffffff` (text) | glass-modal (~`#141720`) | 19.2:1 | ✓ AAA |
| `#d1d5db` (text-body) | glass-elevated (~`#1e2229`) | 10.6:1 | ✓ AAA |
| `#9ca3af` (text-muted) | glass-sidebar (~`#141720`) | 7.8:1 | ✓ AA |
| `#9ca3af` (text-muted) | glass-tooltip (~`#181b23`) | 7.1:1 | ✓ AA |
| `#3b82f6` (primary) | glass-sidebar (~`#141720`) | 5.1:1 | ✓ AA |

> O glassmorphism escuro sobre fundo escuro preserva contraste muito acima do mínimo AA (4.5:1) porque a transparência revela um fundo igualmente escuro — sem degradação de contraste.

---

## 3. App Shell — layout com glassmorphism

```
╔════════════════════════════════════════════════════════════╗
║ TOPBAR (62px) — glass: blur-sm, glass-topbar bg            ║
╠════════════════════╦═══════════════════════════════════════╣
║ SIDEBAR (256/64px) ║ MAIN CONTENT AREA                     ║
║ glass: blur-md     ║ bg: #181b23                           ║
║ glass-sidebar bg   ║                                        ║
║                    ║ <PageContent />                        ║
║                    ║                                        ║
║                    ║                                        ║
╚════════════════════╩═══════════════════════════════════════╝
```

### 3.1 Topbar glass

| Propriedade | Valor |
|---|---|
| Background | `var(--glass-topbar)` |
| Backdrop-filter | `blur(8px) saturate(1.1)` |
| Border-bottom | `1px solid var(--glass-border)` |
| Position | `sticky` top-0, `z-index: 50` |
| Height | 62px (`spacing.topbar`) |
| Padding | `0 24px` |

**Shimmer rule:** a borda inferior `1px solid rgba(255,255,255,0.07)` cria o efeito de borda de luz que sinaliza que o topbar está "acima" do conteúdo. Não usar `border-color: #2a2e38` no topbar — o glass border substitui.

**Tailwind classes:**
```tsx
<header className="sticky top-0 z-50 h-topbar flex items-center px-6
                   bg-glass-topbar backdrop-blur-sm border-b border-glass-border">
```

### 3.2 Sidebar glass (estado expandido)

| Propriedade | Valor |
|---|---|
| Background | `var(--glass-sidebar)` |
| Backdrop-filter | `blur(14px) saturate(1.2)` |
| Border-right | `1px solid var(--glass-border)` |
| Width | `256px` |
| Position | `fixed` left-0 top-0 bottom-0, `z-index: 40` |
| Padding | `20px 14px` |

**Tailwind classes:**
```tsx
<nav className="fixed inset-y-0 left-0 z-40 flex flex-col
                w-sidebar bg-glass-sidebar backdrop-blur-md border-r border-glass-border">
```

---

## 4. Sidebar recolhível — especificação completa

### 4.1 Dois estados

#### Estado EXPANDIDO (padrão)

```
┌──────────────────────────────────┐   width: 256px
│                                  │
│  ●  Anki Concursos               │   ← Brand: logo 32×32px + nome
│     ADMIN                        │        nome: 14px/700; env: 10px/600/uppercase/muted
│ ─────────────────────────────── │   ← Divisor: 1px solid glass-border
│                                  │
│  ⊞  Visão Geral                  │   ← NavItem: icon 20px + label 13px/600
│  □  Cartões          ◀ ativo    │   ← NavItem ativo: text-primary, bg #1e2a3f
│  ◫  Decks                        │
│  ⚑  Reports                      │
│  ◷  Operação                     │
│  ◎  Usuários                     │   ← admin only
│                                  │
│ ─────────────────────────────── │   ← Divisor
│                                  │
│  [AV] Nome do Usuário  [→ sair]  │   ← Footer: avatar 32px + nome + logout
│       CURADOR                    │        role badge abaixo do nome
│                                  │
│  [⊣ Recolher sidebar]            │   ← Toggle button (ver §4.2)
└──────────────────────────────────┘
```

#### Estado COLAPSADO

```
┌──────────┐   width: 64px
│          │
│    ●     │   ← Logo 32×32px, centralizado (sem texto)
│          │
│  ──────  │
│          │
│    ⊞     │   ← Ícone 20px, centralizado
│    □  ◀  │   ← Ícone ativo: text-primary
│    ◫     │
│    ⚑     │
│    ◷     │
│    ◎     │
│          │
│  ──────  │
│          │
│   [AV]   │   ← Avatar 32px, centralizado (sem texto)
│          │
│   [⊢]    │   ← Toggle ícone apenas (ver §4.2)
└──────────┘
```

### 4.2 Toggle button (recolher/expandir)

| Propriedade | Expandido | Colapsado |
|---|---|---|
| Ícone Phosphor | `ph-sidebar-simple` | `ph-sidebar-simple` (flip horizontal) |
| Variant | Ghost (transparente, text-muted) | Ghost |
| Hover | background: `#2a2e38`, texto branco | background: `#2a2e38` |
| Width | `100%` com label "Recolher sidebar" | `40px`, centralizado |
| Height | `36px` | `36px` |
| Posição | Bottom of sidebar, padding-top 8px | Bottom, centralizado |
| `aria-label` | "Recolher sidebar" | "Expandir sidebar" |
| `aria-expanded` | `"true"` | `"false"` |

**Ícone flip no colapsado:**

```tsx
// ph-sidebar-simple virado horizontalmente quando colapsado
<PhSidebarSimple
  size={20}
  className={cn(
    'text-text-muted transition-transform duration-250',
    isCollapsed && 'scale-x-[-1]'
  )}
/>
```

### 4.3 Transição CSS

```css
/* Na sidebar */
.sidebar {
  transition: width 250ms cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;        /* evita reflow de labels durante transição */
  will-change: width;      /* GPU acceleration para a animação */
}

/* Labels de NavItem — fadeout ao recolher */
.nav-label {
  transition: opacity 120ms ease, width 250ms cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  overflow: hidden;
}

/* Colapsado: label desaparece primeiro, depois width */
.sidebar.collapsed .nav-label {
  opacity: 0;
  width: 0;
}

/* Expandido: width primeiro, depois label aparece */
.sidebar.expanded .nav-label {
  opacity: 1;
  width: auto;
  transition-delay: opacity 80ms;
}
```

**Tailwind equivalent:**
```tsx
// Sidebar wrapper
<nav className={cn(
  'fixed inset-y-0 left-0 z-40 flex flex-col transition-[width] duration-250',
  'bg-glass-sidebar backdrop-blur-md border-r border-glass-border',
  isCollapsed ? 'w-16' : 'w-sidebar'
)}>

// NavItem label
<span className={cn(
  'transition-[opacity,width] overflow-hidden whitespace-nowrap',
  isCollapsed
    ? 'opacity-0 w-0 duration-[120ms]'
    : 'opacity-100 duration-[200ms] delay-[80ms]'
)}>
  {label}
</span>
```

### 4.4 NavItem em modo colapsado

| Estado | Ícone | Background | Tooltip |
|---|---|---|---|
| **Default** | `#9ca3af` (text-muted) | transparent | label ao lado direito |
| **Hover** | `#ffffff` | `#2a2e38` (surface-high) | não mostrar (já visível no hover) |
| **Active** | `#3b82f6` (primary) | `#1e2a3f` | não mostrar |
| **Focus-visible** | — | outline 2px `#3b82f6` offset 2px | — |

**Dimensões no estado colapsado:**
- Container item: `48px × 42px`, display flex, items-center justify-center
- Padding: `0` (ícone centralizado)
- Border-radius: `8px`

**Tooltip no colapsado:**
- Aparece ao lado direito (`left: calc(64px + 8px)`)
- Background: `var(--glass-tooltip)` com `backdrop-blur-sm`
- Borda: `1px solid var(--glass-border-strong)`
- Padding: `6px 10px`
- Font: `12px / 600 / Inter`
- Box-shadow: `0 4px 12px rgba(0,0,0,0.35)`
- Border-radius: `6px`
- Z-index: `60`
- Delay de entrada: `400ms` (evita flash em hover rápido)
- Animação: `opacity 0→1, translateX(-4px→0)` em 150ms

```tsx
// Tooltip pattern (usar Radix Tooltip do shadcn/ui)
<Tooltip delayDuration={400} disableHoverableContent>
  <TooltipTrigger asChild>
    <NavItemLink ... />
  </TooltipTrigger>
  {isCollapsed && (
    <TooltipContent
      side="right"
      className="bg-glass-tooltip backdrop-blur-sm border border-glass-border-strong
                 text-text text-xs font-semibold px-2.5 py-1.5 shadow-lg"
    >
      {label}
    </TooltipContent>
  )}
</Tooltip>
```

### 4.5 Acessibilidade

- `<nav>` com `aria-label="Navegação principal"`
- Toggle button: `aria-expanded={!isCollapsed}` + `aria-controls="sidebar-nav"`
- Sidebar nav list: `id="sidebar-nav"`
- NavItem ativo: `aria-current="page"`
- Labels invisíveis no colapsado: usar `sr-only` no estado collapsed em vez de `width: 0` — garante leitura por screen reader mesmo quando não visível
  ```tsx
  <span className={cn(isCollapsed ? 'sr-only' : 'block')}>
    {label}
  </span>
  ```
- Tooltips do Radix são anunciados por screen readers automaticamente — garantir que `TooltipContent` não repita o que o `sr-only` já anuncia
- Focus trap: sidebar mobile tem modo drawer com `role="dialog"` + `aria-modal="true"`
- Atalho de teclado: `Ctrl+B` ou `[` para toggle (opcional, documentar em tooltip)

### 4.6 Comportamento responsivo

| Breakpoint | Comportamento |
|---|---|
| Desktop (≥1024px) | Sidebar fixa, expandida por padrão. Usuário pode recolher. Estado persistido em `localStorage` |
| Tablet (768–1023px) | Sidebar começa colapsada (64px). Usuário pode expandir. |
| Mobile (<768px) | Sidebar some completamente. Abre como drawer (overlay) via botão hamburguer no topbar. |

```tsx
// Controle de estado com persistência
const [isCollapsed, setIsCollapsed] = useState(() => {
  if (window.innerWidth < 1024) return true;
  return localStorage.getItem('sidebar-collapsed') === 'true';
});

const toggle = () => {
  const next = !isCollapsed;
  setIsCollapsed(next);
  localStorage.setItem('sidebar-collapsed', String(next));
};
```

### 4.7 Adjustment do layout principal com sidebar dinâmica

```tsx
// AppShell.tsx — ajuste de margem conforme estado
<div className={cn(
  'flex flex-col min-h-screen transition-[margin-left] duration-250',
  isMobile ? 'ml-0' : isCollapsed ? 'ml-16' : 'ml-sidebar'
)}>
  <Topbar onMenuClick={openDrawer} />
  <main className="flex-1 p-6">
    {children}
  </main>
</div>
```

**Importante:** o `margin-left` no main content deve ter a **mesma transição** da sidebar (`250ms cubic-bezier(0.4,0,0.2,1)`) para evitar "jump" no layout.

---

## 5. Glass panels — Modals e Dialogs

### 5.1 Overlay de fundo (scrim)

```tsx
// Radix Dialog Overlay
<DialogOverlay
  className="fixed inset-0 z-50 bg-glass-overlay backdrop-blur-xs
             data-[state=open]:animate-in data-[state=closed]:animate-out
             data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
/>
```

| Propriedade | Valor |
|---|---|
| Background | `rgba(0, 0, 0, 0.68)` |
| Backdrop-filter | `blur(4px)` |
| Z-index | `50` |
| Animação | `fade-in 150ms ease` / `fade-out 120ms ease` |

### 5.2 Dialog glass panel

```tsx
// Radix Dialog Content
<DialogContent
  className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2
             z-50 w-full max-w-lg
             bg-glass-modal backdrop-blur-xl
             border border-glass-border-strong
             rounded-2xl shadow-xl
             data-[state=open]:animate-in data-[state=closed]:animate-out
             data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
             data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
/>
```

| Propriedade | Valor |
|---|---|
| Background | `rgba(20, 23, 32, 0.92)` |
| Backdrop-filter | `blur(28px) saturate(1.2)` |
| Border | `1px solid rgba(255,255,255,0.12)` |
| Box-shadow | `0 24px 64px rgba(0,0,0,0.60)` |
| Border-radius | `20px` (2xl) |
| Padding | `24px` |
| Max-width | `512px` (modal padrão), `640px` (modal largo, ex: confirm release) |

**Shimmer header:** a borda superior do dialog glass panel cria um reflexo de luz sutil que diferencia o painel do overlay. Isso é o único elemento "decorativo" permitido no glassmorphism deste projeto.

### 5.3 Tamanhos de dialog

| Tipo | Max-width | Uso |
|---|---|---|
| Compact | `380px` | Confirmações simples (excluir, sair) |
| Default | `512px` | Formulários curtos (approve, publish) |
| Wide | `640px` | Formulários longos (nova versão, review report) |
| Full | `calc(100vw - 48px)` max `880px` | Deck hero completo, sincronização |

### 5.4 Animação de entrada/saída

```css
/* Usar shadcn/ui animate-in/animate-out */
/* Entrada: fade + zoom suave */
@keyframes dialogIn {
  from { opacity: 0; transform: translate(-50%, -48%) scale(0.97); }
  to   { opacity: 1; transform: translate(-50%, -50%) scale(1); }
}

/* Saída: fade + zoom suave */
@keyframes dialogOut {
  from { opacity: 1; transform: translate(-50%, -50%) scale(1); }
  to   { opacity: 0; transform: translate(-50%, -48%) scale(0.97); }
}
```

Duração: entrada 180ms, saída 140ms. Easing: `cubic-bezier(0.16, 1, 0.3, 1)` (deceleration).

---

## 6. Tooltips glass

Tooltips gerados via Radix Tooltip (shadcn/ui) usam o token `glass-tooltip`.

```tsx
<TooltipContent
  className="bg-glass-tooltip backdrop-blur-sm
             border border-glass-border-strong
             text-text-body text-xs font-semibold
             px-2.5 py-1.5 rounded-md shadow-lg
             max-w-xs"
>
```

| Propriedade | Valor |
|---|---|
| Background | `rgba(24, 27, 35, 0.95)` |
| Backdrop-filter | `blur(8px)` |
| Border | `1px solid rgba(255,255,255,0.12)` |
| Font | 12px / 600 / Inter |
| Color | `#d1d5db` (text-body) |
| Max-width | `240px` |
| Padding | `6px 10px` |
| Border-radius | `6px` (sm) |
| Delay | `400ms` (padrão), `0ms` para tooltips de ícone de ação crítica |

---

## 7. Regras de uso — o que é e o que não é glassmorphism neste projeto

### Recebe glass treatment:
- `<Sidebar>` — blur-md, glass-sidebar
- `<Topbar>` — blur-sm, glass-topbar, sticky
- `<Dialog>` (modals, confirm dialogs) — blur-xl, glass-modal
- `<Tooltip>` — blur-sm, glass-tooltip
- `<Popover>` de filtros e menus contextuais — blur-sm, glass-elevated

### NÃO recebe glass treatment:
- Cards de conteúdo (`<ContentCard>`) — mantém `bg-surface` sólido
- `<DataTable>` — mantém `bg-surface` sólido
- `<FilterBar>` inline — mantém `bg-surface-low` sólido
- StatusBadges, botões, tabs — sem alteração
- `<EmptyState>`, `<ErrorState>`, `<LoadingSkeleton>` — sem alteração

**Regra de ouro:** glass é reservado para elementos que fisicamente "flutuam" sobre o conteúdo. Um card de dados não flutua — ele está no conteúdo.

---

## 8. Alternativas descartadas

| Alternativa | Motivo da rejeição |
|---|---|
| Glassmorphism em cards de dados (`ContentCard`) | Criaria confusão visual — dados ficam "aquém" do conteúdo ao invés de nele; prejudica legibilidade de texto longo |
| Sidebar completamente transparente (alpha 0.5) | Background muito claro revelaria gradientes do conteúdo atrás, comprometendo contraste de texto muted (abaixo de 4.5:1) |
| Borda de luz `rgba(255,255,255,0.20)` | Muito visível, tornaria o efeito decorativo ao invés de sutil |
| Backdrop-filter no conteúdo principal (pg bg) | O conteúdo principal não tem nada "atrás" — blur seria no vácuo; desperdício de GPU |
| Sidebar colapsando para 0px (ocultando completamente) | Perde a âncora visual de navegação; usuário perde referência de onde está no app |
| Toggle no topo da sidebar | Menos intuitivo — o toggle muda a dimensão (largura), que o usuário percebe mais facilmente no canto inferior onde a sidebar "termina" |

---

## 9. Checklist de implementação (para o Caio)

- [ ] Adicionar CSS vars em `index.css :root` (§2.1)
- [ ] Adicionar tokens em `tailwind.config.ts` (§2.2)
- [ ] Adicionar extensões de `backdropBlur` e `transitionProperty` no tailwind (§2.2)
- [ ] Atualizar `<Topbar>` com glass classes (§3.1)
- [ ] Atualizar `<Sidebar>` com glass classes e backdrop-blur (§3.2)
- [ ] Implementar estado colapsado/expandido na sidebar com `isCollapsed` state (§4)
- [ ] Implementar toggle button com `ph-sidebar-simple` + flip (§4.2)
- [ ] Implementar transição CSS na sidebar e no margin do main content (§4.3)
- [ ] Implementar tooltip para NavItem no modo colapsado via Radix Tooltip (§4.4)
- [ ] Adicionar `aria-expanded`, `aria-controls`, `aria-current` (§4.5)
- [ ] Implementar lógica de breakpoint (desktop: memória, tablet: colapsado por padrão, mobile: drawer) (§4.6)
- [ ] Atualizar `<Dialog>` e `<AlertDialog>` do shadcn com glass classes (§5)
- [ ] Atualizar `<Tooltip>` do shadcn com glass classes (§6)
- [ ] Atualizar `<Popover>` do shadcn com glass-elevated (§7)
- [ ] Rodar o build (`npm run build` em `admin/`) antes de abrir PR
- [ ] Checar contraste em dev tools (nenhum par deve ficar abaixo de 4.5:1)
