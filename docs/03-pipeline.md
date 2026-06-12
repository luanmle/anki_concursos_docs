# Fluxo de Cartões e Exportação

## Objetivo

Transformar conteúdo cadastrado ou importado em releases versionadas e arquivos
CSV reproduzíveis para o Anki.

## Fluxo principal

```text
1. Cadastrar ou importar cartão
2. Validar taxonomia e conteúdo
3. Criar card e card_version
4. Revisar e aprovar
5. Publicar versão
6. Associar cartão ao deck
7. Criar release
8. Gerar CSV da release
```

## Fluxo pela interface administrativa

A interface planejada deve representar o fluxo existente da API, sem criar um
segundo conjunto de regras de negócio:

```text
Cadastrar cartão
→ revisar conteúdo
→ aprovar e publicar versão
→ adicionar ao deck
→ publicar release
→ baixar CSV
```

Ao modificar um cartão, a interface deve chamar a operação de criação de nova
versão. Não deve apresentar uma ação que sobrescreva uma versão publicada.

```text
Abrir cartão
→ consultar versão atual e histórico
→ informar novo conteúdo e change_reason
→ criar nova card_version em needs_review
→ aprovar e publicar
→ atualizar explicitamente o vínculo no deck
→ publicar nova release
→ baixar novo CSV
```

O download deve usar o endpoint de exportação de uma release específica. A
interface não deve montar o CSV no navegador.

## Cadastro

A criação inicial deve ocorrer em uma única transação:

- criar `cards`;
- criar `card_versions` com `version_number = 1`;
- gerar `public_id` único;
- definir `cards.current_version_id`;
- registrar `change_reason`;
- iniciar em estado não publicado.

No MVP 2, cartão e versão inicial usam `needs_review`. A versão 1 é definida
como versão atual para permitir consulta administrativa.

## Nova versão

Uma alteração pedagógica deve:

- preservar o `card_id`;
- criar nova `card_version`;
- incrementar `version_number`;
- preservar a versão anterior;
- atualizar `current_version_id` somente quando a nova versão for aprovada ou
  publicada.

No MVP 2, novas versões nascem em `needs_review` e não substituem a versão
atual.

Se a versão atual estiver publicada, criar uma nova versão em revisão não
altera o status público nem remove a versão atual de circulação.

## Aprovação e publicação

- aprovação seleciona a versão revisada como atual e marca cartão e versão como
  `approved`;
- publicação exige versão `approved`;
- publicação marca cartão e versão como `published`;
- versões publicadas anteriores permanecem preservadas;
- decks não mudam automaticamente de versão: a atualização deve ser aplicada
  explicitamente ao vínculo do deck.

## Release

A publicação de uma release deve:

- ser transacional;
- registrar apenas versões publicadas;
- comparar o estado atual do deck com a release anterior;
- gerar `release_items` com ações explícitas;
- tornar a release imutável após a publicação.

O delta é calculado comparando o estado ativo do deck com o estado reconstruído
pelas releases anteriores.

## Exportação CSV

O CSV deve ser gerado a partir de uma release específica, com ordenação e
codificação determinísticas.

Regras mínimas:

- UTF-8;
- cabeçalho explícito;
- escape correto de delimitadores, aspas e quebras de linha;
- uma linha por cartão ativo no snapshot da release;
- inclusão obrigatória de `card_id` e `card_version_id`;
- inclusão obrigatória de `public_id` para identificação pelo usuário;
- conteúdo obtido da versão registrada na release;
- mesma release e mesma configuração produzem o mesmo arquivo.

O snapshot é reconstruído reproduzindo os deltas desde a primeira release até
a release solicitada. Ações `removed` e `deprecated` retiram o cartão do
snapshot exportado, mas permanecem preservadas no histórico.

Contrato implementado:

```text
GET /decks/{deck_id}/releases/{release_id}/export.csv
```

Configurações controladas:

```text
delimiter=comma|semicolon|tab
include_tags=true|false
```

As tags padrão usam IDs estáveis:

```text
deck::<deck_id> card::<public_id>
```

O arquivo é ordenado por `public_id`. A resposta inclui
`X-Content-SHA256`, `X-Row-Count` e `X-Release-Number`.

Tags por disciplina ou assunto só devem ser adicionadas quando a classificação
também for versionada ou registrada no snapshot da release. Isso evita alterar
retroativamente o hash de uma exportação histórica.

Para importação inicial, o CSV pode representar o snapshot completo do deck.
Para integrações futuras, a API de sync continua sendo o mecanismo correto para
consultar deltas entre releases.

## Curadoria por report

```text
Usuário reporta versão publicada
→ cria card_report
→ cria review_task pendente
→ administrador revisa
→ rejeita, marca duplicidade ou converte em nova versão
```

Regras:

- report aponta para a versão exata analisada pelo usuário;
- rejeição e duplicidade não alteram cartões ou versões;
- conversão exige os quatro campos completos e `change_reason`;
- report `outdated_law` exige atestação de revisão de evidência;
- a nova versão nasce em `needs_review`;
- a versão publicada reportada permanece imutável e consultável;
- `cards.current_version_id` permanece apontando para a versão publicada;
- aprovação e publicação da correção usam o fluxo normal já existente;
- atualização do deck continua sendo explícita.

Endpoints:

```text
POST /reports
GET /admin/reports
GET /admin/reports/{report_id}
POST /admin/reports/{report_id}/review
```

## Jobs

`processing_jobs` pode registrar exportações grandes ou operações de publicação,
mas filas assíncronas não são obrigatórias no primeiro incremento.
