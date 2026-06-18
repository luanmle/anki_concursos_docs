# Upload De Baralho Completo Pelo Add-on

## Objetivo

Este documento descreve como o add-on Anki deve enviar um baralho completo para
a plataforma.

O contrato foi ajustado para um modelo mais proximo do Anki/AnkiHub: o deck e
enviado como pacote, com modelos de nota, templates, HTML, CSS, campos
arbitrarios, tags e subdecks. A plataforma nao exige um schema unico como
`Front`, `Back`, `Answer` ou `Explanation`.

## Regra Principal

O add-on nao envia notas soltas.

Ele envia um pacote completo de baralho, e a plataforma:

- cria ou reutiliza o deck;
- cria cards e card_versions;
- vincula cada card ao deck;
- preserva campos, template, HTML, CSS, tags e origem da nota;
- registra um snapshot do pacote recebido;
- publica release quando houver conteudo novo ou atualizado.

## Endpoint

```text
POST /addon/decks/upload
```

Permissao:

- qualquer usuario autenticado da plataforma aceito pelo add-on.

## Autenticacao

O add-on deve enviar:

```text
Authorization: Bearer <access_token>
```

O endpoint aceita usuarios autenticados de qualquer role suportada pelo add-on
(`admin`, `curator`, `reviewer` ou `student`), desde que o token seja valido.

## Fonte De Verdade

A fonte de verdade do upload e do sync e o pacote nativo do Anki:

- `templates[].fields`
- `templates[].front_html`
- `templates[].back_html`
- `templates[].styling_css`
- `notes[].fields`
- `notes[].source_note_id` ou `notes[].source_note_guid`, quando disponivel

`field_mapping` pode ser enviado por compatibilidade com fluxos antigos, telas
administrativas e exportacoes canonicas, mas nao e mais obrigatorio para que o
upload funcione.

## Payload

```json
{
  "deck_name": "Direito Constitucional - Base",
  "description": "Pacote completo exportado do Anki",
  "source_name": "addon",
  "source_deck_path": "Direito::Constitucional",
  "publish_release": true,
  "templates": [
    {
      "template_name": "Basic",
      "note_type": "Meu Modelo Customizado",
      "card_kind": "basic",
      "fields": ["Enunciado", "Alternativas", "Comentario"],
      "field_mapping": {},
      "front_html": "<section>{{Enunciado}}</section>",
      "back_html": "<section>{{Alternativas}}{{Comentario}}</section>",
      "styling_css": ".card { font-family: Arial; }"
    }
  ],
  "notes": [
    {
      "note_type": "Meu Modelo Customizado",
      "template_name": "Basic",
      "card_kind": "basic",
      "source_note_id": "1714851485108",
      "source_note_guid": "abc123",
      "source_deck_path": "Direito::Constitucional::Controle",
      "fields": {
        "Enunciado": "Julgue o item.",
        "Alternativas": "Certo ou errado",
        "Comentario": "Comentario livre."
      },
      "tags": ["constitucional", "controle"]
    }
  ]
}
```

## Templates

Cada item de `templates` representa um modelo/template do Anki.

Campos obrigatorios:

- `template_name`
- `note_type`
- `card_kind`
- `fields`
- `front_html`
- `back_html`

Campos opcionais:

- `field_mapping`
- `styling_css`

O backend armazena o template completo recebido. Isso permite que o add-on
reconstrua o modelo, os campos, o HTML e o CSS no download/sync.

## Notes

Cada item de `notes` representa uma nota do baralho.

Campos obrigatorios:

- `note_type`
- `card_kind`
- `fields`

Campos opcionais:

- `template_name`
- `tags`
- `source_note_id`
- `source_note_guid`
- `source_deck_path`

Recomendacao: o add-on deve sempre enviar `source_note_id` ou
`source_note_guid`. Esse identificador mantem a identidade estavel da nota.
Quando a mesma nota chegar depois com conteudo diferente, a plataforma cria uma
nova `card_version` do mesmo `card_id`.

## Campos Arbitrarios

Nao existe schema unico obrigatorio. Um baralho pode ter modelos diferentes,
campos diferentes e subdecks diferentes no mesmo upload.

