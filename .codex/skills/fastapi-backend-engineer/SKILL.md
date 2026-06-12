---
name: fastapi-backend-engineer
description: Orienta arquitetura FastAPI com routes, services, repositories, schemas, workers, pipelines e testes.
---
# fastapi-backend-engineer

## Propósito

Use esta skill para implementar ou revisar o backend FastAPI do projeto.

O objetivo é manter uma arquitetura simples, testável e organizada.

## Quando usar

Use esta skill para tarefas como:

- criar endpoints;
- criar routers;
- criar schemas;
- criar services;
- criar repositories;
- integrar banco;
- integrar filas;
- implementar autenticação;
- estruturar projeto;
- adicionar testes de API.

## Estrutura recomendada

```text
app/
  main.py
  core/
    config.py
    database.py
    security.py
  models/
  schemas/
  repositories/
  services/
  api/
    routes/
  workers/
  pipelines/
  integrations/
  tests/
```

## Regras obrigatórias

1. Não colocar regra de negócio complexa diretamente em routes.
2. Routes devem chamar services.
3. Services devem conter regras de negócio.
4. Repositories devem concentrar acesso ao banco quando aplicável.
5. Schemas Pydantic devem validar entrada e saída.
6. Usar transações em operações críticas.
7. Operações longas devem ir para fila/job.
8. Endpoints administrativos devem exigir autenticação/autorização.
9. Erros devem ser claros e consistentes.
10. Não vazar stack trace em resposta pública.

## Padrão recomendado

```text
Route → Service → Repository → Model
```

Exemplo:

```text
POST /cards/{card_id}/versions
→ CardVersionService.create_new_version()
→ CardRepository.get_card()
→ CardVersionRepository.create()
```

## Endpoints iniciais sugeridos

```text
GET /health

POST /documents/upload
GET /documents/{document_id}
POST /documents/{document_id}/process

GET /questions
GET /questions/{question_id}

POST /cards/from-question/{question_id}
GET /cards
GET /cards/{card_id}
POST /cards/{card_id}/versions
POST /cards/{card_id}/approve

POST /decks
GET /decks
POST /decks/{deck_id}/publish-release
GET /decks/{deck_id}/sync

POST /reports
GET /admin/reports
POST /admin/reports/{report_id}/review
```

## Regras de resposta

- Retornar IDs explícitos.
- Retornar status claro.
- Evitar payloads gigantes em listagens.
- Usar paginação.
- Usar filtros por status, disciplina e assunto.

## Checklist antes de finalizar

- A route está fina?
- A regra está em service?
- Existe schema de entrada e saída?
- Existe tratamento de erro?
- Operações críticas usam transação?
- Tarefa longa foi enviada para worker?
- Existem testes de endpoint?
