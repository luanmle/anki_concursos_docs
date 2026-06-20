# AGENTS.md

Leia `CONTEXT.md` e respeite os ADRs em `docs/adr/` antes de iniciar qualquer tarefa.

## Convenção de branches e deploy

- `main` é a branch principal do repositório e publica o backend.
- `admin-deploy` é uma branch gerada automaticamente a partir de `admin/` e publica o frontend administrativo.
- Não editar `admin-deploy` manualmente.
- Branches de trabalho devem seguir a convenção:
  - `feat/<slug>` para funcionalidades;
  - `fix/<slug>` para correções;
  - `docs/<slug>` para documentação;
  - `design/<slug>` para UI, design system e especificação visual;
  - `codex/<slug>` apenas para uso temporário por agente.
