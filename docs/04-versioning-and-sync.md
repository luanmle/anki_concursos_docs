# Versionamento e Sincronização

## Princípio fundamental

O sistema deve separar:

- identidade do cartão;
- versão do conteúdo.

## Identidade estável

A tabela `cards` representa a identidade do cartão.

O `card_id` nunca muda.

O `public_id` também nunca muda e representa essa identidade para o usuário.
Ele não substitui o UUID interno nas relações do banco.

## Versão imutável

A tabela `card_versions` representa o conteúdo de uma versão específica.

Toda alteração relevante deve gerar nova versão.

Nunca editar uma versão publicada diretamente.

Referências a versões também devem preservar a identidade do cartão:

- `cards.current_version_id` deve pertencer ao próprio cartão;
- `deck_cards.card_version_id` deve pertencer ao `deck_cards.card_id`;
- `release_items.card_version_id` deve pertencer ao `release_items.card_id`.

## Exemplo

```text
card_id: CARD-000123

v1:
front: O habeas corpus protege qual direito?
back: Protege a liberdade de locomoção.

v2:
front: Qual remédio constitucional protege a liberdade de locomoção?
back: Habeas corpus. Fundamentação: art. 5º, LXVIII, CF.
```

O usuário mantém progresso em `CARD-000123`, mesmo que o conteúdo mude de v1 para v2.

## Regras de versionamento

Criar nova versão quando mudar:

- frente;
- verso;
- resposta;
- explicação;
- fundamentação;
- classificação;
- status jurídico;
- correção de erro material relevante.

Não criar nova versão para:

- alteração interna de log;
- metadado administrativo irrelevante;
- mudança de status ainda não publicada.

## Estados do cartão

```text
generated
needs_review
approved
published
reported
revised
deprecated
archived
```

## Releases

Uma release agrupa mudanças publicadas.

Exemplo:

```text
Release 12
- 120 cartões adicionados
- 35 cartões atualizados
- 4 cartões depreciados
```

No MVP 3, a release é criada como delta:

- `added`: cartão ativo que não existia no estado publicado anterior;
- `updated`: mesmo `card_id` com novo `card_version_id`;
- `removed`: cartão retirado do deck;
- `deprecated`: cartão retirado com indicação explícita de descontinuação.

Releases e `release_items` não podem ser editados ou apagados.

## Exportação CSV

Cada CSV representa uma release específica. Mudanças posteriores não podem
alterar retroativamente o conteúdo exportável daquela release.

Como `release_items` armazena deltas, o snapshot exportável é reconstruído pela
aplicação de todas as ações até o `release_number` solicitado. `added` e
`updated` definem a versão ativa; `removed` e `deprecated` removem a identidade
do snapshot sem apagar o histórico.

Colunas mínimas:

```text
card_id
public_id
card_version_id
front_text
back_text
answer_text
explanation_text
tags
```

O `card_id` permite reconhecer a mesma identidade entre versões. O CSV não
substitui a API incremental e, isoladamente, não preserva o progresso do Anki.

O endpoint implementado é:

```text
GET /decks/{deck_id}/releases/{release_id}/export.csv
```

O conteúdo é ordenado por `public_id` e acompanhado de hash SHA-256 para
verificação de reprodutibilidade.

Busca pública conceitual:

```text
GET /cards/public/{public_id}
```

## Sincronização incremental

```text
GET /decks/{deck_id}/releases?page=1&page_size=20
GET /decks/{deck_id}/sync?since_release=12
```

A listagem de releases é ordenada da mais recente para a mais antiga e inclui
contagens de `added`, `updated`, `removed` e `deprecated`.

No endpoint de sync:

- `since_release=0` representa um cliente sem estado local;
- um número positivo deve identificar uma release existente no deck;
- `to_release` informa a release mais recente disponível;
- `has_changes=false` indica que o cliente já está atualizado;
- mudanças são retornadas em ordem crescente de release;
- todas as mudanças posteriores são preservadas, sem condensação;
- o cliente deve aplicar os deltas sequencialmente.

Resposta implementada:

