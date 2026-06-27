# Contexto Ativo

**Atualizado:** 2026-06-27
**Branch:** `codex/publish-admin`
**Status:** em andamento

## O que está sendo trabalhado

UI admin da fila de moderação de sugestões de notas, consumindo o backend
persistente `note_suggestions` criado nesta mesma branch.

## Últimas mudanças (desta sessão)

- Nova página de **Sugestões de Mudanças** em `/admin/suggestions`,
  consumindo `GET /admin/note-suggestions` e `POST .../{id}/review`.
- Componentes modulares novos em `admin/src/components/suggestions/`:
  `DiffViewer.tsx`, `SuggestionCard.tsx`, `SuggestionList.tsx`,
  `diff.ts` (+ `diff.test.ts`).
- `AdminSuggestionsPage` (em `CommunityInterfacePages.tsx`) reescrita;
  removido o fluxo localStorage antigo e helpers órfãos.
- Testes da página migrados para o backend.

## Verificação

- `npm run lint` — passou.
- `npm test -- --run` — 18 passed.
- `npm run build` — passou.
- Verificado no app real (Playwright + login admin): lista, diff
  (cloze/imagem/tags), aceitar com comentário → conta migra
  Aguardando→Aceitas e grava revisor/comentário. Dados de demo
  semeados e removidos do banco após o teste.

## Próximos passos

- [ ] Integrar add-on com `POST /addon/cards/{card_id}/suggestions`
  enviando `fields[campo] = {old,new}`.
- [ ] (Opcional) Conversão de sugestão aceita em nova versão de card,
  reaproveitando o fluxo de cards/reports.
- [ ] (Opcional) Paginação na fila quando o volume crescer
  (hoje `page_size=100`).

## Decisões recentes

- **Contrato de diff `{old,new}` por campo** — auto-contido; a UI fixa o
  contrato que o add-on deverá enviar. `normalizeFieldDiff` tolera string crua.
- **Votos display-only** — backend não tem campo de voto; controle aparece
  desabilitado por fidelidade à referência.

## O que NÃO tocar agora

- `admin-deploy` manualmente; gerada pelo workflow.
- O contrato de `fields` deve casar com o que o add-on vier a enviar
  (`{old,new}`), ao integrar do lado do add-on.
