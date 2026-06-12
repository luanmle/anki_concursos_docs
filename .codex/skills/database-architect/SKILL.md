---
name: database-architect
description: Orienta modelagem PostgreSQL, migrations, constraints, índices e relações para o sistema de flashcards versionados.
---
# database-architect

## Propósito

Use esta skill para criar, revisar ou alterar modelos de banco de dados, migrações, constraints, índices, relacionamentos e seeds.

O projeto é uma plataforma de dados versionados para flashcards de concursos públicos.

## Quando usar

Use esta skill para tarefas como:

- criar migrations;
- criar models SQLAlchemy;
- revisar schema;
- adicionar constraints;
- criar índices;
- adicionar tabelas novas;
- revisar relações entre entidades;
- criar seeds de disciplinas e assuntos.

## Princípios do banco

1. O sistema é relacional e auditável.
2. Cartões têm identidade estável.
4. Versões são imutáveis depois de publicadas.
5. Toda fundamentação deve ser rastreável.
6. Releases representam mudanças incrementais.
7. Exportações devem ser derivadas de releases.
8. Taxonomia deve ser controlada por tabelas oficiais.
9. Não usar texto livre para disciplina e assunto quando existir tabela oficial.
10. Evitar JSON para dados que precisam de integridade relacional.

## Tabelas principais esperadas

```text
disciplines
topics
cards
card_versions
knowledge_sources
knowledge_chunks
card_evidence
decks
deck_cards
card_reports
review_tasks
releases
release_items
quality_checks
processing_jobs
```

`raw_documents`, `exams`, `questions` e `question_alternatives` são legado do
schema inicial e não devem receber novas dependências.

`prompt_templates`, embeddings e estruturas específicas de IA ficam fora do
MVP do sistema principal. Um futuro produtor externo deve integrar-se por API.

## Extensões futuras esperadas

```text
card_fields
card_templates
card_template_fields
card_public_pages
```

## Regras para chaves

- Preferir UUID para entidades principais.
- Usar `public_id` único e imutável para identificação pelo usuário.
- Usar foreign keys explícitas.
- Usar timestamps em tabelas relevantes.
- Usar constraints para impedir inconsistência básica.
- Criar índices para foreign keys frequentes.
- Criar índices para sync, release e busca.

## Regras para versionamento

- `cards.current_version_id` deve apontar para a versão atual.
- `card_versions.card_id` deve apontar para `cards.id`.
- `version_number` deve ser único por `card_id`.
- Não permitir duas versões com mesmo `card_id` e mesmo `version_number`.

Constraint sugerida:

```text
UNIQUE(card_id, version_number)
```

## Regras para evidência

- `card_evidence.card_version_id` aponta para uma versão específica.
- `card_evidence.knowledge_chunk_id` aponta para o trecho usado.
- Cartão publicado deve ter ao menos uma evidência válida.

## Regras para sincronização

- `release_items` deve conter:
  - `release_id`;
  - `card_id`;
  - `card_version_id`;
  - `action`.

Ações esperadas:

```text
added
updated
removed
deprecated
```

## Índices recomendados

Criar índices para:

```text
cards.current_version_id
cards.public_id
cards.discipline_id
cards.topic_id
card_versions.card_id
card_versions.content_hash
deck_cards.deck_id
deck_cards.card_id
releases.deck_id
release_items.release_id
release_items.card_id
knowledge_chunks.source_id
card_evidence.card_version_id
card_reports.card_id
processing_jobs.entity_type + entity_id
```

## Regras para exportação

- Exportar a versão registrada na release.
- Incluir `public_id`, `card_id` e `card_version_id`.
- Gerar saída determinística.
- Não persistir o CSV como fonte de verdade.

## Checklist antes de finalizar

- As relações têm foreign keys?
- Os status críticos usam enum ou domínio controlado?
- Existe unique constraint onde necessário?
- A modelagem preserva histórico?
- A modelagem evita duplicidade de taxonomia?
- O schema respeita `/docs/02-data-model.md`?
- O schema respeita `/docs/09-future-card-extensions.md`?
