# Especificação de Primitivos — Estados e Acessibilidade

> Referência visual: `site.HTML` (Scrimba) + `docs/design/01-tokens.md`
> Ícones: Phosphor (`ph-*`)
> Todos os valores de cor em hex. Tokens semânticos entre parênteses.

---

## 1. NavItem / Sidebar

### 1.1 Anatomia

```
[ícone Phosphor 20px] [label 13px / 600]     height: 42px
                                              padding: 0 12px
                                              gap ícone–label: 10px
                                              border-radius: 8px (rounded)
```

### 1.2 Estados

| Estado | Cor do texto | Background | Borda | Ícone |
|---|---|---|---|---|
| **Default** | `#9ca3af` (text-muted) | transparent | 1px solid transparent | `#9ca3af` |
| **Hover** | `#ffffff` (text) | `#2a2e38` (surface-high) | 1px solid transparent | `#ffffff` |
| **Active** | `#3b82f6` (primary) | `#1e2a3f`¹ | 1px solid `#2a2e38` (border) | `#3b82f6` |
| **Focus-visible** | — | — | outline: 2px solid `#3b82f6`, offset: 2px | — |
| **Disabled** | N/A — nav items não têm disabled state | | | |

> ¹ `#1e2a3f` = variante azul do `primary-dim` para hover de nav ativo. Definir como `--nav-active-bg: #1e2a3f` no componente.

### 1.3 Sidebar — estrutura

| Propriedade | Valor |
|---|---|
| Largura desktop | 256px (`spacing.sidebar`) |
| Background | `#141720` (sidebar) |
| Border-right | 1px solid `#2a2e38` (border) |
| Padding | 20px 14px |
| Z-index | 30 |
| Mobile: width | 256px, fixado fora da viewport até ativado |
| Mobile: overlay | `rgba(0,0,0,0.68)` backdrop |

**Sidebar header (brand):**
- Logo mark: 36×36px, `border-radius: 8px`, background `#3b82f6` (primary), ícone branco
- Nome produto: 14px / 700
- Subtítulo/ambiente: 10px / 700 / uppercase / `#9ca3af`
- Separador bottom: 1px solid `#2a2e38`

**Sidebar footer (user):**
- Avatar: 34×34px, `border-radius: full`, background `#1e3a5f`, borda `#1d4ed8`
- Nome: 12px / 700, max-width: 115px, ellipsis
- Role: 10px / `#9ca3af`
- Logout button: `#9ca3af`, hover `#f87171` (danger)

### 1.4 Acessibilidade

- Cada `<a>` de nav deve ter `aria-current="page"` quando ativo.
- Ícones são decorativos quando acompanhados de label — `aria-hidden="true"`.
- Largura mínima de alvo de toque: 44px (height mínimo de 42px está abaixo; garantir pelo menos `min-height: 44px` em mobile).
- Navegação por teclado: Tab move entre itens; Enter ativa.
- Focus trap quando sidebar está aberta em mobile (modal mode).

---

## 2. Button

### 2.1 Propriedades base

| Propriedade | Valor |
|---|---|
| Min-height | 40px |
| Padding | 0 16px |
| Border-radius | 8px (rounded) |
| Font | 13px / 600 / Inter |
| Gap (ícone + texto) | 8px |
| Border | 1px solid (varia por variante) |
| Cursor | pointer |
| Transition | background 0.15s ease, border-color 0.15s ease |

### 2.2 Variante Primary (filled)

| Estado | Background | Borda | Texto |
|---|---|---|---|
| **Default** | `#3b82f6` (primary) | transparent | `#ffffff` |
| **Hover** | `#2563eb` (primary-hover) | transparent | `#ffffff` |
| **Focus-visible** | `#3b82f6` | outline: 2px solid `#3b82f6`, offset: 2px | `#ffffff` |
| **Disabled** | `#3b82f6` opacity 0.5 | — | `#ffffff` opacity 0.5 |
| **Loading** | `#3b82f6` | — | `#ffffff` + spinner Phosphor `ph-spinner-gap` 16px, animação `spin 0.8s linear infinite` |
| **Error** | N/A — usar variante Danger para ações destrutivas | | |

