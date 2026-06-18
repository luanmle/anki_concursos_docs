# Upload De Baralho Completo Pelo Add-on

## Objetivo

Este documento descreve como o desenvolvedor do add-on Anki deve implementar o
envio de um baralho completo para a plataforma.

O contrato cobre:

- baralho;
- notas/cartões;
- modelo de cartão;
- mapeamento de campos;
- HTML das faces;
- CSS de estilização;
- tags;
- publicação automática de release quando houver conteúdo novo.

## Regra Principal

O add-on nao envia notas soltas.

Ele envia um pacote completo de baralho, e a plataforma:

- cria ou reutiliza o deck;
- cria cards e card_versions;
- vincula cada card ao deck;
- registra um snapshot do pacote recebido;
- publica release quando necessario.

## Endpoint

```text
POST /addon/decks/upload
```

Permissao:

- qualquer usuario autenticado da plataforma que receba permissao no add-on

## Autenticacao

O add-on deve autenticar com um usuario valido da plataforma e enviar o header:

```text
Authorization: Bearer <access_token>
```

O endpoint aceita usuarios autenticados de qualquer role suportada pelo add-on
(`admin`, `curator`, `reviewer` ou `student`), desde que o token seja valido.

## O Que O Add-on Deve Enviar

O payload deve conter:

- nome do baralho;
- descricao opcional;
- origem do upload;
- decisao de publicar release;
- lista de templates;
- lista de notas.

O add-on tambem deve manter um mapeamento explicito por note type na sua
configuracao local (`upload_field_mappings`). O pacote nao deve depender de
heuristica para descobrir nomes de campo.

### Exemplo de payload

```json
{
  "deck_name": "Direito Constitucional - Base",
  "description": "Pacote completo exportado do Anki",
  "source_name": "addon",
  "publish_release": true,
  "templates": [
    {
      "template_name": "Basic",
      "note_type": "Anki Concursos Basic",
      "card_kind": "basic",
      "fields": ["Front", "Back", "Answer", "Explanation"],
      "field_mapping": {
        "Front": "front_text",
        "Back": "back_text",
        "Answer": "answer_text",
        "Explanation": "explanation_text"
      },
      "front_html": "<div>{{Front}}</div>",
      "back_html": "<div>{{Back}}</div>",
      "styling_css": ".card { font-family: Inter; }"
    }
  ],
  "notes": [
    {
      "note_type": "Anki Concursos Basic",
      "card_kind": "basic",
      "fields": {
        "Front": "Qual e a capital do Brasil?",
        "Back": "Brasilia.",
        "Answer": "Brasilia.",
        "Explanation": "Capital federal do Brasil."
      },
      "tags": ["geografia", "capital"]
    }
  ]
}
```

## Regras De Estrutura

### `deck_name`

- identifica o baralho no backend;
- se o deck nao existir, a plataforma cria um novo;
- se existir, o upload atualiza o mesmo deck.

### `publish_release`

- `true`: publica uma release se houver mudancas;
- `false`: grava o pacote e os cards, mas nao publica release.

### `templates`

Cada template representa um modelo de nota/cartao do pacote.

Campos obrigatorios:

- `template_name`
- `note_type`
- `card_kind`
- `fields`
- `field_mapping`
- `front_html`
- `back_html`

`styling_css` e aceito para preservar o design do cartao.

O `field_mapping` precisa ser declarado explicitamente no add-on. O upload nao
faz inferencia por nome, ordem ou conteudo de campo.

### `notes`

Cada item de `notes` representa uma nota do baralho.

Campos obrigatorios:

- `note_type`
- `card_kind`
- `fields`

`tags` e opcional.

## Mapeamento De Campos

O backend converte os campos enviados pelo add-on em campos internos.

Campos canônicos internos:

- `front_text`
- `back_text`
- `answer_text`
- `explanation_text`

Exemplo de mapeamento:

```json
{
  "Front": "front_text",
  "Back": "back_text",
  "Answer": "answer_text",
  "Explanation": "explanation_text"
}
```

O add-on deve enviar apenas os campos que estiverem definidos no
`field_mapping` explicito. Campos nao mapeados nao precisam existir no pacote e
nao sao inferidos.

Importante:

- o backend nao assume que o campo cloze esteja em uma posicao fixa;
- o backend usa o `field_mapping` informado pelo add-on para descobrir qual
  campo preenche `front_text`;
- o mesmo deck pode conter varios templates com campos diferentes;
- cada `note_type` deve ter um mapeamento explicito no add-on.
- `explanation_text` e opcional e pode ficar vazio se o modelo de nota nao
  possuir um campo equivalente;
