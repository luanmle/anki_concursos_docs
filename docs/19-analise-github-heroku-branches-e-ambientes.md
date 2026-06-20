# Analise de GitHub, Heroku, branches e separacao de ambientes

## Objetivo

Este documento explica, de forma didatica, como este repositorio distribui o sistema entre GitHub e Heroku, como as branches sao usadas, qual parte do sistema e frontend ou backend, e quais pontos estao bem desenhados ou ainda precisam de ajustes.

O foco aqui e a organizacao do projeto. Nao ha analise de codigo-fonte nem mudancas de implementacao.

## Resumo executivo

O repositorio nao representa dois projetos independentes no GitHub.

Ele organiza um unico produto com dois aplicativos publicados no Heroku:

- o **backend**, que e a API FastAPI;
- o **frontend administrativo**, que fica dentro da pasta `admin/` e e publicado separadamente.

A separacao principal e esta:

- `main` representa o codigo-base do projeto e publica o backend;
- `admin-deploy` e uma branch derivada, gerada automaticamente apenas com o conteudo de `admin/`, e publica o frontend.

Isso significa que:

- o GitHub guarda o codigo-fonte inteiro;
- o Heroku recebe dois deploys diferentes;
- o frontend nao acessa banco de dados diretamente;
- o backend continua sendo a fonte de verdade do negocio.

## Como o sistema esta dividido

### 1. Backend

O backend e a aplicacao principal do produto. Ele:

- expoe a API REST;
- controla autenticacao e permissao;
- registra cards, versoes, releases e reports;
- conversa com PostgreSQL;
- executa migrations e rotinas de predeploy.

Arquivos que mostram isso:

- [`README.md`](../README.md)
- [`docs/11-production-operations.md`](11-production-operations.md)
- [`CONTEXT.md`](../CONTEXT.md)

### 2. Frontend administrativo

O frontend administrativo fica dentro de `admin/` e serve como painel visual para:

- curadoria;
- revisao;
- administracao de usuarios;
- fluxos de cards e decks;
- acesso operacional ao backend.

Ele nao conversa direto com o banco. A interface usa a API do backend via `API_URL` ou `VITE_API_URL`, dependendo do ambiente.

Arquivos que mostram isso:

- [`docs/14-admin-ui-frontend-specification.md`](14-admin-ui-frontend-specification.md)
- [`docs/11-production-operations.md`](11-production-operations.md)
- [`README.md`](../README.md)

## Mapa visual

```text
                    GitHub
  -------------------------------------------------
  main  -------------------------------> backend app
   |                                         |
   |                                         |  API + banco + migrations
   |                                         v
   |                                  Heroku backend
   |
   +--> admin/  -- git subtree split --> admin-deploy ---> frontend app
                                                   |
                                                   |  interface administrativa
                                                   v
                                            Heroku frontend

Fluxo de uso:

  pessoa administrativa -> frontend -> API do backend -> PostgreSQL
  aluno/add-on Anki      -> API do backend -> PostgreSQL
```

Leitura do diagrama:

- o trabalho nasce no GitHub;
- a branch `main` publica o backend;
- a pasta `admin/` gera a branch `admin-deploy`;
- `admin-deploy` publica o frontend em outro app Heroku;
- o frontend conversa com o backend por HTTP, nao direto com o banco.

## Como GitHub e Heroku trabalham juntos

### GitHub

O GitHub guarda:

- a branch principal `main`;
- a branch derivada `admin-deploy`;
- branches de trabalho e historico de desenvolvimento;
- automacoes via GitHub Actions.

No repositorio foi encontrado:

- [`main`](../..), usada como linha principal do projeto;
- [`admin-deploy`](../..), que existe como branch de distribuicao do frontend;
- branches locais de trabalho como `docs/context-adrs-skills` e outras branches de desenvolvimento historico;
- remotes para dois apps Heroku separados.

### Heroku

O Heroku hospeda duas aplicacoes separadas:

- uma aplicacao para o backend;
- uma aplicacao para o frontend administrativo.

Pelos remotes locais encontrados, existem dois destinos Heroku distintos:

- `backend-heroku` apontando para `flashcards-stagging.git`;
- `heroku` apontando para `flashcards-admin-staging.git`.

Isso confirma que a separacao no Heroku e por aplicativo, nao por pasta ou rota dentro do mesmo deploy.

## Branches existentes e o que cada uma faz

### `main`

E a branch principal do repositorio.

Papel:

- concentra o desenvolvimento normal;
- publica o backend FastAPI;
- recebe as mudancas de `app/`, `docs/`, testes, migrations e tambem do frontend em `admin/`.

