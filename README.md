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

## Design Stitch

A interface implementa o projeto Google Stitch `App Specification Interface`
(`projects/13880116207067144925`) e seu design system Obsidian.

Foram incorporados:

- tema escuro de alto contraste com tokens centralizados;
- navegação lateral compacta e cabeçalho de ambiente;
- tabelas densas, filtros e paginação;
- estados editoriais semânticos;
- detalhe do cartão com conteúdo, metadados e histórico;
- criação de cartão e de novas versões com preview;
- criação e composição operacional de decks;
- publicação de releases imutáveis e exportação CSV;
- revisão de reports com conversão opcional em nova versão;
- ações de aprovação e publicação condicionadas ao papel do usuário;
- layout responsivo com navegação móvel.

Elementos demonstrativos do protótipo, como métricas globais sem endpoint,
foram deliberadamente removidos. O frontend continua usando apenas a API HTTP.

Telas adicionais criadas no mesmo projeto Stitch:

- `projects/13880116207067144925/screens/4c26571b3e284f3f9af5b6be59373c55`
  para detalhes do deck;
- `projects/13880116207067144925/screens/20e516bdb5f94b5d85b0c705f669c8d2`
  para revisão de report.
- `projects/13880116207067144925/screens/edf45647aa6a48deae9e5c881c97d301`
  para gestão de usuário.
