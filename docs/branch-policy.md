# Branch Policy

## Objetivo

Padronizar nomes de branches e o fluxo de deploy para evitar confusao entre
desenvolvimento, distribuicao e ambientes.

## Branches oficiais

### `main`

- Branch principal do repositorio.
- Recebe merges de features, correcoes, documentacao e design.
- Publica o backend.

### `admin-deploy`

- Branch gerada automaticamente a partir de `admin/`.
- Contem apenas o frontend administrativo pronto para deploy.
- Nao deve ser editada manualmente.
- Publica o frontend no Heroku do admin.

### Branches de trabalho

- `feat/<slug>`: funcionalidades.
- `fix/<slug>`: correcoes.
- `docs/<slug>`: documentacao.
- `design/<slug>`: UI, design system e especificacao visual.
- `codex/<slug>`: uso temporario por agente, quando necessario.

## Regras

1. Nao criar branches de deploy manual para frontend.
2. Nao editar `admin-deploy` diretamente.
3. Nao usar `codex/*` como padrao permanente para trabalho humano.
4. Novas branches devem seguir a convenção oficial.
5. Mudancas no frontend administrativo devem ser publicadas por `admin-deploy`.
6. Mudancas no backend devem seguir o fluxo de `main`.
7. O GitHub Actions publica `admin-deploy` quando houver push em `main`
   tocando `admin/**`.
8. O app Heroku do backend acompanha `main`; o app Heroku do admin acompanha
   `admin-deploy`.
9. A validacao do frontend acontece no workflow
   `.github/workflows/publish-admin-deploy.yml`, antes de gerar e publicar
   `admin-deploy`.

## Exemplos

```text
feat/ui-spec-dark-glass
fix/admin-login-redirect
docs/context-adrs-skills
design/ank-5-design-system-tokens
```

## Observacoes

- O nome dos apps Heroku e um detalhe de infraestrutura, nao uma regra de
  branch.
- `flashcards-stagging` e um nome legado de ambiente e deve ser tratado como
  tal.
- Se uma branch nao se encaixar nas categorias acima, ela deve ser tratada
  como excecao e revisada antes de virar padrao.
- O workflow `.github/workflows/publish-admin-deploy.yml` e a fonte de verdade
  para gerar a branch de distribuicao do frontend.
