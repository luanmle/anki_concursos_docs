# Contexto Ativo

**Atualizado:** 2026-06-26
**Branch:** `frontend-redesign`
**Status:** sync contract — concluído (não commitado); frontend redesign — em andamento

## O que está sendo trabalhado

Endurecimento do **contrato de sincronização entre o backend (`app/`) e o add-on
do Anki (`../addon-anki`)** — revisão exaustiva que corrigiu bugs de perda de
dados/desync e divergências de contrato. Concluído e testado; ainda **não commitado**
nos dois repositórios.

A thread anterior (migração de design Muriae do admin) segue pendente — ver
"O que NÃO tocar agora".

## Últimas mudanças (desta sessão)

- Backend: `app/services/decks.py`, `app/api/routes/addon.py`, `app/schemas/decks.py`,
  `app/schemas/__init__.py`, `tests/test_decks_api.py` — `to_release` em `/sync`,
  flag `native` + `content_hash` no change, endpoint `GET /addon/decks/{id}/state`.
- Add-on (`../addon-anki`): `sync/engine.py`, `api/client.py`, `api/models.py`,
  `services/note_manager.py`, `sync/fields.py`, `storage/database.py` +
  `tests/test_sync.py`, `tests/test_contract.py` (novo) — watermark pós-fetch-completo,
  isolamento por-deck, version-check defensivo, undo agrupado, skip por hash,
  reconcile de deleções via `/state`.
- Detalhe completo: `docs/CHANGELOG.md` (entrada 2026-06-26).

## Próximos passos

- [ ] Commitar as mudanças de sync nos dois repos (backend `frontend-redesign`;
      add-on `main`) — mensagens separadas por repo.
- [ ] Rodar `tests/test_addon_can_upload_full_deck_package_and_publish_release`
      com Postgres ativo (falha atual é só ambiente).
- [ ] Avaliar wiring do endpoint `/addon/decks/{id}/templates/sync` (hoje sem
      consumidor no add-on) ou removê-lo.
- [ ] Retomar migração frontend Muriae (páginas restantes do app — ver thread abaixo).

## Decisões recentes

- **Atomicidade coleção+DB inexiste na API do Anki** — garantia via undo agrupado +
  idempotência por Card ID + watermark só após fetch completo.
- **Reconcile via endpoint full-state separado** (404 → skip), não tombstones no snapshot.
- **Flag `native` como contrato explícito**, heurística de formato só como fallback.

## O que NÃO tocar agora

- `note_type_manager.py` e `installer.py` no add-on — têm alterações não commitadas
  de sessão anterior, fora do escopo da revisão de sync.
- `admin-deploy` — branch gerada automaticamente.
- Frontend Muriae (`admin/`) — thread separada em andamento (DashboardPage, CardsPage,
  CardDetailPage, CardFormPage, CardImportPage, DecksPage/DeckDetailPage, AddonPage,
  ReportDetailPage, UserPages, OperationPage ainda no tema escuro legado).
