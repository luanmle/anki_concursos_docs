# Proposta de modelo de sync para deck Anki nativo

## Objetivo

Manter a sincronização entre plataforma e add-on o mais próxima possível do
comportamento do Anki e do AnkiHub, sem perder a simplicidade do nosso domínio.

O foco é sincronizar de forma eficiente:

- identidade do deck;
- definição do note type/template;
- conteúdo das notas;
- diffs incrementais entre versões.

## Referências analisadas

### Anki

O manual do Anki deixa claro que:

- note types definem campos, cards gerados e estilo do cartão;
- templates controlam front, back e styling;
- a sincronização de mídia existe no ecossistema Anki, mas fica fora do escopo
  desta fase.

Fontes:

- [Card Templates](https://docs.ankiweb.net/templates/intro.html)
- [Field Replacements](https://docs.ankiweb.net/templates/fields.html)
- [Styling & HTML](https://docs.ankiweb.net/templates/styling.html)
- [Syncing with AnkiWeb](https://docs.ankiweb.net/syncing.html)
- [Media](https://docs.ankiweb.net/media.html)

### AnkiHub

O ecossistema AnkiHub confirma a mesma direção prática:

- o add-on é um cliente que sincroniza conteúdo com um backend;
- decks compartilhados preservam templates, fields e regras de atualização;
- o cliente precisa conseguir instalar e reaplicar modelos do deck.

Fontes:

- [AnkiHub add-on](https://github.com/AnkiHubSoftware/ankihub_addon)
- [AnkiHub shared deck page](https://ankiweb.net/shared/info/1322529746)

## Situação atual do nosso sistema

Hoje o upload do add-on já persiste:

- `note_type`
- `template_name`
- `anki_fields`
- `anki_template`
- `anki_tags`
- `source_note_id`
- `source_note_guid`
- `source_deck_path`

Esses dados ficam em `card_versions`, e o pacote bruto também fica salvo em
`deck_snapshots.payload_json`.

Além disso:

- `GET /addon/decks/{deck_id}/manifest` entrega templates e mapping;
- `GET /addon/decks/{deck_id}/sync` entrega mudanças incrementais;
- o deck publicado continua sendo a unidade principal de consumo.

## Lacuna

O sistema ainda trata o modelo do deck como parte do snapshot/manifesto, mas não
como uma entidade de sincronização explicitamente versionada.

Isso deixa três limitações:

- renomeação de template depende demais de texto livre;
- mudanças estruturais em fields ou HTML/CSS não têm um diff dedicado;
- o cliente precisa inferir mais do que deveria na primeira instalação.

## Arquitetura alvo

### 1. Versionar o modelo do deck separadamente

Criar uma entidade própria para o modelo do deck, por exemplo:

- `deck_templates`
- `deck_template_versions`

Cada versão deve guardar:

- `template_key` estável;
- `template_name`;
- `note_type`;
- `card_kind`;
- `fields`;
- `field_mapping`;
- `front_html`;
- `back_html`;
- `styling_css`;
- `content_hash`;
- `version_number`;
- `created_at`;
- `created_by`.

### 2. Separar sync de template e note

O add-on deve consumir três camadas:

#### Manifesto inicial

Usado para instalar ou reinstalar o deck localmente.

Deve conter:

- versão atual do modelo;
- templates completos;
- mapping de fields;
- tags estruturais;
- versão do pacote.

#### Delta de conteúdo

Usado para sincronizar notas e alterações publicadas.

Deve conter:

- `card_id`;
- `card_version_id`;
- ação (`added`, `updated`, `removed`, `deprecated`);
- conteúdo das notas;

#### Delta de modelo

Usado quando a estrutura do card mudou.

Deve conter:

- template version anterior e nova;
- diff de fields;
- diff de HTML/CSS;
- status de compatibilidade com o cliente.

#### Mídia

Fora do escopo desta fase.

### 3. Chave estável de template

Hoje o sistema depende demais de `note_type` e `template_name`.

O ideal é introduzir um identificador estável, por exemplo:

- `template_key`
- `model_key`

Esse identificador deve sobreviver a renomeações visuais.

### 4. Política de overrides locais

Precisamos decidir o que o cliente pode alterar sem quebrar o próximo sync.

Recomendação:

- conteúdo das notas é sincronizado do servidor;
- campos protegidos podem ter regra explícita de preservação;
- HTML/CSS do modelo seguem a versão publicada;
- alterações locais não viram fonte de verdade.

## Modelo de dados sugerido

### Novas tabelas

```text
deck_templates
id
deck_id
template_key
template_name
note_type
card_kind
current_version_id
created_at
updated_at
```

```text
deck_template_versions
id
deck_template_id
version_number
fields
field_mapping
front_html
back_html
styling_css
content_hash
status
created_by
created_at
updated_at
```

### Implementacao iniciada

Nesta fase o backend ja passou a persistir:

- `deck_templates`
- `deck_template_versions`

O fluxo de upload grava a estrutura do template separadamente do conteudo da nota.
Isso prepara o terreno para sync incremental de modelo sem acoplar essa logica ao
snapshot bruto do deck.

### Escopo fora desta fase

- midias;
- diff visual de template no cliente;
- resolucao automatica de conflitos locais de template.

### Reuso das tabelas atuais

- `card_versions` continua sendo a unidade imutável de conteúdo;
- `deck_snapshots` continua registrando o upload bruto;
- `deck_cards` continua apontando para a versão ativa;
- `releases` continuam sendo a unidade de distribuição.

## Endpoints sugeridos

### Manifesto

```text
GET /addon/decks/{deck_id}/manifest
```

Passa a entregar:

- deck metadata;
- template versions;
- compatibilidade;
- campos protegidos;
- versão do manifesto.

### Sync incremental

```text
GET /addon/decks/{deck_id}/sync?since_release=0
```

Continua entregando mudanças de cards, mas pode incluir:

- diffs de template;
- marcação de quebra de compatibilidade.

### Sync de modelo

```text
GET /addon/decks/{deck_id}/templates/sync?since_version=0
```

Retorna apenas diffs de modelo.

### Implementacao atual

O backend ja expõe `templates/sync` lendo `deck_template_versions` como fonte
primaria. O endpoint entrega a versao atual de cada template e aceita filtro
por `since_version`, para que o add-on reaplique apenas o que mudou.

## Como isso se compara ao modelo atual

### Nosso modelo atual

- simples;
- funcional;
- suficiente para deck básico com note types estáticos;
- já preserva persistência e rastreabilidade.

### Modelo alvo

- mais próximo de Anki/AnkiHub;
- melhor para decks grandes;
- melhor para mudanças estruturais no template;
- mais previsível para instalação inicial e upgrades incrementais.

## Decisão recomendada

Manter a arquitetura atual como base e evoluir em três passos:

1. introduzir versionamento explícito de template;
2. separar manifesto de conteúdo;
3. adicionar sync incremental de modelo.

Isso preserva compatibilidade com o que já existe e reduz risco de ruptura no
add-on.