- o importador nao bloqueia o upload apenas porque nao existe explicacao.

## Tipos Suportados

O upload suporta inicialmente:

- `basic`
- `cloze`

### Basic

Use quando a nota tiver um campo de frente mapeado e, opcionalmente, campos de
verso, resposta e explicacao.

### Cloze

Use quando a nota tiver lacunas no texto.

O campo mapeado para `front_text` deve conter a marcação cloze:

```text
{{c1::...}}
```

Se o cloze vier em um campo chamado `Cloze`, o add-on deve mapear esse campo
para `front_text`. Se vier em outro campo, o add-on deve declarar esse campo no
`field_mapping`.

Se a nota cloze nao tiver um campo de explicacao, resposta ou verso, o upload
continua valido desde que o `field_mapping` explicito esteja coerente.

## Taxonomy

O upload de baralho completo nao depende de taxonomy.

Ou seja:

- nao enviar `discipline_id`;
- nao enviar `topic_id`;
- nao enviar `card_id`;
- nao enviar `canonical_key`;
- nao enviar `public_id`.

A plataforma gera os identificadores internos.

## O Que O Backend Gera

Ao receber o upload, a plataforma gera:

- `deck_id`
- `snapshot_id`
- `release_id` quando publicar
- `card_id`
- `public_id`
- `card_version_id`
- `canonical_key`
- `content_hash`

## Deduplicacao

O backend evita duplicacao por conteudo.

Se a mesma nota chegar novamente:

- a plataforma reutiliza o card existente quando o conteudo for identico;
- nao cria duplicata acidental;
- atualiza o vínculo com o deck quando necessario.

Isso permite reenviar o mesmo pacote sem quebrar o banco.

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
  "items": [
    {
      "note_index": 1,
      "status": "created",
      "canonical_key": "deck-...",
      "card_id": "uuid",
      "public_id": "AC-...",
      "card_version_id": "uuid",
      "note_type": "Anki Concursos Basic",
      "card_kind": "basic"
    }
  ]
}
```

## Fluxo Recomandado No Add-on

1. O add-on carrega as configuracoes do ambiente.
2. O usuario autentica.
3. O add-on monta o pacote completo do deck.
4. O add-on envia `POST /addon/decks/upload`.
5. O add-on mostra o resultado da importacao.
6. Se a API retornar `published=true`, o pacote ja entrou como release.

## Erros Que O Add-on Deve Tratar

O add-on precisa tratar:

- `401` para token ausente ou expirado;
- `403` para permissao insuficiente;
- `409` para conflito de dados;
- `422` para template invalido, campo ausente ou card kind invalido.

## Recomendacoes De Implementacao

### 1. Configuracao

Manter a URL do backend em arquivo de configuracao do add-on, com suporte a
ambientes:

- `production`
- `staging`
- `local`

### 2. Validaçao Antes Do Upload

Antes de enviar o pacote, o add-on deve validar:

- se existe mapeamento explicito para cada `note_type`;
- se os campos fonte existem na nota local;
- se `card_kind` bate com o template;
- se cloze possui markup `{{c1::...}}` no campo mapeado para `front_text`.

### 3. Envio Em Lote

Enviar o baralho como um unico payload.

Nao fragmentar as notas em chamadas separadas, porque o backend trata o upload
como um pacote atomico de baralho.

### 4. Reenvio Seguro

Se o upload falhar por rede ou timeout, o add-on pode reenviar o pacote.
O backend foi desenhado para tolerar repeticao do mesmo conteudo.

## Relacao Com Sync E Manifest

Este endpoint e apenas para envio do pacote inicial ou de uma nova versao do
baralho.

Depois do upload, o add-on continua usando:

- `GET /addon/status`
- `GET /addon/decks/{deck_id}/manifest`
- `GET /addon/decks/{deck_id}/sync`

para descobrir versao atual e sincronizar mudancas.

## Regra Arquitetural

O add-on nao deve assumir que a taxonomy existe no upload.

O modelo do sistema agora trata o deck completo como unidade principal de
entrada, e a taxonomy fica fora desse caminho.

## Observacao Final

Esse contrato foi desenhado para ser consistente com a logica tipo AnkiHub:

- deck completo como artefato principal;
- cards versionados internamente;
- notas sempre vinculadas ao deck;
- HTML/CSS e mapeamento preservados no snapshot;
- integracao futura com sincronizacao incremental.
