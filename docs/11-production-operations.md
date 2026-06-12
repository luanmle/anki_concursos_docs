# Operação de Produção

## Ambientes

Manter bancos e secrets separados:

```text
development
staging
production
```

Homologação deve usar PostgreSQL 17 e executar a mesma imagem da produção.

## Variáveis obrigatórias

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://...
AUTH_SECRET_KEY=<segredo aleatório com pelo menos 32 caracteres>
ALLOW_LEGACY_ADMIN_API_KEY=false
BOOTSTRAP_ADMIN_EMAIL=<email inicial>
BOOTSTRAP_ADMIN_PASSWORD=<senha inicial forte>
CORS_ORIGINS=https://admin.exemplo.com
DOCS_ENABLED=false
```

Secrets devem ficar no gerenciador do provedor. Não inserir valores reais no
repositório, imagem Docker ou logs.

Depois que o administrador inicial for criado, remover
`BOOTSTRAP_ADMIN_PASSWORD` e `BOOTSTRAP_ADMIN_EMAIL` do ambiente.

## Deploy

Executar uma vez, antes de liberar a nova aplicação:

```bash
python -m app.operations.predeploy
```

Essa operação:

1. obtém advisory lock no PostgreSQL;
2. aplica `alembic upgrade head`;
3. executa o seed idempotente de taxonomia;
4. cria o administrador inicial caso ele ainda não exista.

Depois, iniciar a API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
```

Em múltiplas instâncias, migrations não devem fazer parte do comando de start
de cada réplica. Usar job ou etapa única de pré-deploy.

## DigitalOcean

Arquitetura recomendada:

```text
App Platform
→ container FastAPI
→ conexão privada
→ Managed PostgreSQL 17
```

Configurar `/ready` como health check da aplicação. Restringir o banco por
trusted sources e manter API e banco na mesma região.

O template de homologação está em:

```text
deploy/digitalocean/staging.example.yaml
```

Antes do deploy:

1. substituir todos os valores `CHANGE_ME`;
2. revisar região e tamanho das instâncias;
3. autenticar o `doctl`;
4. validar e criar a aplicação.

```bash
doctl auth init
doctl apps spec validate deploy/digitalocean/staging.yaml
doctl apps create --spec deploy/digitalocean/staging.yaml
```

O template usa `DATABASE_PRIVATE_URL`. A aplicação normaliza URLs
`postgresql://` para `postgresql+psycopg://`.

## PostgreSQL real

Usar exclusivamente um banco descartável para o teste:

```bash
TEST_DATABASE_URL=postgresql+psycopg://... pytest -m postgres
```

O teste aplica todas as migrations e valida a revisão `20260612_0006`.

## Backup

Em PostgreSQL gerenciado, habilitar backups automáticos e point-in-time
recovery conforme o plano contratado. Para uma cópia lógica adicional:

```bash
pg_dump --format=custom --no-owner --no-acl \
  --dbname="$POSTGRES_URL" --file="anki-concursos.dump"
```

O arquivo deve ser criptografado e armazenado fora do servidor da aplicação.

## Restore

Restaurar sempre em banco vazio de homologação:

```bash
pg_restore --clean --if-exists --no-owner --no-acl \
  --dbname="$POSTGRES_RESTORE_URL" anki-concursos.dump
```

Validar depois do restore:

```bash
DATABASE_URL="$SQLALCHEMY_RESTORE_URL" alembic current
DATABASE_URL="$SQLALCHEMY_RESTORE_URL" python -m app.seeds.taxonomy
```

`POSTGRES_URL` usa o formato nativo `postgresql://`. As variáveis usadas pela
aplicação e Alembic usam `postgresql+psycopg://`.

Também verificar `/ready`, login, consulta de cartões, releases e exportação
CSV. Registrar data, duração, tamanho do backup e responsável pelo teste.

## Monitoramento

Alertas mínimos:

- `/ready` indisponível;
- taxa elevada de respostas 5xx;
- latência acima do limite definido;
- conexões ou armazenamento do PostgreSQL próximos do limite;
- falha na etapa de pré-deploy;
- backup atrasado ou restore periódico não executado.

O template configura os alertas disponíveis na especificação da App Platform:

- falha de deployment;
- falha de domínio;
- CPU acima de 80% por cinco minutos;
- memória acima de 80% por cinco minutos;
- mais de três reinícios em cinco minutos;
- latência P95 acima de dois segundos por cinco minutos.

Indisponibilidade externa de `/ready` e alertas específicos do PostgreSQL devem
ser configurados no painel da DigitalOcean ou em um monitor externo.

Logs são JSON em stdout e incluem `request_id`, método, caminho, status e
duração. Tokens, senhas e URLs com credenciais não devem ser registrados.

## Rollback

Preferir rollback da imagem da aplicação. Downgrade de migration exige análise
específica e backup confirmado; não executar automaticamente em produção.
