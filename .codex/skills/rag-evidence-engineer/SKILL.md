---
name: rag-evidence-engineer
description: Orienta o cadastro de fontes, chunks e evidências manuais no sistema principal e o limite arquitetural de uma futura integração externa com RAG.
---
# rag-evidence-engineer

## Propósito

Use esta skill no sistema principal apenas para implementar base teórica, busca
textual e vínculos manuais de evidência. Embeddings, busca semântica e RAG
pertencem a um aplicativo futuro separado.

O objetivo é impedir que cartões sejam publicados com explicações sem fonte.

## Quando usar

Use esta skill para tarefas como:

- criar `knowledge_sources`;
- criar `knowledge_chunks`;
- criar busca textual;
- vincular evidências ao cartão;
- validar fundamentação;
- atualizar base teórica.

## Princípio central

Todo cartão publicado deve ter evidência rastreável.

```text
card_version → card_evidence → knowledge_chunk → knowledge_source
```

## Tabelas esperadas

```text
knowledge_sources
- id
- title
- source_type
- jurisdiction
- publication_date
- valid_from
- valid_until
- status

knowledge_chunks
- id
- source_id
- chunk_text
- section_title
- article_number
- paragraph
- version_date
- content_hash

card_evidence
- id
- card_version_id
- knowledge_chunk_id
- relevance_score
- citation_text
```

## Regras obrigatórias

1. Não inventar fundamento.
2. Não aceitar explicação jurídica sem base nos chunks associados.
3. Salvar quais chunks foram usados.
4. Usar busca textual e filtros estruturados no sistema principal.
5. Filtrar por disciplina, assunto, fonte, vigência e jurisdição quando possível.
6. Cartão publicado deve ter pelo menos uma evidência válida.
7. Chunks devem ser citáveis e pequenos o suficiente para auditoria.
8. Fontes desatualizadas devem ter status ou vigência controlada.
9. A explicação deve ser consistente com a evidência.
10. Registrar score de relevância quando ele for fornecido e auditável.

## Limite arquitetural

- Não adicionar `pgvector`, chamadas a LLMs ou RAG ao sistema principal.
- Não criar `prompt_templates` neste banco.
- Um produtor externo pode enviar propostas por API autenticada.
- Toda proposta externa entra em revisão e nunca em estado `published`.

## Validação de evidência

Antes de associar evidência:

- verificar se a fonte está ativa;
- verificar vigência;
- verificar se o chunk tem texto;
- verificar se há relação com a disciplina/assunto;
- registrar score de relevância quando aplicável.

## Regras para explicação

A explicação do cartão deve:

- ser didática;
- ser curta quando possível;
- citar fundamento;
- não extrapolar os chunks;
- apontar pegadinhas quando houver;
- separar resposta objetiva de justificativa.

## Checklist antes de finalizar

- O cartão possui `card_evidence`?
- A evidência aponta para `knowledge_chunk`?
- O chunk aponta para `knowledge_source`?
- A fonte está vigente?
- A explicação está sustentada pela evidência?
- Existe teste impedindo publicação sem evidência?
