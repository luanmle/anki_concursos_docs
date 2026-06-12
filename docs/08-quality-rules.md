# Regras de Qualidade

## Objetivo

Garantir que cartões publicados sejam úteis, confiáveis, rastreáveis e corrigíveis.

## Regras para flashcards

Um flashcard deve ser:

- atômico;
- objetivo;
- autoexplicativo;
- fundamentado;
- classificado;
- versionado;
- rastreável.

## Checklist antes da publicação

O cartão só pode ser publicado se:

- possui frente;
- possui verso;
- possui resposta;
- possui explicação;
- possui disciplina válida;
- possui assunto válido;
- possui questão de origem ou origem explícita;
- possui evidência vinculada;
- passou por revisão ou validação mínima;
- não é duplicata evidente;
- está em status permitido.

## Checks automáticos sugeridos

### Conteúdo

- `front_not_empty`
- `back_not_empty`
- `answer_not_empty`
- `explanation_not_empty`
- `is_atomic`
- `no_excessive_question_copy`

### Classificação

- `valid_discipline`
- `valid_topic`
- `classification_confidence_above_threshold`

### Evidência

- `has_evidence`
- `evidence_is_valid`
- `source_is_current`
- `citation_exists`

### Versionamento

- `card_has_stable_id`
- `version_number_incremented`
- `content_hash_changed`
- `previous_version_preserved`

### Publicação

- `status_allows_publication`
- `deck_exists`
- `release_created`

## Tipos de report

```text
typo
wrong_answer
outdated_law
bad_explanation
classification_error
duplicate_card
suggestion
```

## Regra final

Nenhum cartão gerado automaticamente deve ser publicado sem passar por validação mínima.
