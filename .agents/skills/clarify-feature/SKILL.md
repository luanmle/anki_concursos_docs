---
name: clarify-feature
description: >
  Análise crítica e esclarecimento de funcionalidade antes da implementação.
  Use ANTES de implementar qualquer feature nova, endpoint, mudança de schema ou
  alteração em regras de negócio. Força as perguntas difíceis que evitam retrabalho.
---

# Clarify Feature — Análise antes da implementação

## Quando usar

Obrigatório antes de implementar qualquer mudança que envolva:
- Novo endpoint ou alteração de contrato de API existente
- Mudança no schema do banco (nova migration)
- Lógica de sincronização ou cálculo de delta
- Regras de versionamento de cartões ou releases
- Qualquer interação com o add-on Anki
- Mudança em fluxo de autenticação ou papéis

Para mudanças cosméticas isoladas (renomear variável local, ajustar mensagem de erro), esta skill é opcional.

## O protocolo

### Passo 1 — Reformule em uma frase

Escreva a funcionalidade em uma única frase antes de continuar. Se não conseguir, pergunte antes de prosseguir.

> "Implementar endpoint `POST /decks/{id}/cards/batch` que adiciona múltiplos cartões em uma única transação."

Se a frase for vaga ("melhorar o sync"), refine até ser acionável.

### Passo 2 — Perguntas obrigatórias

Responda cada grupo abaixo antes de escrever código.

**Identidade e imutabilidade**
- A mudança afeta `Card.public_id` ou `Card.canonical_key`? (ADR-0001 — imutáveis)
- Ela cria, modifica ou remove uma `CardVersion` com `status=published`? (ADR-0002 — proibido)
- Ela toca em `Release` ou `ReleaseItem`? (ADR-0003 — imutáveis após criação)
- Um `CardReport` aprovado criará versão com `status=needs_review`, não `published`? (ADR-0004)

**Contrato de API**
- Algum campo obrigatório some de um response existente?
- Campos novos em requests são opcionais (não quebram clientes antigos)?
- O add-on Anki consome esse endpoint? A mudança é retrocompatível?
- A mudança afeta `/addon/decks/{id}/sync` ou `/decks/{id}/sync`?
- O frontend admin (`admin/`) consome esse endpoint? Qual o impacto?

**Banco de dados**
- É necessária migration Alembic? Se sim:
  - O nome seguirá o padrão `YYYYMMDD_NNNN_<descricao>.py`?
  - O `downgrade` foi implementado?
  - Dados existentes ficam consistentes?
- Nenhuma migration antiga será modificada?

**Prevenção de duplicatas**
- Como o sistema evitará criar duplicatas? (`canonical_key`? `content_hash`? constraint SQL?)
- O que acontece se a operação for executada duas vezes seguidas?

**Sincronização**
- O que o aluno vê após essa mudança?
- Um full sync (`since_release=0`) retorna o estado correto?
- Um sync incremental (`since_release=N`) produz o delta correto?
- Todas as `ReleaseAction` relevantes (`added`, `updated`, `removed`, `deprecated`) são cobertas?

**Segurança e papéis**
- Qual papel (`admin`, `curator`, `reviewer`, `student`) pode executar essa ação?
- O guard correto está sendo usado (`require_admin`, `require_curator`, `require_reviewer`, `require_staff`, `require_authenticated_user`)?
- Inputs do usuário são validados via Pydantic antes de chegar ao service?

**Testabilidade**
- Pode ser testado com SQLite em memória, ou precisa de PostgreSQL real (`@pytest.mark.postgres`)?
- Quais fixtures existem? O que precisa ser criado?
- Qual o critério de sucesso verificável por um teste automatizado?

### Passo 3 — Mapa de riscos

Preencha antes de implementar:

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| Regressão no sync do add-on | ? | Alto | Teste `test_sync_*` com `since_release=0` e `>0` |
| Perda de dados em migration | ? | Alto | Migration reversível; testar em staging |
| Quebra de retrocompatibilidade da API | ? | Alto | Campos novos opcionais; não remover campos |
| Duplicata silenciosa | ? | Médio | `content_hash` + constraint único |
| Violação de imutabilidade | ? | Alto | Eventos SQLAlchemy + triggers PostgreSQL |

Riscos com impacto Alto e probabilidade não-zero bloqueiam a implementação até terem mitigação concreta.

### Passo 4 — Esboço do plano

Só após responder os passos anteriores, escreva:

1. **Arquivos a modificar** — path e o que muda em cada um
2. **Testes a criar** — comportamentos cobertos e fixtures necessárias
3. **Migration** — nome, o que faz, é reversível?
4. **Diff de contrato de API** — campos adicionados/removidos/renomeados

### Passo 5 — Ponto de decisão

Apresente o plano. **Aguarde confirmação antes de implementar** quando a mudança:
- Altera contrato consumido pelo add-on Anki
- Exige migration sem `downgrade`
- Toca nas regras de imutabilidade (ADRs 0001–0003)
- Tem risco Alto sem mitigação definida

Para mudanças pequenas e isoladas (campo opcional novo, nova rota sem quebra), prosseguir sem confirmar é aceitável.

## Referências deste projeto

| Referência | Localização |
|-----------|------------|
| Dicionário de domínio | `CONTEXT.md` |
| Decisões de arquitetura | `docs/adr/0001` a `docs/adr/0006` |
| Eventos de imutabilidade | `app/models/entities.py:660-808` |
| Lógica de sync | `app/services/decks.py:263-334` |
| Hash de conteúdo (manual) | `app/services/cards.py:42-62` |
| Hash de conteúdo (upload) | `app/services/decks.py:1113-1135` |
| Fixtures de teste | `tests/conftest.py` |
| Guards de autenticação | `app/core/security.py:240-244` |
