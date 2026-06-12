# Relatório Final do Sistema

Data da avaliação: 12 de junho de 2026.

## Resumo executivo

O sistema implementa um backend para armazenamento, versionamento, publicação,
distribuição e curadoria de flashcards. O banco de dados é a fonte de verdade;
CSV e sincronização são projeções do histórico publicado.

Os MVPs 0 a 6 estão implementados e o código do MVP 7 foi concluído:

- fundação FastAPI, PostgreSQL, SQLAlchemy e Alembic;
- catálogo de cartões e taxonomia;
- versionamento imutável;
- decks e releases incrementais;
- exportação CSV determinística;
- sincronização incremental;
- reports e curadoria auditável.
- autenticação individual, papéis e tokens expirados;
- hardening HTTP, logs estruturados e readiness do PostgreSQL;
- pré-deploy controlado e suíte PostgreSQL opt-in.

O sistema está em nível de **MVP backend funcional**, mas ainda não em nível de
produção pública. O núcleo de domínio está consistente; segurança, operação,
testes PostgreSQL reais e distribuição de conteúdo para um add-on ainda
precisam evoluir.

## Escopo atual

O sistema é responsável por:

- armazenar flashcards;
- manter identidade estável por `card_id` e `public_id`;
- preservar versões anteriores;
- aprovar e publicar versões;
- organizar cartões em decks;
- publicar releases imutáveis;
- exportar snapshots em CSV;
- informar deltas entre releases;
- registrar reports e decisões de curadoria.

Permanecem fora do escopo:

- PDF, OCR e extração de questões;
- geração por inteligência artificial;
- embeddings e RAG;
- progresso e agendamento de revisões;
- acesso direto ao banco interno do Anki;
- aplicativo móvel ou add-on do Anki.

## Arquitetura

O backend segue:

```text
Route -> Service -> Repository -> Model
```

Componentes:

```text
app/api/routes     contratos HTTP
app/schemas        validação Pydantic
app/services       regras de negócio
app/repositories   consultas SQLAlchemy
app/models         entidades e proteções ORM
app/exporters      geração determinística de CSV
migrations         evolução do schema PostgreSQL
tests              testes de API e integridade
```

Stack:

- Python 3.12;
- FastAPI;
- SQLAlchemy 2;
- PostgreSQL 17;
- Alembic;
- pytest;
- Docker Compose;
- Redis disponível, mas não utilizado pelo fluxo principal.

## Modelo de domínio

Entidades ativas:

- `users`;
- `disciplines` e `topics`;
- `cards` e `card_versions`;
- `decks` e `deck_cards`;
- `releases` e `release_items`;
- `card_reports` e `review_tasks`;
- `processing_jobs`.

Entidades legadas fora do escopo:

- `raw_documents`;
- `exams`;
- `questions`;
- `question_alternatives`.

Princípios preservados:

```text
card_id            identidade interna estável
public_id          identidade visível ao usuário
card_version_id    conteúdo específico e imutável
release_number     marco incremental de distribuição
```

Há constraints, eventos ORM e triggers PostgreSQL protegendo:

- pertencimento de uma versão ao cartão correto;
- unicidade do número da versão;
- imutabilidade de versão publicada;
- imutabilidade de releases;
- integridade das versões em decks e releases;
- integridade e imutabilidade da auditoria de curadoria.

## Funcionalidades entregues

### Cartões

- criação transacional do cartão com versão 1;
- geração automática de `public_id`;
- paginação e filtros;
- consulta administrativa por UUID;
- consulta pública por `public_id`;
- criação de nova versão sem sobrescrever a anterior;
- bloqueio de conteúdo idêntico.

### Publicação e decks

- aprovação e publicação separadas;
- deck aceita apenas versão atual publicada;
- atualização de versão no deck é explícita;
- remoção e depreciação são preservadas;
- release sem alterações é rejeitada;
- releases e itens são imutáveis.

### Exportação CSV

- snapshot reconstruído a partir dos deltas;
- UTF-8 e escaping padrão CSV;
- delimitador configurável;
- ordenação por `public_id`;
- IDs estáveis no arquivo;
- hash SHA-256 e contagem de linhas;
- removidos e depreciados não aparecem no snapshot final.

### Sincronização

- listagem paginada de releases;
- sincronização desde `since_release`;
- instalação inicial com `since_release=0`;
- ações `added`, `updated`, `removed` e `deprecated`;
- versões anterior e nova;
- deltas retornados em ordem de release.

### Curadoria

- report público sobre versão publicada;
- tarefa administrativa criada automaticamente;
- filtros e paginação;
- rejeição e duplicidade sem alteração de conteúdo;
- conversão em nova versão `needs_review`;
- preservação da versão publicada atual;
- decisão, responsável, comentário e data auditáveis;
- revisão de evidência exigida para atualização legislativa;
- reports e tarefas concluídas protegidos contra alteração ou exclusão.

## API implementada

Principais endpoints:

