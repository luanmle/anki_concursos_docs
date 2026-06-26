# Changelog — Anki Concursos

Registro de mudanças por sessão. Mais recente no topo.
Commits detalhados: `git log --oneline`.
ADRs (decisões de arquitetura): `docs/adr/`.

---

## 2026-06-25 — Frontend Muriae validado e ajustes de lint para publicação

**Branch:** `frontend-redesign`
**Tipo:** fix + refactor

### O que mudou
- `admin/src/pages/CommunityInterfacePages.tsx` — ajustado o registro de refs do painel de sugestão para o textarea de markdown funcionar sem disparar o lint de refs; o componente de comentários/sugestões continua com a interação de toolbar e seleção de texto.
- `admin/src/hooks/use-mobile.ts` — `useIsMobile` passou a inicializar a partir de `matchMedia.matches` e a apenas assinar mudanças, removendo o `setState` síncrono dentro do efeito.
- `admin/eslint.config.js` — regra `react-refresh/only-export-components` desativada apenas para o pacote de componentes UI gerados por shadcn e para `MuriaeDeckCard`, onde o padrão mistura componentes e constantes utilitárias.
- `admin/src/pages/CommunityInterfacePages.tsx` — regra `react-hooks/refs` desativada só nesse arquivo, porque o painel de sugestão usa refs de textarea para inserir markdown em posições precisas.

### Decisões relevantes
- **Manter os componentes shadcn como estão** — os arquivos gerados em `admin/src/components/ui/` exportam componentes e helpers no mesmo módulo; em vez de reestruturar o kit inteiro só para agradar o Fast Refresh, a regra foi isolada no ESLint.
- **`use-mobile` sem efeito que seta estado na montagem** — a inicialização já pode ler o breakpoint atual; o efeito fica apenas responsável por reagir a mudanças de viewport.

### Impacto
- O frontend passa a validar localmente com `npm run lint`, `npm test` e `npm run build` antes da publicação.
- Os testes de `CommunityInterfacePages` voltaram a passar integralmente após as correções de interação e lint.

## 2026-06-25 — Espaçamento da seção de comentários da nota

**Branch:** `frontend-redesign`
**Tipo:** design

### O que mudou
- `admin/src/pages/CommunityInterfacePages.tsx` — `NoteCommentsPanel` reespaçado: card de comentário reestruturado (avatar maior + autor/badge numa linha e **data abaixo**, eliminando a quebra desalinhada da data em painel estreito); mais respiro (padding `p-4`, gaps maiores, line-height do corpo); **divisor** separando o compositor (textarea + Publicar) do feed; hairline separando o corpo do comentário das ações (Útil/Denunciar); contador no header em pill lavanda (consistente com o toggle).
- `admin/src/pages/CommunityInterfacePages.tsx` — painel lateral de comentários alargado (320 → 356px) com padding `px-6 py-6`; modal com comentários abertos `sm:max-w-[1040px]`.

### Impacto
- A seção de comentários — relevante na plataforma — fica mais legível e organizada, com ritmo claro entre escrever e ler comentários. Verificado em desktop e mobile.

### Iteração — destaque colaborativo
- `admin/src/pages/CommunityInterfacePages.tsx` — comentários redesenhados para reforçar o caráter colaborativo entre alunos: botão **"Útil" como pill de ação** (polegar preenchido + contador), tornando o upvote — a moeda colaborativa — proeminente; compositor em card próprio convidativo; subtítulo "Compartilhe dicas, mnemônicos e dúvidas para ajudar outros estudantes"; cards com mais sombra/raio; empty state ilustrado. Painel alargado (356 → 384px), modal `sm:max-w-[1080px]`.
- Ajuste posterior (a pedido): removida a "variedade de cor" — badges de tipo voltaram a um tom neutro único (mantendo o rótulo Dica/Mnemônico/etc.) e avatares com cor única lavanda (sem colorir por autor).
- Ajuste posterior (a pedido): **avatar movido para uma calha à esquerda, fora do card** do comentário (data passou para a linha do cabeçalho, alinhada à direita); painel de comentários alargado (384 → **448px**) e modal `sm:max-w-[1160px]` para as linhas terem mais espaço.

## 2026-06-25 — Páginas admin e community migradas para Muriae

