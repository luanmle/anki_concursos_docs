# CONTEXT.md — Dicionário de domínio

> Leia este arquivo antes de qualquer tarefa. Ele descreve o sistema como ele **realmente é** no código.
> Convenções de branch, deploy e processo estão em AGENTS.md.

---

## O que é este sistema

Backend FastAPI para flashcards versionados de concursos públicos. Produz e distribui cartões de estudo no formato Anki via API REST. Tem dois consumidores principais:

1. **Curadores internos** — criam, revisam e publicam cartões pelo backoffice.
2. **Add-on Anki** — sincroniza cartões publicados no aplicativo Anki do aluno.

Código de produção em `app/`; testes em `tests/`; migrations Alembic em `migrations/versions/`.

---

## Glossário de identidade

### Card

| Campo | Tipo | Regra |
|---|---|---|
| `id` | UUID | Chave primária interna. |
| `public_id` | `String(35)`, formato `AC-<UUID.hex.upper()>` | Identificador público permanente. **Imutável após criação** (evento `prevent_public_card_id_update` em `app/models/entities.py:669`). |
| `canonical_key` | `String(255)`, único | Chave de deduplicação. Gerada pelo serviço; nunca exposta ao aluno. |
| `card_kind` | `basic` \| `cloze` | Define o template Anki. Não muda após criação. |
| `status` | `CardStatus` | Estado de curadoria do cartão (ver abaixo). |
| `current_version_id` | FK → `card_versions.id` | Aponta para a versão mais recente ativa. |

**Formato de `public_id`:** `AC-` seguido de 32 caracteres hexadecimais maiúsculos.
Exemplo: `AC-3F7A2B1C4D5E6F7A8B9C0D1E2F3A4B5C` (`app/models/entities.py:53-54`).

### CardVersion

| Campo | Tipo | Regra |
|---|---|---|
| `id` | UUID | Chave primária interna. |
| `version_number` | Integer ≥ 1 | Sequencial por cartão. Constraint: `uq_card_version_number`. |
| `content_hash` | SHA-256 | Hash do conteúdo canônico (ver abaixo). Impede duplicatas. |
| `status` | `CardVersionStatus` | Estado do ciclo de vida da versão (ver abaixo). |
| `front_text` | Text | Frente do cartão. Obrigatório e não-vazio. |
| `back_text` | Text | Verso do cartão. |
| `answer_text` | Text | Resposta. |
| `explanation_text` | Text | Explicação. |

**Regra de imutabilidade:** versão com `status=published` **nunca é alterada nem excluída** — eventos SQLAlchemy `prevent_published_version_update` e `prevent_published_version_delete` levantam `ValueError` (`app/models/entities.py:724-741`). PostgreSQL aplica a mesma restrição via trigger `trg_card_versions_immutable`.

**Content hash (cartão manual):** `SHA-256(JSON({card_kind, front_text, back_text, answer_text, explanation_text}))` — `app/services/cards.py:42-62`.
**Content hash (upload Anki):** hash mais rico, inclui `fields`, `note_type`, `template_name`, `tags`, definição do template — `app/services/decks.py:1113-1135`.

### Release

| Campo | Tipo | Regra |
|---|---|---|
| `release_number` | Integer ≥ 1 | Sequencial por deck. Constraint: `uq_release_deck_number`. |
| `items` | list[`ReleaseItem`] | Cada item registra `action + card_id + card_version_id`. |

**Release e ReleaseItem são imutáveis após criação** — eventos `prevent_release_mutation` e `prevent_release_item_mutation` em `app/models/entities.py:744-755`.

---

## Enums de status

### `CardStatus` (`app/models/enums.py:17-25`)
`generated → needs_review → approved → published → reported / revised / deprecated / archived`

### `CardVersionStatus` (`app/models/enums.py:28-35`)
`generated → needs_review → approved → published`
Também: `rejected`, `superseded`

### `DeckStatus` (`app/models/enums.py:42-45`)
`draft → published → archived`

### `ReleaseAction` (`app/models/enums.py:48-52`)
`added`, `updated`, `removed`, `deprecated`

---

## Papéis e autenticação

### Papéis (`app/models/enums.py:97-100`)

| Papel | Código | Permissões principais |
|---|---|---|
| `admin` | `UserRole.ADMIN` | Tudo. Pode gerir usuários. |
| `curator` | `UserRole.CURATOR` | Criar e editar cartões, gerenciar decks. |
| `reviewer` | `UserRole.REVIEWER` | Publicar releases, revisar reports. |
| `student` | `UserRole.STUDENT` | Assinar decks, sincronizar via add-on. |

### Guards (`app/core/security.py:240-244`)

| Guard | Papéis aceitos |
|---|---|
| `require_admin` | `admin` |
| `require_curator` | `admin, curator` |
| `require_reviewer` | `admin, reviewer` |
| `require_staff` | `admin, curator, reviewer` |
| `require_authenticated_user` | qualquer papel ativo |

