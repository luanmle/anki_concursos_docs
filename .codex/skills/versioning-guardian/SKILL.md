---
name: versioning-guardian
description: Protege regras de versionamento de flashcards, garantindo card_id estável, card_versions imutáveis e criação correta de novas versões.
---
# versioning-guardian

## Propósito

Use esta skill sempre que uma tarefa envolver cartões, versões, edição de conteúdo, reports, sugestões, curadoria, publicação ou sincronização.

Esta skill protege a regra central do projeto:

> O `card_id` é a identidade estável do cartão. O `card_version_id` representa uma versão específica e imutável do conteúdo.

## Quando usar

Use esta skill para tarefas como:

- criar cartão;
- editar cartão;
- aprovar sugestão;
- revisar report;
- publicar cartão;
- criar nova versão;
- implementar sincronização;
- alterar status de cartões;
- migrar dados relacionados a `cards` e `card_versions`.

## Regras obrigatórias

1. Nunca editar diretamente uma `card_version` publicada.
2. Toda alteração pedagógica relevante deve criar uma nova `card_version`.
3. O `card_id` deve permanecer estável durante todo o ciclo de vida do cartão.
4. O progresso futuro do usuário deve se vincular ao `card_id`, não ao `card_version_id`.
5. Ao criar nova versão, incrementar `version_number`.
6. Ao criar nova versão aprovada/publicada, atualizar `cards.current_version_id`.
7. Preservar versões antigas para auditoria.
8. Registrar `change_reason` em toda nova versão gerada por edição, report ou sugestão.
9. Não apagar histórico de versões.
10. Não confundir `cards.status` com `card_versions.status`.

## Modelo conceitual

```text
cards
- id
- origin_question_id
- discipline_id
- topic_id
- current_version_id
- status

card_versions
- id
- card_id
- version_number
- front_text
- back_text
- answer_text
- explanation_text
- change_reason
- created_by
- status
- content_hash
```

## Regra de decisão

Criar nova versão quando mudar:

- `front_text`;
- `back_text`;
- `answer_text`;
- `explanation_text`;
- fundamentação pedagógica;
- classificação pedagógica relevante;
- correção de erro;
- atualização legislativa;
- melhoria aprovada por curadoria.

Não criar nova versão apenas por:

- mudança de domínio;
- mudança de slug;
- alteração de layout;
- alteração de metadado administrativo;
- mudança de logs;
- alteração interna não visível ao estudante.

## Campos extras futuros

Se a tarefa envolver campos extras, seguir:

```text
card_versions = 4 campos principais do conteúdo pedagógico
card_fields = campos pedagógicos extras
card_public_pages = metadados de publicação web
```

Não adicionar URL pública como quinto campo principal de `card_versions`.

## Checklist antes de finalizar código

- Existe teste garantindo que versão antiga não foi alterada?
- Existe teste garantindo que `card_id` permanece igual?
- Existe teste garantindo que `current_version_id` aponta para a versão nova?
- Existe `change_reason`?
- A versão anterior continua consultável?
- O endpoint ou serviço não edita conteúdo publicado diretamente?