```text
GET  /health
GET  /ready

POST /auth/token
GET  /auth/me
POST /admin/users

POST /cards
GET  /cards
GET  /cards/{card_id}
GET  /cards/public/{public_id}
POST /cards/{card_id}/versions
POST /cards/{card_id}/versions/{version_id}/approve
POST /cards/{card_id}/versions/{version_id}/publish

POST /decks
GET  /decks
GET  /decks/{deck_id}
POST /decks/{deck_id}/cards
POST /decks/{deck_id}/cards/{card_id}/remove
POST /decks/{deck_id}/publish-release
GET  /decks/{deck_id}/releases
GET  /decks/{deck_id}/sync
GET  /decks/{deck_id}/releases/{release_id}/export.csv

POST /reports
GET  /admin/reports
GET  /admin/reports/{report_id}
POST /admin/reports/{report_id}/review
```

Operações administrativas usam Bearer token e papéis. A API key antiga é
permitida apenas quando explicitamente habilitada fora de produção.

## Estado de qualidade

Validações executadas:

- 66 testes automatizados locais aprovados;
- 1 teste de integração aprovado contra PostgreSQL 17 ativo;
- migrations `0001` a `0006`, triggers, seed e bootstrap administrativo
  validados no PostgreSQL;
- build da imagem, backup, restore e smoke test do banco restaurado aprovados;
- compilação de `app`, `tests` e `migrations` sem erros;
- `docker compose config` válido;
- cadeia Alembic válida de `0001` até `0005`;
- `git diff --check` sem erros.

Cobertura comportamental relevante:

- integridade de chaves e ownership;
- imutabilidade;
- versionamento;
- publicação;
- releases;
- CSV e UTF-8;
- sincronização;
- reports e decisões administrativas.

Limitação de validação:

- os testes funcionais usam SQLite em memória;
- as migrations foram verificadas por geração SQL offline;
- não foi executada uma suíte de integração contra PostgreSQL ativo.

## Riscos e limitações

### Alta prioridade

1. A suíte PostgreSQL foi validada localmente, mas ainda precisa ser executada
   no ambiente de homologação do provedor.
2. O rate limit de `POST /reports` é local por processo; múltiplas réplicas
   exigem limitação adicional no proxy ou armazenamento compartilhado.
3. Backup e restore foram validados localmente; ainda falta repetir o
   procedimento no PostgreSQL gerenciado de homologação.
4. O endpoint de sync retorna IDs e ações, mas não entrega o conteúdo completo
   das novas versões para um cliente Anki.

### Média prioridade

1. O schema ainda contém quatro tabelas legadas de documentos e questões.
2. `processing_jobs` existe, mas não há worker ou fluxo assíncrono ativo.
3. Há logs estruturados, mas métricas, tracing e integração de erros dependem
   da infraestrutura de hospedagem.
4. A política de backup e restore foi definida, mas retenção e point-in-time
   recovery dependem do plano do provedor.
5. Quality checks são regras de serviço e testes, não registros persistidos.
6. Evidência jurídica é apenas atestada por `evidence_reviewed`; fontes e
   citações estruturadas ainda não existem.

### Baixa prioridade

1. O CSV é genérico; templates e mapeamento avançado de tipos de nota do Anki
   ainda não foram implementados.
2. Não há interface administrativa; ela permanece no MVP 8.
3. O Redis está provisionado sem uso funcional.

## Complexidade

Complexidade atual: **média-alta**.

O CRUD isolado é simples, mas o sistema possui regras de domínio com maior
complexidade:

- identidade separada do conteúdo;
- histórico imutável;
- reconstrução de snapshots;
- reprodução sequencial de deltas;
- concorrência na criação de versões e releases;
- auditoria de curadoria;
- constraints duplicadas entre ORM e PostgreSQL.

O próximo aumento relevante de complexidade ocorrerá com autenticação
multiusuário, evidência estruturada e um add-on do Anki.

## Próximos passos recomendados

Ordem recomendada:

1. Implantar homologação e repetir a suíte PostgreSQL e o restore no provedor.
2. Executar o MVP 8 com uma interface administrativa simples para cadastrar,
   modificar por nova versão, publicar, organizar em decks e baixar CSV.
3. Proteger o envio público de reports contra abuso.
4. Definir endpoint de distribuição do conteúdo de `card_version_id`.
5. Criar contrato e protótipo do add-on do Anki.
6. Persistir quality checks e política de publicação por deck.
7. Modelar fontes e evidências quando houver necessidade jurídica concreta.
8. Remover as tabelas legadas em migration própria, após backup e decisão de
   compatibilidade.

A interface deve consumir a API e não manipular diretamente o banco. Seu
critério funcional principal será completar o fluxo até o download do CSV sem
dependência de Swagger, SQL ou terminal.

## Conclusão

O sistema possui um núcleo de dados coerente e suficientemente completo para
operar um catálogo versionado de flashcards. A identidade estável, o histórico,
as releases, o CSV, o sync e a curadoria foram implementados sem dependência de
PDF ou inteligência artificial.

O próximo passo ideal não é ampliar o domínio. É transformar o MVP funcional
em uma base operacional confiável: PostgreSQL real nos testes, autenticação,
proteção contra abuso e contrato de distribuição para o cliente Anki.
