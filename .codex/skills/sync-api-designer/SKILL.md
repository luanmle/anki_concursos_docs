---
name: sync-api-designer
description: Orienta decks, releases e endpoints de sincronização incremental baseados em card_id e card_version_id.
---
# sync-api-designer

## Propósito

Use esta skill para implementar ou revisar baralhos, releases e endpoints de sincronização incremental.

O objetivo é permitir atualização tipo AnkiHub: baixar apenas mudanças sem perder o progresso do usuário.

## Quando usar

Use esta skill para tarefas como:

- criar decks;
- adicionar cartões a decks;
- publicar release;
- listar releases;
- criar endpoint de sync;
- calcular mudanças desde release;
- remover ou depreciar cartões;
- exportar pacotes de atualização.
- exportar releases em CSV para o Anki.

## Princípio central

A sincronização deve ser baseada em:

```text
card_id = identidade estável
public_id = identidade estável visível ao usuário
card_version_id = conteúdo específico
release_id/release_number = marco de publicação
```

## Tabelas esperadas

```text
decks
- id
- name
- discipline_id
- description
- status

deck_cards
- id
- deck_id
- card_id
- card_version_id
- added_at
- removed_at

releases
- id
- deck_id
- release_number
- published_at
- description

release_items
- id
- release_id
- card_id
- card_version_id
- action
```

## Ações de release

```text
added
updated
removed
deprecated
```

## Endpoints conceituais

```text
GET /decks
GET /decks/{deck_id}
GET /decks/{deck_id}/releases
POST /decks/{deck_id}/publish-release
GET /decks/{deck_id}/sync?since_release=12
```

Operações administrativas de composição:

```text
POST /decks/{deck_id}/cards
POST /decks/{deck_id}/cards/{card_id}/remove
```

## Resposta conceitual de sync

```json
{
  "deck_id": "deck_constitucional",
  "from_release": 12,
  "to_release": 13,
  "changes": [
    {
      "action": "updated",
      "card_id": "CARD-000123",
      "old_version_id": "VERSION-000111",
      "new_version_id": "VERSION-000222"
    },
    {
      "action": "added",
      "card_id": "CARD-000456",
      "new_version_id": "VERSION-000333"
    },
    {
      "action": "deprecated",
      "card_id": "CARD-000789"
    }
  ]
}
```

## Regras obrigatórias

1. Não implementar sync como download completo obrigatório.
2. Não usar texto do cartão como identificador.
3. Sempre retornar `card_id`.
4. Sempre retornar `public_id` nas respostas destinadas ao usuário.
5. Para updates, retornar o novo `card_version_id`.
6. Não quebrar progresso do usuário.
7. Releases devem ser imutáveis depois de publicadas.
8. Release deve representar snapshot ou delta rastreável.
9. Cartão removido/depreciado deve ser comunicado explicitamente.
10. Não apagar card antigo para representar remoção.
11. Sync deve respeitar status publicado.
12. CSV deve ser gerado a partir de uma release específica.
13. CSV deve incluir `public_id`, `card_id` e `card_version_id`.
14. CSV não substitui o contrato incremental de sync.
15. Deck deve apontar apenas para versão publicada.
16. Release e itens devem ser imutáveis.

## Exportação CSV

Colunas mínimas:

```text
public_id
card_id
card_version_id
front_text
back_text
answer_text
explanation_text
tags
```

Usar UTF-8, escape compatível com CSV e ordenação determinística.

## Checklist antes de finalizar

- O endpoint retorna mudanças incrementais?
- As ações são explícitas?
- O `card_id` está presente?
- O `card_version_id` está presente quando necessário?
- A release publicada é imutável?
- Existem testes de added/updated/removed/deprecated?
- A exportação é reproduzível para a mesma release?
