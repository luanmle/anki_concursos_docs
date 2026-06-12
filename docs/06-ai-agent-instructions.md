# Instruções para Agentes de Desenvolvimento

## Objetivo

Implementar uma plataforma de dados para flashcards versionados, releases e
exportações CSV compatíveis com importação no Anki.

## Regras Obrigatórias

1. Manter `card_id` estável.
2. Manter `public_id` único, imutável e visível ao usuário.
3. Nunca editar uma `card_version` publicada.
4. Criar nova versão para alteração pedagógica.
5. Preservar versões antigas.
6. Atualizar `current_version_id` apenas com versão do mesmo cartão.
7. Não exigir questão ou documento de origem.
8. Usar taxonomia controlada.
9. Publicar apenas versões aprovadas.
10. Tornar releases imutáveis.
11. Gerar CSV a partir de release específica.
12. Incluir `public_id`, `card_id` e `card_version_id` nas exportações.
13. Não tratar CSV como fonte de verdade.
14. Não adicionar PDF, OCR, IA, embeddings ou RAG.
15. Não acessar diretamente o banco interno do Anki.
16. Proteger endpoints administrativos com autenticação.
17. Expor publicamente apenas cartões publicados.
18. Não inserir versão não publicada em deck.
19. Não alterar release ou item de release depois da publicação.
20. Calcular releases comparando identidade e versão, nunca texto.
21. Não ocultar versão publicada apenas porque existe nova versão em revisão.
22. Vincular report ao cartão e à versão exata reportada.
23. Nunca editar a versão reportada para aplicar uma correção.
24. Registrar responsável, comentário, decisão e data da revisão.
25. Criar correção aprovada em `needs_review`.
26. Não atualizar automaticamente `current_version_id` ou decks após report.
27. Não reintroduzir API key administrativa como autenticação de produção.
28. Aplicar autorização por papel nos endpoints administrativos.
29. Derivar autoria e revisão da identidade autenticada quando disponível.
30. Não executar migrations concorrentemente sem advisory lock.
31. Manter `/health` independente e `/ready` dependente do PostgreSQL.
32. Não registrar senhas, tokens, secrets ou URLs com credenciais em logs.

## Prioridades

### Cartões

- schemas, repositories e services;
- criação transacional de cartão e versão 1;
- consulta, filtros e paginação;
- busca exata por `public_id`;
- criação de novas versões.

### Publicação

- aprovação;
- decks;
- associação de cartões;
- releases e deltas.

Fluxo obrigatório:

```text
needs_review → approved → published
```

### CSV

- UTF-8;
- escape correto;
- ordenação determinística;
- hash e contagem de linhas;
- testes com aspas, delimitadores e quebras de linha.

### Sync

- mudanças desde uma release;
- ações `added`, `updated`, `removed` e `deprecated`;
- contrato para futuro add-on do Anki.

### Curadoria

- report público apenas para versão publicada;
- fila administrativa paginada e filtrável;
- rejeição e duplicidade sem alteração de conteúdo;
- conversão em nova versão com conteúdo completo;
- histórico e decisão imutáveis;
- publicação da correção pelo fluxo normal.

## Legado

`raw_documents`, `exams`, `questions` e `question_alternatives` existem no
schema inicial, mas estão fora do escopo ativo. Não criar dependências novas.
