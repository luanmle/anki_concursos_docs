# Changelog — Anki Concursos

Registro de mudanças por sessão. Mais recente no topo.
Commits detalhados: `git log --oneline`.
ADRs (decisões de arquitetura): `docs/adr/`.

---

## 2026-06-27 — Página de Sugestões de Mudanças (fila de moderação)

**Branch:** `codex/publish-admin`
**Tipo:** feature + design

### O que mudou
- `admin/src/components/suggestions/DiffViewer.tsx` (novo) — diff por campo no estilo AnkiHub: Atual (vermelho) vs Sugerido (verde), HTML sanitizado (texto, tags, imagens, cloze), toggle `<>` por painel para ver o HTML-fonte; também renderiza diff de tags (adicionadas verdes / removidas riscadas em vermelho).
- `admin/src/components/suggestions/diff.ts` (novo) + `diff.test.ts` — `normalizeFieldDiff`: normaliza cada campo de `fields` para `{old,new}`, tolerante a `{old,new}` ou string crua (separado em módulo p/ não disparar `react-refresh/only-export-components`).
- `admin/src/components/suggestions/SuggestionCard.tsx` (novo) — card de sugestão: avatar (iniciais do e-mail), autor, data, ID, badge de status, título (rótulo do tipo), votos display-only, bloco Justificativa, `DiffViewer`, e ações Aceitar/Rejeitar com comentário de revisão opcional (some quando não pendente, mostra "Revisada por…").
- `admin/src/components/suggestions/SuggestionList.tsx` (novo) — filtros de status (Aguardando/Aceitas/Rejeitadas) com contagem por aba + estados loading/error/empty.
- `admin/src/pages/CommunityInterfacePages.tsx` — `AdminSuggestionsPage` reescrita: consome `GET /admin/note-suggestions` (3 queries por status p/ contagens) e `POST /admin/note-suggestions/{id}/review`. Removido o fluxo localStorage antigo e os órfãos `resolveSuggestionCardId`/`buildVersionPayload`; imports `CardSummary`/`CardVersion` removidos.
- `admin/src/pages/CommunityInterfacePages.test.tsx` — testes da página migrados de localStorage para o backend (lista do diff, aceitar/rejeitar via endpoint de review).

### Decisões relevantes
- **Contrato de diff `fields[campo] = {old,new}`** (HTML) — auto-contido, a UI compara sem buscar a versão atual; diff calculado no add-on (igual AnkiHub). `normalizeFieldDiff` aceita também string crua (só sugerido) p/ clientes antigos. Como o add-on ainda não envia, esta UI fixa o contrato.
- **Substitui localStorage** — `/admin/suggestions` agora é a fila persistente; aceitar/rejeitar chama o endpoint de review (sem conversão automática em nova versão neste bloco).
- **Votos display-only** — `NoteSuggestion` não tem campo de voto no backend; o controle aparece (fidelidade à referência) mas desabilitado, marcado com `ponytail:`.

### Impacto
- A equipe de curadoria tem fila de moderação real para sugestões vindas do add-on, com diff visual e revisão. Verificado no app real (login admin, dados semeados e removidos): lista, diff (cloze/imagem/tags), aceitar com comentário → migra de Aguardando p/ Aceitas e grava revisor/comentário. Lint limpo, 18 testes passam, build OK.

---

## 2026-06-27 — Sugestoes de notas pelo add-on

**Branch:** `codex/publish-admin`
**Tipo:** backend feature

### O que mudou
- `app/models/entities.py` + `migrations/versions/20260627_0017_note_suggestions.py` — nova tabela `note_suggestions` para persistir sugestoes vindas do add-on.
- `app/schemas/suggestions.py`, `app/repositories/suggestions.py`, `app/services/suggestions.py`, `app/api/routes/suggestions.py` — contrato para criar sugestoes por card existente, sugestoes de nota nova por deck, listar e revisar sugestoes.
- `app/main.py` — registra as rotas e inclui `PATCH` no CORS, necessario para frontend admin.
- `admin/src/types.ts` — tipos TypeScript para a futura tela de sugestoes persistentes.
- `tests/test_suggestions_api.py` — cobre criacao, listagem e revisao no nivel de service.
- `docs/changes/2026-06-27-addon-note-suggestions.md` — documenta contrato, decisoes e gap anterior.

