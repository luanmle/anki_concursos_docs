---
name: quality-checker
description: Define validações e quality checks para impedir publicação de cartões incompletos, sem evidência ou inconsistentes.
---
# quality-checker

## Propósito

Use esta skill para implementar validações, quality checks e regras de publicação de flashcards.

O objetivo é impedir que cartões incompletos, sem evidência ou inconsistentes sejam publicados.

## Quando usar

Use esta skill para tarefas como:

- validar cartão;
- publicar cartão;
- criar quality checks;
- revisar pipeline de validação;
- criar testes de qualidade;
- criar regras de aprovação;
- impedir publicação automática insegura.

## Tabela esperada

```text
quality_checks
- id
- card_version_id
- check_type
- result
- score
- message
- created_at
```

## Regras mínimas para publicação

Um cartão só pode ser publicado se:

- possui `front_text`;
- possui `back_text`;
- possui `answer_text`;
- possui `explanation_text`;
- possui disciplina válida;
- possui assunto válido;
- possui questão de origem ou origem explícita;
- possui evidência vinculada;
- não é duplicata evidente;
- está em status permitido;
- passou por validação mínima.

## Checks sugeridos

### Conteúdo

```text
front_not_empty
back_not_empty
answer_not_empty
explanation_not_empty
is_atomic
no_excessive_question_copy
```

### Classificação

```text
valid_discipline
valid_topic
classification_confidence_above_threshold
```

### Evidência

```text
has_evidence
evidence_is_valid
source_is_current
citation_exists
```

### Versionamento

```text
card_has_stable_id
version_number_incremented
content_hash_changed
previous_version_preserved
```

### Publicação

```text
status_allows_publication
deck_exists
release_created
```

## Regras obrigatórias

1. Não publicar cartão gerado automaticamente sem validação mínima.
2. Quality checks devem ser salvos para auditoria.
3. Falhas devem ter mensagem clara.
4. Checks automáticos não substituem curadoria humana quando confiança for baixa.
5. Cartões sem evidência não devem ser publicados.
6. Cartões com classificação inválida não devem ser publicados.
7. Cartões duplicados devem ser marcados para revisão.
8. Scores baixos devem gerar `needs_review`.

## Resultado dos checks

Usar resultados como:

```text
passed
failed
warning
skipped
```

## Checklist antes de finalizar

- Existe função central de validação?
- Publicação chama validação?
- Falhas impedem publicação?
- Warnings geram revisão quando necessário?
- Checks ficam persistidos?
- Existem testes para bloqueios de publicação?
