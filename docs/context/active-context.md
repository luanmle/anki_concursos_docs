# Contexto Ativo

**Atualizado:** 2026-06-25
**Branch:** `frontend-redesign`
**Status:** em andamento

## O que está sendo trabalhado

Migração do design Muriae (`design-reference/`) para o admin, em **Tailwind v4 + shadcn**, com a branch local `frontend-redesign` pronta para publicação.

## Estado atual (verde)

- `tsc` ✓, `npm run build` ✓, `npm test` **8/8** ✓.
- `npm run lint` ✓ depois dos ajustes de `eslint.config.js`, `use-mobile.ts` e do painel de sugestões.
- Telas migradas neste fluxo: **Explore** (hero, toolbar, cards), **Meus baralhos**, **Página do deck** (hero, lista de notas, **modal de nota** com abas Conteúdo/Sugerir mudanças + painel de comentários), **Comunidade**, **Histórico de sugestões**, e **Admin** (Dashboard, Gerenciar baralhos, Sugestões).
- Mojibake do arquivo inteiro limpo (ftfy); ~600+ linhas de CSS legado órfão removidas (`index.css` ~2564 linhas, 0 órfãs).
- Cards de baralho/notas: superfície branca (design system) com elevação + hover.
- **Seção de comentários** reforçada (colaborativa): subtítulo, compositor em card, botão "Útil" como pill, **avatar na calha à esquerda (fora do card)**, painel largo (448px). Sem cores por tipo/autor (badges/avatar neutros, a pedido).

## Próximos passos

- [ ] Migrar as **demais páginas do app** (fora de CommunityInterfacePages.tsx) que ainda usam o tema escuro legado do `tailwind.config.ts`: `DashboardPage`, `CardsPage`, `CardDetailPage`, `CardFormPage`, `CardImportPage`, `DecksPage`/`DeckDetailPage`, `AddonPage`, `ReportDetailPage`, `UserPages`, `OperationPage`.
- [ ] Converter `SkeletonDeckCard` (`.ac-skeleton-card`) para o visual do novo card no loading.
- [ ] Antes de PR/merge: `npm run build`, `npm test`, `npm run lint` e skill `review-change`.
- [ ] Publicar `frontend-redesign` no fluxo correto do repositório, sem tocar `admin-deploy` manualmente.

## Decisões/Padrões desta sessão

- **Constantes reutilizáveis** no topo de `CommunityInterfacePages.tsx`: `muriaePrimaryBtn`/`muriaeSecondaryBtn`/`muriaeSurface`/`muriaeEyebrow`. Heroes via `ExploreHero`.
- **`!text-white` no botão primário** — regra global de `a` (cor escura) vence `text-white` em `<Link>` escuro.
- **Abas underline do shadcn Tabs**: usar `TabsList variant="line"` + `border-b` com `data-[state=active]` (o Radix usa `data-state`, não `data-active`).
- **Limpeza de CSS órfão** guiada por análise definido-vs-referenciado (`scratchpad/strip_orphans.py`); ressalva: seletor órfão 1º item de lista vírgula multilinha em `@media` precisa fix manual.
- **Preferência do usuário:** cores sólidas (não gradiente/mistura); perguntar quando a aplicação for ambígua (ver memória).
- **Lint de Fast Refresh isolado** — os módulos UI gerados e `MuriaeDeckCard` exportam constantes e componentes no mesmo arquivo; a regra ficou desativada só nesses pontos.
- **`use-mobile`** — inicialização por `matchMedia.matches` evita o `setState` síncrono no efeito.

## O que NÃO tocar agora

- `admin-deploy` — branch gerada automaticamente.
- Backend (`app/`) — escopo atual é frontend/design.