Regra operacional:

- o backend acompanha `main`;
- o deploy do backend deve partir dela.

### `admin-deploy`

E a branch de distribuicao do frontend.

Papel:

- nao e branch de desenvolvimento;
- e gerada automaticamente a partir do conteudo de `admin/`;
- representa o frontend pronto para deploy no Heroku.

Regra operacional:

- nao deve ser editada manualmente;
- nao deve receber merge normal;
- e regenerada por `git subtree split --prefix=admin`.

### Branches locais de desenvolvimento

Foi visto historico com branches como:

- `docs/context-adrs-skills`
- `codex/admin-deploy-split`
- `codex/admin-addon-prep-deploy`
- `codex/admin-card-kind-deploy`
- `codex/admin-csv-import-deploy`
- `codex/admin-student-role-deploy`

Essas branches indicam trabalho incremental e tematica de features. Elas nao fazem parte da arquitetura de deploy em si, mas mostram que o projeto usa branches curtas para evolucao e integracao.

### Branches remotas observadas

Nos remotes, apareceram:

- `origin/main`
- `origin/admin-deploy`
- `origin/docs/context-adrs-skills`
- `origin/admin-deploy`
- `heroku/main`
- `backend-heroku/main`

O ponto importante aqui e que os remotes do Heroku estao ligados a branches diferentes, o que reforca a separacao entre backend e frontend.

## Como o deploy funciona na pratica

### Backend

O backend pode ser implantado de duas formas:

1. via buildpack Python usando `requirements.txt`, `.python-version` e `Procfile`;
2. via container usando `Dockerfile` e `heroku.yml`.

Na configuracao atual, o backend roda:

- `release: python -m app.operations.predeploy`
- `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`

A fase de release executa migrations e rotinas iniciais antes de o app subir.

### Frontend

O frontend e publicado como outro app Heroku.

O fluxo documentado e:

1. o GitHub Action valida o frontend;
2. gera a branch `admin-deploy`;
3. essa branch e conectada ao app Heroku do frontend;
4. o frontend recebe a URL da API do backend via variavel de ambiente;
5. o backend recebe a origem do frontend em `CORS_ORIGINS`.

O frontend nao deve ter:

- `DATABASE_URL`;
- migrations;
- acesso direto ao PostgreSQL;
- responsabilidade por regra de negocio.

## O que esta bem desenhado

### 1. Separacao clara de responsabilidades

O desenho segue uma divisao saudavel:

- backend = regra de negocio, dados, autenticacao, sincronizacao;
- frontend = interface administrativa.

Isso reduz acoplamento e evita que a interface vire uma segunda fonte de verdade.

### 2. Deploy independente por ambiente

O projeto nao tenta empacotar frontend e backend como um unico deploy monolitico.

Vantagens:

- o backend pode escalar e evoluir sem depender do bundle visual;
- o frontend pode ser publicado sem mexer no banco;
- ha menos risco de misturar infraestrutura de banco com interface;
- o Heroku fica simples de operar em cada app.

### 3. Branch de distribuicao separada

Usar `admin-deploy` como branch derivada e uma boa pratica quando:

- o frontend esta dentro do mesmo repositorio;
- o host de deploy espera raiz do projeto;
- voce quer publicar apenas um subdiretorio como aplicacao autonoma.

Isso evita manter um segundo repositorio so para o painel.

### 4. Release phase no backend

A estrategia de `release phase` antes do `web` subir e boa pratica porque:

- migrations nao ficam rodando em cada dyno;
- o banco e atualizado de forma controlada;
- falhas de migration impedem deploy incompleto;
- o historico fica mais previsivel.

### 5. Configuracao de ambiente documentada

A documentacao deixa explicito:

- `development`, `staging` e `production`;
- uso de `CORS_ORIGINS`;
- separacao entre API de staging e API de producao;
- necessidade de `APP_ENV`, `API_URL` e `ALLOW_LEGACY_ADMIN_API_KEY=false` em producao.

## Inconsistencias e lacunas observadas

### 1. Nome do app Heroku e remoto com grafia suspeita

Foi encontrado o remote:

- `backend-heroku` -> `flashcards-stagging.git`

O nome `stagging` parece um erro de grafia de `staging`.

Impacto:

- nao quebra o sistema por si so;
- mas aumenta confusao operacional e dificulta a manutencao por pessoas nao tecnicas.

### 2. Nomes de apps e ambientes podem gerar confusao

A documentacao fala em:

- staging;
- production;
- backend;
- frontend;
- admin-deploy.

