# AGENTS.md

Leia `CONTEXT.md` e respeite os ADRs em `docs/adr/` antes de iniciar qualquer tarefa.

## Skills disponíveis

Skills são instruções estruturadas que guiam o agente em tarefas específicas.  
Localização: `.agents/skills/<nome>/SKILL.md` (symlinks em `.claude/skills/`).

| Skill | Quando usar |
|-------|------------|
| `clarify-feature` | **Antes** de implementar qualquer feature nova, endpoint ou migration |
| `diagnose-bug` | Ao depurar comportamentos inesperados |
| `implement-with-tests` | Durante a implementação, ciclo TDD |
| `review-change` | **Antes** de commitar ou abrir PR |
| `create-handoff` | Ao encerrar sessão com trabalho em andamento ou transferir para Codex |
| `document-changes` | Após implementações significativas — atualiza `docs/CHANGELOG.md` e `docs/context/active-context.md` |

**Claude Code:** use `/clarify-feature`, `/diagnose-bug`, etc. como slash commands.  
**Codex:** leia o `SKILL.md` correspondente antes de iniciar a tarefa.

Documentação detalhada de uso: `docs/skills-guide.md`.

Skills nativas do Claude Code (mais detalhadas, apenas Claude Code): `skills/tdd/` e `skills/diagnosing-bugs/`.

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
