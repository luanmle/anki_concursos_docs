# Skills Guide — Como usar as skills com Claude Code e Codex

Este guia explica como usar as skills do Anki Concursos no dia a dia. Skills são instruções estruturadas que guiam o agente em tarefas específicas do projeto.

---

## Onde ficam as skills

```
.agents/skills/           ← arquivos fonte (cross-agent)
  clarify-feature/SKILL.md
  diagnose-bug/SKILL.md
  implement-with-tests/SKILL.md
  review-change/SKILL.md
  create-handoff/SKILL.md

.claude/skills/           ← symlinks para descoberta pelo Claude Code
  clarify-feature → ../../.agents/skills/clarify-feature
  diagnose-bug    → ../../.agents/skills/diagnose-bug
  ...

skills/                   ← skills nativas do Claude Code (mais detalhadas)
  diagnosing-bugs/SKILL.md
  tdd/SKILL.md
```

---

## Como usar com Claude Code

### Ativar uma skill com slash command

No prompt do Claude Code, digite `/` seguido do nome da skill:

```
/clarify-feature
/diagnose-bug
/implement-with-tests
/review-change
/create-handoff
```

O Claude Code carregará o `SKILL.md` correspondente e seguirá as instruções.

### Fluxo típico de uma nova feature

```
1. /clarify-feature          ← analisa a feature antes de começar
   (responda as perguntas, refine o plano)

2. /implement-with-tests     ← guia o ciclo TDD durante a implementação
   (Red → Green → Refactor por comportamento)

3. /review-change            ← checklist antes do commit
   (garante conformidade com ADRs, testes, segurança)
```

### Fluxo de diagnóstico de bug

```
1. /diagnose-bug             ← loop estruturado
   (reproduzir → minimizar → hipótese → instrumentar → corrigir → regressão)
```

### Encerrar sessão com trabalho pendente

```
/create-handoff <para que será a próxima sessão>
```

Exemplo:
```
/create-handoff implementar validação de content_hash no endpoint de upload
```

O Claude Code criará `docs/handoffs/YYYY-MM-DD_<slug>.md` com o estado atual.

### Dicas de uso

- Você pode descrever a tarefa antes do slash command para dar contexto:
  ```
  Preciso adicionar paginação ao endpoint /cards. /clarify-feature
  ```

- As skills com referência às versões nativas (`skills/tdd/`, `skills/diagnosing-bugs/`) são mais detalhadas. Se quiser o guia completo:
  ```
  /tdd
  /diagnosing-bugs
  ```

---

## Como usar com Codex

O Codex não tem acesso a slash commands. Para usar as skills, inclua o conteúdo do `SKILL.md` no prompt ou na instrução de sistema.

### Opção 1 — Referenciar a skill no prompt

```
Leia o arquivo .agents/skills/clarify-feature/SKILL.md e siga as instruções
para analisar esta feature antes de implementar: [descrição da feature]
```

### Opção 2 — Usar um handoff

Quando o Claude Code cria um handoff em `docs/handoffs/`, o Codex pode usá-lo como ponto de partida:

```
Leia docs/handoffs/2026-06-22_adicionar-endpoint-batch.md e continue a tarefa
descrita. Siga as skills indicadas na seção "Skills sugeridas".
```

### Diferenças importantes para o Codex

| Aspecto | Claude Code | Codex |
|---------|------------|-------|
| Acesso a slash commands | Sim (`/clarify-feature`) | Não |
| Acesso ao banco local | Sim (via Docker) | Não |
| Execução de testes | Sim (`pytest`) | Sim (se configurado) |
| Leitura de SKILL.md | Automática via symlink | Manual (incluir no prompt) |
| Contexto de conversa | Acumulado na sessão | Por prompt; use handoff |

### Fluxo recomendado Claude Code → Codex