```json
{
  "deck_id": "deck_constitucional",
  "from_release": 12,
  "to_release": 14,
  "has_changes": true,
  "changes": [
    {
      "release_id": "release_13",
      "release_number": 13,
      "published_at": "2026-06-12T19:00:00Z",
      "action": "updated",
      "card_id": "CARD-000123",
      "public_id": "AC-550E8400E29B41D4A716446655440000",
      "old_card_version_id": "v1",
      "new_card_version_id": "v2"
    },
    {
      "release_id": "release_14",
      "release_number": 14,
      "published_at": "2026-06-12T20:00:00Z",
      "action": "added",
      "card_id": "CARD-000456",
      "public_id": "AC-550E8400E29B41D4A716446655440001",
      "old_card_version_id": null,
      "new_card_version_id": "v1"
    },
    {
      "release_id": "release_14",
      "release_number": 14,
      "published_at": "2026-06-12T20:00:00Z",
      "action": "deprecated",
      "card_id": "CARD-000789",
      "public_id": "AC-550E8400E29B41D4A716446655440002",
      "old_card_version_id": "v3",
      "new_card_version_id": null
    }
  ]
}
```

`old_card_version_id` é reconstruído pela reprodução das releases anteriores.
Isso permite confirmar qual versão local está sendo substituída ou removida.

O contrato atual retorna identidades e versões, não o conteúdo completo da
versão. Um futuro add-on poderá usar esses IDs em endpoints de distribuição
específicos sem alterar o modelo de releases.

## Assinaturas e add-on do Anki

O fluxo tipo AnkiHub usa decks como unidade de assinatura. Um usuario
autenticado assina um deck publicado e o add-on consome apenas decks com
assinatura ativa.

Endpoints de assinatura:

```text
GET /subscriptions/decks
GET /subscriptions
POST /subscriptions/{deck_id}
POST /subscriptions/{deck_id}/cancel
```

Endpoints do add-on:

```text
GET /addon/decks/{deck_id}/manifest
GET /addon/decks/{deck_id}/sync?since_release=0
```

O manifesto informa como o add-on deve criar ou atualizar o note type local:

```json
{
  "deck_id": "deck_id",
  "name": "Direito Constitucional",
  "latest_release": 12,
  "note_type": "Anki Concursos Basic",
  "fields": ["Front", "Back", "Answer", "Explanation"],
  "field_mapping": {
    "Front": "front_text",
    "Back": "back_text",
    "Answer": "answer_text",
    "Explanation": "explanation_text"
  },
  "supported_note_types": {
    "basic": {
      "note_type": "Anki Concursos Basic",
      "fields": ["Front", "Back", "Answer", "Explanation"],
      "field_mapping": {
        "Front": "front_text",
        "Back": "back_text",
        "Answer": "answer_text",
        "Explanation": "explanation_text"
      }
    },
    "cloze": {
      "note_type": "Anki Concursos Cloze",
      "fields": ["Text", "Extra", "Answer", "Explanation"],
      "field_mapping": {
        "Text": "front_text",
        "Extra": "back_text",
        "Answer": "answer_text",
        "Explanation": "explanation_text"
      }
    }
  },
  "tags": ["deck::deck_id"]
}
```

O sync do add-on difere do sync administrativo em um ponto importante:

- `since_release=0` retorna o snapshot atual do deck como acoes `added`;
- `since_release>0` retorna apenas deltas posteriores a release local.

Cada mudanca destinada ao add-on inclui os campos do cartao quando a acao e
`added` ou `updated`. Acoes `removed` e `deprecated` retornam `fields = null`.
Para acoes com conteudo, cada item tambem retorna `card_kind` e `note_type`;
assim o add-on escolhe entre `Anki Concursos Basic` e `Anki Concursos Cloze`
sem inferir pelo texto.

O progresso do estudante continua pertencendo ao Anki local e deve ser
associado pelo add-on ao `card_id`, nunca ao texto do cartao.

## Curadoria e versionamento

Um report é vinculado ao `card_id` e à `card_version_id` publicada que motivou
a denúncia. A versão reportada nunca é editada.

Quando a decisão é `converted_to_new_version`:

- uma nova `card_version` é criada;
- `version_number` é incrementado;
- `change_reason` é obrigatório;
- o conteúdo inicia em `needs_review`;
- `current_version_id` não muda;
- o cartão continua público com a versão anterior;
- decks e releases existentes permanecem inalterados.

A nova versão só substitui a publicada após aprovação, publicação e atualização
explícita do vínculo do deck.

## Regra crítica

O progresso do usuário deve estar vinculado ao `card_id`, não ao `card_version_id`.