> Contraste `#3b82f6` / `#ffffff` = 4.5:1 (WCAG AA). Verificar após implementação.

### 2.3 Variante Secondary (outline)

| Estado | Background | Borda | Texto |
|---|---|---|---|
| **Default** | `#22252d` (surface) | `#2a2e38` (border) | `#d1d5db` (text-body) |
| **Hover** | `#2a2e38` (surface-high) | `#374151` (border-strong) | `#ffffff` |
| **Focus-visible** | `#22252d` | outline: 2px solid `#3b82f6`, offset: 2px | `#d1d5db` |
| **Disabled** | `#22252d` opacity 0.5 | `#2a2e38` opacity 0.5 | `#d1d5db` opacity 0.5 |
| **Loading** | `#22252d` | `#2a2e38` | spinner Phosphor |

### 2.4 Variante Danger

| Estado | Background | Borda | Texto |
|---|---|---|---|
| **Default** | transparent | `#2a2e38` (border) | `#f87171` (danger) |
| **Hover** | `#3b1111` (danger-dim) | `#b91c1c` | `#fca5a5` |
| **Focus-visible** | transparent | outline: 2px solid `#f87171`, offset: 2px | `#f87171` |
| **Disabled** | transparent opacity 0.5 | `#2a2e38` opacity 0.5 | `#f87171` opacity 0.5 |

### 2.5 Variante Ghost

| Estado | Background | Borda | Texto |
|---|---|---|---|
| **Default** | transparent | transparent | `#9ca3af` (text-muted) |
| **Hover** | `#2a2e38` (surface-high) | transparent | `#ffffff` |
| **Focus-visible** | transparent | outline: 2px solid `#3b82f6`, offset: 2px | `#9ca3af` |
| **Disabled** | transparent opacity 0.5 | — | `#9ca3af` opacity 0.5 |

### 2.6 Tamanhos opcionais

| Tamanho | Height | Padding | Font |
|---|---|---|---|
| **sm** | 32px | 0 10px | 12px / 600 |
| **md (default)** | 40px | 0 16px | 13px / 600 |
| **lg** | 48px | 0 20px | 14px / 600 |

### 2.7 Acessibilidade

- Todo botão deve ter label acessível: texto visível ou `aria-label`.
- Botões de loading: `aria-busy="true"`, texto muda para "Carregando..." (ou `aria-label` explícito).
- Botões de ação crítica (excluir, publicar): usar `<button type="button">` com dialog de confirmação, não `onSubmit` direto.
- Alvo mínimo de toque: 44×44px (garantir padding vertical em mobile).
- `role="button"` não é necessário em `<button>`.

---

## 3. Tabs com Badge de Contagem

### 3.1 Anatomia

```
[Tab label 14px / 500]  [badge 10px / 700]    height: auto
                                               padding-bottom: 12px
                                               border-bottom: 2px solid
                                               gap label–badge: 8px
```

### 3.2 Estados (por tab individual)

| Estado | Cor do texto | Borda inferior | Badge bg | Badge texto |
|---|---|---|---|---|
| **Default** | `#9ca3af` (text-muted) | 2px solid transparent | `#2a2e38` | `#9ca3af` |
| **Hover** | `#d1d5db` (text-body) | 2px solid transparent | `#2a2e38` | `#d1d5db` |
| **Active** | `#ffffff` (text) | 2px solid `#ffffff` | `#2a2e38` | `#ffffff` |
| **Focus-visible** | `#d1d5db` | outline: 2px solid `#3b82f6`, offset: -2px (interno) | — | — |

> Alternativa: a borda inferior do tab ativo usa `#3b82f6` (primary) em vez de branco. Ambas as opções são válidas; a referência Scrimba usa branco. Recomendo **branco** para o admin (mais neutro, reservando o azul para ações).

### 3.3 Container de tabs

