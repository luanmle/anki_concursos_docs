---
name: diagnosing-bugs
description: >
  Loop disciplinado de diagnóstico de bugs neste projeto: reproduzir → minimizar → hipótese → instrumentar → corrigir → teste de regressão.
  Use ao depurar comportamentos inesperados em services, rotas, eventos SQLAlchemy, sync de deck ou autenticação.
---

# Diagnosing Bugs — Loop disciplinado de diagnóstico

## O loop

```
1. Reproduzir          — confirme que o bug acontece de forma determinística
2. Minimizar           — reduza ao menor caso que ainda reproduz o problema
3. Hipótese            — formule UMA causa provável antes de mexer no código
4. Instrumentar        — adicione logs/asserts para confirmar ou refutar a hipótese
5. Corrigir            — aplique a correção mínima
6. Teste de regressão  — escreva um teste que teria falhado com o bug e agora passa
```

Não pule etapas. Ir direto para "corrigir" sem hipótese é a principal causa de regressões.

## Passo 1 — Reproduzir

Use o `TestClient` do projeto para reproduzir o bug em teste:

```python
# tests/test_regression_<nome>.py
def test_bug_reproducao(client):
    # mínimo para chegar ao estado problemático
    resp = client.post("/decks/upload", json={...})
    assert resp.status_code == 201  # aqui deveria funcionar mas não funciona
```

Rodar: `pytest tests/test_regression_<nome>.py -v`

Se não conseguir reproduzir com SQLite em memória, tente com PostgreSQL real:
```bash
TEST_DATABASE_URL=postgresql+psycopg://... pytest tests/test_regression_<nome>.py -m postgres -v
```

Note: erros de imutabilidade que dependem de triggers PostgreSQL (e.g., `trg_card_versions_immutable`) **não** são capturados pelos testes SQLite — precisam do banco real.

## Passo 2 — Minimizar

Remova tudo que não seja necessário para reproduzir:
- Reduza o payload ao mínimo de campos.
- Remova releases, cartões e decks desnecessários.
- Se o bug aparece na release 3, tente reproduzir já na release 1.

Um caso mínimo é mais fácil de raciocinar e mais barato de manter como teste de regressão.

## Passo 3 — Hipótese

Antes de abrir qualquer arquivo, escreva em uma linha o que você acha que está errado. Exemplos:

> "O sync retorna `removed` mas deveria retornar `deprecated` porque `removal_action` não está sendo lido."

> "A versão criada pelo report está chegando como `published` — suspeito que `_create_resulting_version` está passando o status errado."

Se a hipótese for vaga ("algo no sync está errado"), refine antes de prosseguir.

## Passo 4 — Instrumentar

### Verificar estado do banco durante o teste

```python
def test_bug_hipotese(session, client):
    # ... setup ...
    card = session.get(Card, card_id)
    print(f"card.status={card.status}, current_version_id={card.current_version_id}")
    version = session.get(CardVersion, card.current_version_id)
    print(f"version.status={version.status}")
```

### Pontos de atenção por área

**Sync (`GET /decks/{id}/sync`):**
- O algoritmo replay em `DeckService.sync` (`app/services/decks.py:263-334`) percorre **todos** os release items em ordem. Verifique se `since_release` está sendo comparado corretamente (`item.release.release_number > since_release`).
- `ReleaseAction` tem quatro valores: `added`, `updated`, `removed`, `deprecated`. Confirme qual ação está sendo gravada em `DeckCard.removal_action` ao remover um cartão.

**Imutabilidade:**
- Eventos SQLAlchemy (`app/models/entities.py:660-808`) disparam no `flush()`, não no `commit()`. Se o teste faz flush manual, verifique se o evento foi registrado.
- Triggers PostgreSQL só existem no banco real — se o teste usa SQLite, a proteção de banco não é testada. Use `pytest -m postgres` para isso.

**Autenticação:**
- Token JWT expirado: verificar `payload["exp"]` vs `datetime.now(UTC).timestamp()` (`app/core/security.py:135`).
- Token revogado: `user.credential_version != token_version` (`app/core/security.py:194`).
- `X-Admin-API-Key` só funciona se `allow_legacy_admin_api_key=True` na config (`app/core/security.py:219`).

**Reports:**
- `review_report` usa `for_update=True` no select — em testes SQLite isso não causa lock real mas garante que o fluxo seja exercitado.
- Rejeição de `outdated_law` sem `evidence_reviewed=True`: verificar `_validate_review_evidence` (`app/services/reports.py:131-146`).

**Upload Anki:**
- `canonical_key` para upload usa lógica diferente do cartão manual: se `source_note_guid` existe, usa `deck-{deck_id.hex}-anki-note-{source_key}-{template_key}` (`app/services/decks.py:1148-1159`).
- `content_hash` do upload inclui `tags` e o objeto `template` completo — diferente do hash de cartão manual.

## Passo 5 — Corrigir

Aplique a correção mínima. Não refatore o entorno enquanto corrige um bug — mistura o sinal do teste.

Se a correção exigir migração de schema, crie uma nova migration Alembic em `migrations/versions/` seguindo o padrão `YYYYMMDD_NNNN_<descricao>.py`.

## Passo 6 — Teste de regressão

O teste escrito no Passo 1 já é o ponto de partida. Ajuste para ser o mais preciso possível:

```python
def test_sync_retorna_deprecated_nao_removed_quando_marcado(client):
    """Regressão: DeckCard.removal_action=deprecated estava sendo ignorado."""
    # ... setup mínimo com removal_action=deprecated ...
    resp = client.get(f"/decks/{deck_id}/sync?since_release=0")
    changes = resp.json()["changes"]
    assert any(c["action"] == "deprecated" for c in changes)
```

Confirme que:
1. O teste **falha** na versão do código antes da correção.
2. O teste **passa** após a correção.
3. Nenhum outro teste existente quebrou (`pytest`).
