---
name: pipeline-engineer
description: Orienta pipelines de ingestão, extração de PDF, segmentação de questões, classificação, geração de cards e jobs assíncronos.
---
# pipeline-engineer

## Propósito

Use esta skill para implementar ou revisar o pipeline que transforma documentos brutos em flashcards versionados e fundamentados.

## Quando usar

Use esta skill para tarefas como:

- upload de prova;
- extração de PDF;
- OCR;
- segmentação de questões;
- extração de alternativas;
- classificação;
- geração de flashcards;
- busca de evidências;
- validação automática;
- processamento assíncrono;
- logs de jobs;
- reprocessamento.

## Jornada do dado

```text
Documento bruto
→ Questão estruturada
→ Questão classificada
→ Flashcard gerado
→ Flashcard fundamentado
→ Flashcard validado
→ Flashcard revisado
→ Flashcard publicado
→ Release
```

## Etapas esperadas

```text
1. upload_document
2. extract_text
3. split_questions
4. parse_alternatives
5. detect_or_import_answer_key
6. classify_question
7. generate_flashcard
8. retrieve_evidence
9. run_quality_checks
10. save_card_version
11. submit_for_review
```

## Regras obrigatórias

1. Não processar documento pesado dentro do request HTTP.
2. Usar fila ou job assíncrono para tarefas longas.
3. Cada etapa deve registrar status em `processing_jobs`.
4. Cada etapa deve poder falhar de forma rastreável.
5. Não descartar o texto bruto original.
6. Não sobrescrever outputs intermediários sem registro.
7. Separar questão original de flashcard gerado.
8. Classificação automática deve ter score de confiança.
9. Geração automática deve produzir status `generated` ou `needs_review`, não `published`.
10. Publicação exige validações mínimas.

## Tabela de jobs

Usar ou respeitar estrutura equivalente:

```text
processing_jobs
- id
- job_type
- entity_type
- entity_id
- status
- started_at
- finished_at
- error_message
- input_snapshot
- output_snapshot
- created_at
- updated_at
```

## Status de job

```text
pending
running
succeeded
failed
cancelled
retrying
```

## Regras de idempotência

Antes de criar novos registros, verificar se a etapa já foi executada.

Exemplos:

- Não duplicar `questions` se o documento já foi segmentado.
- Não duplicar `card_versions` para o mesmo conteúdo.
- Usar `content_hash` quando apropriado.
- Permitir reprocessamento controlado.

## Regras de erro

Quando falhar:

- registrar erro em `processing_jobs.error_message`;
- manter status do documento/entidade coerente;
- não apagar dados intermediários;
- permitir retry.

## Checklist antes de finalizar

- A etapa roda fora do request principal?
- Existe log de processamento?
- A falha é rastreável?
- A etapa é idempotente ou tem proteção contra duplicação?
- O pipeline preserva documento bruto?
- O pipeline não publica conteúdo automaticamente sem validação?