```
display: flex;
align-items: center;
gap: 24px;
border-bottom: 1px solid #2a2e38;
```

### 3.4 Badge

```
min-width: 18px;
height: 18px;
padding: 0 5px;
border-radius: 4px;
font-size: 10px;
font-weight: 700;
background: #2a2e38;
color: [herda do estado do tab]
```

### 3.5 Acessibilidade

- Container: `role="tablist"`, `aria-label="Seções do deck"`.
- Cada tab: `role="tab"`, `aria-selected="true/false"`, `aria-controls="panel-id"`.
- Painel associado: `role="tabpanel"`, `id="panel-id"`, `aria-labelledby="tab-id"`.
- Navegação por teclado: Tab move para o tablist; setas ← → navegam entre tabs; Enter/Space ativa.
- Badge de contagem: `aria-label` no tab deve incluir a contagem (ex: `aria-label="Todos os cursos, 71 itens"`).

---

## 4. SearchBar

### 4.1 Anatomia

```
[ícone ph-magnifying-glass 16px] [input text]    height: 40px
                                                  border-radius: 8px
                                                  padding: 0 12px 0 38px
```

### 4.2 Estados

| Estado | Background | Borda | Ícone | Texto |
|---|---|---|---|---|
| **Default** | `#0f1117` (surface-lowest) | 1px solid `#2a2e38` (border) | `#9ca3af` | `#d1d5db` |
| **Hover** | `#0f1117` | 1px solid `#374151` (border-strong) | `#9ca3af` | `#d1d5db` |
| **Focus** | `#0f1117` | 1px solid `#3b82f6` (primary) | `#3b82f6` | `#d1d5db` |
| **Com valor** | `#0f1117` | 1px solid `#2a2e38` | `#9ca3af` | `#ffffff` |
| **Disabled** | `#0f1117` opacity 0.5 | 1px solid `#2a2e38` opacity 0.5 | `#9ca3af` opacity 0.5 | `#6b7280` |
| **Erro** | N/A — SearchBar não retorna erro de validação | | | |

**Placeholder:** `#6b7280` (text-disabled)

### 4.3 Variante com botão clear (×)

Quando há valor digitado, exibir botão ícone `ph-x` (16px) à direita:
- Color: `#9ca3af`
- Hover: `#ffffff`
- `aria-label="Limpar busca"`

### 4.4 Acessibilidade

- `<label>` persistente associado (pode ser `.sr-only` — visualmente oculto, semanticamente presente).
- `type="search"` no `<input>`.
- `placeholder` não substitui `<label>`.
- Se debounce: anunciar resultados com `aria-live="polite"` na lista de resultados.

---

## 5. Card de Conteúdo (ContentCard)

Usado em `CardDetailPage` e `DeckDetailPage` para exibir o conteúdo de uma nota/cartão.

### 5.1 Anatomia

```
╔═══════════════════════════════════════╗
║  LABEL (9px / 800 / uppercase)        ║  padding: 20px
║                                       ║  border-radius: 12px
║  Conteúdo do campo (14px / 400)       ║  background: surface (#22252d)
║  linha 1 da frente do cartão...       ║  border: 1px solid border (#2a2e38)
╚═══════════════════════════════════════╝
```

### 5.2 Estados

| Estado | Background | Borda | Label | Corpo |
|---|---|---|---|---|
| **Default** | `#22252d` (surface) | 1px solid `#2a2e38` | `#9ca3af` (text-muted) | `#d1d5db` (text-body) |
| **Hover** (se clicável) | `#2a2e38` (surface-high) | 1px solid `#374151` | `#9ca3af` | `#ffffff` |
| **Focus-visible** | `#22252d` | outline: 2px solid `#3b82f6`, offset: 2px | `#9ca3af` | `#d1d5db` |
| **Disabled** | `#22252d` opacity 0.5 | 1px solid `#2a2e38` opacity 0.5 | `#6b7280` | `#6b7280` |
| **Erro / inválido** | N/A | 1px solid `#f87171` (danger) | `#f87171` | `#d1d5db` |

