# Projeto: Plataforma de Flashcards Versionados para Concursos Públicos

## Objetivo

Construir um sistema semelhante ao AnkiHub/AnKing, mas voltado para concursos públicos.

O foco inicial do projeto não é o produto final para o usuário, mas sim o núcleo de dados e servidor:

- ingestão de provas;
- extração de questões;
- classificação por disciplina e assunto;
- transformação em flashcards;
- enriquecimento com base teórica;
- versionamento seguro;
- curadoria administrativa;
- geração de releases;
- sincronização futura.

## Princípio central

O sistema deve tratar cada flashcard como uma entidade versionada, rastreável e auditável.

Um cartão não deve ser apenas um texto de frente e verso. Ele precisa ter:

- origem;
- questão base;
- disciplina;
- assunto;
- evidência/fundamentação;
- versão atual;
- histórico de versões;
- status de revisão;
- rastreabilidade de geração e curadoria.

## Jornada do dado

```text
Documento bruto
→ Questão estruturada
→ Questão classificada
→ Flashcard gerado
→ Flashcard fundamentado
→ Flashcard revisado
→ Flashcard publicado
→ Release
→ Sincronização
```

## Stack recomendada

### MVP

- PostgreSQL
- pgvector
- FastAPI
- Python
- SQLAlchemy
- Alembic
- Redis + RQ
- Prefect
- PyMuPDF
- pdfplumber
- Tesseract OCR
- OpenAI API ou outro LLM
- Supabase Storage ou S3/R2
- Appsmith ou Retool
- Sentry
- Docker
- GitHub Actions

### Evitar no início

- Kubernetes
- microserviços
- app mobile
- sistema de pagamento
- interface final complexa
- modelo local de IA
- sincronização em tempo real

## Estado atual

Os MVPs 0 e 1 estao implementados:

- FastAPI com `GET /health`;
- PostgreSQL e Redis via Docker Compose;
- SQLAlchemy 2 e Alembic;
- migration das 12 tabelas prioritarias;
- seed idempotente de disciplinas e assuntos;
- testes de health check e integridade do banco.

## Execucao com Docker

```bash
docker compose up --build
```

A API fica em `http://localhost:8000` e o health check em
`http://localhost:8000/health`. O container aplica as migrations e executa o
seed de taxonomia antes de iniciar a API.

## Execucao local

Requer Python 3.12 ou superior e PostgreSQL acessivel pela `DATABASE_URL`.

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
python -m app.seeds.taxonomy
uvicorn app.main:app --reload
```

Testes:

```bash
pytest
```

## Documentos adicionais

- `docs/09-future-card-extensions.md`: extensões futuras para campos extras, templates e páginas web dos cartões.
