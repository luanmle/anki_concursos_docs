---
name: document-changes
description: >
  Documenta mudanças recentes do projeto em docs/CHANGELOG.md e atualiza
  docs/context/active-context.md com o estado atual do trabalho. Use este skill
  sempre que terminar uma implementação significativa, ao fechar uma sessão com
  mudanças feitas, ao concluir uma feature, fix ou refactor que vale registrar,
  ou quando o usuário pedir para documentar. Também use para registrar decisões
  técnicas, decisões de produto e mudanças de arquitetura. Use mesmo que o usuário
  não peça explicitamente — se houve mudança real no código, registre.
argument-hint: "O que foi feito? (ex: refatorei CardFormPage para shadcn/ui)"
---

# Document Changes

Registra o que mudou e atualiza o contexto ativo para que a próxima sessão comece
com visibilidade do estado real do projeto — sem depender de memória ou histórico de conversa.

## Dois arquivos, dois propósitos

**`docs/CHANGELOG.md`** — registro histórico imutável de mudanças. Cresce para cima (mais recente no topo). Nunca edite entradas passadas.

**`docs/context/active-context.md`** — snapshot do estado atual. Sobrescreva completamente a cada atualização. É o que a próxima sessão vai ler para entender onde parou.

## Passo a passo

### 1. Coletar o que mudou

Se o usuário forneceu uma descrição como argumento, use-a como base.

Caso contrário, colete via git:

```bash
git diff --stat HEAD~1 HEAD      # arquivos alterados no último commit
git log --oneline -5             # últimos commits
git diff --name-only             # alterações não commitadas
```

Se não houver commits ainda, use `git status` e leia os arquivos alterados.

### 2. Atualizar docs/CHANGELOG.md

Adicione uma nova entrada **no topo** do arquivo (abaixo do cabeçalho), sem modificar entradas anteriores:

```markdown
## YYYY-MM-DD — <título curto da mudança>

**Branch:** `<branch atual>`
**Tipo:** feature | fix | refactor | docs | design | infra

### O que mudou
- `<arquivo>:<linha aprox>` — <descrição do que mudou e por quê, não apenas o que>
- Exemplo: `admin/src/pages/CardFormPage.tsx` — migrado para componentes shadcn/ui (Input, Select, Textarea); removida dependência de ui.tsx legado

### Decisões relevantes
- <decisão técnica ou de produto tomada, com motivação>
- Se nenhuma: omita esta seção

### Impacto
- <o que quebra, o que muda de comportamento, o que o usuário final verá>
- Se nenhum: omita esta seção
```

Se `docs/CHANGELOG.md` não existir ainda, crie com o cabeçalho:

```markdown
# Changelog — Anki Concursos

Registro de mudanças por sessão. Mais recente no topo.
Commits detalhados: `git log --oneline`.
ADRs (decisões de arquitetura): `docs/adr/`.

---
```

### 3. Atualizar docs/context/active-context.md

Sobrescreva o arquivo completo com o estado atual:

```markdown
# Contexto Ativo

**Atualizado:** YYYY-MM-DD
**Branch:** `<branch>`
**Status:** em andamento | concluído | bloqueado

## O que está sendo trabalhado

<Uma frase clara do foco atual. Ex: "Migração do admin para shadcn/ui — branch frontend-redesign">

## Últimas mudanças (desta sessão)

- <mudança concreta, com arquivo quando relevante>
- <mudança concreta>

## Próximos passos

- [ ] <próxima tarefa concreta>
- [ ] <próxima tarefa>

## Decisões recentes

- **<decisão>** — <motivação não óbvia>
- Se nenhuma: omita esta seção

## O que NÃO tocar agora

- <área do código que está instável, em migração, ou que outro agente está trabalhando>
- Se nenhuma restrição: omita esta seção
```

### 4. Confirmar ao usuário

Após atualizar ambos os arquivos, informe:

```
✓ docs/CHANGELOG.md — entrada adicionada para YYYY-MM-DD
✓ docs/context/active-context.md — atualizado com estado atual
```

Não exiba o conteúdo completo dos arquivos na resposta — apenas confirme o que foi registrado e destaque decisões importantes que merecem atenção.

## Regras

**Inclua:**
- Mudanças com impacto real no comportamento ou na estrutura
- Decisões com motivação não óbvia pelo código
- Bloqueios ou dependências que afetam o próximo trabalho

**Não inclua:**
- Mudanças cosméticas sem impacto (espaços, imports reorganizados sem efeito)
- Informações já nos commits ou nos ADRs — referencie por path
- Secrets, tokens, senhas

## Relação com outros skills

- **`create-handoff`** — use quando vai transferir para outro agente ou outra sessão com tarefa incompleta. `document-changes` documenta o que foi feito; `create-handoff` instrui o próximo a continuar.
- **`review-change`** — use antes de commitar. `document-changes` pode ser chamado após o commit.
- Use ambos quando encerrar uma sessão com trabalho completo: primeiro `review-change`, depois commit, depois `document-changes`.
