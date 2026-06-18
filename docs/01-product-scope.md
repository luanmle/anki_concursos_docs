# Escopo do Produto

## Visao Geral

Anki Concursos e uma plataforma de flashcards versionados para concursos
publicos. O produto combina:

- backend FastAPI com versionamento, releases e sync;
- painel administrativo em React;
- add-on do Anki para sincronizacao e upload de baralhos completos;
- area futura de community e comentarios por nota.

## Unidade Principal Do Produto

```text
card_id           identidade estavel
card_version_id   conteudo imutavel
deck_id           unidade de distribuicao
release_id        pacote publicado
public_id         identificador pesquisavel
```

## Fluxo Atual

```text
cartao/nota -> nova versao -> revisao -> publicacao
deck -> release -> exportacao CSV ou sync do add-on
upload do add-on -> deck completo com templates, fields, html e css
```

## O Que O Produto Faz

- armazena cartoes e versoes imutaveis;
- organiza cartoes em decks;
- publica releases deterministicas;
- exporta CSV por release;
- sincroniza decks com o Anki;
- recebe upload de baralho completo do add-on;
- registra reports e revisao editorial;
- expoe painel administrativo;
- envia erros e eventos criticos ao Honeybadger no backend.

## Papéis

```text
admin
curator
reviewer
student
```

- `admin`: acesso total e administracao de usuarios.
- `curator`: cria cartoes, versoes e compoe decks.
- `reviewer`: aprova, publica, revisa reports e releases.
- `student`: assina decks, sincroniza e interage com a experiencia de estudo.

## Experiencia Do Estudante

O estudante deve ver:

- Explore;
- Meus Baralhos;
- detalhe de deck;
- preview de nota;
- sugestao de mudanca;
- comentarios futuros.

O estudante nao deve ver:

- importacao CSV;
- cards/new;
- filtros editoriais internos;
- operacoes administrativas.

## Fora Do Escopo Imediato

- OCR;
- PDFs;
- geracao por IA;
- RAG;
- aplicativo movel;
- edicao direta de versao publicada;
- sincronizacao direta com o banco do Anki.

## Canais E Integrações

- backend principal: FastAPI;
- frontend administrativo: React + Vite;
- add-on Anki: upload e sync de decks assinados;
- observabilidade: Honeybadger no backend;
- deploy: backend e frontend em apps Heroku separados.
