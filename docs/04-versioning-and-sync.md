# Versionamento E Sync

## Regras Base

- `card_id` e a identidade estavel;
- `card_version_id` e o conteudo imutavel;
- versao publicada nunca e editada;
- `release` e a unidade imutavel de distribuicao.

## CSV

O CSV continua sendo exportado por release. Ele nao e a fonte de verdade.

Colunas relevantes:

```text
card_id
public_id
card_version_id
front_text
back_text
answer_text
explanation_text
tags
```

## Sync Administrativo

```text
GET /decks/{deck_id}/sync?since_release={n}
```

Retorna apenas deltas posteriores a `since_release`.

## Sync Do Add-on

```text
GET /addon/decks/{deck_id}/manifest
GET /addon/decks/{deck_id}/sync?since_release=0
```

O add-on agora trabalha com pacote nativo:

- `note_type`;
- `template_name`;
- `fields`;
- `template`;
- `source_note_id`;
- `source_note_guid`;
- `source_deck_path`.

O manifesto passa a ser montado a partir de `deck_templates` e
`deck_template_versions` quando essas tabelas existem para o deck. O snapshot
bruto continua como fallback de compatibilidade.

Isso aproxima o fluxo do que o Anki faz com note types e templates:

- identidade do deck continua separada da estrutura do card;
- a estrutura do template tem versao propria;
- o cliente recebe a forma atual da definicao antes de aplicar deltas de
  conteudo.

## Upload Do Add-on

```text
POST /addon/decks/upload
```

O upload preserva templates, html, css e campos do Anki. O backend gera
identificadores internos, snapshot do pacote e versao persistida do template,
sem exigir schema unico.

## Curadoria

Reports convertidos em nova versao nao alteram a versao publicada ate
aprovação e publicaçao explicita.
