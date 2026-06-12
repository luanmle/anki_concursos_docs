# Stack Técnica Recomendada

## Objetivo da stack

Criar um sistema confiável para:

- armazenar dados estruturados;
- processar documentos;
- gerar flashcards;
- versionar conteúdo;
- executar pipelines;
- publicar releases;
- expor APIs de sincronização.

## Stack implementada nos MVPs 0 e 1

- Python 3.12;
- FastAPI;
- SQLAlchemy 2;
- Alembic;
- PostgreSQL 17;
- Redis 7;
- pytest;
- Docker e Docker Compose.

`pgvector`, RQ, Prefect, ferramentas de extracao, IA, storage e
observabilidade permanecem planejados para os MVPs que efetivamente usam essas
capacidades.

## Stack MVP recomendada

### Banco de dados

- PostgreSQL
- pgvector

Uso:

- entidades relacionais;
- versionamento;
- taxonomia;
- busca textual;
- embeddings;
- evidências.

### Backend

- Python
- FastAPI

Uso:

- APIs REST;
- upload de documentos;
- endpoints administrativos;
- endpoints de sincronização;
- integração com workers e pipelines.

### ORM e migrações

- SQLAlchemy
- Alembic

Uso:

- modelagem do banco;
- migrações versionadas;
- controle de schema.

### Storage

MVP:

- Supabase Storage

Futuro:

- S3;
- Cloudflare R2;
- MinIO.

Uso:

- armazenar PDFs originais;
- guardar exportações;
- guardar pacotes de release.

### Filas

- Redis
- RQ

Uso:

- processar documentos;
- gerar embeddings;
- chamar IA;
- criar releases;
- reprocessar cartões.

### Orquestração

- Prefect

Uso:

- controlar pipeline;
- reexecutar etapas;
- monitorar falhas;
- criar fluxos de processamento.

### Extração de PDF

- PyMuPDF
- pdfplumber
- Tesseract OCR

Uso:

- extrair texto;
- ler tabelas simples;
- processar PDFs escaneados.

### IA

- OpenAI API ou outro LLM equivalente

Uso:

- classificar questões;
- gerar flashcards;
- resumir fundamentação;
- validar consistência;
- detectar duplicatas semanticamente.

### Painel administrativo

- Appsmith;
- Retool;
- ou painel próprio simples.

Uso:

- revisar questões;
- revisar flashcards;
- aprovar versões;
- ver reports;
- publicar releases.

### Observabilidade

- Sentry
- logs no banco

Uso:

- capturar erros;
- rastrear jobs;
- entender falhas do pipeline.

### DevOps

- Docker
- Docker Compose
- GitHub
- GitHub Actions

Uso:

- ambiente local;
- deploy;
- CI/CD;
- testes automatizados.

## Stack que deve ser evitada no começo

- Kubernetes;
- Airflow;
- microserviços;
- app mobile;
- interface complexa para usuário final;
- modelo local de IA;
- sistema de pagamento;
- real-time complexo.
