---
name: review-change
description: >
  Checklist de revisão antes de finalizar qualquer mudança no Anki Concursos.
  Execute antes de criar um commit ou abrir um PR. Cobre ADRs, contratos de API,
  migrations, testes, segurança e compatibilidade com o add-on.
---

# Review Change

Execute este checklist antes de criar um commit ou abrir um PR.

## Pré-requisito: rode a suíte

```bash
ruff check app tests migrations    # lint — zero erros
pytest                             # SQLite — zero falhas
pytest -m postgres                 # PostgreSQL — se a mudança afeta triggers
coverage run --source=app -m pytest && coverage report --fail-under=80
```

Se qualquer comando falhar, corrija antes de continuar.

---

## 1. Conformidade com ADRs

- [ ] `Card.public_id` nunca foi alterado em um cartão existente? (ADR-0001)
- [ ] Nenhuma `CardVersion` com `status=published` foi modificada ou deletada? (ADR-0002)
- [ ] Nenhum `Release` ou `ReleaseItem` foi alterado após criação? (ADR-0003)
- [ ] Reports aprovados criam `CardVersion` com `status=needs_review`? (ADR-0004)

## 2. Contrato de API

- [ ] Nenhum campo obrigatório foi removido de respostas existentes?
- [ ] Campos novos em requests são opcionais (não quebram clientes antigos que não os enviam)?
- [ ] Endpoints consumidos pelo add-on mantêm retrocompatibilidade?
- [ ] Se `/addon/decks/{id}/sync` foi tocado: testou com `since_release=0` **e** `since_release=N`?
- [ ] Se `/decks/{id}/sync` foi tocado: todas as `ReleaseAction` (`added`, `updated`, `removed`, `deprecated`) continuam corretas?

## 3. Banco e migrations

- [ ] Se há migration: nome segue `YYYYMMDD_NNNN_<descricao>.py`?
- [ ] O método `downgrade()` está implementado (migration reversível)?
- [ ] Dados existentes ficam consistentes após o upgrade?
- [ ] Nenhuma migration antiga foi modificada?
- [ ] `alembic upgrade head --sql` gera SQL válido? (`alembic upgrade head --sql > /dev/null`)

## 4. Testes

- [ ] Existe pelo menos um teste para cada comportamento novo?
- [ ] Existe teste de regressão para cada bug corrigido?
- [ ] Os testes novos falham **antes** da mudança e passam **depois**?
- [ ] A suíte completa (`pytest`) passa sem falhas?
- [ ] Cobertura do módulo `app/` mantém ≥ 80%?

## 5. Segurança e autenticação

- [ ] O guard correto protege o endpoint novo/modificado?
  - `require_admin` — apenas admin
  - `require_curator` — admin + curator
  - `require_reviewer` — admin + reviewer
  - `require_staff` — admin + curator + reviewer
  - `require_authenticated_user` — qualquer papel ativo
- [ ] Inputs do usuário são validados por Pydantic antes de chegar ao service?
- [ ] Nenhum dado sensível (token, senha, `credential_version`) vaza em responses ou logs?
- [ ] `X-Admin-API-Key` não foi usado em código novo de produção (apenas em testes)?

## 6. Compatibilidade backend ↔ add-on

- [ ] `public_id` no formato `AC-<32hex>` é preservado em todas as respostas de cartão?
- [ ] `card_kind` não muda para cartões existentes?
- [ ] Upload via add-on: `canonical_key` usa o padrão correto com `source_note_guid`?
- [ ] `content_hash` é calculado com a função correta para o tipo de operação?
  - Manual: `app/services/cards.py:42-62`
  - Upload Anki: `app/services/decks.py:1113-1135`

## 7. Qualidade e escopo

- [ ] Nenhuma função nova tem complexidade ciclomática > 12?
- [ ] A mudança não inclui refatorações não relacionadas ao objetivo principal?
- [ ] Nenhuma abstração prematura foi introduzida (três cópias similares antes de extrair)?
- [ ] A mudança pode ser revertida via `git revert` sem consequências irreversíveis?

---

## Veredicto

**Pronto para commit** se grupos 1, 2, 3 e 4 estão todos verificados.  
**Pronto para PR** se todos os 7 grupos estão verificados.

Se um item do grupo 1 falhar: **bloqueante** — a mudança viola uma invariante do sistema.  
Se um item dos grupos 2–4 falhar: **bloqueante** — corrija antes de commitar.  
Se um item dos grupos 5–7 falhar: avalie o risco; documente se aceitar conscientemente.