### Decisoes relevantes
- **Sem conversao automatica agora** — aceitar sugestao e criar card version pode reaproveitar o fluxo existente de cards/reports no frontend.
- **Base versionada** — sugestao em card existente guarda o `card_version_id` publicado no momento do envio.
- **Substitui localStorage** — backend agora tem destino persistente para o fluxo que antes existia apenas no frontend comunitario.

### Impacto
- Add-on pode enviar diff de campos/tags/comentario direto para a plataforma.
- Frontend admin ja tem tipos e endpoints para construir fila de moderacao.

---

## 2026-06-27 — Campos protegidos no contrato do add-on

**Branch:** `codex/publish-admin`
**Tipo:** feature

### O que mudou
- `app/models/entities.py` + `migrations/versions/20260627_0016_template_protected_fields.py` — `deck_template_versions` ganhou `protected_fields` JSON com default `[]`, preservando templates existentes.
- `app/schemas/decks.py`, `app/services/decks.py`, `app/api/routes/addon.py` — upload, manifesto e template sync passam a aceitar/expor `protected_fields`; novo endpoint `PATCH /addon/decks/{deck_id}/templates/{template_id}/protected-fields`.
- `admin/src/pages/AddonPage.tsx` + `admin/src/types.ts` — página do add-on ganhou editor de campos protegidos por template, com checkboxes e salvamento via API.
- `tests/test_decks_api.py` — cobre upload com `protected_fields`, atualização por curator/admin, validação de campo desconhecido e propagação no manifesto/template sync.
- `docs/changes/2026-06-27-protected-fields-contract.md` — documentação operacional da mudança.

### Decisões relevantes
- **Contrato `protected_fields`** — mantido o nome usado pelo add-on para retrocompatibilidade direta entre backend e cliente.
- **Proteção por versão de template** — mudar campos protegidos cria nova `DeckTemplateVersion`, preservando histórico e `content_hash`.
- **Permissão de escrita curator/admin** — assinantes podem consumir o contrato, mas não alterar regra de preservação do baralho.

### Impacto
- Add-on pode preservar campos locais definidos pela plataforma sem bloquear o sync inteiro.
- Frontend admin permite configurar quais campos do template não devem ser sobrescritos no Anki local.

## 2026-06-26 — Campos HTML do Anki: render formatado + toggle de fonte + editor WYSIWYG

**Branch:** `frontend-redesign`
**Tipo:** feature + design

Campos do Anki são HTML; antes o modal de nota renderizava `<p>{value}</p>` (React
escapava → notas reais mostravam as tags como texto literal). Adicionado o padrão do
editor do Anki: visão formatada + botão `<>` que alterna para o código-fonte HTML.

### O que mudou
- `admin/src/lib/html.ts` (novo) — `sanitizeHtml` (DOMPurify, allowlist de tags/attrs),
  `htmlToText` (HTML → texto puro p/ previews), `renderCloze` (`{{c1::...}}` → destaque).
- `admin/src/components/HtmlField.tsx` (novo) — `HtmlFieldView` (somente-leitura: HTML
  sanitizado + toggle `<>` p/ fonte mono) e `HtmlFieldEditor` (contenteditable WYSIWYG +
  toolbar via `document.execCommand` + toggle `<>` p/ editar HTML cru; os dois modos
  compartilham a mesma string).
- `admin/src/pages/CommunityInterfacePages.tsx` — aba **Conteúdo** usa `HtmlFieldView`;
  `SuggestChangePanel` troca os textareas markdown por `HtmlFieldEditor` (toolbar virou
  comandos HTML: bold/italic/underline/strike/h3/link/listas/citação/hr/alinhamento);
  `noteTitle`/`noteSummary` passam por `htmlToText` (previews da lista não mostram tags).
- `admin/src/data/communityData.ts` — campos demo enriquecidos com HTML (`<b>`, `<i>`,
  `<span style>`) p/ exercitar render/fonte.
- `admin/package.json` — dep `dompurify`.

### Decisões relevantes
- **Sanitização obrigatória** — campos vêm de sync Anki + sugestões da comunidade
  (não confiável); render de HTML cru = XSS armazenado. Todo HTML passa por DOMPurify.
