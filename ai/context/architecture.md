# Arquitetura do Projeto Anki Concursos

O projeto é uma plataforma web para compartilhamento, revisão e sincronização de flashcards Anki.

Objetivo principal:
- Repositório de flashcards Anki.
- Sistema de sugestões de alterações.
- Add-on Anki para sincronização.
- Fluxo semelhante ao AnkiHub, mas focado em concursos.

Responsabilidades principais:
- Backend: FastAPI, PostgreSQL, SQLAlchemy/Alembic, autenticação, API REST.
- Frontend: React/Next, Tailwind, interface simples e limpa.
- Add-on: Python, Anki API, sincronização com backend.
- DevOps: GitHub, Heroku, migrations, health checks e deploy.

Regra geral:
- Agentes não devem modificar áreas fora de sua responsabilidade.
- Deploy em produção só pode ocorrer após aprovação humana.