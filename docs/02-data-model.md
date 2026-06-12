# Modelo de Dados

## Princípios

1. A questão original e o flashcard são entidades diferentes.
2. O cartão possui identidade estável.
3. Cada alteração gera uma nova versão.
4. Evidências devem ser vinculadas ao cartão.
5. O histórico nunca deve ser apagado.
6. O progresso do usuário deve se vincular ao `card_id`, não ao `card_version_id`.

## Entidades principais

### raw_documents

Armazena documentos originais.

Campos sugeridos:

```text
id
file_name
file_path
source_type
original_file_hash
raw_text
metadata
extraction_status
uploaded_at
created_at
updated_at
```

### exams

Representa uma prova.

```text
id
raw_document_id
exam_name
institution
board
year
role
level
metadata
created_at
updated_at
```

### questions

Representa uma questão extraída da prova.

```text
id
raw_document_id
exam_id
question_number
statement_text
full_raw_text
detected_answer
official_answer
extraction_confidence
status
created_at
updated_at
```

### question_alternatives

```text
id
question_id
label
text
is_correct
created_at
updated_at
```

### disciplines

```text
id
name
parent_id
created_at
updated_at
```

### topics

```text
id
discipline_id
name
parent_id
created_at
updated_at
```

### question_classifications

```text
id
question_id
discipline_id
topic_id
confidence_score
classification_method
reviewed_by_admin
created_at
updated_at
```

### cards

Identidade estável do flashcard.

```text
id
origin_question_id
canonical_key
discipline_id
topic_id
current_version_id
status
created_at
updated_at
```

### card_versions

Versões imutáveis do cartão.

```text
id
card_id
version_number
front_text
back_text
answer_text
explanation_text
change_reason
created_by
status
content_hash
created_at
updated_at
```

### knowledge_sources

Fontes teóricas.

```text
id
title
source_type
jurisdiction
publication_date
valid_from
valid_until
status
created_at
updated_at
```

### knowledge_chunks

Trechos citáveis da base teórica.

```text
id
source_id
chunk_text
section_title
article_number
paragraph
version_date
content_hash
embedding
created_at
updated_at
```

### card_evidence

Vínculo entre cartão e fundamentação.

```text
id
card_version_id
knowledge_chunk_id
relevance_score
citation_text
created_at
updated_at
```

### decks

```text
id
name
discipline_id
description
status
created_at
updated_at
```

### deck_cards

```text
id
deck_id
card_id
card_version_id
added_at
removed_at
```

### card_reports

Sugestões e problemas enviados por usuários.

```text
id
card_id
card_version_id
user_id
report_type
message
status
created_at
updated_at
```

### review_tasks

```text
id
report_id
assigned_to
decision
admin_comment
resulting_card_version_id
reviewed_at
created_at
updated_at
```

### releases

```text
id
deck_id
release_number
published_at
description
created_at
updated_at
```

### release_items

```text
id
release_id
card_id
card_version_id
action
created_at
updated_at
```

Ações possíveis:

```text
added
updated
removed
deprecated
```

### quality_checks

```text
id
card_version_id
check_type
result
score
message
created_at
```

### prompt_templates

```text
id
name
version
task_type
prompt_text
created_at
updated_at
```

### processing_jobs

```text
id
job_type
entity_type
entity_id
status
started_at
finished_at
error_message
input_snapshot
output_snapshot
created_at
updated_at
```
## Extensões futuras do modelo de cartão

O modelo inicial do cartão deve manter 4 campos principais em `card_versions`:

```text
front_text
back_text
answer_text
explanation_text
```

Esses campos são o núcleo pedagógico do cartão e devem continuar estáveis no MVP.

### Campos extras de conteúdo

Para adicionar campos pedagógicos extras no futuro, não criar colunas novas em `card_versions` sem necessidade.

Usar uma tabela flexível:

```text
card_fields
- id
- card_version_id
- field_name
- field_label
- field_type
- field_value
- display_order
- is_required
- created_at
- updated_at
```

Exemplos de campos extras:

```text
legal_basis
source_quote
mnemonic
common_trap
teacher_comment
jurisprudence
example
related_article
```

Regra:

- `card_fields` deve ser usado para conteúdo complementar do cartão.
- Campos extras devem estar vinculados a uma versão específica do cartão.
- Se um campo extra alterar o conteúdo pedagógico publicado, uma nova `card_version` deve ser criada.

### Templates de cartão

Para controlar diferentes modelos de cartão no futuro, usar:

```text
card_templates
- id
- name
- description
- status
- created_at
- updated_at
```

```text
card_template_fields
- id
- card_template_id
- field_name
- field_label
- field_type
- display_order
- is_required
- created_at
- updated_at
```

Exemplos de templates:

```text
Cartão básico
Cartão jurídico
Cartão de lei seca
Cartão de jurisprudência
Cartão de questão comentada
Cartão de português
Cartão de informática
```

### Página web do cartão

Links públicos ou privados para uma página web do cartão não devem ser tratados como campos principais do conteúdo pedagógico.

Usar tabela própria:

```text
card_public_pages
- id
- card_id
- card_version_id
- slug
- canonical_path
- visibility
- status
- created_at
- updated_at
```

Recomendação:

- salvar preferencialmente `slug` e `canonical_path`, não a URL absoluta;
- montar a URL final dinamicamente a partir do domínio/base URL da aplicação;
- não criar nova versão do cartão apenas porque o domínio mudou;
- criar nova versão apenas se o conteúdo pedagógico da página/cartão mudar.

Exemplo:

```text
card_id: CARD-000123
card_version_id: VERSION-000456
slug: habeas-corpus-liberdade-locomocao
canonical_path: /cards/habeas-corpus-liberdade-locomocao
visibility: public
status: published
```

## Separação conceitual

```text
card_versions = conteúdo pedagógico versionado
card_fields = campos pedagógicos extras versionados
card_public_pages = metadados de publicação/exibição web
```

Essa separação evita que mudanças de interface, URL ou domínio contaminem o histórico pedagógico do cartão.
