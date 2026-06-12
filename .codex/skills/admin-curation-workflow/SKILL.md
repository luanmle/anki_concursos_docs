---
name: admin-curation-workflow
description: Orienta fluxos administrativos de reports, revisão, aprovação, rejeição e criação de novas versões.
---
# admin-curation-workflow

## Propósito

Use esta skill para implementar ou revisar fluxos de curadoria administrativa, reports de usuários, aprovação, reprovação e criação de novas versões.

## Quando usar

Use esta skill para tarefas como:

- criar painel administrativo;
- aprovar cartão;
- reprovar cartão;
- editar cartão;
- revisar report;
- aprovar sugestão;
- criar review task;
- alterar status;
- registrar decisão do administrador.

## Entidades esperadas

```text
card_reports
- id
- card_id
- card_version_id
- user_id
- report_type
- message
- status
- created_at
- updated_at

review_tasks
- id
- report_id
- assigned_to
- decision
- admin_comment
- resulting_card_version_id
- reviewed_at
- created_at
- updated_at
```

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

## Decisões administrativas

```text
approved
rejected
needs_more_info
duplicate
converted_to_new_version
```

## Regras obrigatórias

1. Report deve apontar para `card_id` e `card_version_id`.
2. A versão reportada deve continuar preservada.
3. Sugestão aprovada não edita versão antiga.
4. Sugestão aprovada cria nova `card_version` quando altera conteúdo pedagógico.
5. Toda decisão administrativa deve ser registrada.
6. Admin deve informar ou gerar `change_reason`.
7. Rejeição de report não deve alterar conteúdo.
8. Report de erro jurídico deve exigir revisão de evidência.
9. Alteração de disciplina/assunto deve respeitar taxonomia oficial.
10. Publicação após curadoria deve passar por quality checks.

## Fluxo recomendado

```text
Usuário reporta problema
→ cria card_report
→ cria ou atualiza review_task
→ admin revisa
→ admin aprova/rejeita
→ se aprovado e muda conteúdo, cria card_version nova
→ atualiza current_version_id se aplicável
→ registra resulting_card_version_id
```

## Status sugeridos

Para `card_reports`:

```text
open
in_review
approved
rejected
resolved
duplicate
```

Para `review_tasks`:

```text
pending
assigned
completed
cancelled
```

## Checklist antes de finalizar

- A versão antiga foi preservada?
- A decisão do admin foi registrada?
- A sugestão aprovada criou nova versão quando necessário?
- O report aponta para a versão reportada?
- O status ficou coerente?
- Existem testes de aprovação e rejeição?