- **`execCommand` para WYSIWYG** — depreciado mas universal e simples p/ contenteditable
  (o próprio Anki usa contenteditable). DOM do editor só sincroniza do valor ao (re)entrar
  no modo rich, p/ não resetar o cursor a cada tecla.
- **Helpers em `lib/html.ts` separado** — evita o lint `react-refresh/only-export-components`
  (componente + função no mesmo arquivo).

### Impacto
- Modal de nota mostra campos formatados e permite ver/editar o HTML-fonte por campo.
  Validado no app real (login admin): Conteúdo (render + `<>`), Sugerir (WYSIWYG + fonte).
  Lint limpo, build OK, 14 testes passam.

### Iteração — botões cloze (só cartões cloze)
- `admin/src/components/HtmlField.tsx` — `HtmlFieldEditor` ganhou prop `cloze`; quando
  ligada, a toolbar mostra `[...]` (**sempre c1**) e `[...]+` (**continuação: maior `cN`+1**),
  envolvendo a seleção em `{{cN::...}}`. Número calculado do maior `cN` já no campo.
- `admin/src/pages/CommunityInterfacePages.tsx` — passa `cloze={note.card_kind === 'cloze'}`.
- Validado no app: cartão cloze mostra os botões; sequência `[...]+`/`[...]+`/`[...]` →
  `{{c1::Art}}. 5o, {{c2::LXVIII}}, {{c1::CF}}.`; cartão basic não mostra.

## 2026-06-26 — Endpoint de releases para add-on

**Tipo:** backend feature

### O que mudou
- `app/api/routes/addon.py` — novo endpoint autenticado `GET /addon/decks/{deck_id}/releases`.
- `app/services/decks.py` — novo `anki_releases`, exigindo assinatura ativa e retornando releases paginadas.
- `app/schemas/decks.py` + `app/schemas/__init__.py` — novos responses `AnkiDeckReleaseListResponse` e `AnkiDeckReleaseSummaryResponse`.
- `tests/test_decks_api.py` — teste cobre 403 sem assinatura ativa, paginação e contadores por ação.

### Contrato
Resposta por release:
- `release_id`
- `release_number`
- `published_at`
- `summary` (mapeado de `Release.description`)
- `cards_added`
- `cards_updated`
- `cards_removed`
- `cards_deprecated`

### Impacto
- O add-on passa a ter contrato remoto para histórico/changelog de baralho.
- Sem migração de banco: usa `releases` e `release_items` existentes.
- Correção de teste: `test_addon_can_upload_full_deck_package_and_publish_release`
  agora limpa `app.dependency_overrides` só após concluir também `/templates/sync`.

## 2026-06-26 — Modo noturno (dark mode) na superfície Muriae

**Branch:** `frontend-redesign`
**Tipo:** feature + design

Implementado o **modo noturno** presente em `design-reference/redesign.html` para a
superfície já migrada ao design system Muriae (shell + Explore/deck/modal/admin/community).
Paleta dark extraída 1:1 do protótipo via Playwright (computed styles do `[data-theme]`).

### O que mudou
- `admin/src/index.css` — novo sistema de **tokens semânticos `--mu-*`** escopados em
  `:root`, com swap claro→escuro via `html[data-theme="dark"]`. Mapas de
  utilitários Tailwind no `@theme` (`bg-mu-bg`, `text-mu-text`, `border-mu-border`,
  `text-mu-brand`, `bg-mu-brand-bg`, categorias `mu-cat-comm/ai`, status validated/danger).
  Reescrita do chrome do shell (`.topbar`, `.muriae-sidebar-*`, brand, hero, `.ac-page-muriae`,
  `.ac-main-content`) de hex literal para `var(--mu-*)`. Tokens dark: bg `#100B24`,
  surface `#191238`, text `#ECE9F7`, muted `#9D97B8`, border `#2C2552`, brand `#c7bbf0`.