Os campos internos antigos ainda existem por compatibilidade:

- `front_text`
- `back_text`
- `answer_text`
- `explanation_text`

No upload pelo add-on, esses campos internos sao derivados apenas como fallback
para telas antigas, CSV e fluxos administrativos. O sync do add-on deve usar os
campos nativos preservados em `fields`.

Se nenhum campo da nota tiver conteudo, o upload retorna `422`.

## Cloze

Para `card_kind = cloze`, algum campo da nota deve conter a marcacao:

```text
{{c1::...}}
```

O backend nao assume que o cloze esta em `Text`, `Cloze`, `Lesson` ou
`front_text`. Ele procura a marcacao nos campos da nota para montar o fallback
interno, mas preserva os campos originais para o sync.

## Taxonomy

O upload de baralho completo nao depende de taxonomy.

Nao enviar:

- `discipline_id`
- `topic_id`
- `card_id`
- `canonical_key`
- `public_id`

A plataforma gera os identificadores internos.

## Identidade E Versionamento

Quando o add-on envia `source_note_id` ou `source_note_guid`, a plataforma usa
esse valor junto com `template_name` como identidade estavel do card dentro do
deck. Isso evita colisao quando uma unica nota Anki gera mais de um card por
templates diferentes.

Regras:

- mesma nota + mesmo conteudo: reutiliza o card e a versao existente;
- mesma nota + conteudo diferente: cria nova `card_version` do mesmo `card_id`;
- nota sem identificador de origem: deduplica por hash do pacote nativo;
- conteudo atualizado gera release nova quando `publish_release = true`.

## Resposta Esperada

```json
{
  "deck_id": "uuid",
  "deck_name": "Direito Constitucional - Base",
  "snapshot_id": "uuid",
  "release_id": "uuid",
  "latest_release": 1,
  "published": true,
  "total_notes": 1,
  "created_cards": 1,
  "reused_cards": 0,
  "updated_cards": 0,
  "items": [
    {
      "note_index": 1,
      "status": "created",
      "canonical_key": "deck-...",
      "card_id": "uuid",
      "public_id": "AC-...",
      "card_version_id": "uuid",
      "note_type": "Meu Modelo Customizado",
      "card_kind": "basic"
    }
  ]
}
```

`status` pode ser:

- `created`
- `reused`
- `updated`

## Sync

Depois do upload, o add-on continua usando:

- `GET /addon/status`
- `GET /addon/decks/{deck_id}/manifest`
- `GET /addon/decks/{deck_id}/sync`

Para mudancas `added` e `updated`, o sync pode retornar:

- `note_type`
- `template_name`
- `fields`
- `template`
- `source_note_id`
- `source_note_guid`
- `source_deck_path`
- `tags`

O add-on deve preferir esses campos nativos para criar ou atualizar a nota local.
Campos canonicos antigos devem ser tratados apenas como fallback.

## Fluxo Recomendado No Add-on

1. Autenticar o usuario.
2. Ler o deck local, subdecks, note types, templates, CSS, tags e notes.
3. Montar `templates[]` com os modelos encontrados.
4. Montar `notes[]` com os campos brutos e identificadores de origem.
5. Enviar `POST /addon/decks/upload`.
6. Se a resposta tiver `published = true`, registrar a release retornada.
7. Usar `manifest` e `sync` para downloads e atualizacoes futuras.

## Erros Que O Add-on Deve Tratar

- `401`: token ausente ou expirado;
- `403`: permissao insuficiente;
- `409`: conflito real de dados;
- `422`: pacote invalido, template ausente, card kind invalido ou nota sem
  campos.

## Relacao Com Anki

O desenho segue o modelo conceitual do Anki:

- note type/model define campos;
- template define frente, verso e CSS;
- note carrega valores arbitrarios por campo;
- cloze e tratado como tipo especial, mas ainda preserva os campos originais.

## Regra Arquitetural

O deck completo e a unidade principal de entrada. A plataforma preserva o pacote
Anki para permitir sincronizacao incremental sem depender da estrutura interna
do cartao.
