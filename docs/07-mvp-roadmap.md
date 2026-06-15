# Roadmap do MVP

## Objetivo

Entregar primeiro o banco de dados e os serviços necessários para armazenar,
versionar e exportar flashcards para o Anki.

## MVP 0 — Fundação

Status: implementado em 12 de junho de 2026.

- FastAPI;
- PostgreSQL;
- SQLAlchemy;
- Alembic;
- Docker Compose;
- health check.

## MVP 1 — Schema inicial

Status: implementado em 12 de junho de 2026.

- cartões e versões;
- taxonomia;
- decks;
- releases;
- constraints iniciais;
- seeds e testes.

O schema também contém documentos e questões, que estão fora do escopo ativo.

## MVP 1.5 — Hardening

Status: implementado em 12 de junho de 2026.

- `processing_jobs`;
- proteção da relação entre `card_id` e `card_version_id`;
- imutabilidade de versões publicadas;
- testes negativos de integridade.

## MVP 2 — Serviço de cartões

Status: implementado em 12 de junho de 2026.

- schemas de entrada e saída;
- repositories e services;
- criar cartão com versão 1 em uma transação;
- gerar e retornar `public_id`;
- listar e consultar cartões;
- buscar cartão por `public_id`;
- criar nova versão sem alterar a anterior;
- filtros por disciplina, assunto e status;
- paginação;
- testes unitários e de API.

Implementação:

- `POST /cards`;
- `GET /cards`;
- `GET /cards/{card_id}`;
- `GET /cards/public/{public_id}`;
- `POST /cards/{card_id}/versions`;
- autenticação administrativa por API key;
- hash determinístico e bloqueio de versões idênticas;
- lock do cartão e unique constraint para concorrência de versões.

## MVP 3 — Publicação e decks

Status: implementado em 12 de junho de 2026.

- criar e listar decks;
- adicionar ou remover cartões;
- aprovar e publicar versões;
- impedir inclusão de versão não publicada;
- publicar release imutável;
- calcular `added`, `updated`, `removed` e `deprecated`.

Implementação:

- aprovação e publicação por `card_version_id`;
- inclusão e atualização explícita da versão no deck;
- remoção ou depreciação por deck;
- release incremental e imutável;
- bloqueio de release sem alterações;
- autenticação administrativa e testes de API.

## MVP 4 — Exportação CSV

Status: implementado em 12 de junho de 2026.

- exportar snapshot completo de uma release;
- incluir `public_id`, `card_id` e `card_version_id`;
- usar UTF-8 e escape correto;
- permitir configuração controlada de delimitador e tags;
- garantir exportação determinística;
- registrar metadados ou hash do arquivo exportado.

Implementação:

- reconstrução do snapshot pela reprodução dos deltas até a release escolhida;
- exclusão de `removed` e `deprecated` do snapshot, sem apagar o histórico;
- ordenação por `public_id`;
- delimitadores `comma`, `semicolon` e `tab`;
- tags estáveis por `deck_id` e `public_id`;
- hash SHA-256 e contagem de linhas nos cabeçalhos da resposta;
- testes de UTF-8, escaping, determinismo e preservação histórica.

## MVP 5 — Sincronização incremental

Status: implementado em 12 de junho de 2026.

- listar releases;
- consultar mudanças desde uma release;
- retornar identidade estável e nova versão;
- preservar ações de remoção e depreciação;
- preparar contrato para um futuro add-on do Anki.

Implementação:

- `GET /decks/{deck_id}/releases` com paginação e contagem por ação;
- `GET /decks/{deck_id}/sync?since_release=<n>`;
- suporte a instalação inicial com `since_release=0`;
- validação de release de origem;
- deltas sequenciais, sem condensação;
- retorno de `card_id`, `public_id`, versão anterior e nova versão;
- suporte explícito a `added`, `updated`, `removed` e `deprecated`;
- normalização de datas de release em UTC;
- testes de instalação inicial, atualização e cliente já sincronizado.

## MVP 6 — Curadoria

Status: implementado em 12 de junho de 2026.

- reports;
- review tasks;
- aprovação ou rejeição auditável;
- correção por nova versão;
- histórico preservado.

Implementação:

- tabelas `card_reports` e `review_tasks`;
- integridade entre cartão, versão reportada e versão resultante;
- `POST /reports` para versões publicadas;
- listagem e detalhe administrativos com filtros e paginação;
- decisões `rejected`, `duplicate` e `converted_to_new_version`;
- correção criada em `needs_review`, sem trocar a versão publicada atual;
- comentários, responsável e data de revisão obrigatórios;
- atestação de revisão de evidência para atualização legislativa;
- conteúdo original do report e estados terminais imutáveis;
- reports e tarefas não podem ser apagados;
- tarefas concluídas são imutáveis;
- testes de aprovação, rejeição, duplicidade e integridade.

## MVP 7 — Preparação para produção

Status: implementação de código concluída e reforçada em 15 de junho de 2026;
homologação Heroku e restore no provedor ainda pendentes.

Objetivo: transformar o backend funcional em uma base operacional confiável
antes da construção da interface administrativa.

