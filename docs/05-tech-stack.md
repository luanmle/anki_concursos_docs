# Stack Técnica

## Objetivo

Manter um núcleo relacional, auditável e simples para versionamento e
distribuição de flashcards.

## Stack principal

- PostgreSQL 17;
- Python 3.12;
- FastAPI;
- SQLAlchemy 2;
- Alembic;
- pytest;
- Docker e Docker Compose.

## Banco de dados

PostgreSQL é a fonte de verdade para:

- identidade dos cartões;
- histórico de versões;
- taxonomia;
- decks;
- releases;
- itens de release;
- auditoria e curadoria.

## Backend

FastAPI deve expor APIs administrativas e de distribuição usando:

```text
Route → Service → Repository → Model
```

Endpoints administrativos usam Bearer tokens HMAC-SHA256 com expiração.
Usuários e papéis são persistidos em `users`. Senhas usam
PBKDF2-HMAC-SHA256 com salt individual e não dependem de serviço externo.

Papéis iniciais:

```text
admin
curator
reviewer
```

`X-Admin-API-Key` é compatibilidade temporária para desenvolvimento e testes.
`ALLOW_LEGACY_ADMIN_API_KEY` deve ser `false` em produção.

## Operação

- logs estruturados em JSON para stdout;
- `X-Request-ID` propagado em cada resposta;
- `/health` para liveness;
- `/ready` para readiness com consulta ao PostgreSQL;
- CORS explícito por `CORS_ORIGINS`;
- Swagger e OpenAPI desabilitados por padrão em produção;
- migrations executadas por `python -m app.operations.predeploy`;
- advisory lock PostgreSQL serializa execuções concorrentes de migration;
- backup e restore seguem `docs/11-production-operations.md`.

## Exportação CSV

Usar inicialmente a biblioteca padrão `csv` do Python. Não adicionar bibliotecas
de processamento tabular sem necessidade real.

O MVP 4 gera arquivos sob demanda em `app/exporters`, usando `csv`,
`io.StringIO` e `hashlib` da biblioteca padrão. O resultado é retornado
diretamente enquanto o volume esperado for pequeno.

Streaming, jobs e storage externo só devem ser introduzidos quando houver
necessidade comprovada de arquivos grandes, retenção ou distribuição.

## Redis

Redis existe no ambiente atual, mas não é dependência funcional do MVP.
RQ ou outro worker só deve ser adicionado quando métricas demonstrarem que
publicação ou exportação não podem ocorrer de forma síncrona.

## Fora da stack

- ferramentas de PDF e OCR;
- `pgvector`;
- LLMs, embeddings e RAG;
- Prefect ou Airflow;
- Kubernetes;
- microserviços;
- integração direta com arquivos internos do Anki.
