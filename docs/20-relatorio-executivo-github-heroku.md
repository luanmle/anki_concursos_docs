# Relatorio executivo: GitHub, Heroku, branches e ambientes

## Em uma frase

Este projeto usa um unico repositorio no GitHub para manter o codigo, mas publica dois aplicativos separados no Heroku: o backend e o painel administrativo.

## Como funciona

### GitHub

O GitHub e o local onde o codigo fica armazenado e versionado.

- `main` e a branch principal do projeto.
- `admin-deploy` e uma branch gerada automaticamente a partir da pasta `admin/`.
- Outras branches servem para desenvolvimento e testes de novas funcionalidades.

### Heroku

O Heroku hospeda os aplicativos publicados.

- Um app Heroku roda o backend FastAPI.
- Outro app Heroku roda o frontend administrativo.

## Divisao entre frontend e backend

### Backend

E a parte que:

- guarda as regras do sistema;
- conversa com o banco de dados;
- autentica usuarios;
- controla cards, decks, versoes e releases.

### Frontend

E a interface visual usada pela equipe para:

- revisar conteudo;
- administrar usuarios;
- operar o sistema;
- acessar as funcoes do backend de forma organizada.

O frontend nao acessa o banco direto. Ele conversa com o backend pela API.

## Branches principais

### `main`

- E a branch oficial do desenvolvimento.
- Publica o backend.
- Recebe o codigo-fonte principal.

### `admin-deploy`

- E uma branch de distribuicao, nao de desenvolvimento.
- E criada automaticamente a partir da pasta `admin/`.
- Publica o frontend no Heroku.

## O que esta bem feito

- separa interface e regras do sistema;
- evita acesso direto do frontend ao banco;
- permite publicar backend e frontend de forma independente;
- reduz risco de misturar codigos com responsabilidades diferentes;
- deixa o backend como fonte unica de verdade.

## Pontos de atencao

- `admin-deploy` nao deve ser editada manualmente;
- os nomes dos ambientes precisam ser claros para evitar confusao;
- o frontend depende de configuracoes corretas de API e CORS;
- ha sinais de nomes pouco padronizados em alguns remotes do Heroku;
- e importante deixar claro para a equipe qual ambiente e staging e qual e producao.

## Conclusao

O desenho geral e bom e comum em sistemas com painel administrativo:

- um repositorio unico;
- duas aplicacoes publicadas separadamente;
- backend centralizado;
- frontend isolado do banco;
- deploy controlado por branches diferentes.

Para nao tecnicos, a ideia principal e simples: o GitHub guarda o projeto, o backend faz o trabalho pesado, e o frontend so mostra e organiza as operacoes.