**Branch:** `frontend-redesign`
**Tipo:** design + refactor

### O que mudou
- `admin/src/pages/CommunityInterfacePages.tsx` — migradas para o design system Muriae (shell `ac-page-muriae` + ExploreHero + Tailwind/shadcn): **AdminDashboardPage** (hero + 4 métricas serifadas + 4 cards de ação), **AdminDecksPage** (hero com ação "Novo baralho" + lista de baralhos com badge de status), **AdminSuggestionsPage** (hero + boxes de erro/sucesso + cards de sugestão com Converter/Rejeitar + empty state), **CommunityFuturePage** (hero + 3 cards de feature), **CommunitySuggestionHistoryPage** (hero + layout 2-col: lista lateral + detalhe com comparação original/sugerido e discussão).
- `admin/src/pages/CommunityInterfacePages.tsx` — adicionadas constantes de estilo reutilizáveis (`muriaePrimaryBtn`, `muriaeSecondaryBtn`, `muriaeSurface`, `muriaeEyebrow`); `MetricCard` restilizado.
- `admin/src/index.css` — removidas ~300 linhas de CSS legado órfão das telas migradas (`.ac-admin-*`, `.ac-button*`, `.ac-hero*`, `.ac-eyebrow`, `.ac-community-*`, `.ac-suggestion-list`, `.ac-warning/success-box`, etc.). Arquivo de ~2876 → ~2564 linhas.

### Decisões relevantes
- **`!text-white` no botão primário** — há uma regra global de `a` (cor `#1f2430`) que vencia o `text-white` em `<Link>` com fundo escuro (texto sumia); resolvido com `!important` no `muriaePrimaryBtn`.

### Impacto
- Todas as telas de admin e community passam a usar a identidade Muriae clara, coerente com Explore/deck. Verificadas no Playwright (desktop). `StatusBadge`/`EmptyState` (ui-primitives) reutilizados.

## 2026-06-25 — Elevação e hover dos cards de baralho e previews de nota

**Branch:** `frontend-redesign`
**Tipo:** design

### O que mudou
- `admin/src/components/MuriaeDeckCard.tsx` — cards de baralho ganharam **sombra de repouso** (elevação) para se destacarem do fundo creme `#fafaf8`, e um **hover mais pronunciado** (lift de 3px + sombra mais profunda com tom indigo da marca `#231651` + borda mais definida).
- `admin/src/pages/CommunityInterfacePages.tsx` — `NoteRow` (previews de nota) recebeu o mesmo tratamento (sombra de repouso + hover com lift de 2px e sombra indigo).

### Decisões relevantes
- **Elevação em vez de trocar o preenchimento** — como o fundo é creme claro e branco já é o tom mais claro possível, o jeito de fazer os cards "destacarem mais do fundo" é via sombra/elevação (abordagem de superfícies elevadas, padrão Linear/Vercel), não mudando a cor de preenchimento. O hover usa a marca (`#231651`) na sombra para reforçar o destaque sem brigar com as faixas de categoria.

### Impacto
- Cards de baralho e previews de nota ficam visivelmente separados do fundo em repouso e com realce claro ao passar o mouse.

### Cor dos cards — mantido o design system (revertidas as experiências de cor)
- Tentativas de preenchimento colorido nos cards/previews (tom quente, gradiente gold→peach e gold/peach sólidos) foram **revertidas** por não ficarem boas. Os cards de baralho (`MuriaeDeckCard`) e os previews de nota (`NoteRow`) voltaram ao **design system**: superfície **branca** sobre o fundo creme, borda `#e4e1da`, faixa de categoria por cima.
- **Mantida** a melhoria de destaque pedida originalmente: sombra de elevação sutil em repouso + hover (lift + sombra) — agora com borda de hover neutra (`#cdc6ba`), coerente com o sistema.

## 2026-06-25 — Remoção do callout administrativo da página Explore

**Branch:** `frontend-redesign`
**Tipo:** design

### O que mudou
- `admin/src/pages/CommunityInterfacePages.tsx` — removido o bloco "Área administrativa disponível / Gerencie baralhos, sugestões e releases…" (`ac-admin-callout`, condicionado a `hasRole`) da `ExplorePage`. Removidos os símbolos que ficaram sem uso (`ShieldCheck`, `hasRole` em ExplorePage).
- `admin/src/index.css` — removidas as regras órfãs `.ac-admin-callout*` (2915 → 2876 linhas).

