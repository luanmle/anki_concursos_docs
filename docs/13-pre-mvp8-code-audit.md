# Auditoria de Código e Prontidão para o MVP 8

Data da avaliação: 15 de junho de 2026.

## Resumo executivo

O repositório possui um backend funcional e bem organizado para os MVPs 0 a 7.
A separação `Route -> Service -> Repository -> Model`, o versionamento de
cartões, as releases imutáveis e a exportação determinística são pontos fortes.

Os bloqueadores de código identificados nesta auditoria foram implementados em
15 de junho de 2026. O início da UI continua condicionado à validação externa
do staging no Heroku.

Validação executada nesta auditoria:

```text
81 testes aprovados
2 testes PostgreSQL aprovados contra PostgreSQL 17
compileall aprovado
git diff --check aprovado
Ruff e complexidade aprovados
cobertura de aplicação acima de 90%
```

O teste PostgreSQL existente verifica migrations, revisão Alembic e presença de
alguns triggers. Ele não executa os fluxos críticos completos no PostgreSQL nem
testa concorrência.

## Classificação

```text
P0  bloqueia deploy ou pode causar indisponibilidade imediata
P1  deve ser corrigido antes do MVP 8
P2  pode entrar no início do MVP 8, antes da produção
P3  melhoria posterior, orientada por volume e métricas
```

## Bloqueadores P0 — corrigidos

### 1. O container não usa a porta fornecida pelo Heroku

Status: corrigido no `Dockerfile`, `Procfile` e `heroku.yml`.

O `Dockerfile` inicia o Uvicorn na porta fixa `8000`:

