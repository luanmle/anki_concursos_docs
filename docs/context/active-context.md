# Contexto Ativo

**Atualizado:** 2026-06-26
**Branch:** `frontend-redesign` (dark mode) · sync já mergeado em `main` (Heroku v97)
**Status:** modo noturno Muriae — concluído, não commitado; sync — mergeado e no ar

## O que está sendo trabalhado

**Modo noturno (dark mode)** da superfície Muriae — tema escuro do
`design-reference/redesign.html`, com toggle no topbar e persistência. Concluído e
verificado visualmente (claro + escuro); ainda **não commitado** (branch `frontend-redesign`).

Em paralelo, o **contrato de sync backend ↔ add-on** já foi mergeado em `main` e
publicado (Heroku v97) — ver "Sync (estado herdado)" abaixo; ainda há ações pendentes lá,
incluindo uma **urgente de segurança**.

## Últimas mudanças (desta sessão — dark mode)

- `admin/src/index.css` — tokens semânticos `--mu-*` escopados em `.app-shell`,
  swap via `html[data-theme="dark"]`; utilitários no `@theme`; chrome do shell
  (topbar/sidebar/hero/page) reescrito de hex para `var(--mu-*)`.
- `admin/src/pages/CommunityInterfacePages.tsx` — ~242 cores hard-coded → tokens
  (prefix-aware: fill sólido da marca mantido, marca-como-texto invertida).
- `admin/src/components/MuriaeDeckCard.tsx` — `CATEGORY` migrado para tokens.
- `admin/src/lib/theme.ts` + `theme.test.ts` (novos), `ThemeToggle.tsx` (novo),
  `AppShell.tsx` (toggle no topbar), `main.tsx` (`initTheme()`).
- Detalhe completo: `docs/CHANGELOG.md` (entrada 2026-06-26 — Modo noturno).

## Próximos passos

- [ ] **Segurança (urgente, herdado do sync):** rotacionar segredos expostos no terminal
      via `heroku releases:info` — `AUTH_SECRET_KEY`, senha do admin,
      `heroku pg:credentials:rotate -a flashcards-stagging`.
- [ ] Validar o dark mode **no app real** com backend de pé + login
      (`admin@example.com` / `development-password`) — nesta sessão a API local estava
      fora; validação feita sobre o CSS do build.
- [ ] `review-change` e commit do dark mode em `frontend-redesign`.
- [ ] Aplicar tokens `--mu-*` às demais páginas Muriae ao migrá-las.
- [ ] Revisar e mergear add-on PR **#2** (`luanmle/addon-anki#2`); avaliar
      `/addon/decks/{id}/templates/sync` (sem consumidor) ou removê-lo.

## Decisões recentes (dark mode)

- **Tokens semânticos `--mu-*` num único `[data-theme]`**, não variantes `dark:` por
  elemento — espelha a arquitetura do protótipo e isola o tema.
- **Escopo só Muriae** (decisão do usuário); legado fica fora do toggle.
- **Fill sólido da marca não inverte** no escuro; só marca como texto/borda clareia.
- **Padrão claro + lembrar** (decisão do usuário); ignora `prefers-color-scheme`.

## Sync (estado herdado, já no ar)

- Backend PR **#6** (squash) → `main` (`7cbb9666`); add-on PR **#2** aberto, **não mergeado**.
- Heroku `flashcards-stagging` release **v97** — alembic limpo; `/state` responde 401 (vivo).
- ⚠️ **Vazamento de segredos** (ver "Próximos passos"): `heroku releases:info` despejou
  `AUTH_SECRET_KEY`, `BOOTSTRAP_ADMIN_PASSWORD` e `DATABASE_URL` de produção no terminal.

## O que NÃO tocar agora

- `admin-deploy` — branch gerada automaticamente.
- Tema escuro **legado** (`:root` global, `.sidebar`/`.brand*`/`.topbar` base) — de páginas
  ainda não migradas; não confundir com os tokens `--mu-*` da superfície Muriae.
- `note_type_manager.py` / `installer.py` no add-on — alterações soltas de sessão anterior.
- Páginas Muriae ainda não migradas (DashboardPage, CardsPage, CardDetailPage, CardFormPage,
  CardImportPage, DecksPage/DeckDetailPage, AddonPage, ReportDetailPage, UserPages, OperationPage).