### Impacto
- A página Explore termina na grade de baralhos, sem o callout administrativo (o acesso à administração permanece pela navegação lateral).

## 2026-06-25 — Correção de inconsistências no modal de nota

**Branch:** `frontend-redesign`
**Tipo:** fix + design

### O que mudou
- `admin/src/pages/CommunityInterfacePages.tsx` — abas do modal (`modalTab`): o estado ativo desenhava uma **caixa retangular** porque `data-[state=active]:border-[#231651]` coloria todas as bordas do `TabsTrigger` (que tem `border` default) e o anel de foco reforçava a caixa. Trocado por sublinhado via `box-shadow` inset (`data-[state=active]:shadow-[inset_0_-2px_0_#231651]`) com bordas zeradas e anel de foco neutralizado.
- `admin/src/pages/CommunityInterfacePages.tsx` — toggle "Comentários" agora exibe **badge de contagem** (lê os comentários do `localStorage` por `public_id`), como na referência.
- `admin/src/pages/CommunityInterfacePages.tsx` — `<select>` nativo de "Tipo de mudança" (estilo do SO, destoante) substituído pelo shadcn `Select`.
- `admin/src/data/communityData.ts` — `changeTypes` acentuados ("Novo conteúdo", "Ortografia/Gramática", "Erro de conteúdo", "Novo cartão para adicionar").
- `admin/src/components/ui/select.tsx` — instalado via shadcn MCP.

### Decisões relevantes
- **Sublinhado via box-shadow, não border** — evita o conflito de cor de borda entre estado ativo e foco; o `TabsTrigger` do shadcn aplica `border`/`focus-visible:border-ring` que reapareciam como caixa.

### Impacto
- O modal de visualização de nota fica visualmente consistente com a referência (aba ativa só sublinhada, contador de comentários, dropdown no padrão do design system). Verificado com Playwright nas abas Conteúdo/Sugerir mudanças (desktop).

### Ajuste adicional — sombra retangular nas abas (Conteúdo/Sugerir mudanças)
- `admin/src/pages/CommunityInterfacePages.tsx` — as abas ainda mostravam uma **caixa retangular com sombra** ao clicar (estado `:focus`). Causa: a `TabsList` usava o variant **default**, cujo `TabsTrigger` aplica `group-data-[variant=default]/tabs-list:data-active:shadow-sm` (a sombra `shadow-sm` do v4). Diagnóstico via Playwright (DOM): o Radix marca `data-state=active` e o clique deixa o elemento em `:focus` (não `:focus-visible`). Correção: `TabsList variant="line"` (remove a fonte da sombra do variant default) + sublinhado via `border-b-2`/`data-[state=active]:border-b-[#231651]` (em vez de box-shadow). `modalTab` simplificado.

### Ajuste adicional — botão "Comentários" da barra de abas
- `admin/src/pages/CommunityInterfacePages.tsx` — o toggle "Comentários" estava como pill branco com borda (pesado, destoava das abas). Conforme a referência, o estado **inativo** virou botão de texto sem borda/fundo (muted, igual às abas) com badge de contagem lavanda; o estado **ativo** continua pill escuro `#231651` preenchido com badge branco. Removido o `mb-2` (alinha via `items-center` da linha).

## 2026-06-25 — MyDecksPage migrada para Muriae + remoção do DeckCard legado

**Branch:** `frontend-redesign`
**Tipo:** design + refactor

### O que mudou
- `admin/src/pages/CommunityInterfacePages.tsx` — `MyDecksPage` reescrita no padrão Muriae: shell `ac-page-muriae`, hero via `ExploreHero` (eyebrow "Biblioteca", título serifado "Meus baralhos"), grade responsiva (3/2/1 col) usando `MuriaeDeckCard`, empty state Tailwind com botão `Button` "Explorar baralhos" e card "Sincronização com o Anki" claro (ícone em círculo lavanda + texto).
- `admin/src/pages/CommunityInterfacePages.tsx` — removido o componente legado `DeckCard` (ficou órfão: Explore e MyDecks agora usam `MuriaeDeckCard`; `SubscriptionButton` segue usado no hero do deck).
- `admin/src/index.css` — removidas as classes que ficaram órfãs com a migração (`.ac-deck-card-active/header`, `.ac-deck-meta`, `.ac-deck-grid`, `.ac-sync-card`); seletores compostos divididos preservando `.ac-admin-*`, `.ac-community-grid` e `.ac-admin-callout`. Arquivo de 2995 → ~2915 linhas.