```text
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

No Heroku, o processo web deve escutar em `$PORT`. `EXPOSE 8000` não resolve
essa exigência. No estado atual, o container pode iniciar sem receber tráfego do
router.

Correção:

- escolher explicitamente deploy por container ou buildpack;
- para container, iniciar com
  `uvicorn app.main:app --host 0.0.0.0 --port "$PORT"`;
- testar a imagem com uma porta dinâmica;
- adicionar teste de smoke do comando real de produção.

### 2. O pré-deploy não está conectado ao ciclo de release do Heroku

Status: corrigido com release phase. O advisory lock agora compartilha a mesma
conexão usada pelo Alembic.

Existe `python -m app.operations.predeploy`, mas não existe `Procfile`,
`heroku.yml` ou imagem/processo `release` que o execute automaticamente.

Executar migrations no comando de inicialização de cada réplica não é aceitável.
O Heroku oferece release phase para migrations e impede a implantação da nova
release quando o comando falha.

Correção:

- declarar `release: python -m app.operations.predeploy`;
- declarar separadamente o processo `web`;
- manter o advisory lock já implementado;
- confirmar que falhas de seed ou bootstrap retornam código diferente de zero;
- testar upgrade e rollback da aplicação em staging.

### 3. Rate limit público permite crescimento ilimitado de memória

Status: corrigido com limite de chaves, limpeza e confiança explícita em proxy.

O rate limiter:

- mantém um dicionário global em memória;
- nunca remove chaves antigas;
- confia diretamente no primeiro valor de `X-Forwarded-For`;
- é isolado por processo.

Um cliente pode criar muitas chaves de IP e aumentar `_attempts` indefinidamente.
Em múltiplos dynos, os limites também ficam inconsistentes.

Correção:

- não confiar em `X-Forwarded-For` sem uma política de proxy conhecida;
- remover chaves expiradas;
- limitar o número total de chaves;
- preferir rate limit no edge ou armazenamento compartilhado;
- adicionar limites de tamanho para corpo e campos do report.

## Pendências P1 antes da interface

### 4. A API não expõe a taxonomia

Status: corrigido com endpoints autenticados de disciplinas e assuntos.

A interface precisa selecionar `discipline_id` e `topic_id`, mas não existem
endpoints para listar disciplinas e assuntos. Hoje os testes criam taxonomia
diretamente pelo banco.

Adicionar, no mínimo:

```text
GET /disciplines
GET /disciplines/{discipline_id}/topics
```

As respostas devem ser ordenadas, estáveis e adequadas para componentes de
seleção da UI.

### 5. Gestão de usuários está incompleta

Status: corrigido para listagem, papel, ativação, senha e revogação de token.

Existe criação de usuário, login e `/auth/me`, mas faltam operações
administrativas necessárias para operação contínua:

- listar usuários;
- desativar e reativar usuário;
- alterar papel;
- trocar ou redefinir senha;
- invalidar sessões após mudança sensível.

O token atual só deixa de funcionar quando o usuário é desativado. Não existe
versão de credencial, revogação ou refresh token.

### 6. Reports públicos aceitam identidade informada pelo cliente

Status: corrigido. O campo agora é `reporter_reference` e está documentado como
referência não autenticada.

`POST /reports` aceita `user_id` livre e não autenticado. Esse valor não pode ser
tratado como identidade confiável ou usado em auditoria.

Correção:

- renomear para um identificador opcional sem garantia, ou
- derivar o usuário de autenticação quando existir, ou
- remover o campo do contrato público.

### 7. Não existem limites máximos para conteúdo textual

Status: corrigido nos schemas e por limite global do corpo HTTP.

Campos de cartão, explicação, comentário administrativo, descrição de deck e
mensagem de report têm tamanho mínimo, mas em vários casos não têm tamanho
máximo. Isso permite requests e registros excessivamente grandes.

Definir:

- limite global do corpo HTTP;
- limites por campo no Pydantic;
- limites equivalentes no PostgreSQL quando fizer sentido;
- resposta `413` para corpo acima do permitido.

### 8. Testes PostgreSQL são insuficientes para as alegações documentadas

Status: ampliado no repositório e CI. A execução no staging ainda é externa.

O teste opt-in atual valida:

- aplicação das migrations;
- revisão Alembic;
- existência de tabelas e quatro triggers.

Ele não valida no PostgreSQL:

- comportamento de todos os triggers;
- concorrência de criação de versão e release;
- imutabilidade por SQL direto;
- fluxo completo de cartão, publicação, deck, release, CSV e report;
- upgrade a partir de um backup representativo;
- downgrade ou estratégia de rollback.

Antes do MVP 8, criar uma suíte PostgreSQL executada em CI e staging.

### 9. Documentação de validação está contraditória

Status: corrigido e destino operacional alterado para Heroku.

`docs/10-final-system-report.md` afirma que:

- um teste PostgreSQL real foi aprovado; e
- nenhuma suíte PostgreSQL ativa foi executada.

O segundo texto está desatualizado ou incorreto. O relatório também está
orientado à DigitalOcean, enquanto o destino informado agora é Heroku.

Correção:

- consolidar uma única evidência de validação;
- registrar data, commit, ambiente e comandos;
- substituir o runbook de DigitalOcean por Heroku ou declarar os dois destinos;
- não marcar MVP 7 como encerrado antes do staging no provedor escolhido.

### 10. Dependências de produção não são reproduzíveis

Status: corrigido para dependências diretas por `constraints.txt`.

O `pyproject.toml` usa intervalos amplos e não há lock ou constraints file.
Builds realizados em datas diferentes podem instalar versões diferentes.

Correção:

- gerar arquivo de lock/constraints;
- fixar versões testadas;
- automatizar atualização de dependências;
- adicionar verificação de vulnerabilidades;
- fixar de forma mais precisa a imagem base Python.

## Pendências P2

### 11. Pool de conexões não está dimensionado para o Heroku

Status: corrigido por configuração de pool e TLS.

O engine usa os padrões do SQLAlchemy, com apenas `pool_pre_ping=True`.
O total potencial de conexões cresce por processo e por dyno, enquanto planos
Heroku Postgres possuem limites próprios.

Adicionar configuração por ambiente:

- `pool_size`;
- `max_overflow`;
- `pool_timeout`;
- `pool_recycle`;
- telemetria de uso do pool.

Também deve ser exigido SSL em produção. O Heroku Postgres requer TLS e recomenda
configuração explícita de `sslmode`.

### 12. Listagem de decks não é paginada

Status: corrigido com resposta resumida e paginada.

`GET /decks` carrega todos os decks e todos os cartões ativos de cada deck. Isso
gera payload e consumo de memória crescentes para uma tela que normalmente
precisa apenas de resumo.

Separar:

```text
GET /decks                  lista paginada e resumida
GET /decks/{deck_id}        detalhe com cartões paginados
```

### 13. Sync, release e CSV percorrem todo o histórico em memória

Os fluxos atuais são corretos para volume pequeno, mas reconstruções repetidas
custam proporcionalmente ao histórico completo da release.

Antes de otimizar, medir com massa representativa. Se necessário:

- consultar somente colunas necessárias;
- paginar ou transmitir sync;
- usar streaming para CSV;
- persistir snapshots ou checkpoints derivados, sem substituir releases como
  fonte de verdade.

### 14. Não existe pipeline de qualidade automatizado no repositório

Status: corrigido em `.github/workflows/ci.yml`.

Não foram encontrados workflows de CI para:

- testes SQLite;
- testes PostgreSQL;
- lint;
- formatação;
- type checking;
- cobertura;
- auditoria de dependências;
- build e smoke test do container.

Essas verificações devem ser obrigatórias antes de integrar o frontend.

### 15. Tabelas e serviços sem uso aumentam custo cognitivo

Status: legado formalmente congelado. Remoção foi adiada por exigir decisão de
compatibilidade e backup.

As quatro tabelas legadas de documentos e questões e o Redis não fazem parte do
fluxo ativo. `processing_jobs` também não possui worker.

Decidir antes do MVP 8:

- remover por migration, se não houver compatibilidade a preservar; ou
- manter formalmente como legado congelado, sem expor na UI.

## Complexidade ciclomática

### Resultado

Uma medição aproximada pela AST encontrou:

```text
172 funções analisadas
complexidade média estimada: 2,35
complexidade máxima estimada: 19
funções acima de 10: 3
```

Pontos principais:

```text
19  DeckService.publish_release
14  ReportService.review_report
12  DeckService.add_card
10  DeckService.export_release_csv
 9  DeckService.sync
