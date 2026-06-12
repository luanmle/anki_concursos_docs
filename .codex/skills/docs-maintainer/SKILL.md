---
name: docs-maintainer
description: Mantém a pasta docs sincronizada com alterações de banco, arquitetura, pipeline, stack, versionamento e regras do projeto.
---
# docs-maintainer

## Propósito

Use esta skill sempre que uma alteração de código modificar arquitetura, banco, pipeline, stack, versionamento, sincronização ou regras de qualidade.

O objetivo é manter a pasta `/docs` sincronizada com o código.

## Quando usar

Use esta skill para tarefas como:

- criar tabela nova;
- alterar modelo de dados;
- alterar fluxo de versionamento;
- alterar pipeline;
- alterar regra de publicação;
- alterar endpoint de sync;
- adicionar campo futuro;
- mudar stack;
- adicionar nova dependência relevante;
- mudar estrutura do projeto.

## Documentos principais

```text
/docs/01-product-scope.md
/docs/02-data-model.md
/docs/03-pipeline.md
/docs/04-versioning-and-sync.md
/docs/05-tech-stack.md
/docs/06-ai-agent-instructions.md
/docs/07-mvp-roadmap.md
/docs/08-quality-rules.md
/docs/09-future-card-extensions.md
```

## Regras obrigatórias

1. Se criar tabela, atualizar `/docs/02-data-model.md`.
2. Se alterar versionamento, atualizar `/docs/04-versioning-and-sync.md`.
3. Se alterar pipeline, atualizar `/docs/03-pipeline.md`.
4. Se alterar stack, atualizar `/docs/05-tech-stack.md`.
5. Se alterar regras para agentes, atualizar `/docs/06-ai-agent-instructions.md`.
6. Se alterar roadmap, atualizar `/docs/07-mvp-roadmap.md`.
7. Se alterar regras de qualidade, atualizar `/docs/08-quality-rules.md`.
8. Se adicionar campos extras ou página web de cartão, atualizar `/docs/09-future-card-extensions.md`.
9. Não deixar documentação contradizer o código.
10. Não remover decisões arquiteturais sem registrar motivo.

## Checklist de consistência

Antes de finalizar uma alteração, verificar:

- O código criou tabela não documentada?
- O código criou endpoint não mencionado?
- O código mudou regra de versionamento?
- O código mudou status ou enum?
- O código mudou pipeline?
- O código mudou regra de publicação?
- O código mudou comportamento de sync?
- O README precisa ser atualizado?

## Formato recomendado

Ao atualizar docs, usar:

- seções curtas;
- listas objetivas;
- nomes reais de tabelas;
- exemplos conceituais;
- avisos de regras críticas.

## Regra final

Se houver conflito entre código e documentação, sinalizar o conflito e corrigir a documentação ou o código antes de concluir a tarefa.