### Fluxo de autenticação

1. `POST /auth/token` (email + password) → retorna `access_token` (JWT HS256) + `refresh_token`.
2. Bearer token enviado no header `Authorization: Bearer <token>`.
3. JWT contém: `sub` (user UUID), `email`, `role`, `ver` (credential_version), `token_type`, `iat`, `exp`.
4. Incrementar `user.credential_version` invalida todos os tokens emitidos anteriormente.
5. **Chave legada:** `X-Admin-API-Key` é aceito como alternativa quando `allow_legacy_admin_api_key=true` na configuração — concede papel `admin` sem banco (`app/core/security.py:219-229`).
6. Implementação customizada HS256 sem biblioteca externa (`app/core/security.py:69-95`).

---

## Fluxo: cadastro → revisão → versão → release → consumo

```
[Curador]
  POST /cards          → Card(status=needs_review) + CardVersion(v1, status=needs_review)
  POST /cards/{id}/versions/{vid}/approve  → version=approved, card=approved
  POST /cards/{id}/versions/{vid}/publish  → version=published, card=published
                                           (exige version=approved antes)

[Revisor]
  POST /decks/{id}/publish-release → Release(N) criada com ReleaseItems
                                   → deck.status = published

[Add-on/Aluno]
  POST /addon/decks/upload         → sobe baralho Anki nativo (qualquer usuário autenticado)
  GET  /addon/decks/{id}/sync      → consome delta desde since_release
  GET  /addon/decks/{id}/manifest  → descobre note_types e field_mapping

[Qualquer usuário]
  POST /reports                    → abre CardReport + ReviewTask(pending)

[Admin/Revisor]
  POST /admin/reports/{id}/review  → fecha ReviewTask
    decision=converted_to_new_version → nova CardVersion(status=needs_review) entra em curadoria
    decision=rejected / duplicate   → report fechado sem nova versão
```

---

## Contrato de sync exato

### Endpoint staff (`GET /decks/{deck_id}/sync`)

- Requer `require_staff` (admin, curator, reviewer).
- Parâmetro: `since_release: int = 0` (0 = full sync).
- Retorna `DeckSyncResponse`:

```json
{
  "deck_id": "<uuid>",
  "from_release": 0,
  "to_release": 5,
  "has_changes": true,
  "changes": [
    {
      "release_id": "<uuid>",
      "release_number": 3,
      "published_at": "<ISO8601+UTC>",
      "action": "added | updated | removed | deprecated",
      "card_id": "<uuid>",
      "public_id": "AC-...",
      "old_card_version_id": "<uuid> | null",
      "new_card_version_id": "<uuid> | null"
    }
  ]
}
```

- `new_card_version_id` é `null` para `removed` e `deprecated` (`app/services/decks.py:296-305`).

### Endpoint add-on (`GET /addon/decks/{deck_id}/sync`)

- Requer `require_authenticated_user` + assinatura ativa no deck.
- Parâmetros: `since_release: int = 0`, `page`, `page_size` (opcional, máx 1000).
- Quando `since_release=0`: retorna snapshot completo (todos os cartões ativos com `action=added`).
- Quando `since_release>0`: retorna delta incremental.
- Cada mudança inclui também `card_kind`, `note_type`, `fields`, `template`, `tags`.

---

## Tabelas fora de escopo da API pública

As tabelas abaixo existem no schema (migrations aplicadas) mas **não possuem endpoints REST**:

| Tabela | Propósito |
|---|---|
| `raw_documents` | Documentos brutos enviados para extração de questões. |
| `exams` | Concursos extraídos dos documentos. |
| `questions` | Questões extraídas; podem ser origem de `Card`. |
| `question_alternatives` | Alternativas de cada questão. |
| `processing_jobs` | Fila de jobs assíncronos de processamento. |

Código em `app/models/entities.py` mas sem rotas em `app/api/routes/`.

---

## Templates Anki

| `card_kind` | Note type | Campos |
|---|---|---|
| `basic` | `Anki Concursos Basic` | Front, Back, Answer, Explanation |
| `cloze` | `Anki Concursos Cloze` | Text, Extra, Answer, Explanation |

Cloze exige marcação `{{c1::...}}` no `front_text` (`app/services/cards.py:35`).

---

## Configuração de testes

- **Comando padrão:** `pytest` (config em `pyproject.toml:46-51`).
- **Banco de testes:** SQLite em memória (`conftest.py:15-29`); foreign keys habilitadas via PRAGMA.
- **Autenticação nos testes:** header `X-Admin-API-Key: development-admin-key` (legacy admin, `conftest.py:44`).
- **Testes PostgreSQL:** marcados com `@pytest.mark.postgres`; requerem `TEST_DATABASE_URL` (ex.: `postgresql+psycopg://...`). Rodar com `pytest -m postgres`.