```

### Parecer

**Sim, vale utilizar complexidade ciclomática**, mas como alerta seletivo.
Não há evidência para refatorar o projeto inteiro. A média é baixa e a
complexidade está concentrada em regras críticas de domínio.

Recomendação:

- adotar `ruff` com `C901` ou `radon` no ambiente de desenvolvimento/CI;
- usar limite inicial entre 10 e 12;
- permitir exceção documentada para orquestrações claras;
- exigir testes adicionais quando uma função crítica ultrapassar o limite;
- priorizar a decomposição de `publish_release` e `review_report`;
- acompanhar também tamanho, acoplamento, número de queries e cobertura de
  branches, pois complexidade ciclomática isolada não mede risco de banco.

Refatorações sugeridas:

- extrair reconstrução do estado anterior da release;
- extrair cálculo de deltas do deck como função pura;
- extrair validação e criação da versão resultante de report;
- testar essas funções com tabelas de casos.

## Requisitos específicos para Heroku

Checklist mínimo:

```text
[ ] processo web usa $PORT
[ ] release phase executa predeploy
[ ] Heroku Postgres anexado via DATABASE_URL
[ ] sslmode configurado explicitamente
[ ] pool dimensionado para o plano do banco
[ ] APP_ENV=production
[ ] ALLOW_LEGACY_ADMIN_API_KEY=false
[ ] AUTH_SECRET_KEY forte
[ ] CORS_ORIGINS restrito ao domínio da UI
[ ] DOCS_ENABLED=false
[ ] bootstrap removido após criação do primeiro admin
[ ] staging executa testes PostgreSQL e restore
[ ] PGBackups e retenção configurados
[ ] logs e alertas validados
```

O banco deve ser um add-on Heroku Postgres. A aplicação deve acessar somente
`DATABASE_URL`; a UI nunca deve acessar o banco diretamente.

## Ordem recomendada

1. Corrigir `$PORT` e definir a estratégia de deploy Heroku.
2. Configurar release phase e staging com Heroku Postgres.
3. Corrigir rate limit, confiança em proxy e limites de payload.
4. Criar endpoints de taxonomia e completar gestão de usuários.
5. Executar suíte PostgreSQL ampliada, concorrência, backup e restore.
6. Fixar dependências e criar CI obrigatório.
7. Paginar decks e definir contratos estáveis para a UI.
8. Refatorar as funções de maior complexidade com testes de branch.
9. Atualizar toda a documentação de produção para Heroku.
10. Somente então iniciar a interface do MVP 8.

## Critério de liberação

O MVP 8 pode começar quando:

```text
deploy de staging no Heroku aprovado
release phase e migrations aprovadas
PostgreSQL real aprovado em CI/staging
restore testado
rate limit e payload protegidos
taxonomia disponível por API
contratos da UI definidos e versionados
CI obrigatório ativo
```

## Fontes de operação do Heroku

- Container Runtime e requisito de `$PORT`:
  https://devcenter.heroku.com/articles/container-registry-and-runtime
- Release phase para migrations:
  https://devcenter.heroku.com/articles/release-phase
- Conexão e TLS no Heroku Postgres:
  https://devcenter.heroku.com/articles/connecting-heroku-postgres
- Limites e dimensionamento de conexões:
  https://devcenter.heroku.com/articles/python-concurrency-and-database-connections
