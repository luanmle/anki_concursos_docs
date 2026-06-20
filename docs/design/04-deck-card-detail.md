# Aplicação do Design System: DeckDetailPage e CardDetailPage

> Referência visual: `site.HTML` (Scrimba) — adaptada para contexto administrativo
> Tokens: `docs/design/01-tokens.md`
> Primitivos: `docs/design/03-primitives.md`

---

## 1. Contexto

Ao clicar num deck na lista (`/decks`) o usuário abre o `DeckDetailPage` (`/decks/:deckId`).
Ao clicar numa nota/cartão dentro do deck, abre a `CardDetailPage` (`/cards/:cardId`).

A referência Scrimba mostra um grid de cursos com cards clicáveis que expandem para modal de detalhe. Para o admin, adaptamos esse padrão para:
- **DeckDetailPage**: deck hero + lista de cartões do deck (table-like com previews)
- **CardDetailPage**: header do cartão + abas (Conteúdo / Histórico / Metadados) + ContentCards por campo

---

## 2. DeckDetailPage

### 2.1 Layout geral (desktop)

```
┌─────────────────────────────────────────────────────────────┐
│ TOPBAR (62px) — breadcrumb: Decks / [Nome do Deck]         │
├─────────────────────────────────────────────────────────────┤
│ DECK HERO                                        [Ações]    │
│ ┌──────────────────────────────────────┐ ┌──────────────┐  │
│ │ [status badge] Direito Const.        │ │ [Publicar    │  │
│ │ Nome completo do deck                │ │  Release]    │  │
│ │ Descrição do deck...                 │ │ [Adicionar   │  │
│ │ Disciplina · 47 cartões · Release 8  │ │  Cartão]     │  │
│ └──────────────────────────────────────┘ └──────────────┘  │
├─────────────────────────────────────────────────────────────┤
│ TABS: [Cartões  47] | [Releases  8] | [Sync]               │
├─────────────────────────────────────────────────────────────┤
│ SEARCH + FILTROS                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [🔍 Buscar cartão...]        [Status ▼]  [Tipo ▼]      │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ LISTA DE CARTÕES (NoteList)                                 │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ [tipo] [status]  Front text (preview 1 linha)  [Ações] │ │
│ │ [tipo] [status]  Front text (preview 1 linha)  [Ações] │ │
│ │ [tipo] [status]  Front text...                 [Ações] │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                     [← 1 2 3 ... 47 →]     │
└─────────────────────────────────────────────────────────────┘
```

**Mobile:** DeckHero em coluna única; Ações se movem abaixo do hero; NoteList vira lista de cards empilhados (sem grid).

### 2.2 Deck Hero

| Propriedade | Valor |
|---|---|
| Background | `radial-gradient(circle at 95% 0%, rgba(59,130,246,0.10), transparent 26rem), #22252d` |
| Border | 1px solid `#2a2e38` |
| Border-radius | 20px |
| Padding | 28px 30px |
| Grid desktop | `minmax(0,1fr) auto` (hero info + ações) |

**Hero info:**
- StatusBadge do deck (`draft`/`published`/`archived`) no topo
- Nome do deck: Heading-L (28px / 700)
- Descrição: Body-M (14px), max 780px, `#9ca3af`
- Metadata row: `[ícone ph-books] Disciplina · [ícone ph-cards] 47 cartões · [ícone ph-package] Release 8`
  - Font: 13px, `#9ca3af`
  - Gap entre itens: `·` com espaço
- Tags de tipo (PRO/HOT/FREE/UPDATED) se aplicável — badge pattern da referência Scrimba

**Ações (coluna direita, min-width: 200px):**
- `[ph-package] Publicar Release` → Button Primary — visível para admin e reviewer
- `[ph-plus] Adicionar Cartão` → Button Secondary — visível para admin e curator
- Status de conectividade (se sync ativo): dot verde + texto "Sincronizado"

### 2.3 Tabs

Ver especificação em `03-primitives.md §3`. Tabs específicas:
- **Cartões** + badge com total de cartões ativos
- **Releases** + badge com número da última release
- **Sync** (sem badge)

### 2.4 SearchBar do deck

Ver `03-primitives.md §4`. Contexto específico:
- Placeholder: "Buscar por frente, `public_id`..."
- Filtros adicionais: Select de Status (todos / needs_review / approved / published / deprecated) e Select de Tipo (basic / cloze)
- Layout: `grid-template-columns: 1fr 180px 180px` → mobile: 1 coluna

### 2.5 NoteList (lista de cartões do deck)

Baseada no padrão `.ac-note-list` / `.ac-note-row` existente, adaptada com os novos tokens.

**Container:**
```
border: 1px solid #2a2e38
border-radius: 16px
overflow: hidden
background: #2a2e38  /* gap visual entre linhas */
gap: 1px            /* linhas separadas pelo background do container */
```

