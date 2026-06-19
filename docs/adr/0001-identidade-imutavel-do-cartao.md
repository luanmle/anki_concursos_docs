# ADR-0001 — Identidade pública do cartão é imutável

**Status:** Aceito
**Data:** 2026-06-12

## Contexto

O add-on Anki e o cliente web identificam cartões pelo `public_id` (formato `AC-<32 hex>`). O aluno pode fazer anotações e vincular progresso a esse identificador. Se o `public_id` pudesse mudar, o aluno perderia o vínculo com seu histórico de estudos após uma correção de conteúdo.

Ao mesmo tempo, o *conteúdo* do cartão precisa poder evoluir (correções, atualizações de lei). A solução é separar a identidade da versão.

## Decisão

`Card.public_id` é gerado na criação (`AC-{uuid.uuid4().hex.upper()}`) e nunca alterado. O evento SQLAlchemy `prevent_public_card_id_update` levanta `ValueError` em qualquer tentativa de update (`app/models/entities.py:669-671`). Correções de conteúdo criam uma nova `CardVersion` — nunca um novo `Card`.

## Consequências

- **Positivas:** o aluno pode confiar que `AC-XYZ` sempre se refere ao mesmo cartão conceitual; integrações externas não quebram por mudança de ID.
- **Negativas:** merges de cartões duplicados exigem lógica de migração manual (o sistema atual não tem esse fluxo).
- **Neutras:** o `canonical_key` é a chave de deduplicação interna e pode assumir diferentes formatos dependendo da origem (manual, CSV, upload Anki).

## Alternativas consideradas

- **UUID interno como ID público:** descartado porque UUIDs internos são instáveis entre ambientes (staging vs. produção) e não carregam semântica legível.
- **Slug baseado em conteúdo:** descartado porque o conteúdo muda entre versões.