### 5.3 Variante Success (conteúdo publicado)

Para campos de cartões publicados — borda esquerda colorida indica conteúdo em produção:

```
border-left: 3px solid #34d399 (success)
background: linear-gradient(90deg, rgba(52,211,153,0.05), #22252d 35%)
label: #34d399
```

### 5.4 Variante Highlight (campo em foco de revisão)

Para o campo reportado num report — destaque amarelo de atenção:

```
border-left: 3px solid #fbbf24 (warning)
background: linear-gradient(90deg, rgba(251,191,36,0.05), #22252d 35%)
```

### 5.5 Acessibilidade

- `<article>` ou `<section>` com `aria-label="[Campo]: [conteúdo resumido]"`.
- Se expansível (mostrar/ocultar conteúdo longo): `aria-expanded` + controle visível.
- Texto do cartão: renderizar como `<pre>` ou `white-space: pre-wrap` — **não** renderizar como HTML (prevenção de XSS).
- Contraste label sobre background: `#9ca3af` sobre `#22252d` = 4.65:1 ✓ WCAG AA.

---

## 6. StatusBadge

### 6.1 Anatomia base

```
height: 22px (min)
padding: 2px 8px
border-radius: 4px (rounded-sm)
border: 1px solid
font: 9px / 800 / Inter / uppercase / tracking 0.08em
display: inline-flex
align-items: center
```

### 6.2 Variantes de cor

| Variante | Background | Borda | Texto |
|---|---|---|---|
| **success** | `#052e25` (success-dim) | `#047857` | `#6ee7b7` |
| **warning** | `#3a2a05` (warning-dim) | `#a16207` | `#fde68a` |
| **danger** | `#3b1111` (danger-dim) | `#b91c1c` | `#fca5a5` |
| **info** | `#1e3a5f` (info-dim) | `#1d4ed8` | `#93c5fd` |
| **curator** | `#2e1065` | `#6d28d9` | `#ddd6fe` |
| **neutral** | `#1f2937` | `#374151` | `#9ca3af` |

> **Nota:** A variante `curator` mantém violeta intencionalmente para diferenciar visualmente do accent azul. Não alterar.

### 6.3 Mapeamento completo de domínio

#### `CardStatus` (CONTEXT.md: `app/models/enums.py:17-25`)

| Valor do enum | Rótulo PT-BR | Variante badge | Justificativa |
|---|---|---|---|
| `generated` | Gerado | **neutral** | Estado inicial, neutro |
| `needs_review` | Precisa de revisão | **warning** | Exige atenção humana |
| `approved` | Aprovado | **success** | Revisado e liberado |
| `published` | Publicado | **success** | Em produção |
| `reported` | Reportado | **danger** | Problema identificado |
| `revised` | Revisado | **success** | Report tratado com revisão |
| `deprecated` | Depreciado | **danger** | Inativo permanentemente |
| `archived` | Arquivado | **neutral** | Fora de circulação |

#### `CardVersionStatus` (CONTEXT.md: `app/models/enums.py:28-35`)

| Valor do enum | Rótulo PT-BR | Variante badge |
|---|---|---|
| `generated` | Gerado | **neutral** |
| `needs_review` | Precisa de revisão | **warning** |
| `approved` | Aprovado | **success** |
| `published` | Publicado | **success** |
| `rejected` | Rejeitado | **danger** |
| `superseded` | Substituído | **neutral** |

#### `DeckStatus` (CONTEXT.md: `app/models/enums.py:42-45`)

| Valor do enum | Rótulo PT-BR | Variante badge |
|---|---|---|
| `draft` | Rascunho | **neutral** |
| `published` | Publicado | **success** |
| `archived` | Arquivado | **neutral** |

#### `ReleaseAction` (CONTEXT.md: `app/models/enums.py:48-52`)

| Valor do enum | Rótulo PT-BR | Variante badge |
|---|---|---|
| `added` | Adicionado | **success** |
| `updated` | Atualizado | **info** |
| `removed` | Removido | **danger** |
| `deprecated` | Depreciado | **warning** |

