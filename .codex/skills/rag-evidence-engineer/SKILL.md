---
name: rag-evidence-engineer
description: Orienta base teórica, chunks, embeddings, busca híbrida, RAG e vínculo de evidências aos flashcards.
---
# rag-evidence-engineer

## Propósito

Use esta skill para implementar base teórica, embeddings, busca textual, busca semântica, recuperação de evidências e fundamentação dos flashcards.

O objetivo é impedir que cartões sejam publicados com explicações sem fonte.

## Quando usar

Use esta skill para tarefas como:

- criar `knowledge_sources`;
- criar `knowledge_chunks`;
- gerar embeddings;
- implementar pgvector;
- criar busca semântica;
- criar busca textual;
- vincular evidências ao cartão;
- gerar explicações com base em fontes;
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
- embedding

card_evidence
- id
- card_version_id
- knowledge_chunk_id
- relevance_score
- citation_text
```

## Regras obrigatórias

1. Não inventar fundamento.
2. Não gerar explicação jurídica sem base nos chunks recuperados.
3. Salvar quais chunks foram usados.
4. Preferir busca híbrida: textual + vetorial.
5. Filtrar por disciplina, assunto, fonte, vigência e jurisdição quando possível.
6. Cartão publicado deve ter pelo menos uma evidência válida.
7. Chunks devem ser citáveis e pequenos o suficiente para auditoria.
8. Fontes desatualizadas devem ter status ou vigência controlada.
9. A explicação deve ser consistente com a evidência.
10. Registrar score de relevância.

## Busca híbrida

Usar combinação de:

```text
full-text search
similaridade vetorial com pgvector
filtros estruturados
reranking opcional
```

## Validação de evidência

Antes de associar evidência:

- verificar se a fonte está ativa;
- verificar vigência;
- verificar se o chunk tem texto;
- verificar se há relação com a disciplina/assunto;
- calcular score de relevância.

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
- A explicação foi gerada com base em evidência?
- Existe teste impedindo publicação sem evidência?
