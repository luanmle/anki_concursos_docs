# Plano de Migração: `index.css :root` → `tailwind.config.ts`

> **Objetivo:** Eliminar a fonte duplicada de tokens em `admin/src/index.css` (bloco `:root` e o bloco `.ac-shell`), consolidando tudo em `admin/tailwind.config.ts`.
> **Responsável pela implementação:** Caio
> **Referência de valores canônicos:** `docs/design/01-tokens.md`

---

## 1. Estratégia

O arquivo `index.css` tem 2700+ linhas com centenas de classes semânticas CSS que usam variáveis custom (`var(--primary)`, `var(--muted)`, etc.). **Não é viável reescrever tudo de uma vez** em utilities Tailwind. A migração é incremental em duas fases:

### Fase 1 (imediata — esta issue)
1. Atualizar `tailwind.config.ts` com os novos tokens canônicos (ver `01-tokens.md`).
2. Substituir os valores do bloco `:root` em `index.css` pelos novos valores — **mantendo as variáveis CSS** (os nomes `--primary`, `--muted`, etc. ficam; só os _valores_ mudam).
3. Remover o bloco `.ac-shell` (override Material 3 que cria inconsistência) — as classes `.ac-*` continuarão funcionando com o `:root` principal.

### Fase 2 (issue seguinte — scope do Caio)
- Ao refatorar componente por componente, migrar de `var(--color)` para utilities Tailwind (`text-primary`, `bg-surface`, etc.).
- Remover variáveis CSS de `:root` conforme as classes migrarem.

---

## 2. Mapeamento: variável atual → novo valor

### 2.1 Bloco `:root` — substituição de valores

| Variável `--nome` | Valor atual | **Novo valor** | Token canônico |
|---|---|---|---|
| `--background` | `#09090b` | **`#181b23`** | `bg` |
| `--surface-lowest` | `#09090b` | **`#0f1117`** | `surface-lowest` |
| `--surface` | `#0c0c0f` | **`#1d2029`** | `surface-low` |
| `--surface-low` | `#0f0f12` | **`#1d2029`** | `surface-low` |
| `--surface-container` | `#121215` | **`#22252d`** | `surface` |
| `--surface-high` | `#18181b` | **`#2a2e38`** | `surface-high` |
| `--surface-highest` | `#1e1e22` | **`#2a2e38`** | `surface-high` |
| `--outline` | `#52525b` | **`#374151`** | `border-strong` |
| `--outline-variant` | `#27272a` | **`#2a2e38`** | `border` |
| `--text` | `#fafafa` | **`#ffffff`** | `text` |
| `--muted` | `#a1a1aa` | **`#9ca3af`** | `text-muted` |
| `--primary` | `#a78bfa` | **`#3b82f6`** | `primary` |
| `--primary-strong` | `#8b5cf6` | **`#2563eb`** | `primary-hover` |
| `--primary-container` | `#2e1065` | **`#1e3a5f`** | `primary-dim` |
| `--success` | `#34d399` | **`#34d399`** ✓ | `success` |
| `--success-container` | `#052e25` | **`#052e25`** ✓ | `success-dim` |
| `--warning` | `#fbbf24` | **`#fbbf24`** ✓ | `warning` |
| `--warning-container` | `#3a2a05` | **`#3a2a05`** ✓ | `warning-dim` |
| `--danger` | `#ef4444` | **`#f87171`** | `danger` |
| `--danger-container` | `#3b1111` | **`#3b1111`** ✓ | `danger-dim` |
| `--radius-sm` | `6px` | **`6px`** ✓ | `rounded-sm` |
| `--radius` | `8px` | **`8px`** ✓ | `rounded` |
| `--sidebar-width` | `244px` | **`256px`** | `spacing.sidebar` |

> ✓ = valor permanece idêntico

**Variáveis a remover do `:root`** (não têm equivalente no novo sistema):
- `--surface-lowest` (manter como `--surface-lowest` mas com novo valor acima)

