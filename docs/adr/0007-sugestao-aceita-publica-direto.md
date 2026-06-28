# ADR-0007 — Sugestão aceita publica direto (supera ADR-0004 para sugestões)

## Contexto
O fluxo de aceitar uma `note_suggestion` exigia versão em `needs_review` +
aprovação + publicação no card + atualização e release no deck (3 telas).
Considerado burocrático para sugestões da comunidade.

## Decisão
Aceitar uma sugestão de card cria uma `CardVersion` já `published` e publica
release em todos os decks ativos que contêm o card, numa única ação
(`NoteSuggestionService._publish_from_suggestion`). Não há segunda revisão.

Escopo: **apenas sugestões**. Reports continuam sob ADR-0004 (`needs_review`).

No-op (só marca `accepted`): sugestão sem card, só de tags, `delete`, sem
mudança mapeável, ou `content_hash` idêntico.

## Consequências
- Nota atualiza imediatamente após o aceite; menos telas/cliques.
- 1 aceite pode gerar N releases (1 por deck afetado).
- Curadoria perde a segunda revisão para sugestões (decisão de produto).
- Imutabilidade preservada: cria nova versão publicada; não modifica publicadas.
