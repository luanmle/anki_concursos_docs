# Console Administrativo

Frontend React/TypeScript para administração da plataforma Anki Concursos.

## Responsabilidade

O frontend:

- consome exclusivamente a API HTTP;
- não importa código Python;
- não acessa PostgreSQL;
- não executa migrations;
- não contém regras de publicação ou versionamento;
- respeita permissões retornadas pela API.

## Desenvolvimento

```bash
cp .env.example .env
npm install
npm run dev
```

Variáveis:

```text
VITE_API_URL=http://localhost:8000
VITE_APP_ENV=DEVELOPMENT
```

## Qualidade

```bash
npm run lint
npm test
npm run build
```

## Container

```bash
docker build -t anki-concursos-admin .
docker run --rm -p 8080:8080 \
  -e PORT=8080 \
  -e API_URL=https://api.example.com \
  -e APP_ENV=STAGING \
  anki-concursos-admin
```

O container gera `/config.js` no início do processo. Assim, a mesma imagem pode
ser promovida entre ambientes sem recompilar o bundle.

## Deploy

O console deve ser publicado como aplicação separada do backend. No Heroku, o
app do frontend não recebe Postgres, não possui release phase e usa
`admin/Dockerfile`.

Depois do deploy, adicionar a origem pública do console em `CORS_ORIGINS` no
backend.