### 2.2 Font-family no `:root`

| Atual | Novo |
|---|---|
| `font-family: Geist, Inter, ...` | `font-family: Inter, ui-sans-serif, ...` |

**Remover `Geist`** — não está no design system canônico. A fonte Geist não deve ser carregada.

---

## 3. Bloco `.ac-shell` — remover

O bloco `.ac-shell` (linhas ~1893–1934 em `index.css`) sobrepõe as variáveis `:root` com valores Material 3 quando a classe `.ac-shell` está presente. Esse bloco deve ser **removido completamente**.

As classes `.ac-*` (`.ac-page`, `.ac-deck-card`, `.ac-hero`, `.ac-note-list`, etc.) continuarão funcionando com as variáveis do `:root` principal (os novos valores canônicos).

**Antes de remover**, verificar se `.ac-shell` está aplicado em algum componente e remover a classe do JSX/HTML também.

---

## 4. Classes semânticas: o que migra, o que permanece

### 4.1 Permanece (sem alteração de estrutura)

As classes semânticas abaixo continuarão sendo classes CSS em `index.css`. Os valores que usam `var()` serão atualizados automaticamente quando o `:root` for atualizado.

| Classe | O que muda |
|---|---|
| `.status-badge` | `border-color` usa `--outline` → novo `#374151` |
| `.button-primary` | `background: var(--primary)` → novo `#3b82f6` |
| `.button-primary:hover` | `background: #c4b5fd` → **mudar para `#2563eb`** (hardcoded, precisa de edição manual) |
| `.sidebar-nav a.active` | `color: var(--primary)` → novo `#3b82f6` |
| `.avatar` | `border: 1px solid #6d4cc7` → **mudar para `#1d4ed8`** (hardcoded azul) |
| `.brand-mark` | `background: var(--primary)` → novo `#3b82f6` |
| `.history-icon` | `background: #21123c` → **mudar para `#1e3a5f`** (hardcoded violeta → azul) |
| `.workflow-steps b` | `border: 1px solid #6d4cc7` → **mudar para `#1d4ed8`** |
| `.row-action:hover` | `color: var(--primary)` → novo `#3b82f6` |
| `.file-drop-zone` | `border-color: #6d4cc7` → **mudar para `#3b82f6`** |
| `.release-panel` | `border: 1px solid #6d4cc7` → **mudar para `#3b82f6`** |
| `.release-panel` (bg gradient) | `linear-gradient(110deg, #21123c, ...)` → **mudar para `#1e3a5f`** |
| `.user-audit-card` | `border: 1px solid #6d4cc7` → **mudar para `#3b82f6`** |
| `.user-audit-card` (bg) | `linear-gradient(145deg, #21123c, ...)` → **mudar para `#1e3a5f`** |
| `.version-preservation-notice` | violeta → azul (ver abaixo) |
| `.dashboard-action-card:hover` | `border-color: #6d4cc7` → **mudar para `#3b82f6`** |
| `.addon-deck-card-selected` | `border-color: #6d4cc7` → **mudar para `#3b82f6`** |
| `.dashboard-nav-link:hover` | `border-color: #6d4cc7` → **mudar para `#3b82f6`** |
| `.login-page` background gradient | `rgba(167,139,250,.05)` → **mudar para `rgba(59,130,246,.05)`** |

### 4.2 Valores hardcoded violeta → azul (busca e substituição)

O tema violeta (`#6d4cc7`, `#7c3aed`, `#21123c`, `#4c277e`, `#c4b5fd`, `#ddd6fe`, `#a78bfa`, `#8b5cf6`) deve ser substituído pelas contrapartes azuis em todas as classes. Mapeamento:

