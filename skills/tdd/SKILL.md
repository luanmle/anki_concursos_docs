---
name: tdd
description: >
  Discipline de TDD para este projeto: escrever um teste que falha, implementar o mínimo para passar, repetir.
  Use ao criar ou corrigir qualquer comportamento em services, rotas ou modelos — especialmente regras de versionamento,
  imutabilidade, sync, reports e autenticação.
---

# TDD — Test-Driven Development neste projeto

## Princípio central

Teste comportamento acessível pela interface pública do módulo — não detalhe de implementação interna. Um teste que passa pela mesma surface que o código de produção usa (service, rota HTTP, evento SQLAlchemy) sobrevive a refatorações sem precisar ser reescrito.

## Ciclo obrigatório

```
1. Escreva um teste que falha (Red)
   └─ um único comportamento por teste
   └─ use fixtures mínimas — só o que o teste precisa existir

2. Implemente o mínimo para o teste passar (Green)
   └─ não antecipe casos não testados ainda

3. Refatore se necessário (Refactor)
   └─ os testes devem continuar verdes

4. Repita para o próximo comportamento
```

Não escreva todos os testes antes de implementar. Não implemente sem ter um teste falhando primeiro.

## Como rodar a suíte

```bash
# Testes rápidos (SQLite em memória) — rodar sempre antes de commitar
pytest

# Testes de integração PostgreSQL — requerem banco real
TEST_DATABASE_URL=postgresql+psycopg://user:pass@host/db pytest -m postgres
```

Configuração em `pyproject.toml:46-51`. Banco de teste padrão: SQLite em memória com foreign keys habilitadas (`tests/conftest.py:15-29`).

> **Atenção add-on Anki:** o código do add-on Anki (cliente Python rodando dentro do Anki) é testado com mocks e isolado do runtime do Anki. Não assuma que testes do add-on chegam ao banco de dados real — eles testam a lógica de sincronização localmente.

## Fixtures desta suíte

- `session` — `Session` SQLite em memória; cria schema completo via `Base.metadata.create_all`.
- `client` — `TestClient` FastAPI com `get_db` substituído pela mesma session SQLite; envia `X-Admin-API-Key: development-admin-key` em todos os requests (autenticação legada de admin).
- `clear_rate_limits` — autouse; reseta contadores de rate limit entre testes.

Para criar dados de apoio, insira diretamente via `session` antes de chamar `client`. Não use fixtures de outros testes como dependência.

## Regras de negócio que **exigem** teste

### Imutabilidade (ADR-0001, ADR-0002, ADR-0003)

```python
# public_id nunca muda — CONFIRMA via evento SQLAlchemy
def test_public_id_is_immutable(session):
    card = Card(...)
    session.add(card); session.flush()
    original = card.public_id
    with pytest.raises(ValueError, match="immutable"):
        card.public_id = "AC-OUTROVALOR"
        session.flush()
    assert card.public_id == original

# versão publicada não pode ser editada
def test_published_version_cannot_be_updated(session):
    version = CardVersion(..., status=CardVersionStatus.PUBLISHED)
    session.add(version); session.flush()
    with pytest.raises(ValueError, match="immutable"):
        version.front_text = "novo texto"
        session.flush()

# release não pode ser modificada
def test_release_is_immutable(session):
    release = Release(...)
    session.add(release); session.flush()
    with pytest.raises(ValueError):
        release.description = "alterado"
        session.flush()
```

### Versionamento

```python
# nova versão não altera a versão anterior
def test_new_version_preserves_previous(client):
    card = _create_published_card(client)
    v1_id = card["current_version"]["card_version_id"]
    client.post(f"/cards/{card['card_id']}/versions", json={...})
    detail = client.get(f"/cards/{card['card_id']}").json()
    versions = detail["versions"]
    assert any(v["card_version_id"] == v1_id for v in versions)

# version_number é incrementado
def test_version_numbers_are_sequential(client):
    card = _create_published_card(client)
    client.post(f"/cards/{card['card_id']}/versions", json={...})
    detail = client.get(f"/cards/{card['card_id']}").json()
    numbers = sorted(v["version_number"] for v in detail["versions"])
    assert numbers == list(range(1, len(numbers) + 1))
```

### Sync

```python
# delta correto entre releases
def test_sync_returns_only_changes_since_release(client):
    # cria deck, release 1 com card A
    # cria release 2 com card B adicionado
    resp = client.get(f"/decks/{deck_id}/sync?since_release=1")
    changes = resp.json()["changes"]
    assert len(changes) == 1
    assert changes[0]["action"] == "added"
    assert changes[0]["public_id"] == card_b_public_id

# ações suportadas
def test_sync_supports_all_release_actions(client):
    # ciclo: added → updated → removed → deprecated
    for action in ("added", "updated", "removed", "deprecated"):
        _assert_action_in_sync(client, deck_id, action)
```

### Report → nova versão em revisão (ADR-0004)

```python
def test_approved_report_creates_version_in_needs_review(client):
    report_id = _open_report(client, card_id, version_id)
    resp = client.post(f"/admin/reports/{report_id}/review", json={
        "decision": "converted_to_new_version",
        "proposed_version": {"front_text": "...", ...},
        "admin_comment": "corrigido",
        "evidence_reviewed": False,
    })
    assert resp.status_code == 200
    resulting_id = resp.json()["review_task"]["resulting_card_version_id"]
    card_detail = client.get(f"/cards/{card_id}").json()
    resulting = next(v for v in card_detail["versions"]
                     if v["card_version_id"] == resulting_id)
    assert resulting["status"] == "needs_review"  # não publicado diretamente
```

## O que NÃO testar

- Implementação interna de `_release_changes`, `_upload_content_hash` etc. — teste via interface HTTP.
- Queries SQL diretas — use o service ou a rota como entry point.
- Compatibilidade entre SQLite e PostgreSQL para lógica de negócio — os testes unitários usam SQLite; testes de imutabilidade via trigger ficam em `tests/test_postgres_integration.py`.
