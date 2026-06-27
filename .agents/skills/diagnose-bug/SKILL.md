---
name: diagnose-bug
description: >
  Loop disciplinado de diagnóstico de bugs neste projeto: reproduzir → minimizar → hipótese
  → instrumentar → corrigir → regressão. Versão cross-agent (Claude Code e Codex).
  Referência detalhada com exemplos: skills/diagnosing-bugs/SKILL.md
---

# Diagnose Bug

## O loop — não pule etapas

```
1. Reproduzir   — confirme que o bug acontece de forma determinística
2. Minimizar    — reduza ao menor caso que ainda falha
3. Hipótese     — UMA causa em uma frase, antes de abrir qualquer arquivo
4. Instrumentar — adicione logs/asserts para confirmar ou refutar
5. Corrigir     — aplique a correção mínima
6. Regressão    — escreva o teste que teria detectado o bug
```

Ir direto para "corrigir" sem hipótese é a principal causa de regressões neste projeto.

## Passo 1 — Reproduzir

Escreva um teste que falha de forma determinística:

```python
# tests/test_regression_<descricao>.py
def test_bug_reproducao(client):
    resp = client.post("/endpoint", json={...})
    assert resp.status_code == 201  # falha aqui, recebe 422
```

```bash
pytest tests/test_regression_<descricao>.py -v
```

Se SQLite em memória não reproduzir:
```bash
TEST_DATABASE_URL=postgresql+psycopg://anki:anki@localhost:5432/anki_test \
  pytest tests/test_regression_<descricao>.py -m postgres -v
```

Triggers PostgreSQL (`trg_card_versions_immutable`) **não disparam no SQLite**. Erros de imutabilidade no banco precisam do PostgreSQL real.

## Passo 2 — Minimizar

- Reduza o payload ao mínimo de campos que ainda reproduz o bug
- Remova releases, decks e cartões desnecessários do setup
- Se o bug aparece na release 3, tente reproduzir na release 1

## Passo 3 — Hipótese

Escreva em uma frase antes de abrir qualquer arquivo:

❌ "Algo no sync está errado"  
✅ "O sync retorna `removed` mas deveria `deprecated` porque `DeckCard.removal_action` não está sendo lido em `app/services/decks.py:300`"

Se a hipótese for vaga, refine antes de prosseguir.

## Passo 4 — Instrumentar

```python
def test_bug_hipotese(session, client):
    # ... setup ...
    card = session.get(Card, card_id)
    print(f"card.status={card.status}")
    version = session.get(CardVersion, card.current_version_id)
    print(f"version.status={version.status}")
```

### Pontos de atenção por área

| Área | Onde investigar |
|------|----------------|
| Sync delta | `DeckService.sync` em `app/services/decks.py:263-334` — verifique `since_release` e `removal_action` |
| Imutabilidade | Eventos em `app/models/entities.py:660-808` — disparam no `flush()`, não no `commit()` |
| JWT expirado | `payload["exp"]` vs `datetime.now(UTC).timestamp()` em `app/core/security.py:135` |
| JWT revogado | `user.credential_version != token["ver"]` em `app/core/security.py:194` |
| `X-Admin-API-Key` | Só funciona com `allow_legacy_admin_api_key=True` em `app/core/security.py:219` |
| Reports | `_validate_review_evidence` em `app/services/reports.py:131-146` |
| Upload Anki | `canonical_key` com `source_note_guid` em `app/services/decks.py:1148-1159` |
| Content hash | Manual (`app/services/cards.py:42-62`) ≠ upload Anki (`app/services/decks.py:1113-1135`) |

## Passo 5 — Corrigir

Aplique a correção mínima. Não refatore o entorno ao mesmo tempo — mistura o sinal do teste.

Se exigir migration de schema: crie arquivo em `migrations/versions/` seguindo o padrão `YYYYMMDD_NNNN_<descricao>.py`. Nunca modifique migrations existentes.

## Passo 6 — Regressão

Ajuste o teste do Passo 1 para ser preciso e documentar a causa:

```python
def test_sync_retorna_deprecated_nao_removed_quando_marcado(client):
    """Regressão: DeckCard.removal_action=deprecated era ignorado."""
    # setup mínimo
    resp = client.get(f"/decks/{deck_id}/sync?since_release=0")
    changes = resp.json()["changes"]
    assert any(c["action"] == "deprecated" for c in changes)
```

Verifique:
1. O teste **falha** no código antes da correção
2. O teste **passa** após a correção
3. `pytest` continua verde na suíte completa

---

> Referência detalhada com exemplos completos de código: `skills/diagnosing-bugs/SKILL.md`
