# Modelo de Dados

## Princípios

1. `cards` representa identidade estável.
2. `card_versions` representa conteúdo imutável.
3. Alterações pedagógicas criam novas versões.
4. Releases são publicações imutáveis.
5. CSV é uma projeção de uma release.
6. Histórico publicado nunca é apagado.

## Acesso administrativo

### users

```text
id
email
display_name
password_hash
role
is_active
credential_version
last_login_at
created_at
updated_at
```

Papéis:

```text
admin
curator
reviewer
```

Regras:

- `email` é único e normalizado para minúsculas pela API;
- senha nunca é armazenada em texto puro;
- `password_hash` usa PBKDF2-HMAC-SHA256 com salt individual;
- usuário inativo não pode autenticar nem continuar usando tokens;
- alterações de senha, papel ou ativação incrementam `credential_version` e
  revogam tokens emitidos anteriormente;
- a autorização consulta o papel atual no banco, não apenas o papel no token;
- `admin` gerencia usuários e possui todas as permissões;
- `curator` cadastra, consulta e cria versões e decks;
- `reviewer` aprova, publica, cria releases e revisa reports.

## Núcleo

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

### cards

```text
id
public_id
origin_question_id
canonical_key
discipline_id
topic_id
current_version_id
status
created_at
updated_at
```

`origin_question_id` é legado e opcional. A identidade do cartão não depende
de documento ou questão.

`public_id` usa o formato `AC-` seguido de 32 caracteres hexadecimais
maiúsculos. Ele é único, imutável, pesquisável e preservado entre versões.

### card_versions

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

Regras:

- `UNIQUE(card_id, version_number)`;
- versão publicada é imutável;
- `cards.current_version_id` deve pertencer ao mesmo cartão;
- conteúdo exportado deve vir da versão registrada na release.

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
public_id
card_version_id
added_at
removed_at
removal_action
```

`card_version_id` deve pertencer ao mesmo `card_id`.

Quando `removed_at` estiver preenchido, `removal_action` deve ser `removed` ou
`deprecated`. A depreciação registrada aqui é específica da distribuição no
deck.

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

Ações:

```text
added
updated
removed
deprecated
```

`card_version_id`, quando informado, deve pertencer ao mesmo `card_id`.

Releases e seus itens são imutáveis após a criação.

## Curadoria

### card_reports

```text
id
card_id
card_version_id
reporter_reference
report_type
message
status
created_at
updated_at
```

Tipos:

```text
typo
wrong_answer
outdated_law
bad_explanation
classification_error
duplicate_card
suggestion
```

Status:

```text
open
in_review
approved
rejected
resolved
duplicate
```

Regras:

- report sempre aponta para `card_id` e `card_version_id`;
- a versão deve pertencer ao mesmo cartão;
- `reporter_reference` é uma referência opcional informada pelo cliente e não
  representa identidade autenticada;
- cartão, versão, referência, tipo e mensagem do report são imutáveis;
- status terminal não pode ser reaberto;
- reports não podem ser apagados;
- o envio público aceita somente uma versão publicada.

### review_tasks

```text
id
report_id
status
assigned_to
decision
admin_comment
evidence_reviewed
resulting_card_version_id
reviewed_at
created_at
updated_at
```

Existe uma tarefa por report.

Decisões terminais do MVP 6:

```text
rejected
duplicate
converted_to_new_version
```

Regras:

- decisão concluída exige responsável, comentário e data;
- `outdated_law` convertido exige `evidence_reviewed = true`;
- `converted_to_new_version` exige `resulting_card_version_id`;
- a versão resultante deve pertencer ao cartão reportado;
- rejeição e duplicidade não podem gerar versão;
- tarefas concluídas são imutáveis;
- tarefas de revisão não podem ser apagadas.

`quality_checks` permanece como extensão futura.

## Evidências Futuras

```text
knowledge_sources
knowledge_chunks
card_evidence
```

Evidências pertencem a uma `card_version`, pois a fundamentação pode mudar
entre versões.

## Jobs

`processing_jobs` pode registrar publicação ou exportação:

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

Filas assíncronas não são obrigatórias no primeiro MVP.

## Exportações CSV

O CSV deve ser derivado de uma release e incluir:

```text
card_id
card_version_id
deck_id
front_text
back_text
answer_text
explanation_text
tags
```

Uma futura tabela de auditoria pode registrar:

```text
release_exports
- id
- release_id
- format
- delimiter
- content_hash
- row_count
- created_by
- created_at
```

O conteúdo do CSV não deve ser duplicado no banco como fonte primária.

## Entidades Legadas

As tabelas abaixo existem na migration inicial, mas estão fora do escopo ativo:

```text
raw_documents
exams
questions
question_alternatives
```

Não criar novas dependências com elas. Sua remoção exige migration própria e
decisão explícita sobre compatibilidade.

## Extensões

Campos adicionais e templates devem seguir
`docs/09-future-card-extensions.md`.