| Cor violeta (atual) | Cor azul (novo) | Contexto |
|---|---|---|
| `#6d4cc7` | `#1d4ed8` | Bordas de elementos active/selected |
| `#7c3aed` | `#3b82f6` | Backgrounds de ícone active |
| `#21123c` | `#1e3a5f` | Container violeta → container azul |
| `#4c277e` | `#1d4ed8` | Bordas de ícones |
| `#c4b5fd` | `#93c5fd` | Texto sobre container (violet → blue info) |
| `#ddd6fe` | `#bfdbfe` | Texto leve sobre container |
| `#6d28d9` | `#1d4ed8` | Borda curator badge |
| `#2e1065` | `#1e3a5f` | Container primary/curator |
| `#0a0012` | `#ffffff` | Texto sobre primary (mudar para branco) |

**Ferramenta:** `sed` ou busca global no VS Code. Script sugerido:
```bash
# Executar dentro de admin/src/
sed -i 's/#6d4cc7/#1d4ed8/g; s/#7c3aed/#3b82f6/g; s/#21123c/#1e3a5f/g; s/#4c277e/#1d4ed8/g; s/#c4b5fd/#93c5fd/g; s/#ddd6fe/#bfdbfe/g; s/#6d28d9/#1d4ed8/g; s/#2e1065/#1e3a5f/g' index.css
```
> ⚠️ Revisar manualmente após o sed — alguns contextos podem precisar de ajuste fino.

---

## 5. Classe `.button-primary` — ajuste específico

A linha atual:
```css
.button-primary:hover { background: #c4b5fd; }
```
Deve se tornar:
```css
.button-primary:hover { background: #2563eb; }
```
E o texto do botão primary (atual `color: #0a0012`) deve mudar para `color: #ffffff`, pois azul `#3b82f6` tem contraste suficiente para branco mas não para quase-preto.

---

## 6. Classe `.version-preservation-notice` — ajuste específico

Atual (violeta):
```css
.version-preservation-notice {
  border: 1px solid #6d4cc7;
  color: #ddd6fe;
  background: #21123c;
}
```
Novo (azul):
```css
.version-preservation-notice {
  border: 1px solid #1d4ed8;
  color: #bfdbfe;
  background: #1e3a5f;
}
```

---

## 7. Classe `.status-curator` — ajuste

O papel `curator` usa violeta hoje. Como decisão de design, **mantemos violeta para curator** (diferente do azul do primary, permite diferenciar visualmente do papel `student` que fica azul). Portanto `.status-curator` **não muda**:
```css
.status-curator { color: #ddd6fe; border-color: #6d4cc7; background: #21123c; }
```

Apenas `.status-student` muda (atualmente azul já está OK com o novo accent):
```css
.status-student { color: #bfdbfe; border-color: #2563eb; background: #1e3a5f; }
```

---

## 8. Checklist de deprecação

- [ ] `tailwind.config.ts` atualizado com tokens de `01-tokens.md`
- [ ] `:root` em `index.css` atualizado com novos valores
- [ ] `font-family` em `:root` alterado de Geist para Inter
- [ ] Carregamento da fonte Geist removido (se existir em `index.html`)
- [ ] Bloco `.ac-shell` removido de `index.css`
- [ ] Classe `.ac-shell` removida do componente JSX (verificar em `admin/src/`)
- [ ] Substituição global de cores violeta → azul (script + revisão manual)
- [ ] `.button-primary` hover e color ajustados
- [ ] `.version-preservation-notice` atualizado
- [ ] Build sem erros após alterações
- [ ] Verificação visual das telas: login, dashboard, cards, decks, reports

---

## 9. O que NÃO mudar nesta issue

- Estrutura das classes CSS semânticas (`.page-header`, `.filter-panel`, etc.) — elas ficam.
- Classes `.ac-*` (já estão alinhadas com a nova paleta via `:root`).
- Lógica de componentes React (`.tsx`) — esta issue é somente tokens e CSS.
- Ícones (a troca lucide → Phosphor é scope do Caio numa issue separada após esta).