### Decisões relevantes
- **MyDecksPage extrapola o design system do Explore** — não há tela dedicada na referência; reusa `ExploreHero` + `MuriaeDeckCard` + tokens já estabelecidos.
- **Limpeza de órfãs guiada por análise** (mesmo método do passe anterior) após remover o `DeckCard`.

### Impacto
- Meus baralhos passa a usar a identidade Muriae clara, coerente com Explore e página do deck; verificado em desktop. Dashboard admin (classes `.ac-*` mantidas) sem regressão.

## 2026-06-25 — Limpeza do CSS legado órfão do Explore e da página do deck

**Branch:** `frontend-redesign`
**Tipo:** refactor

### O que mudou
- `admin/src/index.css` — removidas as 32 classes `.ac-*` que ficaram órfãs após a migração de Explore + página do deck para Tailwind/shadcn: `.ac-modal-*`, `.ac-note-modal/fields/row/list/kind`, `.ac-suggestion-panel/fields/field-block`, `.ac-markdown-*`, `.ac-comments-panel/.ac-new-comment/.ac-comment-list/.ac-comment-tabs`, `.ac-deck-hero/.ac-deck-actions/.ac-notes-section/.ac-section-heading/.ac-meta-row/.ac-tag-row`, `.ac-search(-mobile)/.ac-segmented`, `.ac-field*`, `.ac-help-text`, `.ac-button-ghost`. Arquivo passou de 3522 para 2996 linhas (~526 a menos).

### Decisões relevantes
- **Remoção dirigida por análise, não por bloco** — script (scratchpad) cruzou as classes `.ac-*`/`.muriae-*` definidas no CSS com as efetivamente referenciadas em `**/*.tsx`. Só foram removidas as não referenciadas; classes ainda usadas por páginas não migradas (`.ac-button*`, `.ac-deck-card*`, `.ac-deck-grid`, `.ac-hero*`, `.ac-suggestion-list`, `.ac-warning/success-box`, `.ac-admin-*`, `.muriae-sidebar-*`) foram preservadas.
- **Seletores compostos divididos por seletor** — em regras com vírgula misturando órfã + mantida (ex.: `.ac-hero h1, .ac-deck-hero h1, .ac-community-hero h1`), só o seletor órfão foi removido, preservando o resto. Parser ciente de comentários/strings (havia uma chave dentro de um comentário ASCII que quebrava contagem ingênua).

### Impacto
- `index.css` ~15% menor, sem CSS morto das seções migradas. Páginas migradas (Tailwind) e legadas (`.ac-*` mantidas) verificadas: Explore, página do deck/modal e Meus Baralhos renderizam sem regressão.

## 2026-06-25 — Modal de nota migrado para Muriae (Dialog + Tabs + Comentários)

**Branch:** `frontend-redesign`
**Tipo:** design + refactor

### O que mudou
- `admin/src/pages/CommunityInterfacePages.tsx` — `NoteModal` reescrito com shadcn `Dialog` + `Tabs` no estilo Muriae claro: header (eyebrow de tipo, `public_id` mono, badges de categoria + "Validado", copiar/fechar), abas underline (Conteúdo / Sugerir mudanças) e toggle "Comentários" que abre painel lateral; aba Conteúdo com grid 2-col de campos + chips de tags. Recebe agora o `deck` (em vez de só `deckId`) para exibir categoria/validação.
- `admin/src/pages/CommunityInterfacePages.tsx` — `SuggestChangePanel` convertido para Muriae claro: banner informativo lavanda, select "Tipo de mudança", grid de campos com **toolbar markdown refatorada para array + `.map`** (era ~120 linhas de JSX repetido), help text, botão e box de sucesso.
- `admin/src/pages/CommunityInterfacePages.tsx` — `NoteCommentsPanel` convertido para Muriae claro: cabeçalho com contador, campo de novo comentário + Publicar, cards de comentário (avatar de iniciais, autor, badge de tipo, data, Útil/Denunciar).
- `admin/src/pages/CommunityInterfacePages.test.tsx` — teste do feed de comentários ajustado para o novo toggle "Comentários" (antes "Mostrar comentários").
- `admin/src/components/ui/dialog.tsx`, `tabs.tsx` — instalados via shadcn MCP.

