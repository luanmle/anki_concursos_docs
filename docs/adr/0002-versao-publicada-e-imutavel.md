# ADR-0002 — Versão publicada de cartão é imutável

**Status:** Aceito
**Data:** 2026-06-12

## Contexto

Quando um `CardVersion` atinge `status=published`, ele foi distribuído a alunos via release. Modificar o conteúdo de uma versão publicada corromperia silenciosamente o histórico — um aluno poderia ter estudado a versão antiga sem nenhum registro da mudança.

## Decisão

`CardVersion` com `status=published` não pode ser alterada nem excluída. A proteção existe em duas camadas:

1. **SQLAlchemy** — evento `prevent_published_version_update` (`app/models/entities.py:724-735`) e `prevent_published_version_delete` (`app/models/entities.py:738-741`) levantam `ValueError`.
2. **PostgreSQL** — trigger `trg_card_versions_immutable` (aplicado na migration `20260615_0007_pre_mvp_8_security`), verificado nos testes de integração em `tests/test_postgres_integration.py:157-165`.

Correções criam uma nova `CardVersion` com `version_number` incrementado e `status=needs_review`, que percorre novamente o ciclo de aprovação → publicação.

## Consequências

- **Positivas:** audit trail completo; cada release aponta para versões específicas que nunca mudam; regressão de conteúdo é impossível sem criar nova versão.
- **Negativas:** correções triviais (typo) exigem o mesmo fluxo de aprovação de mudanças substanciais.
- **Neutras:** o campo `content_hash` impede que duas versões com conteúdo idêntico coexistam no mesmo cartão (`app/services/cards.py:190-196`).

## Alternativas consideradas

- **Edição in-place com log de mudança:** descartado porque releases apontariam para uma versão que pode ter conteúdo diferente do que foi originalmente publicado.
