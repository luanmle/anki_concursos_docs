# Instruções para IA de Desenvolvimento

Este documento orienta agentes como Codex, Antigravity ou outros assistentes de programação.

## Papel da IA

A IA deve atuar como engenheira de software e dados, priorizando:

- consistência do banco;
- rastreabilidade;
- versionamento;
- clareza do pipeline;
- código simples;
- modularidade;
- testes;
- documentação.

## Regras arquiteturais obrigatórias

1. Não misturar questão original com flashcard.
2. Não editar versão publicada diretamente.
3. Toda alteração de conteúdo relevante deve criar nova `card_version`.
4. O `card_id` deve ser estável.
5. O progresso futuro do usuário deve se vincular ao `card_id`.
6. Toda fundamentação deve apontar para um `knowledge_chunk`.
7. Toda etapa de pipeline deve registrar logs.
8. Não criar taxonomia livre sem consultar `disciplines` e `topics`.
9. Não publicar cartão sem passar por validações mínimas.
10. Não apagar histórico de versões.

## Prioridades de implementação

### Fase 1

Criar estrutura base:

- modelos do banco;
- migrações;
- conexão com PostgreSQL;
- tabelas principais;
- endpoints básicos.

### Fase 2

Criar ingestão:

- upload de PDF;
- armazenamento do arquivo;
- extração de texto;
- criação de `raw_documents`;
- criação de `processing_jobs`.

### Fase 3

Criar estruturação de questões:

- segmentação básica;
- criação de `questions`;
- criação de `question_alternatives`.

### Fase 4

Criar cartões:

- geração inicial de `cards`;
- geração de `card_versions`;
- status `generated` ou `needs_review`.

### Fase 5

Criar base teórica:

- `knowledge_sources`;
- `knowledge_chunks`;
- embeddings;
- busca textual e semântica.

### Fase 6

Criar curadoria:

- aprovar/reprovar cards;
- editar e criar nova versão;
- reports;
- review tasks.

### Fase 7

Criar releases e sincronização:

- decks;
- deck_cards;
- releases;
- release_items;
- endpoint `/sync`.

## Convenções

- Usar nomes claros e explícitos.
- Preferir tabelas normalizadas.
- Usar UUIDs para entidades principais.
- Usar timestamps em todas as tabelas importantes.
- Usar enum ou tabela de domínio para status críticos.
- Escrever testes para regras de versionamento.
- Evitar lógica escondida em scripts soltos.

## Testes obrigatórios

Criar testes para garantir que:

- uma nova versão não altera versões antigas;
- `card_id` permanece o mesmo;
- `current_version_id` aponta para a versão correta;
- uma release retorna apenas mudanças desde a release anterior;
- cartão sem evidência não é publicado;
- classificação usa disciplina e assunto existentes;
- reports podem gerar nova versão após aprovação.
## Regras para extensões futuras do cartão

1. Manter os 4 campos principais do MVP em `card_versions`:
   - `front_text`
   - `back_text`
   - `answer_text`
   - `explanation_text`

2. Não adicionar URL pública diretamente como campo principal do cartão.

3. Para página web do cartão, usar `card_public_pages`.

4. Para campos pedagógicos extras, usar `card_fields`.

5. Para modelos oficiais de cartão, usar `card_templates` e `card_template_fields`.

6. Alterações em URL, domínio, slug ou layout não devem gerar nova versão pedagógica, salvo se alterarem o conteúdo do cartão.

7. Alterações em campos pedagógicos extras publicados devem gerar nova `card_version`.

8. Preservar sempre a separação:

```text
card_versions = conteúdo pedagógico principal
card_fields = conteúdo pedagógico extra
card_public_pages = publicação e exibição web
```
