# Stack Tecnica

## Objetivo

Manter um nucleo relacional, auditavel e simples para versionamento e
distribuicao de flashcards.

## Stack Principal

- PostgreSQL 17
- Python 3.12
- FastAPI
- SQLAlchemy 2
- Alembic
- pytest
- Docker e Docker Compose
- Heroku Container Runtime e Heroku Postgres
- GitHub Actions
- Ruff e pytest-cov
- Honeybadger para observabilidade do backend

## Banco De Dados

PostgreSQL e a fonte de verdade para:

- identidade dos cartoes;
- historico de versoes;
- taxonomia;
- decks;
- releases;
- itens de release;
- auditoria e curadoria.

## Backend

FastAPI expoe APIs administrativas e de distribuicao usando:

```text
Route -> Service -> Repository -> Model
```

Endpoints administrativos usam Bearer tokens. Usuarios e papeis sao
persistidos em `users`. Senhas usam PBKDF2-HMAC-SHA256 com salt individual.

Papeis iniciais:

```text
admin
curator
reviewer
student
```

`X-Admin-API-Key` e compatibilidade temporaria para desenvolvimento e testes.
`ALLOW_LEGACY_ADMIN_API_KEY` deve ser `false` em producao.

## Add-on E Frontend

O add-on do Anki e um cliente separado que:

- envia baralhos completos;
- sincroniza decks assinados;
- preserva templates e campos nativos;
- nao acessa o banco diretamente;
- nao substitui o backend como fonte de verdade.

O frontend administrativo vive em `admin/` e e publicado em app Heroku
separado.

## Operacao

- logs estruturados em JSON para stdout;
- `X-Request-ID` propagado em cada resposta;
- `/health` para liveness;
- `/ready` para readiness com consulta ao PostgreSQL;
- CORS explicito por `CORS_ORIGINS`;
- Swagger e OpenAPI desabilitados por padrao em producao;
- migrations executadas por `python -m app.operations.predeploy`;
- advisory lock PostgreSQL serializa execucoes concorrentes de migration;
- o Alembic reutiliza a mesma conexao que mantem o advisory lock;
- release phase do Heroku executa migrations, seed e bootstrap;
- processo web escuta exclusivamente na porta `$PORT`;
- pool SQLAlchemy e configuravel por ambiente;
- producao exige TLS PostgreSQL por `DATABASE_SSLMODE`;
- requests possuem limite global de corpo;
- rate limit em memoria possui limite de chaves e confianca explicita no proxy;
- backup e restore seguem `docs/11-production-operations.md`.

## Qualidade Automatizada

O CI executa:

```text
Ruff com C901 e limite de complexidade 12
compileall
pytest com cobertura minima de 80%
PostgreSQL 17 para migrations, constraints e triggers
Alembic offline SQL
```

As versoes diretas validadas sao fixadas em `constraints.txt`.

## Exportacao CSV

Usar inicialmente a biblioteca padrao `csv` do Python. Nao adicionar
bibliotecas de processamento tabular sem necessidade real.

O CSV continua sendo gerado por release. Streaming, jobs e storage externo
sao introduzidos apenas quando houver necessidade comprovada.

## Redis

Redis existe no ambiente atual, mas nao e dependencia funcional do MVP.
RQ ou outro worker so deve ser adicionado quando metricas demonstrarem que
publicacao ou exportacao nao podem ocorrer de forma sincronica.

## Fora Da Stack

- ferramentas de PDF e OCR;
- `pgvector`;
- LLMs, embeddings e RAG;
- Prefect ou Airflow;
- Kubernetes;
- microservicos;
- integracao direta com arquivos internos do Anki.
