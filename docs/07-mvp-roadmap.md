# Roadmap do MVP

## Objetivo

Criar primeiro o núcleo de dados e servidor, sem foco na experiência final do usuário.

## MVP 0 — Fundação

Status: implementado em 12 de junho de 2026.

Entregáveis:

- repositório;
- Docker Compose;
- PostgreSQL;
- Redis;
- FastAPI;
- SQLAlchemy;
- Alembic;
- estrutura inicial de pastas;
- health check da API.

## MVP 1 — Banco de dados

Status: implementado em 12 de junho de 2026.

Entregáveis:

- migrações das tabelas principais;
- modelos ORM;
- seeds de disciplinas iniciais;
- seeds de assuntos iniciais;
- testes básicos de integridade.

Tabelas prioritárias:

- raw_documents;
- exams;
- questions;
- question_alternatives;
- disciplines;
- topics;
- cards;
- card_versions;
- decks;
- deck_cards;
- releases;
- release_items.

Implementacao:

- migration inicial em `migrations/versions/20260612_0001_mvp_0_mvp_1.py`;
- modelos em `app/models`;
- seed idempotente em `app/seeds/taxonomy.py`;
- testes em `tests`.

## MVP 2 — Ingestão de documentos

Entregáveis:

- upload de PDF;
- armazenamento do arquivo;
- extração de texto;
- criação de documento bruto;
- logs de processamento.

## MVP 3 — Questões

Entregáveis:

- segmentação inicial;
- criação de questões;
- extração de alternativas;
- revisão manual básica.

## MVP 4 — Flashcards

Entregáveis:

- geração de card a partir da questão;
- criação da versão 1;
- status de revisão;
- endpoints de listagem e detalhe.

## MVP 5 — Base teórica

Entregáveis:

- cadastro de fontes;
- divisão em chunks;
- busca textual;
- embeddings;
- associação de evidência ao cartão.

## MVP 6 — Curadoria

Entregáveis:

- aprovar cartão;
- reprovar cartão;
- editar cartão criando nova versão;
- registrar motivo da alteração;
- reports de usuários.

## MVP 7 — Releases e sincronização

Entregáveis:

- criar baralho;
- adicionar cartões ao baralho;
- publicar release;
- listar mudanças desde release anterior;
- endpoint de sincronização.

## Critério de sucesso do MVP

O sistema deve conseguir executar este fluxo:

```text
Subir uma prova
→ extrair texto
→ criar questões
→ gerar cards
→ associar fundamentação
→ aprovar cards
→ publicar deck
→ criar release
→ consultar mudanças por endpoint
```
