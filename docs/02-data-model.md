# Modelo De Dados

## Principios

1. `cards` representa identidade estavel.
2. `card_versions` representa conteudo imutavel.
3. `decks` agrupam cartoes publicados.
4. `releases` sao imutaveis.
5. `card_reports` e `review_tasks` preservam curadoria auditavel.
6. O add-on trabalha com deck completo e templates nativos do Anki.
7. Templates do deck sao versionados em tabelas proprias para permitir sync
   incremental de estrutura.

## Usuarios

```text
users
id, email, display_name, password_hash, role, is_active, credential_version,
last_login_at, created_at, updated_at
```

Roles:

```text
admin
curator
reviewer
student
```

`student` autentica, assina decks e sincroniza o add-on.

## Taxonomia

```text
disciplines
topics
```

Taxonomia segue util para organizacao interna e para cards manuais.

## Cartoes

```text
cards
id, public_id, canonical_key, discipline_id, topic_id, current_version_id,
status, card_kind, created_at, updated_at
```

```text
card_versions
id, card_id, version_number, front_text, back_text, answer_text,
explanation_text, change_reason, created_by, status, content_hash,
note_type, template_name, anki_fields, anki_template, anki_tags,
source_note_id, source_note_guid, source_deck_path, created_at, updated_at
```

O backend preserva os campos nativos do Anki para upload e sync de decks
completos.

## Decks E Releases

```text
decks
deck_cards
deck_subscriptions
releases
release_items
deck_snapshots
deck_templates
deck_template_versions
```

Regras:

- deck e release sao as unidades de distribuicao;
- assinatura e por deck;
- release e imutavel;
- `deck_cards.card_version_id` sempre aponta para a versao atual ativa;
- uploads do add-on criam snapshot do pacote completo;
- `discipline_id` e `topic_id` continuam opcionais no fluxo de upload do deck.

### Templates Do Deck

```text
deck_templates
id, deck_id, template_key, template_name, note_type, card_kind,
current_version_id, created_at, updated_at
```

```text
deck_template_versions
id, deck_template_id, version_number, fields, field_mapping, front_html,
back_html, styling_css, content_hash, status, created_by, created_at,
updated_at
```

`deck_templates.current_version_id` aponta para a versao ativa do template.
O manifesto do add-on le a versao corrente do banco como fonte primaria.

## Curadoria

```text
card_reports
review_tasks
```

Decisoes atuais:

```text
rejected
duplicate
converted_to_new_version
```

## Operacao E Auditoria

```text
processing_jobs
```

Usado para rastrear operacoes criticas, publicacao e exportacao quando
necessario.

## Legado

Tabelas antigas de documentos e questoes continuam fora do fluxo principal.
Nao devem ser reintroduzidas como dependencia de produto.