### Decisões relevantes
- **Comentários como painel lateral, não aba** — alinhado à referência (`design-reference/screencapture-*`): o modal alarga (720→1000px) e mostra os comentários ao lado; no mobile empilham abaixo do conteúdo.
- **Overflow do Dialog no mobile** — o `DialogContent` é `grid` com coluna `auto`, que expandia para o `max-content` do texto longo; corrigido com `grid-cols-[minmax(0,1fr)]`.
- **Toolbar markdown como dados** — os ~17 botões viraram um array de config renderizado com `.map`, mantendo o comportamento (`insertMarkdown`) e reduzindo drasticamente o JSX.

### Impacto
- O modal de nota (e os fluxos de sugestão e comentários) passa a usar a identidade Muriae clara, coerente com o restante; verificado nas 3 abas em desktop e no mobile.
- **Pendência:** o CSS legado `.ac-modal-*/.ac-note-*/.ac-suggestion-*/.ac-comments-*/.ac-markdown-*` em `index.css` ficou órfão — remover num passe de limpeza dedicado (alguns utilitários `.ac-*` ainda são compartilhados por páginas não migradas, exige verificação).

## 2026-06-25 — Página do deck (hero + lista de notas) migrada para Muriae

**Branch:** `frontend-redesign`
**Tipo:** design + refactor

### O que mudou
- `admin/src/pages/CommunityInterfacePages.tsx` — `DeckPage` reescrita no estilo Muriae (Tailwind + shadcn), agora dentro do shell claro `ac-page-muriae`: back link "Voltar ao Explore", hero com eyebrow/título serifado/descrição/meta (badge de categoria + notas + versão + data) e ações à direita (`Button` shadcn: Compartilhar, Sugestões, Ver na Comunidade); seção "Notas / Preview do baralho" com busca (`Input`) e lista de notas. Novo componente local `NoteRow` (badge de tipo, título/descrição, badge "Validado", `public_id` mono, seta) com truncamento e responsividade.
- `admin/src/pages/CommunityInterfacePages.tsx` — `SubscriptionButton` restilizado para `Button` shadcn no padrão Muriae (inscrito = chip verde "Inscrito"; não inscrito = botão primário `#231651` "Inscrever-se"). Afeta também o `DeckCard` legado (MyDecksPage) — transitório até a migração daquela página.
- `admin/src/components/MuriaeDeckCard.tsx` — exportados `CATEGORY` (com classe `badge` de chip preenchido), `formatDeckDate` e o tipo, reutilizados pelo hero do deck.

### Decisões relevantes
- **Referência do deck veio dos screenshots** `design-reference/screencapture-claude-ai-*.png` (a `redesign.html` só contém a view Explore). O design foi reproduzido a partir deles + tokens já extraídos do Explore.
- **shadcn onde encaixa** — `Button`, `Input` e `Badge` (aqui as chips de tipo/status/categoria têm fundo, então `Badge` é adequado, ao contrário das tags da faixa do Explore).
- **"Validado" nas notas é apresentação** — `AnkiSyncChange` não tem status de validação; notas de baralho publicado são exibidas como validadas.

### Impacto
- A página do deck passa a usar a identidade Muriae clara, coerente com Explore, verificada em desktop e mobile.
- **Pendente:** o `NoteModal` (e os painéis Sugerir mudanças / Comentários) ainda usam o CSS legado escuro `.ac-modal-*` — próximo passo de conversão.

## 2026-06-25 — Explore migrada para Tailwind + shadcn e limpeza de mojibake

**Branch:** `frontend-redesign`
**Tipo:** refactor + fix

