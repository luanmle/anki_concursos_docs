# Contexto Ativo

**Atualizado:** 2026-06-27
**Branch:** `codex/publish-admin`
**Status:** concluído, pronto para commit e deploy

## O que está sendo trabalhado

Campos protegidos no contrato do add-on Anki, com persistência no backend e UI
administrativa para configurar `protected_fields` por template.

## Últimas mudanças

- `deck_template_versions` ganhou coluna JSON `protected_fields` via migration
  `20260627_0016_template_protected_fields.py`.
- Upload de baralho aceita `templates[].protected_fields`.
- Manifesto do add-on retorna `protected_fields`, `templates[].protected_fields`
  e `templates[].template_id`.
- Template sync retorna `protected_fields` por versão de template.
- Novo endpoint curator/admin:
  `PATCH /addon/decks/{deck_id}/templates/{template_id}/protected-fields`.
- Página admin do add-on ganhou editor de campos protegidos com checkboxes por
  template e botão `Salvar proteção`.
- Documentação adicionada em
  `docs/changes/2026-06-27-protected-fields-contract.md`.

## Verificação

- `.venv/bin/python -m compileall app` — passou.
- `.venv/bin/python -m pytest` — `110 passed, 2 skipped`.
- `cd admin && npm run build` — passou.
- `git diff --check` — passou.

## Próximos passos

- [ ] Commitar somente os arquivos desta implementação.
- [ ] Levar o commit para `main` e fazer push.
- [ ] Confirmar workflow que gera `admin-deploy`.
- [ ] Confirmar releases Heroku do backend e frontend após deploy.

## Decisões recentes

- **Contrato `protected_fields`** — nome mantido para compatibilidade direta com
  o add-on já preparado.
- **Proteção versionada no template** — alteração cria nova versão de template,
  mantendo histórico e novo `content_hash`.
- **Escrita restrita a curator/admin** — assinantes consomem o contrato, mas não
  alteram regra de preservação local.

## O que NÃO tocar agora

- `admin-deploy` manualmente; essa branch deve ser gerada pelo workflow.
- Arquivos/untracked antigos fora desta implementação.