#### `UserRole` (CONTEXT.md: `app/models/enums.py:97-100`)

| Valor do enum | Rótulo PT-BR | Variante badge |
|---|---|---|
| `admin` | Admin | **success** |
| `curator` | Curador | **curator** (violeta) |
| `reviewer` | Revisor | **warning** |
| `student` | Aluno | **info** |

#### `ReviewDecision` (in `POST /admin/reports/{id}/review`)

| Valor | Rótulo PT-BR | Variante badge |
|---|---|---|
| `rejected` | Rejeitado | **danger** |
| `duplicate` | Duplicado | **warning** |
| `converted_to_new_version` | Convertido em nova versão | **success** |

#### Tags de conteúdo (Scrimba pattern — StatusBadge de deck/curso)

Estas tags indicam o tipo/acessibilidade do deck, similar ao PRO/HOT/FREE/UPDATED da referência:

| Tag | Background | Borda | Texto | Uso |
|---|---|---|---|---|
| **PRO** | `rgba(139,92,246,0.20)` | `#8b5cf6` | `#8b5cf6` | Deck pago/premium |
| **HOT** | `rgba(239,68,68,0.20)` | `#ef4444` | `#ef4444` | Deck em destaque |
| **FREE** | `rgba(59,130,246,0.20)` | `#3b82f6` | `#3b82f6` | Deck gratuito |
| **UPDATED** | `rgba(168,85,247,0.20)` | `#a855f7` | `#a855f7` | Deck recém-atualizado |

> Essas tags de tipo são distintas do StatusBadge de curadoria — podem coexistir na mesma linha de card.

### 6.4 Padrão CSS completo

```css
.status-badge {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border: 1px solid #374151;     /* border-strong */
  border-radius: 4px;
  color: #9ca3af;                /* text-muted — default: neutral */
  background: #1f2937;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* SUCCESS */
.status-published, .status-approved, .status-active,
.status-created, .status-added, .status-admin,
.status-revised, .status-subscribed, .status-converted_to_new_version {
  color: #6ee7b7;
  border-color: #047857;
  background: #052e25;
}

/* WARNING */
.status-needs_review, .status-open, .status-pending,
.status-in_review, .status-reviewer, .status-duplicate, .status-deprecated {
  color: #fde68a;
  border-color: #a16207;
  background: #3a2a05;
}

/* DANGER */
.status-reported, .status-rejected, .status-inactive,
.status-error, .status-removed, .status-archived {
  color: #fca5a5;
  border-color: #b91c1c;
  background: #3b1111;
}

/* INFO (azul) */
.status-updated, .status-student, .status-draft {
  color: #93c5fd;
  border-color: #1d4ed8;
  background: #1e3a5f;
}

/* CURATOR (violeta — não alterar) */
.status-curator {
  color: #ddd6fe;
  border-color: #6d28d9;
  background: #2e1065;
}

/* NEUTRAL */
.status-generated, .status-superseded {
  color: #9ca3af;
  border-color: #374151;
  background: #1f2937;
}
```

### 6.5 Acessibilidade

- **Não usar apenas cor** para comunicar status — o texto abreviado (ex: "PUBLICADO") já carrega o significado.
- Cada badge deve ter `title` ou `aria-label` com o rótulo completo em português (ex: `aria-label="Status: Publicado"`).
- Contraste: verificar todos os pares de cor acima contra WCAG AA (4.5:1 para texto pequeno / 3:1 para texto ≥ 18px):
  - `#6ee7b7` sobre `#052e25`: ~7.2:1 ✓
  - `#fde68a` sobre `#3a2a05`: ~8.1:1 ✓
  - `#fca5a5` sobre `#3b1111`: ~6.3:1 ✓
  - `#93c5fd` sobre `#1e3a5f`: ~5.8:1 ✓
  - `#ddd6fe` sobre `#2e1065`: ~7.4:1 ✓
  - `#9ca3af` sobre `#1f2937`: ~5.9:1 ✓
