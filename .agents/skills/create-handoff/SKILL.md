---
name: create-handoff
description: >
  Cria um documento de handoff estruturado para transferir contexto entre sessões
  ou entre agentes (Claude Code → Codex, ou vice-versa). Salva em docs/handoffs/.
argument-hint: "Para que será usada a próxima sessão? (ex: implementar endpoint X, revisar PR Y)"
---

# Create Handoff

Compacta o estado atual da sessão em um documento que outro agente — ou outra sessão — pode retomar sem perda de contexto.

## Quando usar

- Antes de encerrar uma sessão com trabalho em andamento
- Ao transferir uma tarefa do Claude Code para o Codex (ou vice-versa)
- Quando a conversa atingiu o limite de contexto e precisa continuar
- Antes de mudar de assunto, deixando uma tarefa parcialmente feita

## Formato do documento

Salve em `docs/handoffs/YYYY-MM-DD_<slug>.md`.

```markdown
# Handoff: <título descritivo>

**Data:** YYYY-MM-DD
**De:** Claude Code | Codex
**Para:** Claude Code | Codex
**Branch:** <nome da branch atual>
**Status:** em andamento | bloqueado | pronto para revisão

## Objetivo da próxima sessão

<Uma frase clara do que deve ser feito.>
Se o argumento da skill foi fornecido, use-o como foco principal.

## Estado atual

### O que foi feito
- <item concreto — cite arquivos e linhas, não intenções>
- Exemplo: "Adicionado endpoint `POST /decks/{id}/cards/batch` em `app/api/routes/decks.py:210`"

### O que está pendente
- [ ] <tarefa com contexto suficiente para retomar sem ler toda a conversa>
- [ ] <tarefa>

### Bloqueios
- <descreva bloqueios concretos, ou "nenhum">

## Contexto técnico desta sessão

> Não repita o que está em CONTEXT.md ou nos ADRs.
> Inclua apenas o que é específico desta sessão e não está no código.

- **Decisão tomada:** <decisão> — <motivação não óbvia pelo código>
- **Invariante descoberta:** <o que foi aprendido sobre o comportamento do sistema>
- **Arquivo modificado:** `<path>` — <o que mudou e por quê, se não estiver no commit>

## Riscos desta tarefa

> Apenas riscos específicos desta implementação. Não liste riscos genéricos do projeto.

- <risco concreto com contexto>

## Estado dos testes

```bash
pytest          # <passou / falhou com X erros — descreva>
pytest -m postgres   # <executado? passou?>
```

## Comandos para retomar

```bash
git checkout <branch>
pytest                    # verificar estado atual
git diff main             # ver mudanças pendentes
```

## Skills sugeridas para a próxima sessão

- `clarify-feature` — se a tarefa ainda precisa de análise antes de implementar
- `implement-with-tests` — se é hora de implementar com TDD
- `diagnose-bug` — se há um bug a resolver
- `review-change` — antes do commit final
- `create-handoff` — ao terminar a próxima sessão também sem concluir
```

## Regras do handoff

**O que incluir:**
- Fatos específicos desta sessão que não estão no código nem na documentação
- Decisões com motivação não óbvia
- Contexto que se perderia ao fechar a conversa

**O que NÃO incluir:**
- Conteúdo já em `CONTEXT.md`, `AGENTS.md` ou `docs/adr/` — referencie por caminho
- Intenções sem ação concreta ("a ideia é fazer X") — converta em tarefa pendente
- Secrets, tokens, senhas, chaves de API — nunca

## Diferença Claude Code → Codex

Ao criar handoff para o Codex:
- Inclua path completo de cada arquivo relevante
- Seja explícito sobre o que o Codex pode e não pode fazer (ex.: sem acesso ao banco local, sem `docker compose up`)
- Prefira instruções sequenciais a instruções abertas
- Liste explicitamente os testes que devem passar ao final da tarefa
- Codex não tem acesso ao histórico de conversa — o handoff é sua única fonte de contexto

Ao criar handoff para o Claude Code:
- Pode referenciar conversas anteriores se relevantes
- Claude Code tem acesso ao banco local via `docker compose` — mencione estado esperado
- Inclua qual skill usar para começar a próxima sessão