**Linha (NoteRow):**
```
grid-template-columns: auto minmax(0,1fr) auto auto
align-items: center
gap: 16px
padding: 18px
background: #22252d  /* surface */
height: auto (mín 62px)
```

**Colunas:**
1. **Tipo** — Badge mini `BASIC`/`CLOZE` (info variante, 8px text)
2. **Conteúdo** — Front text em preview, ellipsis em 1 linha; public_id abaixo em `#9ca3af` / 10px
3. **Status** — StatusBadge (CardStatus)
4. **Ações** — ghost button row: `[ph-eye]` Ver, `[ph-arrow-square-out]` Abrir deck item

**Hover da linha:**
```
background: #1d2029  /* surface-low — mais escuro que surface para hover */
```

**Estado selecionado / expandido:**
```
background: #1e2a3f  /* primary-dim — azul tint */
border-left: 3px solid #3b82f6
```

**NoteRow clicável:** `cursor: pointer`, `role="row"` / `role="button"` se for botão de expansão.

**Ao clicar na linha:** abre modal `NoteModal` ou navega para `CardDetailPage`.

### 2.6 NoteModal (ao clicar na linha)

Baseada em `.ac-note-modal` existente, adaptada:

```
width: min(980px, 100%)
max-height: min(900px, 92vh)
border-radius: 22px
background: #22252d
border: 1px solid #2a2e38
box-shadow: 0 28px 80px rgba(0,0,0,0.45)
```

**Grid interno:** `grid-template-rows: auto auto minmax(0,1fr)`
1. Modal header: nome do cartão + `public_id` + StatusBadge + botão fechar (`ph-x` 20px)
2. Modal tabs: **Conteúdo** | **Histórico** | **Metadados** (Tabs sem badge, `ph-` ícones)
3. Modal body: scroll interno, padding 22px

**Conteúdo da aba Conteúdo:**
- Grid de `ContentCard`s: Frente, Verso, Resposta, Explicação
- Layout: 2 colunas em desktop, 1 em mobile

**Acessibilidade do modal:**
- `role="dialog"`, `aria-modal="true"`, `aria-labelledby="modal-title-id"`
- Foco preso dentro do modal enquanto aberto (focus trap)
- Foco retorna ao NoteRow de origem ao fechar
- Fechar com Esc
- Botão de fechar visível e com `aria-label="Fechar detalhes do cartão"`

---

## 3. CardDetailPage

### 3.1 Layout geral (desktop)

```
┌─────────────────────────────────────────────────────────────┐
│ ← Cartões (back link)                                      │
├─────────────────────────────────────────────────────────────┤
│ CARD HEADER                                                 │
│ [kicker: public_id badge + StatusBadge]                    │
│ Front text (título / heading-L)                            │
│ [disciplina · assunto · v3 · data]         [Ações]         │
├─────────────────────────────────────────────────────────────┤
│ TABS: [Conteúdo atual] | [Histórico  3] | [Metadados]      │
├─────────────────────────────────────────────────────────────┤
│ LAYOUT DETALHE                                              │
│ ┌──────────────────────────────────┐ ┌──────────────────┐  │
│ │  ContentCard: Frente            │ │ METADADOS       │  │
│ │  ContentCard: Verso             │ │ ID              │  │
│ │  ContentCard: Resposta          │ │ Versão          │  │
│ │  ContentCard: Explicação        │ │ Status          │  │
│ │                                  │ │ Criado em       │  │
│ │  [Ações editoriais]             │ │ Atualizado      │  │
│ └──────────────────────────────────┘ └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Mobile:** layout em coluna única; sidebar de metadados vai abaixo do conteúdo.

### 3.2 Card Header

```
display: flex
align-items: flex-end
justify-content: space-between
gap: 22px
padding-bottom: 22px
border-bottom: 1px solid #2a2e38
```

**Kicker (acima do título):**
```
display: flex
align-items: center
gap: 9px
margin-bottom: 10px
```
- `public_id` como código: `font: 10px / mono`, `#9ca3af`
- StatusBadge do card
- StatusBadge da versão atual

**Título:** front text do cartão — Heading-L (28px / 700 / -0.01em), max-width 780px

**Metadata row:**
- Disciplina · Assunto · Versão v3 · Atualizado há X dias
- Font: 11px, `#9ca3af`

**Ações (coluna direita):**
- `[ph-plus] Nova versão` → Button Primary — admin / curator
- `[ph-check] Aprovar` → Button Secondary — admin / reviewer, somente se `needs_review`
- `[ph-check-circle] Publicar` → Button Secondary — admin / reviewer, somente se `approved`
- `[ph-copy] Copiar ID` → Button Ghost

### 3.3 ContentCards por campo

Aplicação do primitivo ContentCard (ver `03-primitives.md §5`) em cada campo do cartão:

