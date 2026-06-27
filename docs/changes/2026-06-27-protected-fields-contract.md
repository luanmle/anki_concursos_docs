# Campos protegidos no contrato do add-on

- Data: 2026-06-27
- Área: backend / frontend admin / contrato do add-on
- Tipo: implementação

## Resumo

A plataforma agora persiste, expõe e permite editar `protected_fields` por template de baralho Anki.

## Contrato

- Upload de baralho aceita `templates[].protected_fields`.
- Manifesto `GET /addon/decks/{deck_id}/manifest` retorna:
  - `protected_fields` no nível principal, herdado do template primário;
  - `templates[].protected_fields`;
  - `templates[].template_id`.
- Sync de templates `GET /addon/decks/{deck_id}/templates/sync` retorna `protected_fields` em cada versão.
- Novo endpoint:
  - `PATCH /addon/decks/{deck_id}/templates/{template_id}/protected-fields`
  - Body: `{ "protected_fields": ["Front", "Explanation"] }`
  - Permissão: admin/curator.

## Backend

- `deck_template_versions` ganhou coluna JSON `protected_fields`.
- Alteração de campos protegidos cria nova versão de template, com novo `content_hash`.
- Backend valida se todos os campos protegidos existem em `fields` do template.

## Frontend

- Página do add-on ganhou seção `Campos protegidos`.
- Cada template mostra checkboxes dos campos disponíveis.
- Botão `Salvar proteção` envia o novo contrato ao backend.

## Verificação

Comandos:

```bash
.venv/bin/python -m compileall app
.venv/bin/python -m pytest
cd admin && npm run build
```

Resultado:

- Backend: `110 passed, 2 skipped`.
- Frontend: build concluído.
