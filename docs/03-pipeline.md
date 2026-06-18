# Pipeline De Conteudo

## Fluxo Editorial

```text
cartao -> versao -> aprovacao -> publicacao -> deck -> release -> CSV/sync
```

## Fluxo Atual Do Add-on

O add-on nao envia notas soltas. Ele envia um pacote completo do deck com:

- templates;
- html e css do modelo;
- campos nativos;
- notas;
- tags;
- subdeck path;
- identificadores de origem quando existirem.

## Fluxo Do Administrador

```text
cartao -> nova versao -> revisao -> aprovacao -> publicacao -> deck -> release
```

O frontend administrativo nao edita versao publicada. Toda mudanca gera nova
versao.

## Exportacao

- CSV e sempre derivado de uma release;
- sync incremental usa releases sucessivas;
- deck continua sendo a unidade de assinatura;
- `since_release=0` representa instalacao sem estado local.

## Observabilidade

Operacoes criticas devem ser monitoradas no backend com Honeybadger:

- upload de `.apkg`;
- importacao CSV;
- sync de decks;
- publicacao;
- migrations/predeploy.
