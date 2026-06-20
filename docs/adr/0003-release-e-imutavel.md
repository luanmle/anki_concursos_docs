# ADR-0003 — Release e seus itens são imutáveis após publicação

**Status:** Aceito
**Data:** 2026-06-12

## Contexto

Uma `Release` representa um snapshot distribuível de um deck em um ponto no tempo. O add-on Anki usa `since_release` para sincronização incremental: se uma release pudesse ser modificada, o cliente calcularia deltas incorretos e perderia ou duplicaria cartões.

## Decisão

`Release` e `ReleaseItem` são imutáveis após criação. Eventos SQLAlchemy impedem qualquer update ou delete:

- `prevent_release_mutation` — `app/models/entities.py:744-747`
- `prevent_release_item_mutation` — `app/models/entities.py:750-755`

Adicionar ou remover cartões de um deck após a última release só afeta a *próxima* release. A constraint `uq_release_deck_number` (`app/models/entities.py:569`) garante que `release_number` seja único por deck.

## Consequências

- **Positivas:** `since_release=N` sempre produz o mesmo delta, independente de quando é chamado; o histórico completo de distribuições é preservado.
- **Negativas:** não é possível corrigir uma release com typo na `description` — uma nova release seria necessária.
- **Neutras:** releases com 0 mudanças não são criadas (verificação em `app/services/decks.py:869`).

## Alternativas consideradas

- **Release mutável com versionamento de item:** descartado porque o protocolo de sync incremental pressupõe que o passado é estável.
