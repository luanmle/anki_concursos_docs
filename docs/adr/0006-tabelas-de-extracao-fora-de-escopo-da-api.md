# ADR-0006 — Tabelas de extração de questões existem no schema mas não têm API pública

**Status:** Proposto
**Data:** 2026-06-19

## Contexto

O schema contém tabelas para um pipeline de extração: `raw_documents`, `exams`, `questions`, `question_alternatives` e `processing_jobs`. Estão definidas em `app/models/entities.py` e têm migrations aplicadas, mas não há rotas REST para elas em `app/api/routes/`.

`Card.origin_question_id` permite rastrear que um cartão foi gerado a partir de uma questão extraída (`app/models/entities.py:249-252`).

## Decisão

TODO(confirmar): a decisão de não expor essas tabelas via API foi intencional (pipeline interno, acesso apenas por jobs)? Ou há planos de criar rotas futuras? A ausência de rotas pode ser temporária (MVP) ou definitiva.

## Consequências

- **Se intencional:** o pipeline de extração é operado fora da API pública (scripts, jobs, acesso direto ao banco), e os cartões gerados entram no fluxo de curadoria manualmente.
- **Se temporária:** ao criar rotas para `questions` e `raw_documents`, avaliar o impacto no modelo de permissões (qual papel pode acessar?).

## Alternativas consideradas

- **Expor `/questions` e `/documents` como endpoints admin:** implicaria definir um fluxo completo de curadoria guiado por questões, não apenas por cartões soltos.
