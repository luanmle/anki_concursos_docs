# Versionamento e Sincronização

## Princípio fundamental

O sistema deve separar:

- identidade do cartão;
- versão do conteúdo.

## Identidade estável

A tabela `cards` representa a identidade do cartão.

O `card_id` nunca muda.

## Versão imutável

A tabela `card_versions` representa o conteúdo de uma versão específica.

Toda alteração relevante deve gerar nova versão.

Nunca editar uma versão publicada diretamente.

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

## Endpoint conceitual de sincronização

```text
GET /decks/{deck_id}/sync?since_release=12
```

Resposta conceitual:

```json
{
  "deck_id": "deck_constitucional",
  "from_release": 12,
  "to_release": 13,
  "changes": [
    {
      "action": "updated",
      "card_id": "CARD-000123",
      "old_version_id": "v1",
      "new_version_id": "v2"
    },
    {
      "action": "added",
      "card_id": "CARD-000456",
      "new_version_id": "v1"
    },
    {
      "action": "deprecated",
      "card_id": "CARD-000789"
    }
  ]
}
```

## Regra crítica

O progresso do usuário deve estar vinculado ao `card_id`, não ao `card_version_id`.
