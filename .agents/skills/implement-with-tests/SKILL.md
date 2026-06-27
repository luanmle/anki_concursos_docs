---
name: implement-with-tests
description: >
  Implementação orientada por testes (TDD) para o Anki Concursos. Versão cross-agent
  (Claude Code e Codex). Referência detalhada com exemplos: skills/tdd/SKILL.md
---

# Implement with Tests

## Ciclo obrigatório

```
Red    → escreva um teste que falha (um comportamento por vez, fixtures mínimas)
Green  → implemente o mínimo para o teste passar (não antecipe casos não testados)
Refactor → limpe se necessário; os testes devem continuar verdes
Repita para o próximo comportamento
```

Não escreva todos os testes de uma vez. Não implemente sem ter um teste falhando primeiro.

## Executar a suíte

```bash
# Sempre antes de commitar
pytest

# Integração PostgreSQL (triggers, locks reais)
TEST_DATABASE_URL=postgresql+psycopg://anki:anki@localhost:5432/anki_test pytest -m postgres

# Cobertura (mínimo exigido: 80%)
coverage run --source=app -m pytest && coverage report --show-missing --fail-under=80

# Lint
ruff check app tests migrations
```

## Fixtures disponíveis

| Fixture | O que fornece |
|---------|--------------|
| `session` | `Session` SQLite em memória; schema completo via `Base.metadata.create_all`; foreign keys ativas via PRAGMA |
| `client` | `TestClient` FastAPI; `get_db` → mesma session SQLite; envia `X-Admin-API-Key: development-admin-key` em todos os requests |
| `clear_rate_limits` | `autouse`; reseta contadores de rate limit entre testes |

Para criar dados de apoio: insira via `session` antes de chamar `client`. Não use fixtures de outros testes como dependência.

## Compatibilidade SQLite vs PostgreSQL

| Comportamento | SQLite (padrão) | PostgreSQL (`-m postgres`) |
|--------------|-----------------|--------------------------|
| Foreign keys | Ativo via PRAGMA | Nativo |
| Eventos SQLAlchemy (imutabilidade) | Sim | Sim |
| Trigger `trg_card_versions_immutable` | **Não** | Sim (migration aplicada) |
| `SELECT FOR UPDATE` | Simulado | Real |
| Constraints `UNIQUE` | Sim | Sim |

Use `@pytest.mark.postgres` para testes que dependem de comportamento exclusivo do PostgreSQL.

## Comportamentos que exigem teste antes da implementação

### Imutabilidade (ADRs 0001, 0002, 0003)

```python
def test_public_id_is_immutable(session):
    """public_id nunca muda após criação."""
    card = Card(...)
    session.add(card); session.flush()
    original = card.public_id
    with pytest.raises(ValueError, match="immutable"):
        card.public_id = "AC-NOVO"
        session.flush()
    assert card.public_id == original
```

### Versionamento

```python
def test_new_version_preserves_previous(client):
    card = _create_published_card(client)
    v1_id = card["current_version"]["card_version_id"]
    client.post(f"/cards/{card['card_id']}/versions", json={...})
    versions = client.get(f"/cards/{card['card_id']}").json()["versions"]
    assert any(v["card_version_id"] == v1_id for v in versions)
```

### Sync

```python
def test_sync_delta_correto(client):
    """since_release=N retorna apenas mudanças após N."""
    # cria deck → release 1 com card A → release 2 com card B
    resp = client.get(f"/decks/{deck_id}/sync?since_release=1")
    changes = resp.json()["changes"]
    assert len(changes) == 1
    assert changes[0]["action"] == "added"
    assert changes[0]["public_id"] == card_b_public_id
```

### Reports (ADR-0004)

```python
def test_approved_report_creates_needs_review(client):
    """Correção via report entra em needs_review, não published."""
    report_id = _open_report(client, card_id, version_id)
    resp = client.post(f"/admin/reports/{report_id}/review", json={
        "decision": "converted_to_new_version",
        "proposed_version": {"front_text": "...", ...},
        "admin_comment": "ok",
        "evidence_reviewed": False,
    })
    resulting_id = resp.json()["review_task"]["resulting_card_version_id"]
    versions = client.get(f"/cards/{card_id}").json()["versions"]
    resulting = next(v for v in versions if v["card_version_id"] == resulting_id)
    assert resulting["status"] == "needs_review"
```

## O que NÃO testar

- Funções privadas (`_release_changes`, `_upload_content_hash`) — teste via interface HTTP/service
- Queries SQL diretas — use o service ou a rota como entry point
- Compatibilidade SQLite vs PostgreSQL para lógica de negócio — use `@pytest.mark.postgres` para isso

## Regra de tamanho

Um teste por comportamento. Se um teste precisa de mais de ~10 linhas de setup, refatore o setup para uma função auxiliar `_create_*`, não para uma fixture compartilhada.

---

> Referência detalhada com exemplos completos: `skills/tdd/SKILL.md`