- `admin/src/pages/CommunityInterfacePages.tsx` — ~242 utilitários de cor hard-coded
  (`bg-[#fafaf8]`, `text-[#1f2430]`, `bg-white`, `text-[#231651]`…) convertidos para os
  utilitários de token. **Substituição prefix-aware**: `bg-[#231651]`/`hover:bg-[#1a1040]`
  (preenchimento sólido da marca + texto branco) **mantidos literais** nos dois temas
  — só os usos de `#231651` como texto/borda viraram `text-mu-brand`/`border-mu-brand`
  (que clareia para `#c7bbf0` no escuro). Underline de aba ativa e banner de sugestão também.
- `admin/src/components/MuriaeDeckCard.tsx` — `CATEGORY` (faixas Oficial/Comunidade/IA)
  migrado para tokens `mu-brand-bg`/`mu-official-border`/`mu-cat-comm-*`/`mu-cat-ai-*`,
  que invertem para tons escuros traslúcidos no dark.
- `admin/src/lib/theme.ts` (novo) + `theme.test.ts` — `getStoredTheme`/`setTheme`/
  `applyTheme`/`initTheme`; padrão **claro**, persistência em `localStorage`
  (`anki-concursos-theme`), aplica `data-theme` no `<html>`.
- `admin/src/components/ThemeToggle.tsx` (novo) — botão lua/sol no topbar (aria
  "Ativar modo claro/noturno", `aria-pressed`). Adicionado em `AppShell.tsx` (topbar) e
  estilo `.muriae-theme-toggle` no CSS.
- `admin/src/main.tsx` — `initTheme()` antes do render (evita flash na carga com tema salvo).

### Decisões relevantes
- **Tokens semânticos em vez de variantes `dark:` por elemento** — a superfície Muriae
  usava hex arbitrário em ~290 pontos; mapear cada um com `dark:` seria disperso e frágil.
  Tokens `--mu-*` trocados num único `[data-theme]` espelham a arquitetura do protótipo
  (que faz o mesmo) e isolam o tema num só lugar.
- **Escopo: só a superfície Muriae** (decisão do usuário). Páginas legadas ainda no tema
  escuro antigo (`:root` global) ficam fora do toggle; seus tokens não colidem com `--mu-*`.
- **Preenchimento sólido da marca não inverte** — no protótipo o controle ativo
  (`#231651` + texto branco) permanece igual no escuro; só a marca usada como *texto/borda*
  clareia. Replicado para manter contraste e fidelidade.
- **Padrão claro + lembrar escolha** (decisão do usuário) — ignora `prefers-color-scheme`;
  comportamento previsível, igual ao protótipo.

### Impacto
- A superfície Muriae passa a ter modo claro/escuro alternável pelo topbar, persistente.
  Verificado claro e escuro (paridade com o protótipo) renderizando os utilitários do build
  com os tokens — faixas de categoria, sidebar ativa, botões e badges corretos nos dois temas.
- Backend não tocado. Validado **no app real** (backend `:8000` + login): Explore claro/escuro
  e **modal de nota** (Dialog) corretos nos dois temas.

### Correção pós-implementação — modal de nota vazio
- **Bug:** o modal de nota (shadcn `Dialog`) renderizava **transparente/vazio** — o conteúdo
  aparecia, mas a superfície sumia. Causa: tokens `--mu-*` estavam escopados em `.app-shell`,
  e o `Dialog` (assim como `DropdownMenu`/`Select`) renderiza num **portal no `<body>`**, fora
  do shell → `bg-mu-surface`/`text-mu-text` resolviam para vazio. Afetava os dois temas.
- **Fix:** mover a definição dos tokens de `.app-shell` → `:root` (e o override dark de
  `html[data-theme="dark"] .app-shell` → `html[data-theme="dark"]`). Mesmos valores, só o
  escopo alargou; páginas legadas não consomem `mu-*`, sem regressão.



**Branch:** `frontend-redesign` (alterações de backend + add-on `addon-anki`, repo separado em `main`)
**Tipo:** fix + feature

Revisão exaustiva do contrato de sync entre o backend (`app/`) e o add-on do Anki
(`../addon-anki`). Corrigidos bugs de perda de dados / desync e divergências de
contrato. Mudanças abrangem os dois repositórios.