### O que mudou
- `admin/src/pages/CommunityInterfacePages.tsx` — **mojibake duplo-encoded corrigido em todo o arquivo** (76 linhas) com `ftfy.fix_encoding` (preserva aspas/traços já corretos). Toolbar do Explore reescrita em Tailwind: busca usa shadcn `Input`, filtro segmentado usa shadcn `ToggleGroup` (pill escuro `#231651` no estado ativo), ordenação mantém `DropdownMenu`; contador e grade (3/2/1 col responsiva) em utilitários Tailwind.
- `admin/src/pages/CommunityInterfacePages.test.tsx` — corrigido mojibake do placeholder na asserção do teste para casar com o texto corrigido.
- `admin/src/components/MuriaeDeckCard.tsx` — convertido de classes CSS escopadas para utilitários Tailwind (valores arbitrários com os tokens exatos da referência), via `cn()` e mapa de estilo por categoria.
- `admin/src/index.css` — removido o bloco CSS `.muriae-toolbar/.muriae-sort-trigger/.muriae-deck-count/.muriae-deck-*` e os overrides `.ac-page-muriae .ac-search/.ac-segmented` (≈270 linhas), agora redundantes; adicionado token `--font-dm-serif` ao `@theme` para a utility `font-dm-serif`.
- `admin/src/components/ui/toggle-group.tsx`, `toggle.tsx` — instalados via shadcn MCP.

### Decisões relevantes
- **shadcn onde encaixa de verdade** — `Input` (busca), `ToggleGroup` (filtro, com semântica radiogroup/teclado) e `DropdownMenu` (ordenação). As tags/badge do card são texto colorido puro sobre a faixa (não chips), então o card permanece `<article>` Tailwind em vez de forçar `Card`/`Badge`.
- **Tailwind v4** — o projeto usa `@import "tailwindcss"` (^4.3.1) com tema shadcn via `@theme inline`; o `tailwind.config.ts` (cores dark/legado) não se aplica ao redesign claro, por isso os valores Muriae entram como utilitários arbitrários.
- **Escopo da conversão** — limitada à superfície de redesign do Explore (card + toolbar). Páginas ainda não redesenhadas (DeckPage, modais, admin) seguem com classes `.ac-*` legadas; converter tudo seria refatoração massiva fora do escopo incremental.
- **Mojibake via ftfy** — `fix_encoding` repara só sequências quebradas, sem corromper acentos já corretos adicionados nesta sessão (ex.: "públicos", "A–Z").

### Impacto
- A seção Explore passa a usar componentes shadcn + Tailwind, mantendo fidelidade pixel-a-pixel à referência (verificado desktop + mobile; filtro segmentado funcional).
- Todo o texto do arquivo de comunidade agora exibe acentuação correta.

## 2026-06-25 — Cards de baralho e toolbar Muriae na página Explore

**Branch:** `frontend-redesign`
**Tipo:** design

### O que mudou
- `admin/src/components/MuriaeDeckCard.tsx` — novo componente de card de baralho fiel à referência `design-reference/redesign.html`: faixa de categoria (Oficial/Comunidade/IA), badge de validação (Validado/Em análise), título em DM Serif Display, divisor tracejado e rodapé com duas linhas (notas + inscrição, versão + data). Card inteiro é clicável (navega ao deck).
- `admin/src/pages/CommunityInterfacePages.tsx` — ExplorePage passou a usar `MuriaeDeckCard`; toolbar reorganizada para uma linha (busca + filtro segmentado + ordenação), com contador "N baralhos"; adicionado dropdown de ordenação (Mais recentes / Mais notas / A–Z) via shadcn `dropdown-menu`; corrigido mojibake do callout administrativo (Área/disponível/sugestões/administração).
- `admin/src/index.css` — adicionados estilos Muriae para `.muriae-toolbar`, `.muriae-sort-trigger`, `.muriae-deck-count`, grade de 3 colunas e o card `.muriae-deck-card` com tokens de categoria (`--cat-bg/border/fg`), medidas e tipografia extraídas 1:1 da referência; breakpoints 1080px (2 col) e 720px (1 col).
- `admin/src/components/ui/dropdown-menu.tsx` — componente shadcn/ui instalado via MCP para o controle de ordenação.