Mas os remotes locais encontrados sugerem que o Heroku atual pode estar sendo usado em um contexto de staging, nao necessariamente um ambiente final de producao.

Ponto de atencao:

- vale padronizar nomes para deixar claro qual app e staging e qual e producao;
- evitar que `heroku` e `backend-heroku` sejam interpretados como apps diferentes sem contexto.

### 3. A branch `admin-deploy` depende de um processo que e pouco intuitivo para nao programadores

Apesar de funcionar bem tecnicamente, esse modelo exige que a equipe entenda:

- `admin/` e a fonte de verdade do frontend;
- `admin-deploy` e apenas resultado gerado;
- qualquer edicao manual em `admin-deploy` sera descartada.

Para publico nao tecnico, isso precisa estar muito bem documentado, porque a ideia de uma branch que existe mas nao deve ser editada nao e obvia.

### 4. Existe mais de um caminho de deploy do backend

A documentacao menciona:

- buildpack Python;
- container com `Dockerfile` e `heroku.yml`.

Isso e flexivel, mas pode virar ambiguidade se a equipe nao souber qual caminho e o oficial em cada app.

Risco:

- uma pessoa pode olhar `heroku.yml` e supor que ele sempre manda no deploy;
- outra pode ver o log do Heroku-24 e achar que o container nao esta em uso.

Lacuna:

- falta deixar mais explicito qual estrategia cada app realmente usa hoje.

### 5. O frontend depende de configuracoes muito sensiveis do backend

O esquema funciona, mas o frontend precisa acertar:

- `API_URL`;
- `APP_ENV`;
- CORS no backend;
- compatibilidade entre staging e producao.

Se essas variaveis ficarem desalinhadas, o frontend sobe mas nao conversa com a API.

Isso nao e um defeito da arquitetura, mas e um ponto operacional fragil.

### 6. `admin-deploy` e uma branch gerada, nao uma branch humana

O modelo e valido, mas exige disciplina:

- nao editar manualmente;
- nao abrir PR comum nela;
- nao tratar como branch de feature.

Se a equipe nao respeitar isso, a branch pode virar lixo operacional ou fonte de divergencia.

### 7. O ecossistema mistura documentacao de produto, operacao e implementacao

O repositorio tem:

- especificacao de frontend;
- operação de Heroku;
- fluxos de dominio;
- ADRs;
- README;
- CI.

Isso e positivo para rastreabilidade, mas pode ser pesado para quem quer apenas entender "onde esta o frontend" e "onde esta o backend".

Lacuna:

- faltaria talvez um mapa visual curto, em uma pagina, explicando:
  - qual branch vai para qual app;
  - qual variavel aponta para qual ambiente;
  - quem depende de quem.

## Avaliacao do esquema

### E um bom esquema?

Sim, no geral e um esquema bom para um produto que tem:

- backend forte;
- frontend administrativo separado;
- necessidade de manter regra de negocio centralizada;
- operacao em Heroku;
- deploy simples para cada parte.

### Por que ele e bom

- reduz acoplamento entre interface e dominio;
- evita banco exposto ao frontend;
- permite evoluir o painel sem mexer no backend;
- melhora a separacao conceitual para o time;
- reduz risco de misturar responsabilidade de dados e interface.

### Onde ele exige mais cuidado

- branch derivada precisa ser confiavel;
- configuracao de CORS precisa bater com a URL real;
- o time precisa entender que `admin-deploy` e artefato, nao branch de trabalho;
- nomes dos apps e remotes precisam ser claros para evitar erro humano.

## Conclusao didatica

Pense assim:

- o **GitHub** e a oficina, onde todo o trabalho acontece;
- o **backend no Heroku** e o motor do sistema, onde ficam dados e regras;
- o **frontend no Heroku** e a vitrine operacional, onde as pessoas administram o sistema;
- a branch `main` carrega o projeto principal;
- a branch `admin-deploy` e apenas a copia publicada do painel administrativo.

Portanto, nao existem dois projetos completamente separados. Existe um unico repositorio com dois destinos de deploy, cada um com seu papel.

## Recomendações objetivas

1. Padronizar e documentar melhor os nomes dos apps Heroku, corrigindo qualquer grafia ambigua como `stagging`.
2. Manter uma pagina-resumo visual da arquitetura de deploy para nao tecnicos.
3. Reforcar na documentacao que `admin-deploy` e branch gerada automaticamente e nao deve ser editada.
4. Deixar explicito, em um unico lugar, qual modo de deploy esta ativo em cada app: buildpack ou container.
5. Garantir que staging e producao tenham nomes, URLs e secrets inequivocos.