### O que mudou — Backend (`app/`)
- `app/services/decks.py` `anki_sync` — novo parâmetro `to_release` (teto de release). Cliente paginado fixa o teto da página 1 e o repassa nas demais → snapshot estável mesmo com release publicado durante a paginação. `total_changes` agora retornado em toda resposta paginada (antes só quando `page` presente).
- `app/services/decks.py` `_anki_change_response` — campo `native: bool` no change (True no path de upload nativo com `anki_fields`, False no derivado/CSV) e `content_hash` propagado de `card_version.content_hash`. Fim da inferência native/legacy por formato no cliente.
- `app/services/decks.py` — extraído `_active_snapshot` (compartilhado por `_anki_snapshot_changes`); novo `anki_deck_state` retorna todos os card_ids ativos no `latest_release` (com `public_id`, `card_version_id`, `content_hash`). Exige assinatura ativa.
- `app/api/routes/addon.py` — query `to_release` em `/sync`; novo endpoint `GET /addon/decks/{deck_id}/state`.
- `app/schemas/decks.py` + `__init__.py` — `native`/`content_hash` em `AnkiSyncChangeResponse`; novos `AnkiDeckStateResponse`/`AnkiDeckStateCardResponse`.
- `tests/test_decks_api.py` — testes de `/state` (lista ativos + content_hash; 403 sem assinatura); asserts `native`/`content_hash` nos testes de sync nativo, legado e snapshot.

### O que mudou — Add-on (`../addon-anki`)
- `sync/engine.py` — **watermark só avança após fetch completo** (cliente verifica `len(changes) == total_changes`, aborta antes do apply se incompleto). **Isolamento por-deck na fase de fetch**: um baralho com 403/404/rede não aborta os demais. **Version-check defensivo** (`_version_is_outdated`: parse com regex, segmento não-numérico → 0, padding de tuplas) — antes crashava o sync com `int()` em versão tipo `0.1.0b1`. **Mutações da coleção agrupadas em um único undo** (`add_custom_undo_entry`/`merge_undo_entries`, best-effort). **Skip de write no-op** quando `content_hash` local == remoto (evita bump de `mod` → churn no AnkiWeb). **Reconcile de deleções**: suspende cards locais ativos ausentes do `/state` upstream (hard-delete/squash que o delta nunca entregou), com guarda de `to_release == state.latest_release`.
- `api/client.py` — `sync_deck(to_release=…)` + guarda de completude/drift em `sync_deck_all_pages`; `get_deck_state` (404 → None p/ compat com servidor antigo).
- `api/models.py` — `native`/`content_hash` no change; dataclasses de state.
- `services/note_manager.py` — `_apply_fields` não dropa mais campo omitido pelo mapping (aplica resto que casa com campo real da nota).
- `sync/fields.py` — `field_mapping_for_change` confia na flag `native`; heurística vira só fallback.
- `storage/database.py` — `get_active_cards_by_deck`.
- `tests/` — `test_contract.py` (novo: flag native, `_apply_fields`); casos novos em `test_sync.py` (version parse, isolamento de fetch, undo agrupado, skip por hash, reconcile).

### Decisões relevantes
- **Atomicidade coleção+DB não existe na API do Anki** (ops não são transacionais). Melhor garantia: agrupar num único undo + idempotência por Card ID + watermark só após fetch completo. Não foi inventada API transacional.
- **Reconcile via endpoint full-state separado**, não tombstones no snapshot (que cresceriam sem limite). Opcional: 404 → reconcile pulado.
- **Flag `native` como contrato explícito** em vez de heurística de formato; cliente antigo (sem a flag) ainda cai no fallback heurístico.
- **`note_type_manager.py`/`installer.py`** no add-on têm alterações não commitadas de sessão anterior — fora do escopo desta revisão, não tocados.

### Impacto
- Sync resiliente: sem gaps de release silenciosos, sem um baralho derrubar os outros, sem crash por string de versão atípica, menos churn no AnkiWeb, e deleções upstream agora refletidas localmente.
- Endpoint `/addon/decks/{deck_id}/state` disponível para o add-on.
- Pendência de ambiente: `tests/test_decks_api.py::test_addon_can_upload_full_deck_package_and_publish_release` exige Postgres rodando (falha de conexão pré-existente, não relacionada). Demais: backend 107 passed / 2 skipped; add-on 50 passed.

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