| Campo | Label | Variante | Observação |
|---|---|---|---|
| `front_text` | FRENTE | success (se published) / default | Campo principal |
| `back_text` | VERSO | default | — |
| `answer_text` | RESPOSTA | success (se published) | Pode ser vazio |
| `explanation_text` | EXPLICAÇÃO | default | Pode ser vazio |

Para cartão **publicado**: todos os campos usam variante success (borda verde à esquerda).
Para cartão em **needs_review / approved**: variante default.
Para versão **rejected / superseded**: variante neutra com opacity 0.7.

**Renderização do texto:** `white-space: pre-wrap`, `overflow-wrap: anywhere`. **Nunca renderizar como HTML.**

### 3.4 Sidebar de metadados

```
width: 300px
display: grid
align-content: start
gap: 12px
```

**MetadataCard:**
```
padding: 18px
border: 1px solid #2a2e38
border-radius: 8px
background: #22252d
```

Campos a exibir:
- `public_id` (com botão copiar `ph-copy`)
- `canonical_key` (com botão copiar)
- `card_kind` (BASIC / CLOZE — badge info)
- Status do cartão (StatusBadge)
- Versão atual (v3, link para historico)
- Status da versão (StatusBadge)
- `content_hash` (primeiros 12 chars + botão expandir)
- Criado em (data formatada pt-BR)
- Atualizado em (data formatada pt-BR)

**EditorialActions card:**
Abaixo do MetadataCard, ações editoriais em coluna:
- `[ph-plus] Nova versão` → Button Primary (100% largura)
- `[ph-check] Aprovar versão` → Button Secondary (100% largura)
- `[ph-check-circle] Publicar versão` → Button Secondary (100% largura)
- `[ph-warning] Reportar problema` → Button Ghost com `#fbbf24`

Cada botão com `PermissionGate` condicional ao papel e ao estado da versão.

### 3.5 Aba Histórico

Aplicação do padrão `.version-history` com tokens atualizados:

**VersionTimeline:**
```
display: grid
gap: 1px
background: #2a2e38  /* cria separadores visuais */
border: 1px solid #2a2e38
border-radius: 8px
overflow: hidden
```

**VersionRow:**
```
grid-template-columns: 34px 1fr auto
align-items: center
gap: 12px
padding: 14px
background: #1d2029  /* surface-low */
```

Colunas:
1. **Ícone**: círculo 32×32, background `#1e3a5f` (primary-dim), ícone `ph-clock` `#3b82f6`
2. **Info**: `v{number}` em 11px / 700; change_reason em 10px / `#d1d5db`; `by {email} · {date}` em 9px / `#9ca3af`
3. **StatusBadge** da versão

**Versão publicada atual** (destaque):
```
background: linear-gradient(90deg, rgba(59,130,246,0.06), #1d2029 40%)
border-left: 2px solid #3b82f6
```

---

## 4. Aplicação dos tokens por componente (resumo)

| Contexto | Token background | Token borda | Token texto | Token accent |
|---|---|---|---|---|
| DeckHero | `surface` + gradient | `border` | `text` / `text-muted` | `primary` |
| NoteList container | `border` (gap) | — | — | — |
| NoteRow default | `surface` | — | `text-body` | — |
| NoteRow hover | `surface-low` | — | `text-body` | — |
| NoteRow active | `primary-dim` + borda | `primary` | `text` | `primary` |
| ContentCard default | `surface` | `border` | `text-muted` (label) / `text-body` | — |
| ContentCard success | `surface` + gradient | `success` | `success` (label) | `success` |
| MetadataCard | `surface` | `border` | `text-muted` (dt) / `text-body` (dd) | — |
| VersionRow | `surface-low` | — | `text` / `text-muted` | `primary-dim` |
| VersionRow (published) | `surface-low` + gradient | `primary` (borda L) | `text` | `primary` |
| NoteModal | `surface` | `border` | `text` | `primary` |

---

## 5. Acessibilidade geral das páginas

- **Heading hierarchy:** `<h1>` único por página (nome do deck / front text do cartão); seções usam `<h2>`, subseções `<h3>`.
- **Skip link:** "Pular para conteúdo principal" como primeiro elemento focável — navega para o `<main>`.
- **StatusBadge nos cartões:** sempre com `title` ou `aria-label` descritivo.
- **Botões de ação na lista:** ícone-only (ex: `ph-eye`) deve ter `aria-label` explícito.
- **Paginação:** `aria-label="Paginação"` no nav, página atual com `aria-current="page"`.
- **Carregamento:** estado `<LoadingSkeleton>` deve ter `aria-label="Carregando cartões..."` e `aria-busy="true"` no container.
- **Estado vazio:** mensagem clara + ação contextual (ex: "Nenhum cartão encontrado. Adicionar cartão ao deck?").
- **Modais:** foco preso, Esc para fechar, foco retorna ao trigger de abertura.