- executar migrations e fluxos críticos contra PostgreSQL real;
- criar testes de integração para triggers, constraints e concorrência;
- separar ambientes de desenvolvimento, homologação e produção;
- hospedar a API e o PostgreSQL em infraestrutura com conexão privada;
- substituir a API key única por autenticação com usuários e papéis;
- definir inicialmente os papéis `admin`, `curator` e `reviewer`;
- proteger endpoints públicos contra abuso e aplicar rate limiting;
- executar migrations como etapa única e controlada de pré-deploy;
- configurar backups automáticos e validar um procedimento de restauração;
- adicionar logs estruturados, monitoramento, alertas e health check do banco;
- gerenciar secrets fora do repositório;
- restringir CORS e a documentação interativa no ambiente de produção.

Implementação:

- tabela `users` e migration `20260612_0006`;
- login com Bearer token expirável;
- senhas PBKDF2-HMAC-SHA256 com salt individual;
- papéis `admin`, `curator` e `reviewer`;
- autoria de criação, versão e revisão derivada do usuário autenticado;
- API key legada permitida apenas fora de produção;
- validação obrigatória de secrets e driver PostgreSQL em produção;
- rate limit em memória para `POST /reports` e `POST /auth/token`;
- logs JSON, `X-Request-ID`, CORS explícito e docs configuráveis;
- liveness em `/health` e readiness PostgreSQL em `/ready`;
- pré-deploy idempotente com migrations, seed e bootstrap administrativo;
- advisory lock PostgreSQL para serializar migrations;
- suíte PostgreSQL opt-in por `TEST_DATABASE_URL`;
- runbook de deploy, backup, restore e rollback.
- migrations `0001` a `0006` executadas em PostgreSQL 17 local;
- triggers PostgreSQL validados pela suíte de integração;
- pré-deploy validado com seed e bootstrap administrativo.
- imagem Docker reconstruída e executada em configuração de produção;
- backup e restore completos validados com comparação de dados e triggers;
- `/ready`, login e `/auth/me` validados sobre o banco restaurado;
- configuração Heroku por `heroku.yml` e `Procfile`;
- processo web usa `$PORT` e release phase executa o pré-deploy;
- pool e TLS PostgreSQL configuráveis;
- revogação de tokens por versão de credencial;
- limite de payload e rate limit com memória limitada;
- CI com PostgreSQL 17, lint, complexidade e cobertura;
- endpoints de taxonomia e gestão administrativa de usuários;
- listagem paginada e resumida de decks.

Pendências externas:

- criar e configurar o app de staging no Heroku;
- anexar Heroku Postgres ao staging;
- executar a suíte PostgreSQL e smoke test no staging;
- configurar PGBackups, restore periódico, métricas e alertas.

Critério de conclusão:

```text
deploy em homologação
→ migrations aplicadas com sucesso
→ testes PostgreSQL aprovados
→ autenticação individual ativa
→ backup restaurado em teste
→ monitoramento e alertas operacionais
```

## MVP 8 — Interface administrativa essencial

Status: backend pré-MVP 8 implementado; início condicionado à validação externa
do staging Heroku.

Objetivo: oferecer uma interface simples para administrar cartões e gerar o
arquivo de importação do Anki sem acesso direto ao banco de dados.

Escopo obrigatório:

- login de usuário administrativo;
- seleção de disciplina e assunto pela API de taxonomia;
- listar e buscar cartões;
- consultar o conteúdo atual e o histórico de versões;
- adicionar um cartão com sua versão inicial;
- modificar conteúdo criando uma nova `card_version`;
- informar `change_reason` em toda modificação;
- aprovar e publicar versões conforme a permissão do usuário;
- criar e consultar decks;
- adicionar, atualizar ou remover cartões de um deck;
- publicar uma release;
- listar releases;
- baixar o CSV de uma release para importação no Anki;
- apresentar mensagens claras para erros de validação e conflito.

Regras arquiteturais:

- a interface deve consumir exclusivamente a API FastAPI;
- a interface não pode executar SQL nem acessar o PostgreSQL diretamente;
- versões publicadas nunca podem ser editadas;
- alterações pedagógicas sempre criam nova versão;
- `card_id` e `public_id` permanecem estáveis;
- atualização da versão de um cartão no deck continua explícita;
- o CSV deve ser gerado pelo backend a partir de uma release;
- a primeira versão deve priorizar desktop e uso administrativo;
- design avançado, aplicativo móvel e edição colaborativa em tempo real ficam
  fora desta fase.

Telas mínimas:

```text
Login
Lista de cartões
Cadastro de cartão
Detalhe e histórico do cartão
Criação e revisão de nova versão
Lista e detalhe de decks
Publicação e histórico de releases
Download do CSV
```

Fluxo principal da interface:

```text
Entrar
→ cadastrar ou localizar cartão
→ criar nova versão quando necessário
→ aprovar e publicar
→ adicionar ou atualizar no deck
→ publicar release
→ baixar CSV
→ importar no Anki
```

Critério de conclusão:

```text
Um usuário autorizado consegue cadastrar, modificar por nova versão,
publicar, organizar em deck e baixar um CSV sem usar Swagger, SQL ou terminal.
```

## Próximos incrementos

- concluir a validação externa do MVP 7 em homologação;
- executar o MVP 8 de interface administrativa essencial;
- histórico de eventos para `needs_more_info`;
- quality checks persistidos;
- política de evidência por deck;
- endpoints de distribuição do conteúdo para um futuro add-on.

## Critério de sucesso

```text
Cadastrar cartão
→ publicar versão
→ adicionar ao deck
→ criar release
→ exportar CSV
→ alterar cartão criando nova versão
→ publicar nova release com delta rastreável
```