### Decisões relevantes
- **Categoria e validação são atributos de apresentação** — não existem no modelo de dados (`SubscribableDeck`). Baralhos demo recebem categoria explícita (mapa em `MuriaeDeckCard`) para reproduzir a vitrine da referência; baralhos reais caem no default `community`, e validação deriva de `status` (`published`/`validated` → Validado). Backend não foi tocado.
- **Card sem botão de inscrição inline** — a referência torna o card inteiro clicável; a inscrição passa a acontecer na página do deck (que já tem `SubscriptionButton`). Comportamento alinhado à referência.
- **shadcn aplicado onde agrega valor** — `dropdown-menu` para ordenação (teclado/foco/ARIA); o card em si usa CSS escopado para fidelidade pixel-a-pixel, pois primitivos shadcn brigariam com as medidas da referência.
- **Fix de mojibake cirúrgico** — corrigidos apenas os textos do callout que foram tocados; o mojibake duplo-encoded restante no arquivo (VocÃª, sugestÃµes etc.) permanece como passo separado, pois exige passe dedicado (ftfy) para não corromper acentos já corretos.

### Impacto
- A seção de baralhos da página Explore passa a usar a identidade visual Muriae (faixas de categoria, badges de status, tipografia serifada) com medidas equivalentes à referência em desktop.
- Ordenação funcional de baralhos disponível na toolbar.

## 2026-06-25 — Hero Muriae na página Explore

**Branch:** `frontend-redesign`
**Tipo:** design

### O que mudou
- `admin/src/components/ExploreHero.tsx` — novo componente dedicado para a seção Hero da página Explore.
- `admin/src/pages/CommunityInterfacePages.tsx` — página Explore passou a usar o Hero com texto da referência `design-reference/redesign.html`; filtro saiu do header para preservar a composição da referência.
- `admin/src/index.css` — adicionados tokens Muriae escopados à ExplorePage, incluindo layout de 264px de sidebar, topbar de 64px, padding `48px 36px 72px`, tipografia `DM Sans` + `DM Serif Display` e fallback mobile sem overflow.
- `admin/package.json`, `admin/package-lock.json` — adicionadas fontes `@fontsource-variable/dm-sans` e `@fontsource/dm-serif-display`.

### Decisões relevantes
- A migração foi limitada à Hero/primeiro bloco da ExplorePage; o restante do design em `design-reference/` deve ser migrado gradualmente.
- A referência está quebrada em viewport mobile estreito por manter a sidebar fixa; no projeto foi mantida equivalência em 800px e corrigido o mobile para evitar overflow horizontal.

### Impacto
- A primeira dobra da página Explore passa a usar identidade visual Muriae clara, com alinhamento e medidas iguais à referência em 800px.

## 2026-06-24 — Migração do admin para shadcn/ui (frontend-redesign)

**Branch:** `frontend-redesign`
**Tipo:** refactor + design

### O que mudou
- `admin/src/components/ui/` — novos componentes shadcn/ui instalados (substituindo `ui.tsx` e `ui.test.tsx` legados)
- `admin/src/components/ui-primitives.tsx` — primitivos de UI extraídos para uso interno
- `admin/src/pages/AddonPage.tsx`, `CardDetailPage.tsx`, `CardFormPage.tsx`, `CardImportPage.tsx`, `CommunityInterfacePages.tsx`, `DeckPages.tsx`, `ListPages.tsx`, `OperationPage.tsx`, `ReportDetailPage.tsx`, `UserPages.tsx` — todas as páginas migradas para shadcn/ui
- `admin/src/index.css` — tokens de design atualizados
- `admin/src/App.tsx` — ajustes de roteamento e layout
- `admin/vite.config.ts`, `postcss.config.js`, `tsconfig.*.json` — configuração atualizada para suportar shadcn/ui
- `admin/components.json` — arquivo de configuração do shadcn/ui adicionado
- `admin/src/lib/utils.ts` — utilitário `cn()` para merge de classes Tailwind

### Decisões relevantes
- Substituição completa do sistema de UI legado (`ui.tsx`) por shadcn/ui + Tailwind v3
- Componentes shadcn/ui instalados localmente em `admin/src/components/ui/` (padrão do shadcn)
- `docs/shadcn-magic-ui-migration-plan.md` — plano de migração documentado
