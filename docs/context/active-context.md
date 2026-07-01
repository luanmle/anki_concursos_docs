# Contexto Ativo

**Atualizado:** 2026-07-01
**Branch:** `main` (trabalho local não commitado)
**Status:** implementado e verificado; falta commit/PR + migration no deploy

## O que está sendo trabalhado

Auditoria ponytail aplicada (deps e arquivos mortos removidos) + comentários de
nota migrados do mock localStorage para o backend (`note_comments`).

## Últimas mudanças (desta sessão)

- Auditoria: -55 skill-packs em `.agents/skills/`, -4 deps npm (`framer-motion`,
  `shadcn`, `lucide-react`, `postcss`), `tailwind.config.ts`/`postcss.config.js`
  deletados, redis removido (config/compose/env), screenshots e sublime fora do git.
- Feature: tabela `note_comments` (migration `20260701_0019`) + endpoints
  `GET/POST /cards/{card_id}/note-comments` (`require_authenticated_user`);
  `NoteCommentsPanel` com query/mutation reais; `useLocalStorageState` deletado;
  `communityData.ts` reduzido a `changeTypes`.
- Detalhe da sessão anterior ainda pendente de commit: sugestões visíveis à
  comunidade + `suggestion_comments` (ver entrada 2026-06-27 do CHANGELOG).

## Verificação

- Backend: `pytest -m "not postgres"` → 125 passed; `ruff` limpo.
- Frontend: `npm run lint` limpo, 23 testes, `npm run build` OK.
- Migration `20260701_0019` NÃO aplicada localmente (Postgres desligado);
  release phase do Heroku roda `alembic upgrade head`.

## Próximos passos

- [ ] Commit em branch `feat/...` + PR para `main` (decisão do usuário) — inclui
  o trabalho de 2026-06-27 ainda não commitado.
- [ ] Subir Postgres local + `alembic upgrade head` + smoke test no browser.
- [ ] **Rotação dos segredos Heroku vazados (pendente desde 2026-06-26 — prioridade).**
- [ ] (Futuro) add-on enviando `fields[campo]={old,new}` p/ diff completo.

## Decisões recentes

- **Comentários de nota sem `kind` e sem votos persistidos** — mock só enviava
  `kind='comment'`; votos seguem precedente display-only das sugestões.
- **Endpoints no vertical de suggestions** — `community_router` já tinha plumbing.

## O que NÃO tocar agora

- `admin-deploy` manualmente.
- Cards/versions publicados: imutáveis (trigger bloqueia).