```
[Claude Code]
1. /clarify-feature → analisa e planeja
2. /create-handoff "implementar X" → gera docs/handoffs/YYYY-MM-DD_X.md

[Codex]
3. Leia docs/handoffs/YYYY-MM-DD_X.md
4. Leia .agents/skills/implement-with-tests/SKILL.md
5. Implemente seguindo o ciclo TDD descrito
6. Gere novo handoff ao terminar se necessário

[Claude Code]
7. /review-change → verifica conformidade antes do commit
```

---

## Referência rápida de cada skill

### `clarify-feature`

**Quando:** antes de qualquer implementação nova.

**O que faz:** força análise crítica com perguntas sobre identidade de cartões, contratos de API, migrations, sincronização, segurança e testabilidade. Identifica riscos antes de escrever código.

**Prompt de ativação:**
```
/clarify-feature
```
ou com contexto:
```
Quero implementar [descrição]. /clarify-feature
```

---

### `diagnose-bug`

**Quando:** ao depurar comportamento inesperado.

**O que faz:** guia o loop reproduzir → minimizar → hipótese → instrumentar → corrigir → regressão. Inclui referências a pontos críticos do código por área (sync, imutabilidade, autenticação, etc.).

**Prompt de ativação:**
```
/diagnose-bug
```
ou com contexto:
```
O sync está retornando "removed" quando deveria ser "deprecated". /diagnose-bug
```

---

### `implement-with-tests`

**Quando:** durante a implementação, para guiar o ciclo TDD.

**O que faz:** ciclo Red→Green→Refactor, fixtures disponíveis, tabela SQLite vs PostgreSQL, exemplos de testes para as áreas críticas do projeto.

**Prompt de ativação:**
```
/implement-with-tests
```

---

### `review-change`

**Quando:** antes de criar um commit ou abrir um PR.

**O que faz:** checklist em 7 grupos — ADRs, contratos de API, migrations, testes, segurança, compatibilidade com o add-on e qualidade geral. Indica itens bloqueantes vs. aceitáveis com documentação.

**Prompt de ativação:**
```
/review-change
```

---

### `create-handoff`

**Quando:** ao encerrar sessão com trabalho em andamento ou ao transferir para Codex.

**O que faz:** cria `docs/handoffs/YYYY-MM-DD_<slug>.md` com estado atual, pendências, contexto técnico da sessão, riscos específicos e skills sugeridas para a próxima sessão.

**Prompt de ativação:**
```
/create-handoff
```
ou com argumento:
```
/create-handoff implementar validação de content_hash no upload
```

---

## Estrutura dos arquivos gerados por skills

### Handoffs (`docs/handoffs/`)

```
docs/handoffs/
  2026-06-22_endpoint-batch.md    ← gerado por /create-handoff
  2026-06-23_fix-sync-delta.md
```

Mantenha handoffs concluídos — são histórico de decisões e contexto de sessões passadas.

---

## Instalando e atualizando skills

As skills deste projeto estão no repositório e não precisam de instalação adicional.

Para verificar as skills instaladas pelo `npx skills`:
```bash
npx skills check
```

Para adicionar novas skills genéricas do ecossistema:
```bash
npx skills add <owner/repo> --skill <nome>
```

**Não instale skills globalmente** (sem `-g`) para não poluir outros projetos.

---

## Criando novas skills para este projeto

Se precisar criar uma skill específica para o Anki Concursos:

1. Crie o diretório em `.agents/skills/<nome>/`
2. Crie o `SKILL.md` com frontmatter `name`, `description` e instruções adaptadas ao domínio
3. Crie o symlink: `ln -s ../../.agents/skills/<nome> .claude/skills/<nome>`
4. Adicione a skill na tabela de AGENTS.md

Boas skills do projeto:
- São específicas (mencionam arquivos e linhas reais)
- Têm perguntas difíceis que evitam erros comuns
- São curtas o suficiente para serem lidas completamente
- Referenciam as fontes de verdade do projeto (CONTEXT.md, ADRs, conftest.py)
