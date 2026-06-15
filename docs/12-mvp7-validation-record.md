# Registro de Validação do MVP 7

Data: 12 de junho de 2026.

Este documento é um registro histórico da validação original. Em 15 de junho
de 2026, o destino operacional principal passou de DigitalOcean para Heroku.
O runbook vigente está em `docs/11-production-operations.md`.

## Ambiente local

```text
Docker Desktop 29.5.3
PostgreSQL 17 Alpine
Python da imagem 3.12
```

## Imagem

A imagem foi reconstruída a partir do `Dockerfile` atual:

```text
anki_concursos_docs-api:latest
```

O build instalou o pacote e todas as dependências sem erro.

## PostgreSQL

A suíte de integração aplicou migrations `0001` a `0006` em um banco
descartável PostgreSQL 17.

Resultado:

```text
1 teste PostgreSQL aprovado
revisão Alembic: 20260612_0006
triggers críticos encontrados: 4 de 4
```

## Pré-deploy

O comando abaixo foi executado pela imagem construída:

```bash
python -m app.operations.predeploy
```

Resultado:

```text
migrations aplicadas
5 disciplinas cadastradas
15 assuntos cadastrados
administrador inicial criado
```

## Backup e restore

Foi criado um banco fonte descartável, gerado um backup no formato custom do
PostgreSQL e restaurado em outro banco vazio.

Métricas:

```text
tamanho do backup: 65751 bytes
tempo do backup: 2,47 segundos
tempo do restore: 5,26 segundos
```

Comparação:

```text
origem:  revisão 20260612_0006, 1 usuário, 5 disciplinas, 15 assuntos
destino: revisão 20260612_0006, 1 usuário, 5 disciplinas, 15 assuntos
triggers críticos restaurados: 4 de 4
```

## Smoke test restaurado

A API foi iniciada em configuração de produção apontando para o banco
restaurado.

Resultados:

```text
GET /ready: ready, database=ok
POST /auth/token: administrador autenticado
GET /auth/me: identidade e papel admin confirmados
```

## Homologação DigitalOcean

O template está em:

```text
deploy/digitalocean/staging.example.yaml
```

Ele define:

- build pelo `Dockerfile`;
- job `PRE_DEPLOY`;
- PostgreSQL 17;
- readiness em `/ready`;
- liveness em `/health`;
- alertas de falha de deploy, domínio, CPU, memória, reinícios e latência.

A criação efetiva do ambiente depende de uma conta DigitalOcean autenticada.

O `doctl 1.161.0` foi instalado localmente e o YAML foi carregado com sucesso.
A validação oficial:

```bash
doctl apps spec validate deploy/digitalocean/staging.example.yaml
```

foi interrompida antes do envio porque não havia contexto autenticado nem
`DIGITALOCEAN_ACCESS_TOKEN`. O próximo passo exige executar `doctl auth init`
com uma conta DigitalOcean que tenha permissão de escrita.
