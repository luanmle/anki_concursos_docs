# Tag and Release Policy

## Objetivo

Definir quando criar tags e como registrar releases do projeto sem confundir
marcos de produto, pipeline e deploy.

## Princípios

1. Tags representam marcos estáveis do repositório.
2. Tags não substituem branches de deploy.
3. Tags devem apontar para `main`.
4. Nunca taguear `admin-deploy`, porque ela e uma branch derivada e mutável por
   regeneration.
5. Tags devem ser poucas e significativas.

## Esquema de versionamento

Usar SemVer no formato `vMAJOR.MINOR.PATCH`.

### `MAJOR`

- Mudanças incompatíveis de arquitetura, contrato ou fluxo operacional.
- Exemplo: alteração profunda do modelo de releases, sync ou autenticação.

### `MINOR`

- Mudanças funcionais relevantes e compatíveis.
- Exemplo: novo fluxo de curadoria, nova seção do admin, nova integração
  operacional.

### `PATCH`

- Correções e ajustes sem mudança de contrato.
- Exemplo: correção de bug, ajuste de CI, documentação operacional ou fix de
  deploy.

## Quando criar uma tag

Criar tag quando houver um marco que mereça referência fixa:

- mudança estável no pipeline de deploy;
- entrega funcional importante do backend;
- entrega funcional importante do frontend/admin;
- correção crítica que precise de rollback fácil;
- fechamento de um ciclo de release relevante.

## O que não taguear

- commits intermediários de feature;
- branches temporárias de agente;
- `admin-deploy`;
- commits puramente experimentais;
- mudanças sem valor de referência para rollback ou auditoria.

## Processo sugerido

1. Merge na `main`.
2. Validação do Heroku e do CI.
3. Criar a tag anotada no commit da `main`.
4. Escrever release notes curtas com:
   - o que mudou;
   - impacto no backend;
   - impacto no frontend/admin;
   - impacto no deploy/pipeline.
5. Publicar a release no GitHub, se desejar rastreabilidade visual.

## Convenção de nomes

Exemplos:

```text
v0.1.0
v0.1.1
v0.2.0
v1.0.0
```

## Sugestão de uso neste projeto

- `v0.x` enquanto a arquitetura e o pipeline ainda estão evoluindo.
- `v1.0.0` quando backend, admin e deploy estiverem estabilizados.
- Tagger apenas marcos aprovados por merge em `main`.

## Release notes

As notas de release devem ser curtas e objetivas:

- `Backend`
- `Frontend/Admin`
- `Pipeline/Deploy`
- `Docs/Policy`

Exemplo:

```text
v0.2.0
- Backend: ajuste no predeploy e no fluxo de release.
- Frontend/Admin: validação do admin-deploy.
- Pipeline/Deploy: CI ignora admin-deploy; publish do frontend continua no main.
- Docs/Policy: política de branches e tags formalizada.
```

## Observações

- A tag deve sempre corresponder a um estado que possa ser reconstruído a
  partir da `main`.
- Se um release do Heroku precisar ser auditado, a tag deve apontar para o
  commit exato que gerou aquele estado.
- Se houver dúvida, prefira não criar tag.
