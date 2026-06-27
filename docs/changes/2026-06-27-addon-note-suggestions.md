# 2026-06-27: Sugestoes de notas pelo add-on

## Resumo

A plataforma agora tem base persistente para receber sugestoes enviadas pelo
add-on diretamente do Anki, no estilo do fluxo do AnkiHub.

## O que mudou

- Nova tabela `note_suggestions`.
- Novos enums `NoteSuggestionType` e `NoteSuggestionStatus`.
- Novos endpoints:
  - `POST /addon/cards/{card_id}/suggestions`
  - `POST /addon/decks/{deck_id}/note-suggestions`
  - `GET /admin/note-suggestions`
  - `GET /admin/note-suggestions/{suggestion_id}`
  - `POST /admin/note-suggestions/{suggestion_id}/review`
- Novos schemas, repository e service para sugestoes.
- Tipos TypeScript adicionados em `admin/src/types.ts`.
- CORS agora permite `PATCH`, necessario para frontend admin e endpoint de
  campos protegidos ja existente.

## Analise

Antes, a area comunitaria tinha sugestoes no frontend usando `localStorage`.
Isso perdia historico entre dispositivos e nao servia para o add-on enviar
alteracoes reais do Anki para a plataforma.

O add-on do AnkiHub usa um fluxo persistente: calcula diff local, envia campos,
tags e comentario para endpoints de sugestao, e deixa a plataforma revisar.
Esta implementacao prepara o mesmo contrato basico, sem criar ainda a tela de
moderacao completa.

## Decisoes

- Sugestao em card existente fixa o `card_version_id` publicado no momento do
  envio. Isso preserva a base comparada.
- Sugestao de nota nova usa `deck_id` sem `card_id`.
- Conversao automatica em nova versao ficou fora deste bloco. O backend ja tem
  fluxo de criacao/revisao de versoes de cards; a UI pode reaproveitar esse
  fluxo quando aceitar sugestoes.

## Verificacao

- `.venv/bin/python -m compileall app`
- `.venv/bin/ruff check app tests/test_suggestions_api.py tests/test_models.py`
- `.venv/bin/python -m pytest tests/test_suggestions_api.py`
- `.venv/bin/python -m pytest tests/test_models.py tests/test_suggestions_api.py`
- `.venv/bin/alembic upgrade head --sql`

## Observacao

O `TestClient` local travou tambem em rota autenticada antiga (`/subscriptions`).
Os testes novos foram mantidos no nivel de service para nao introduzir teste
que trava por ambiente. A rota compila e o contrato fica pronto para teste HTTP
no CI/ambiente com cliente ASGI funcionando.
