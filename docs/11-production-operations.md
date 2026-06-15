# Operação de Produção no Heroku

## Ambientes

Manter aplicações, bancos e secrets separados:

```text
development
staging
production
```

Staging deve executar a mesma imagem e a mesma release phase de produção.

## Processos

O repositório suporta dois modos de deploy:

- buildpack Python no stack Heroku-24, usando `requirements.txt`,
  `.python-version` e `Procfile`;
- container, usando `Dockerfile` e `heroku.yml`.

Nos dois modos os processos são:

```text
release  python -m app.operations.predeploy
web      uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

A release phase:

1. adquire advisory lock no PostgreSQL;
2. aplica `alembic upgrade head` na mesma conexão bloqueada;
3. executa o seed idempotente de taxonomia;
4. cria o administrador inicial quando configurado.

Uma falha impede a promoção da nova release. Migrations não devem ser executadas
no início de cada dyno web.

## Heroku Postgres

Anexar um add-on Heroku Postgres separado em staging e produção. O Heroku
fornece `DATABASE_URL`; a aplicação normaliza URLs `postgresql://` para o driver
`postgresql+psycopg://`.

Configuração mínima:

```text
APP_ENV=production
DATABASE_SSLMODE=require
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=5
DATABASE_POOL_TIMEOUT_SECONDS=30
DATABASE_POOL_RECYCLE_SECONDS=300
```

O número total potencial de conexões é calculado por processo e dyno. Ajustar
`DATABASE_POOL_SIZE` e `DATABASE_MAX_OVERFLOW` ao limite do plano contratado.

## Secrets

Config vars obrigatórias:

```text
AUTH_SECRET_KEY=<segredo aleatório com pelo menos 32 caracteres>
ALLOW_LEGACY_ADMIN_API_KEY=false
BOOTSTRAP_ADMIN_EMAIL=<email inicial>
BOOTSTRAP_ADMIN_PASSWORD=<senha inicial forte>
CORS_ORIGINS=https://admin.exemplo.com
DOCS_ENABLED=false
TRUST_PROXY_HEADERS=true
MAX_REQUEST_BODY_BYTES=262144
```

Depois da criação do primeiro administrador, remover
`BOOTSTRAP_ADMIN_EMAIL` e `BOOTSTRAP_ADMIN_PASSWORD`.

Nunca registrar tokens, senhas ou URLs com credenciais.

## Deploy

Para usar o buildpack Python no stack Heroku-24, manter o stack padrão e fazer
o deploy normalmente:

```bash
git push heroku main
```

O `requirements.txt` instala o projeto definido em `pyproject.toml` com as
versões de `constraints.txt`. O `.python-version` seleciona Python 3.12.

Para usar container, configurar explicitamente o stack antes do deploy:

```bash
heroku stack:set container -a <app>
git push heroku main
```

Se o log mostrar `Building on the Heroku-24 stack`, o deploy está usando o
buildpack Python e o `heroku.yml` não controla o build. Se a intenção for usar
o `Dockerfile`, conferir o stack com:

```bash
heroku stack -a <app>
```

Verificar a release:

```bash
heroku releases -a <app>
heroku logs --tail -a <app>
```

Critérios mínimos:

```text
release phase concluída
GET /health retorna 200
GET /ready retorna 200
login administrativo funciona
taxonomia pode ser listada
criação e consulta de cartão funcionam
```

## Testes PostgreSQL

Usar banco descartável:

```bash
TEST_DATABASE_URL=postgresql+psycopg://... pytest -m postgres
```

A suíte valida:

- migrations até `20260615_0007`;
- tabelas, colunas e triggers críticos;
- imutabilidade de versão publicada no PostgreSQL;
- unicidade de release por deck.

O CI executa essa suíte com PostgreSQL 17.

## Backup

Ativar PGBackups e definir retenção adequada ao plano:

```bash
heroku pg:backups:schedule DATABASE_URL --at "02:00 America/Sao_Paulo" -a <app>
heroku pg:backups -a <app>
```

Para uma cópia lógica adicional:

```bash
heroku pg:backups:capture -a <app>
heroku pg:backups:download -a <app>
```

Armazenar cópias externas de forma criptografada e com acesso restrito.

## Restore

Restaurar primeiro em staging ou em banco descartável. Nunca testar restore
diretamente sobre produção.

Depois do restore:

```text
alembic current aponta para 20260615_0007
GET /ready retorna ready
login funciona
taxonomia está presente
cartões e releases podem ser consultados
CSV histórico mantém o mesmo hash
```

Registrar data, duração, tamanho, revisão Alembic e responsável pelo teste.

## Monitoramento

Alertas mínimos:

- falha de release phase;
- `/ready` indisponível;
- taxa elevada de respostas 5xx;
- latência P95 acima do limite;
- uso de conexões e armazenamento do PostgreSQL;
- reinícios frequentes de dyno;
- backup atrasado;
- restore periódico não executado.

Logs são JSON em stdout e incluem `request_id`, método, caminho, status e
duração.

## Rate Limit

`TRUST_PROXY_HEADERS=true` deve ser usado apenas atrás do router controlado do
Heroku. O limitador local possui memória limitada, mas continua isolado por
dyno.

Para múltiplos dynos ou tráfego público relevante, aplicar limitação adicional
no edge ou usar armazenamento compartilhado.

## Rollback

Preferir rollback da release da aplicação:

```bash
heroku releases:rollback <release> -a <app>
```

Rollback da aplicação não desfaz automaticamente migrations. Downgrade de banco
exige análise específica, compatibilidade com a versão anterior e backup
confirmado.
