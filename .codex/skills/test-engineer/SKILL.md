---
name: test-engineer
description: Cria e revisa testes para versionamento, publicação, evidência, sincronização, curadoria e regras críticas do sistema.
---
# test-engineer

## Propósito

Use esta skill para criar, revisar ou melhorar testes automatizados do projeto.

O projeto depende de regras fortes de versionamento, publicação, sincronização, curadoria e evidência. Testes são obrigatórios para evitar regressões.

## Quando usar

Use esta skill para tarefas como:

- criar testes unitários;
- criar testes de integração;
- testar migrations;
- testar services;
- testar endpoints;
- testar exportação CSV;
- testar versionamento;
- testar sync;
- testar curadoria;
- testar publicação.

## Princípios

1. Testar regras de negócio críticas.
2. Não testar apenas caminhos felizes.
3. Criar fixtures claras.
4. Testar que histórico não é apagado.
5. Testar que publicação exige qualidade.
6. Testar que sync retorna mudanças incrementais.
7. Testar erros esperados.

## Testes obrigatórios de versionamento

Criar testes para garantir:

- criar `card` com versão 1;
- criar versão 2 sem alterar versão 1;
- `card_id` permanece igual;
- `public_id` é único, imutável e permanece igual;
- `current_version_id` aponta para a versão correta;
- `version_number` é incrementado;
- duas versões do mesmo cartão não têm mesmo `version_number`;
- versão publicada não é editada diretamente;
- `change_reason` é obrigatório em alterações por curadoria.

## Testes obrigatórios de publicação

Criar testes para garantir:

- cartão sem `front_text` não publica;
- cartão sem `back_text` não publica;
- cartão sem `answer_text` não publica;
- cartão sem `explanation_text` não publica;
- cartão sem disciplina válida não publica;
- cartão sem assunto válido não publica;
- cartão sem evidência não publica quando a política do deck exigir;
- status inválido não publica.

## Testes obrigatórios de evidência

Criar testes para garantir:

- `card_evidence` aponta para `card_version`;
- `card_evidence` aponta para `knowledge_chunk`;
- `knowledge_chunk` aponta para `knowledge_source`;
- fonte inativa ou vencida não é usada para publicação sem aviso;
- explicação não é aceita sem evidência quando a política do deck exigir.

## Testes obrigatórios de sync

Criar testes para garantir:

- release contém `release_items`;
- release e itens são imutáveis;
- endpoint de sync retorna apenas mudanças desde release informada;
- ações `added`, `updated`, `removed`, `deprecated` são suportadas;
- update retorna `card_id` e novo `card_version_id`;
- progresso do usuário pode continuar vinculado ao `card_id`.
- nova versão em revisão não oculta versão publicada atual.

## Testes obrigatórios de CSV

- inclui `public_id`, `card_id` e `card_version_id`;
- conteúdo corresponde à versão da release;
- UTF-8 é preservado;
- aspas, delimitadores e quebras de linha são escapados;
- mesma release gera o mesmo conteúdo;
- removidos e depreciados seguem política explícita.

## Testes obrigatórios de curadoria

Criar testes para garantir:

- report é vinculado ao `card_id` e `card_version_id`;
- report aprovado pode criar nova versão;
- report rejeitado não altera versão;
- decisão do admin é registrada;
- versão reportada continua preservada.

## Checklist antes de finalizar

- Foram adicionados testes para a regra alterada?
- Os testes falham sem a implementação?
- Há teste de erro/negação?
- Há fixture mínima e clara?
- Os testes não dependem de ordem de execução?
- O comando de teste está documentado?
