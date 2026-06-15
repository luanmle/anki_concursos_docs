# Plataforma de Flashcards Versionados para Concursos Públicos

## Objetivo

Construir um catálogo versionado de flashcards, inspirado no modelo de
distribuição do AnkiHub, com foco no banco de dados e na preservação da
identidade dos cartões.

O sistema principal é responsável por:

- armazenar e classificar flashcards;
- preservar o histórico de versões;
- revisar e publicar conteúdo;
- organizar cartões em decks;
- gerar releases imutáveis;
- exportar releases em CSV para importação no Anki;
- expor mudanças incrementais para integrações futuras.

Não fazem parte do escopo:

- upload ou processamento de PDFs;
- extração e segmentação de questões;
- OCR;
- geração de conteúdo por IA;
- embeddings ou RAG;
- implementação de um cliente ou add-on do Anki neste momento.

## Princípio central

```text
card_id = identidade estável
public_id = identificador estável visível ao usuário
card_version_id = conteúdo imutável de uma versão
release = conjunto publicado de mudanças
CSV = projeção exportável de uma release
```

O CSV nunca é a fonte de verdade. O banco mantém identidade, histórico,
auditoria e estado de publicação.

Cada cartão possui um `public_id` no formato:

```text
AC-550E8400E29B41D4A716446655440000
```

Esse valor é exportado para o Anki e pode ser copiado para buscar o cartão na
plataforma. Ele não muda quando uma nova versão é publicada.

## Fluxo principal

```text
Cadastrar ou importar flashcard
→ revisar
→ publicar versão
→ associar ao deck
→ criar release
→ gerar CSV
→ importar no Anki
```

## Stack

- PostgreSQL 17
- FastAPI
- Python 3.12
- SQLAlchemy 2
- Alembic
- pytest
- Docker e Docker Compose

Redis permanece disponível no ambiente atual, mas não é requisito para o
fluxo principal enquanto exportações forem processadas de forma síncrona.

## Estado atual

- FastAPI com `GET /health`;
- PostgreSQL e Redis via Docker Compose;
- SQLAlchemy e Alembic;
- modelos iniciais de cartões, versões, decks e releases;
- `processing_jobs` e proteções de integridade;
- seed de disciplinas e assuntos;
- testes de integridade e versionamento.
- MVP 2 com criação, listagem, consulta e novas versões;
- paginação e filtros por taxonomia, status e `public_id`;
- endpoints administrativos protegidos por usuários, papéis e Bearer tokens;
- busca pública por `public_id` limitada a cartões publicados.
- MVP 3 com aprovação, publicação, decks e releases incrementais;
- ações de release `added`, `updated`, `removed` e `deprecated`;
- releases e itens de release imutáveis.
- MVP 4 com exportação CSV determinística do snapshot de uma release;
- UTF-8, delimitadores controlados, tags estáveis e hash SHA-256 do arquivo.
- MVP 5 com listagem paginada de releases e sincronização incremental;
- deltas sequenciais com versões anterior e nova por `card_id`.
- MVP 6 com reports públicos e revisão administrativa auditável;
- correções aprovadas criam nova versão em revisão sem alterar a publicada.
- MVP 7 com usuários, papéis, Bearer tokens e senhas derivadas por PBKDF2;
- papéis `admin`, `curator` e `reviewer`;
- rate limit para reports, logs JSON e `X-Request-ID`;
- readiness check do PostgreSQL em `GET /ready`;
- migrations serializadas, seed e bootstrap administrativo no pré-deploy;
- documentação interativa desabilitável em produção.
- endpoints autenticados de leitura de disciplinas e assuntos;
- administração paginada de usuários, papéis, ativação e senha;
- revogação de tokens por versão de credencial;
- limite global de payload e rate limit com memória limitada;
- configuração de pool, TLS e release phase para Heroku;
- CI com PostgreSQL 17, lint, complexidade e cobertura.

O schema inicial também contém tabelas de documentos e questões. Elas não
fazem parte do escopo ativo e devem ser tratadas como candidatas a remoção em
uma migration futura, após decisão explícita sobre compatibilidade.

## Execução

```bash
docker compose up --build
```

A API fica em `http://localhost:8000` e o health check em
`http://localhost:8000/health`. O readiness check com acesso ao banco fica em
`http://localhost:8000/ready`.

Testes:

```bash
pytest
```

## API de cartões

Obtenha um token:

```http
POST /auth/token
Content-Type: application/json

{"email":"admin@example.com","password":"development-password"}
```

Endpoints administrativos exigem:

```http
Authorization: Bearer <access_token>
```

`X-Admin-API-Key` permanece disponível somente quando
`ALLOW_LEGACY_ADMIN_API_KEY=true`, para compatibilidade local. Produção rejeita
essa configuração.

```text
POST /cards
GET /cards
GET /cards/{card_id}
POST /cards/{card_id}/versions
POST /cards/{card_id}/versions/{version_id}/approve
POST /cards/{card_id}/versions/{version_id}/publish
POST /decks
GET /decks
GET /decks/{deck_id}
POST /decks/{deck_id}/cards
POST /decks/{deck_id}/cards/{card_id}/remove
POST /decks/{deck_id}/publish-release
GET /decks/{deck_id}/releases
GET /decks/{deck_id}/sync?since_release=0
GET /decks/{deck_id}/releases/{release_id}/export.csv
POST /reports
GET /admin/reports
GET /admin/reports/{report_id}
POST /admin/reports/{report_id}/review
POST /auth/token
GET /auth/me
POST /admin/users
GET /admin/users
PATCH /admin/users/{user_id}
POST /admin/users/{user_id}/reset-password
GET /disciplines
GET /disciplines/{discipline_id}/topics
```

Busca pública de cartão publicado:

```text
GET /cards/public/{public_id}
```

A exportação aceita `delimiter=comma|semicolon|tab` e
`include_tags=true|false`. O hash do arquivo é retornado em
`X-Content-SHA256`.

Na sincronização, `since_release=0` representa uma instalação sem estado local.
Cada mudança informa a release, a ação, `card_id`, `public_id`,
`old_card_version_id` e `new_card_version_id`.

Reports podem ser enviados sem a chave administrativa, mas somente para uma
versão publicada. Listagem e decisões de curadoria exigem
um usuário com papel `reviewer` ou `admin`.

Operação no Heroku, PostgreSQL real, backup e restore estão descritos em
`docs/11-production-operations.md`.

## Heroku

O deploy por container usa `heroku.yml`:

```text
release -> python -m app.operations.predeploy
web     -> uvicorn em $PORT
```

Variáveis adicionais obrigatórias em produção:

```text
DATABASE_SSLMODE=require
TRUST_PROXY_HEADERS=true
ALLOW_LEGACY_ADMIN_API_KEY=false
```

As versões testadas das dependências estão em `constraints.txt`.
