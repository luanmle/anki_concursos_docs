# Importacao CSV Administrativa

## Objetivo

Permitir que administradores e curadores importem novos cartoes em lote sem
informar IDs explicitos no CSV. A plataforma gera os identificadores internos e
usa hash de conteudo para evitar duplicatas.

## Endpoint

```text
POST /card-imports/csv
```

Permissao:

- `admin`
- `curator`

## Payload

```json
{
  "csv_text": "...",
  "delimiter": ",",
  "dry_run": true,
  "default_change_reason": "Importacao CSV"
}
```

Campos:

- `csv_text`: conteudo completo do arquivo CSV em UTF-8.
- `delimiter`: separador do arquivo. Valores usados pela interface: `,` ou `;`.
- `dry_run`: quando `true`, valida sem gravar no banco.
- `default_change_reason`: motivo aplicado a todas as versoes criadas.

## Formato Do CSV

Formato recomendado usando nomes de taxonomia:

```csv
discipline,topic,front_text,back_text,answer_text,explanation_text,tags
Direito Constitucional,Controle de constitucionalidade,Pergunta,Verso,Resposta,Explicacao,tag1 tag2
```

Formato alternativo usando IDs de taxonomia ja existentes:

```csv
discipline_id,topic_id,front_text,back_text,answer_text,explanation_text
00000000-0000-0000-0000-000000000000,11111111-1111-1111-1111-111111111111,Pergunta,Verso,Resposta,Explicacao
```

Colunas obrigatorias de conteudo:

- `front_text`
- `back_text`
- `answer_text`
- `explanation_text`

A taxonomia deve ser informada por um destes pares:

- `discipline` e `topic`
- `discipline_id` e `topic_id`

## IDs Gerados Pela Plataforma

O CSV de entrada nao deve conter:

- `card_id`
- `public_id`
- `card_version_id`
- `canonical_key`

Ao importar, o backend gera:

- `card_id`
- `public_id`
- `card_version_id`
- `canonical_key`
- `content_hash`
- `version_number = 1`

## Regras De Duplicidade

A duplicidade e detectada por conteudo identico:

- se o hash do conteudo ja existir no banco, a linha retorna `duplicate`;
- se o mesmo conteudo aparecer duas vezes no mesmo arquivo, a segunda linha
  retorna `duplicate`;
- duplicatas nao criam novos cartoes.

Isso permite importar CSVs sem IDs explicitos e ainda evitar copias acidentais.

## Resultado

A resposta traz um resumo e um resultado por linha:

```json
{
  "dry_run": true,
  "total_rows": 2,
  "created": 1,
  "duplicates": 1,
  "errors": 0,
  "items": [
    {
      "row_number": 2,
      "status": "ready",
      "message": "Linha valida para importacao.",
      "public_id": null,
      "card_id": null,
      "card_version_id": null
    }
  ]
}
```

Status possiveis por linha:

- `ready`: linha valida em `dry_run`.
- `created`: cartao criado.
- `duplicate`: conteudo ja existente ou repetido no arquivo.
- `error`: linha invalida.

## Fluxo Na Interface

1. O administrador acessa `Cartoes > Importar CSV`.
2. Seleciona o arquivo `.csv`.
3. Mantem `Validar sem gravar no banco` marcado.
4. Corrige linhas com erro, se houver.
5. Desmarca `Validar sem gravar no banco`.
6. Envia novamente para criar os cartoes.

Cartoes importados entram como `needs_review`, preservando o fluxo normal de
revisao, aprovacao e publicacao.

## Observacoes

- A coluna `tags` e aceita no modelo para compatibilidade futura, mas ainda nao
  e persistida no banco.
- A taxonomia precisa existir antes da importacao.
- O CSV de exportacao para Anki continua sendo gerado por release e deve conter
  IDs de versionamento; esta regra vale apenas para CSV de entrada.
