# API and Database Map

> Gerado em: 2026-06-22  
> Fonte: análise estática de `app/`, `admin/src/`, `migrations/`

---

## Sumário

1. [Tabela de endpoints](#1-tabela-de-endpoints)
2. [Detalhe por rota](#2-detalhe-por-rota)
3. [Modelos SQLAlchemy e tabelas](#3-modelos-sqlalchemy-e-tabelas)
4. [Schemas Pydantic](#4-schemas-pydantic)
5. [Histórico de migrations](#5-histórico-de-migrations)
6. [Mapa de relacionamentos](#6-mapa-de-relacionamentos)
7. [Seção por tela do frontend](#7-seção-por-tela-do-frontend)
8. [Contrato do add-on Anki](#8-contrato-do-add-on-anki)
9. [Inconsistências encontradas](#9-inconsistências-encontradas)

---

## 1. Tabela de endpoints

| # | Método | Rota | Arquivo | Função | Auth | Router |
|---|--------|------|---------|--------|------|--------|
| 1 | GET | `/` | `routes/health.py` | `root` | nenhuma | `health_router` |
| 2 | GET | `/health` | `routes/health.py` | `health_check` | nenhuma | `health_router` |
| 3 | GET | `/ready` | `routes/health.py` | `readiness_check` | nenhuma | `health_router` |
| 4 | POST | `/auth/token` | `routes/auth.py` | `login` | nenhuma + rate limit | `auth_router` |
| 5 | POST | `/auth/refresh` | `routes/auth.py` | `refresh_token` | nenhuma | `auth_router` |
| 6 | GET | `/auth/me` | `routes/auth.py` | `get_current_user` | qualquer usuário autenticado | `auth_router` |
| 7 | POST | `/admin/users` | `routes/auth.py` | `create_user` | admin | `admin_users_router` |
| 8 | GET | `/admin/users` | `routes/auth.py` | `list_users` | admin | `admin_users_router` |
| 9 | PATCH | `/admin/users/{user_id}` | `routes/auth.py` | `update_user` | admin | `admin_users_router` |
| 10 | POST | `/admin/users/{user_id}/reset-password` | `routes/auth.py` | `reset_user_password` | admin | `admin_users_router` |
| 11 | GET | `/disciplines` | `routes/taxonomy.py` | `list_disciplines` | staff (admin/curator/reviewer) | `taxonomy_router` |
| 12 | GET | `/disciplines/{discipline_id}/topics` | `routes/taxonomy.py` | `list_topics` | staff | `taxonomy_router` |
| 13 | POST | `/cards` | `routes/cards.py` | `create_card` | curator (admin/curator) | `cards_router` |
| 14 | GET | `/cards` | `routes/cards.py` | `list_cards` | staff | `cards_router` |
| 15 | GET | `/cards/public/{public_id}` | `routes/cards.py` | `get_public_card` | nenhuma | `cards_router` |
| 16 | GET | `/cards/{card_id}` | `routes/cards.py` | `get_card` | staff | `cards_router` |
| 17 | POST | `/cards/{card_id}/versions` | `routes/cards.py` | `create_card_version` | curator | `cards_router` |
| 18 | POST | `/cards/{card_id}/versions/{version_id}/approve` | `routes/cards.py` | `approve_card_version` | reviewer (admin/reviewer) | `cards_router` |
| 19 | POST | `/cards/{card_id}/versions/{version_id}/publish` | `routes/cards.py` | `publish_card_version` | reviewer | `cards_router` |
| 20 | POST | `/card-imports/csv` | `routes/cards.py` | `import_cards_csv` | curator | `card_imports_router` |
| 21 | POST | `/decks` | `routes/decks.py` | `create_deck` | curator | `decks_router` |
| 22 | GET | `/decks` | `routes/decks.py` | `list_decks` | staff | `decks_router` |
| 23 | GET | `/decks/{deck_id}` | `routes/decks.py` | `get_deck` | staff | `decks_router` |
| 24 | POST | `/decks/{deck_id}/cards` | `routes/decks.py` | `add_card_to_deck` | curator | `decks_router` |
| 25 | POST | `/decks/{deck_id}/cards/{card_id}/remove` | `routes/decks.py` | `remove_card_from_deck` | curator | `decks_router` |
| 26 | POST | `/decks/{deck_id}/publish-release` | `routes/decks.py` | `publish_release` | reviewer | `decks_router` |
| 27 | GET | `/decks/{deck_id}/releases` | `routes/decks.py` | `list_releases` | staff | `decks_router` |
| 28 | GET | `/decks/{deck_id}/sync` | `routes/decks.py` | `sync_deck` | staff | `decks_router` |
| 29 | GET | `/decks/{deck_id}/releases/{release_id}/export.csv` | `routes/decks.py` | `export_release_csv` | staff | `decks_router` |
| 30 | GET | `/addon/status` | `routes/addon.py` | `get_addon_status` | nenhuma | `addon_router` |
| 31 | GET | `/addon/decks/{deck_id}/manifest` | `routes/addon.py` | `get_anki_deck_manifest` | qualquer autenticado | `addon_router` |
| 32 | GET | `/addon/decks/{deck_id}/sync` | `routes/addon.py` | `sync_anki_deck` | qualquer autenticado | `addon_router` |
| 33 | GET | `/addon/decks/{deck_id}/templates/sync` | `routes/addon.py` | `sync_anki_deck_templates` | qualquer autenticado | `addon_router` |
| 34 | POST | `/addon/decks/upload` | `routes/addon.py` | `upload_anki_deck` | qualquer autenticado | `addon_router` |
| 35 | GET | `/subscriptions/decks` | `routes/subscriptions.py` | `list_subscribable_decks` | qualquer autenticado | `subscriptions_router` |
| 36 | GET | `/subscriptions` | `routes/subscriptions.py` | `list_subscriptions` | qualquer autenticado | `subscriptions_router` |
| 37 | POST | `/subscriptions/{deck_id}` | `routes/subscriptions.py` | `subscribe_to_deck` | qualquer autenticado | `subscriptions_router` |
| 38 | POST | `/subscriptions/{deck_id}/cancel` | `routes/subscriptions.py` | `cancel_deck_subscription` | qualquer autenticado | `subscriptions_router` |
| 39 | POST | `/reports` | `routes/reports.py` | `create_report` | nenhuma + rate limit | `reports_router` |
| 40 | GET | `/admin/reports` | `routes/reports.py` | `list_reports` | reviewer | `admin_reports_router` |
| 41 | GET | `/admin/reports/{report_id}` | `routes/reports.py` | `get_report` | reviewer | `admin_reports_router` |
| 42 | POST | `/admin/reports/{report_id}/review` | `routes/reports.py` | `review_report` | reviewer | `admin_reports_router` |

**Legenda de papéis:**
- `admin` → só `UserRole.ADMIN`
- `curator` → `admin` + `curator`
- `reviewer` → `admin` + `reviewer`
- `staff` → `admin` + `curator` + `reviewer`
- `qualquer autenticado` → qualquer role válida (inclui `student`)

---

## 2. Detalhe por rota

### Health

#### `GET /` — root
- **Arquivo:** `app/api/routes/health.py:13`
- **Autenticação:** nenhuma
- **Resposta:** `{"service": str, "status": str, "health": str, "readiness": str}`
- **Tabelas:** nenhuma
- **Serviços:** nenhum

#### `GET /health` — health_check
- **Arquivo:** `app/api/routes/health.py:20`
- **Autenticação:** nenhuma
- **Resposta:** `{"status": "ok"}`
- **Tabelas:** nenhuma

#### `GET /ready` — readiness_check
- **Arquivo:** `app/api/routes/health.py:25`
- **Autenticação:** nenhuma
- **Resposta:** `{"status": "ready", "database": "ok"}` ou 503
- **Tabelas:** executa `SELECT 1` (verifica conectividade)

---

### Auth

#### `POST /auth/token` — login
- **Arquivo:** `app/api/routes/auth.py:44`
- **Autenticação:** nenhuma; rate-limit via `limit_login_attempts`
- **Entrada:** `LoginRequest` — `{email, password}`
- **Saída:** `TokenResponse` — `{access_token, token_type, expires_in, refresh_token, user: UserResponse}`
- **Tabelas:** `users`
- **Serviços:** `AuthService.authenticate`, `create_access_token`, `create_refresh_token`

#### `POST /auth/refresh` — refresh_token
- **Arquivo:** `app/api/routes/auth.py:58`
- **Autenticação:** nenhuma (token de refresh no body)
- **Entrada:** `RefreshTokenRequest` — `{refresh_token}`
- **Saída:** `TokenResponse`
- **Tabelas:** `users` (valida `credential_version`)
- **Serviços:** `AuthService.get_user`, `decode_refresh_token`

#### `GET /auth/me` — get_current_user
- **Arquivo:** `app/api/routes/auth.py:78`
- **Autenticação:** Bearer token (qualquer role)
- **Saída:** `UserResponse`
- **Tabelas:** `users`

---

### Admin Users

#### `POST /admin/users` — create_user
- **Arquivo:** `app/api/routes/auth.py:85`
- **Autenticação:** admin
- **Entrada:** `UserCreateRequest` — `{email, password, display_name, role}`
- **Saída:** `UserResponse` (201)
- **Tabelas:** `users`
- **Serviços:** `AuthService.create_user`

#### `GET /admin/users` — list_users
- **Arquivo:** `app/api/routes/auth.py:96`
- **Autenticação:** admin
- **Query params:** `page`, `page_size`
- **Saída:** `UserListResponse` — `{items: [UserResponse], page, page_size, total, pages}`
- **Tabelas:** `users`
- **Serviços:** `AuthService.list_users`

#### `PATCH /admin/users/{user_id}` — update_user
- **Arquivo:** `app/api/routes/auth.py:104`
- **Autenticação:** admin
- **Entrada:** `UserUpdateRequest` — `{display_name?, role?, is_active?}` (ao menos 1 campo)
- **Saída:** `UserResponse`
- **Tabelas:** `users`
- **Serviços:** `AuthService.update_user`

#### `POST /admin/users/{user_id}/reset-password` — reset_user_password
- **Arquivo:** `app/api/routes/auth.py:118`
- **Autenticação:** admin
- **Entrada:** `PasswordResetRequest` — `{password}` (mín. 12 chars)
- **Saída:** `UserResponse`
- **Tabelas:** `users`
- **Serviços:** `AuthService.reset_password`

---

### Taxonomy

#### `GET /disciplines` — list_disciplines
- **Arquivo:** `app/api/routes/taxonomy.py:23`
- **Autenticação:** staff
- **Saída:** `DisciplineListResponse` — `{items: [{discipline_id, name, parent_id}], total}`
- **Tabelas:** `disciplines`
- **Serviços:** `TaxonomyService.list_disciplines`

#### `GET /disciplines/{discipline_id}/topics` — list_topics
- **Arquivo:** `app/api/routes/taxonomy.py:30`
- **Autenticação:** staff
- **Saída:** `TopicListResponse` — `{discipline: DisciplineResponse, items: [{topic_id, discipline_id, name, parent_id}], total}`
- **Tabelas:** `topics`, `disciplines`
- **Serviços:** `TaxonomyService.list_topics`

---

### Cards

#### `POST /cards` — create_card
- **Arquivo:** `app/api/routes/cards.py:33`
- **Autenticação:** curator
- **Entrada:** `CardCreateRequest` — `{card_kind, front_text, back_text, answer_text, explanation_text, canonical_key, discipline_id?, topic_id?, change_reason, created_by}`
- **Saída:** `CardDetailResponse` (201)
- **Tabelas:** `cards`, `card_versions`, `disciplines`, `topics`
- **Serviços:** `CardService.create_card`

#### `GET /cards` — list_cards
- **Arquivo:** `app/api/routes/cards.py:47`
- **Autenticação:** staff
- **Query params:** `page`, `page_size`, `discipline_id`, `topic_id`, `status`, `public_id`
- **Saída:** `CardListResponse` — `{items: [CardSummaryResponse], page, page_size, total, pages}`
- **Tabelas:** `cards`, `card_versions`, `disciplines`, `topics`
- **Serviços:** `CardService.list_cards`

#### `GET /cards/public/{public_id}` — get_public_card
- **Arquivo:** `app/api/routes/cards.py:70`
- **Autenticação:** nenhuma (público)
- **Saída:** `CardSummaryResponse`
- **Tabelas:** `cards`, `card_versions` (filtra `status=published`)
- **Serviços:** `CardService.get_public_card`

#### `GET /cards/{card_id}` — get_card
- **Arquivo:** `app/api/routes/cards.py:78`
- **Autenticação:** staff
- **Saída:** `CardDetailResponse` — inclui `versions: [CardVersionResponse]`
- **Tabelas:** `cards`, `card_versions`
- **Serviços:** `CardService.get_card`

#### `POST /cards/{card_id}/versions` — create_card_version
- **Arquivo:** `app/api/routes/cards.py:88`
- **Autenticação:** curator
- **Entrada:** `CardVersionCreateRequest` — `{card_kind, front_text, back_text, answer_text, explanation_text, change_reason, created_by}`
- **Saída:** `CardVersionResponse` (201)
- **Tabelas:** `cards`, `card_versions`
- **Serviços:** `CardService.create_version`

#### `POST /cards/{card_id}/versions/{version_id}/approve` — approve_card_version
- **Arquivo:** `app/api/routes/cards.py:102`
- **Autenticação:** reviewer
- **Saída:** `CardDetailResponse`
- **Tabelas:** `cards`, `card_versions`
- **Serviços:** `CardService.approve_version`

#### `POST /cards/{card_id}/versions/{version_id}/publish` — publish_card_version
- **Arquivo:** `app/api/routes/cards.py:116`
- **Autenticação:** reviewer
- **Saída:** `CardDetailResponse`
- **Tabelas:** `cards`, `card_versions`
- **Serviços:** `CardService.publish_version`

---

### Card Imports

#### `POST /card-imports/csv` — import_cards_csv
- **Arquivo:** `app/api/routes/cards.py:42`
- **Autenticação:** curator
- **Entrada:** `CardCsvImportRequest` — `{csv_text, delimiter, dry_run, default_change_reason}`
- **Saída:** `CardCsvImportResponse` — `{dry_run, total_rows, created, duplicates, errors, items: [CardCsvImportRowResult]}`
- **Tabelas:** `cards`, `card_versions`, `disciplines`, `topics`
- **Serviços:** `CardService.import_csv`

---

### Decks

#### `POST /decks` — create_deck
- **Arquivo:** `app/api/routes/decks.py:29`
- **Autenticação:** curator
- **Entrada:** `DeckCreateRequest` — `{name, discipline_id?, description?}`
- **Saída:** `DeckResponse` (201)
- **Tabelas:** `decks`
- **Serviços:** `DeckService.create_deck`

#### `GET /decks` — list_decks
- **Arquivo:** `app/api/routes/decks.py:37`
- **Autenticação:** staff
- **Query params:** `page`, `page_size`
- **Saída:** `DeckListResponse` — `{items: [DeckSummaryResponse], page, page_size, total, pages}`
- **Tabelas:** `decks`, `deck_cards`, `card_versions`, `disciplines`
- **Serviços:** `DeckService.list_decks`

#### `GET /decks/{deck_id}` — get_deck
- **Arquivo:** `app/api/routes/decks.py:46`
- **Autenticação:** staff
- **Saída:** `DeckResponse` — `{deck_id, name, discipline_id, description, status, cards: [DeckCardResponse], created_at, updated_at}`
- **Tabelas:** `decks`, `deck_cards`, `card_versions`, `cards`
- **Serviços:** `DeckService.get_deck`

#### `POST /decks/{deck_id}/cards` — add_card_to_deck
- **Arquivo:** `app/api/routes/decks.py:55`
- **Autenticação:** curator
- **Entrada:** `DeckCardAddRequest` — `{card_id}`
- **Saída:** `DeckResponse`
- **Tabelas:** `decks`, `deck_cards`, `cards`, `card_versions`
- **Serviços:** `DeckService.add_card`

#### `POST /decks/{deck_id}/cards/{card_id}/remove` — remove_card_from_deck
- **Arquivo:** `app/api/routes/decks.py:66`
- **Autenticação:** curator
- **Entrada:** `DeckCardRemoveRequest` — `{action: "removed" | "deprecated"}`
- **Saída:** `DeckResponse`
- **Tabelas:** `decks`, `deck_cards`
- **Serviços:** `DeckService.remove_card`

#### `POST /decks/{deck_id}/publish-release` — publish_release
- **Arquivo:** `app/api/routes/decks.py:78`
- **Autenticação:** reviewer
- **Entrada:** `ReleasePublishRequest` — `{description?}`
- **Saída:** `ReleaseResponse` (201)
- **Tabelas:** `decks`, `deck_cards`, `releases`, `release_items`, `cards`, `card_versions`
- **Serviços:** `DeckService.publish_release`

#### `GET /decks/{deck_id}/releases` — list_releases
- **Arquivo:** `app/api/routes/decks.py:91`
- **Autenticação:** staff
- **Query params:** `page`, `page_size`
- **Saída:** `ReleaseListResponse` — `{items: [ReleaseSummaryResponse], page, page_size, total, pages, latest_release}`
- **Tabelas:** `releases`, `release_items`
- **Serviços:** `DeckService.list_releases`

#### `GET /decks/{deck_id}/sync` — sync_deck
- **Arquivo:** `app/api/routes/decks.py:103`
- **Autenticação:** staff
- **Query params:** `since_release` (default 0)
- **Saída:** `DeckSyncResponse` — `{deck_id, from_release, to_release, has_changes, changes: [SyncChangeResponse]}`
- **Tabelas:** `decks`, `releases`, `release_items`, `cards`, `card_versions`, `deck_cards`
- **Serviços:** `DeckService.sync`

#### `GET /decks/{deck_id}/releases/{release_id}/export.csv` — export_release_csv
- **Arquivo:** `app/api/routes/decks.py:115`
- **Autenticação:** staff
- **Query params:** `delimiter` (comma/semicolon/tab), `include_tags` (bool)
- **Saída:** `text/csv` com headers `Content-Disposition`, `X-Content-SHA256`, `X-Row-Count`, `X-Release-Number`
- **Tabelas:** `releases`, `release_items`, `cards`, `card_versions`
- **Serviços:** `DeckService.export_release_csv`

---

### Addon

#### `GET /addon/status` — get_addon_status
- **Arquivo:** `app/api/routes/addon.py:29`
- **Autenticação:** nenhuma
- **Saída:** `AddonStatusResponse` — `{api_version, min_addon_version, supported_note_types}`
- **Tabelas:** nenhuma (configuração em `settings`)
- **Serviços:** nenhum

#### `GET /addon/decks/{deck_id}/manifest` — get_anki_deck_manifest
- **Arquivo:** `app/api/routes/addon.py:36`
- **Autenticação:** qualquer autenticado (inclui student)
- **Saída:** `AnkiDeckManifestResponse` — `{deck_id, name, description, latest_release, note_type, fields, field_mapping, supported_note_types, templates: [AnkiDeckTemplatePayload], tags}`
- **Tabelas:** `decks`, `deck_subscriptions`, `deck_templates`, `deck_template_versions`, `releases`, `release_items`, `cards`, `card_versions`
- **Serviços:** `DeckService.anki_manifest`

#### `GET /addon/decks/{deck_id}/sync` — sync_anki_deck
- **Arquivo:** `app/api/routes/addon.py:44`
- **Autenticação:** qualquer autenticado
- **Query params:** `since_release`, `page`, `page_size`
- **Saída:** `AnkiDeckSyncResponse` — igual a `DeckSyncResponse` + campos extras: `card_kind`, `note_type`, `template_name`, `fields`, `template`, `source_note_*`, `tags`, `page`, `pages`, `total_changes`
- **Tabelas:** `decks`, `deck_subscriptions`, `releases`, `release_items`, `cards`, `card_versions`
- **Serviços:** `DeckService.anki_sync`

#### `GET /addon/decks/{deck_id}/templates/sync` — sync_anki_deck_templates
- **Arquivo:** `app/api/routes/addon.py:55`
- **Autenticação:** qualquer autenticado
- **Query params:** `since_version` (default 0)
- **Saída:** `AnkiDeckTemplateSyncResponse` — `{deck_id, from_version, to_version, has_changes, changes: [AnkiDeckTemplateVersionResponse]}`
- **Tabelas:** `decks`, `deck_subscriptions`, `deck_templates`, `deck_template_versions`
- **Serviços:** `DeckService.anki_template_sync`

#### `POST /addon/decks/upload` — upload_anki_deck
- **Arquivo:** `app/api/routes/addon.py:67`
- **Autenticação:** qualquer autenticado
- **Entrada:** `AnkiDeckUploadRequest` — `{deck_name, description?, source_deck_path?, source_name, publish_release, templates: [AnkiDeckTemplatePayload], notes: [AnkiDeckUploadNotePayload]}`
- **Saída:** `AnkiDeckUploadResponse` (201)
- **Tabelas:** `decks`, `deck_cards`, `cards`, `card_versions`, `deck_snapshots`, `releases`, `release_items`, `deck_templates`, `deck_template_versions`
- **Serviços:** `DeckService.upload_anki_deck`

---

### Subscriptions

#### `GET /subscriptions/decks` — list_subscribable_decks
- **Arquivo:** `app/api/routes/subscriptions.py:27`
- **Autenticação:** qualquer autenticado
- **Query params:** `page`, `page_size`
- **Saída:** `SubscribableDeckListResponse` — `{items: [SubscribableDeckResponse], page, page_size, total, pages}`
  - `SubscribableDeckResponse`: herda `DeckSummaryResponse` + `{latest_release, subscribed}`
- **Tabelas:** `decks`, `deck_subscriptions`, `releases`, `deck_cards`
- **Serviços:** `DeckService.list_subscribable_decks`

#### `GET /subscriptions` — list_subscriptions
- **Arquivo:** `app/api/routes/subscriptions.py:37`
- **Autenticação:** qualquer autenticado
- **Saída:** `DeckSubscriptionListResponse` — `{items: [DeckSubscriptionResponse], total}`
- **Tabelas:** `deck_subscriptions`, `decks`, `releases`
- **Serviços:** `DeckService.list_subscriptions`

#### `POST /subscriptions/{deck_id}` — subscribe_to_deck
- **Arquivo:** `app/api/routes/subscriptions.py:46`
- **Autenticação:** qualquer autenticado
- **Saída:** `DeckSubscriptionResponse`
- **Tabelas:** `deck_subscriptions`, `decks`, `releases`
- **Serviços:** `DeckService.subscribe`

#### `POST /subscriptions/{deck_id}/cancel` — cancel_deck_subscription
- **Arquivo:** `app/api/routes/subscriptions.py:55`
- **Autenticação:** qualquer autenticado
- **Saída:** `DeckSubscriptionResponse`
- **Tabelas:** `deck_subscriptions`
- **Serviços:** `DeckService.unsubscribe`

---

### Reports

#### `POST /reports` — create_report
- **Arquivo:** `app/api/routes/reports.py:29`
- **Autenticação:** nenhuma + rate limit (`limit_public_reports`)
- **Entrada:** `ReportCreateRequest` — `{card_id, card_version_id, reporter_reference?, report_type, message}`
- **Saída:** `CardReportResponse` (201)
- **Tabelas:** `card_reports`, `review_tasks`, `cards`, `card_versions`
- **Serviços:** `ReportService.create_report`

#### `GET /admin/reports` — list_reports
- **Arquivo:** `app/api/routes/reports.py:42`
- **Autenticação:** reviewer
- **Query params:** `page`, `page_size`, `status`, `report_type`
- **Saída:** `CardReportListResponse` — `{items: [CardReportResponse], page, page_size, total, pages}`
- **Tabelas:** `card_reports`, `review_tasks`, `cards`, `card_versions`
- **Serviços:** `ReportService.list_reports`

#### `GET /admin/reports/{report_id}` — get_report
- **Arquivo:** `app/api/routes/reports.py:58`
- **Autenticação:** reviewer
- **Saída:** `CardReportResponse`
- **Tabelas:** `card_reports`, `review_tasks`, `cards`, `card_versions`
- **Serviços:** `ReportService.get_report`

#### `POST /admin/reports/{report_id}/review` — review_report
- **Arquivo:** `app/api/routes/reports.py:66`
- **Autenticação:** reviewer
- **Entrada:** `ReportReviewRequest` — `{decision, reviewed_by, admin_comment, evidence_reviewed, proposed_version?}`
  - `proposed_version` obrigatório se `decision == "converted_to_new_version"`
- **Saída:** `CardReportResponse`
- **Tabelas:** `card_reports`, `review_tasks`, `cards`, `card_versions`
- **Serviços:** `ReportService.review_report`

---

## 3. Modelos SQLAlchemy e tabelas

| Tabela | Modelo | Descrição |
|--------|--------|-----------|
| `users` | `User` | Usuários da plataforma. Roles: admin, curator, reviewer, student |
| `raw_documents` | `RawDocument` | Documentos PDF/fonte bruta para extração de questões |
| `exams` | `Exam` | Provas extraídas de raw_documents |
| `questions` | `Question` | Questões extraídas (raw) |
| `question_alternatives` | `QuestionAlternative` | Alternativas das questões |
| `disciplines` | `Discipline` | Hierarquia de disciplinas (auto-referência via parent_id) |
| `topics` | `Topic` | Tópicos de estudo (auto-referência via parent_id, dentro de discipline) |
| `cards` | `Card` | Flashcards canônicos com public_id (AC-xxxxx) e canonical_key |
| `card_versions` | `CardVersion` | Versões imutáveis de cards com conteúdo + status |
| `card_reports` | `CardReport` | Reports de erros submetidos por estudantes |
| `review_tasks` | `ReviewTask` | Tarefa de revisão associada 1:1 a um CardReport |
| `decks` | `Deck` | Baralhos (agrupamento de cards) |
| `deck_cards` | `DeckCard` | Relação deck–card com timestamping de adição/remoção |
| `deck_snapshots` | `DeckSnapshot` | Snapshot do estado do deck num upload do add-on |
| `deck_templates` | `DeckTemplate` | Templates de note type por deck (chave: template_key) |
| `deck_template_versions` | `DeckTemplateVersion` | Versões imutáveis de templates (fields, HTML, CSS) |
| `deck_subscriptions` | `DeckSubscription` | Inscrições de usuário em decks |
| `releases` | `Release` | Releases imutáveis publicadas de um deck |
| `release_items` | `ReleaseItem` | Itens de uma release (action: added/updated/removed/deprecated) |
| `processing_jobs` | `ProcessingJob` | Jobs de processamento assíncrono (pipeline de ingestão) |

### Campos-chave e constraints relevantes

- `cards.public_id` — imutável após criação; formato `AC-{hex.upper()}`
- `card_versions` — imutáveis após `status=published`; `content_hash` único por conteúdo
- `releases` e `release_items` — completamente imutáveis após criação (evento SQLAlchemy bloqueia UPDATE/DELETE)
- `card_reports` — campos de auditoria imutáveis; não podem ser deletados
- `review_tasks` — não podem ser deletadas; após `status=completed` tornam-se imutáveis

### Tabelas sem superfície de API

As seguintes tabelas existem no banco mas **não têm endpoints dedicados** na API REST atual:

| Tabela | Uso |
|--------|-----|
| `raw_documents` | Pipeline de ingestão interna |
| `exams` | Pipeline de ingestão interna |
| `questions` | Pipeline de ingestão interna |
| `question_alternatives` | Pipeline de ingestão interna |
| `processing_jobs` | Jobs assíncronos internos |

---

## 4. Schemas Pydantic

### Entrada (Request)

| Schema | Arquivo | Usado em |
|--------|---------|----------|
| `LoginRequest` | `schemas/auth.py` | `POST /auth/token` |
| `RefreshTokenRequest` | `schemas/auth.py` | `POST /auth/refresh` |
| `UserCreateRequest` | `schemas/auth.py` | `POST /admin/users` |
| `UserUpdateRequest` | `schemas/auth.py` | `PATCH /admin/users/{id}` |
| `PasswordResetRequest` | `schemas/auth.py` | `POST /admin/users/{id}/reset-password` |
| `CardCreateRequest` | `schemas/cards.py` | `POST /cards` |
| `CardVersionCreateRequest` | `schemas/cards.py` | `POST /cards/{id}/versions` |
| `CardCsvImportRequest` | `schemas/cards.py` | `POST /card-imports/csv` |
| `DeckCreateRequest` | `schemas/decks.py` | `POST /decks` |
| `DeckCardAddRequest` | `schemas/decks.py` | `POST /decks/{id}/cards` |
| `DeckCardRemoveRequest` | `schemas/decks.py` | `POST /decks/{id}/cards/{id}/remove` |
| `ReleasePublishRequest` | `schemas/decks.py` | `POST /decks/{id}/publish-release` |
| `AnkiDeckUploadRequest` | `schemas/decks.py` | `POST /addon/decks/upload` |
| `AnkiDeckTemplatePayload` | `schemas/decks.py` | Dentro de `AnkiDeckUploadRequest` |
| `AnkiDeckUploadNotePayload` | `schemas/decks.py` | Dentro de `AnkiDeckUploadRequest` |
| `ReportCreateRequest` | `schemas/reports.py` | `POST /reports` |
| `ReportReviewRequest` | `schemas/reports.py` | `POST /admin/reports/{id}/review` |
| `CuratedVersionInput` | `schemas/reports.py` | Dentro de `ReportReviewRequest` |

### Saída (Response)

| Schema | Arquivo | Usado em |
|--------|---------|----------|
| `TokenResponse` | `schemas/auth.py` | `POST /auth/token`, `POST /auth/refresh` |
| `UserResponse` | `schemas/auth.py` | endpoints de usuário |
| `UserListResponse` | `schemas/auth.py` | `GET /admin/users` |
| `CardSummaryResponse` | `schemas/cards.py` | `GET /cards`, `GET /cards/public/{id}` |
| `CardDetailResponse` | `schemas/cards.py` | `GET /cards/{id}`, mutations de versão |
| `CardVersionResponse` | `schemas/cards.py` | dentro de CardDetailResponse |
| `CardListResponse` | `schemas/cards.py` | `GET /cards` |
| `CardCsvImportResponse` | `schemas/cards.py` | `POST /card-imports/csv` |
| `DeckResponse` | `schemas/decks.py` | CRUD de decks |
| `DeckSummaryResponse` | `schemas/decks.py` | `GET /decks` |
| `DeckListResponse` | `schemas/decks.py` | `GET /decks` |
| `DeckSyncResponse` | `schemas/decks.py` | `GET /decks/{id}/sync` |
| `ReleaseResponse` | `schemas/decks.py` | `POST /decks/{id}/publish-release` |
| `ReleaseListResponse` | `schemas/decks.py` | `GET /decks/{id}/releases` |
| `SubscribableDeckListResponse` | `schemas/decks.py` | `GET /subscriptions/decks` |
| `DeckSubscriptionResponse` | `schemas/decks.py` | endpoints de subscription |
| `DeckSubscriptionListResponse` | `schemas/decks.py` | `GET /subscriptions` |
| `AnkiDeckManifestResponse` | `schemas/decks.py` | `GET /addon/decks/{id}/manifest` |
| `AnkiDeckSyncResponse` | `schemas/decks.py` | `GET /addon/decks/{id}/sync` |
| `AnkiDeckTemplateSyncResponse` | `schemas/decks.py` | `GET /addon/decks/{id}/templates/sync` |
| `AnkiDeckUploadResponse` | `schemas/decks.py` | `POST /addon/decks/upload` |
| `AddonStatusResponse` | `schemas/decks.py` | `GET /addon/status` |
| `CardReportResponse` | `schemas/reports.py` | endpoints de reports |
| `CardReportListResponse` | `schemas/reports.py` | `GET /admin/reports` |
| `ReviewTaskResponse` | `schemas/reports.py` | dentro de CardReportResponse |
| `DisciplineListResponse` | `schemas/taxonomy.py` | `GET /disciplines` |
| `TopicListResponse` | `schemas/taxonomy.py` | `GET /disciplines/{id}/topics` |

---

## 5. Histórico de migrations

| Arquivo | Descrição |
|---------|-----------|
| `20260612_0001` | MVP 0→1: schema inicial (users, cards, decks, releases, taxonomy, reports) |
| `20260612_0002` | processing_jobs + integridade |
| `20260612_0003` | public_card_id no cards |
| `20260612_0004` | MVP 3: integridade de releases |
| `20260612_0005` | MVP 6: curadoria |
| `20260612_0006` | MVP 7: users com roles |
| `20260615_0007` | Pré-MVP 8: segurança (rate limit, credencial_version) |
| `20260616_0008` | deck_subscriptions |
| `20260616_0009` | card_kind (basic/cloze) |
| `20260616_0010` | role student |
| `20260618_0011` | deck_snapshots + anki_upload |
| `20260618_0012` | cards.discipline_id e topic_id nullable |
| `20260618_0013` | explanation_text nullable |
| `20260618_0014` | card_versions com campos Anki nativos (anki_fields, anki_template, source_note_*) |
| `20260620_0015` | deck_templates + deck_template_versions |

---

## 6. Mapa de relacionamentos

```
users ──────────────────────────────────── deck_subscriptions ────── decks
                                                                        │
                                                           ┌────────────┤
                                                           │            │
disciplines ──── topics ──── cards ──── card_versions    deck_cards   deck_snapshots
                               │              │              │
                               └──── card_reports ──── review_tasks
                                         │
                                  (card_version_id)
                                         │
                                  card_versions (resulting)

decks ──── releases ──── release_items ──── cards
      ──── deck_templates ──── deck_template_versions
      ──── deck_snapshots

raw_documents ──── exams
              ──── questions ──── question_alternatives
                             ──── cards (origin_question_id, opcional)

processing_jobs (entidade genérica entity_type/entity_id, sem FK explícita)
```

### Chaves estrangeiras críticas

| De | Para | Regra |
|----|------|-------|
| `cards.current_version_id` | `card_versions.id` | `USE_ALTER` (circular) |
| `deck_templates.current_version_id` | `deck_template_versions.id` | `SET NULL` |
| `card_reports.card_version_id` | `card_versions.id` | `RESTRICT` |
| `release_items.card_version_id` | `card_versions.id` | `RESTRICT` |
| `deck_subscriptions.user_id` | `users.id` | `CASCADE DELETE` |
| `deck_subscriptions.deck_id` | `decks.id` | `CASCADE DELETE` |
| `deck_cards.deck_id` | `decks.id` | `CASCADE DELETE` |
| `releases.deck_id` | `decks.id` | `RESTRICT` |

---

## 7. Seção por tela do frontend

> **Base URL configurada via:** `window.__APP_CONFIG__.API_URL` → `VITE_API_URL` → `http://localhost:8000`
>
> Autenticação Bearer token armazenada em `sessionStorage` (`anki-concursos-admin-token`).

---

### `/login` — LoginPage

**Arquivo:** `admin/src/pages/LoginPage.tsx`  
**Acesso:** público

| Método | Endpoint | Quando |
|--------|----------|--------|
| POST | `/auth/token` | submit do formulário |

**Fluxo adicional (AuthContext):** ao restaurar sessão (token em sessionStorage):
- `GET /auth/me` — valida token existente
- `POST /auth/refresh` — se access token expirou mas refresh token existe

---

### `/dashboard` — DashboardPage

**Arquivo:** `admin/src/pages/DashboardPage.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando | Condicional |
|--------|----------|--------|-------------|
| GET | `/cards?page=1&page_size=1` | montagem | sempre |
| GET | `/decks?page=1&page_size=1` | montagem | sempre |
| GET | `/admin/reports?page=1&page_size=1&status=open` | montagem | só se `canReview` (admin/reviewer) |
| GET | `/admin/users?page=1&page_size=1` | montagem | só se `canManageUsers` (admin) |
| GET | `/health` | montagem | sempre |
| GET | `/ready` | montagem | sempre |

---

### `/cards` — CardsPage

**Arquivo:** `admin/src/pages/ListPages.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/disciplines` | montagem |
| GET | `/disciplines/{discipline_id}/topics` | ao selecionar disciplina |
| GET | `/cards?page=X&page_size=20[&discipline_id&topic_id&status&public_id]` | montagem + filtros |
| GET | `/cards?page=1&page_size=1&status=published` | métricas de resumo |
| GET | `/cards?page=1&page_size=1&status=needs_review` | métricas de resumo |
| GET | `/cards?page=1&page_size=1&status=reported` | métricas de resumo |

---

### `/cards/:cardId` — CardDetailPage

**Arquivo:** `admin/src/pages/CardDetailPage.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/cards/{card_id}` | montagem |
| POST | `/cards/{card_id}/versions/{version_id}/approve` | botão "Aprovar" (admin/reviewer) |
| POST | `/cards/{card_id}/versions/{version_id}/publish` | botão "Publicar" (admin/reviewer) |

---

### `/cards/new` — NewCardPage

**Arquivo:** `admin/src/pages/CardFormPage.tsx`  
**Acesso:** admin/curator

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/disciplines` | montagem |
| GET | `/disciplines/{discipline_id}/topics` | ao selecionar disciplina |
| POST | `/cards` | submit do formulário |

---

### `/cards/:cardId/versions/new` — NewCardVersionPage

**Arquivo:** `admin/src/pages/CardFormPage.tsx`  
**Acesso:** admin/curator

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/cards/{card_id}` | montagem (carrega versão atual como base) |
| POST | `/cards/{card_id}/versions` | submit do formulário |

---

### `/cards/import` — CardImportPage

**Arquivo:** `admin/src/pages/CardImportPage.tsx`  
**Acesso:** admin/curator

| Método | Endpoint | Quando |
|--------|----------|--------|
| POST | `/card-imports/csv` | submit do formulário (dry_run ou efetivo) |

---

### `/decks` — DecksPage

**Arquivo:** `admin/src/pages/ListPages.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/decks?page=X&page_size=20` | montagem + paginação |

---

### `/decks/new` — NewDeckPage

**Arquivo:** `admin/src/pages/DeckPages.tsx`  
**Acesso:** admin/curator

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/disciplines` | montagem |
| POST | `/decks` | submit do formulário |

---

### `/decks/:deckId` — DeckDetailPage

**Arquivo:** `admin/src/pages/DeckPages.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/decks/{deck_id}` | montagem |
| GET | `/decks/{deck_id}/releases?page=X&page_size=20` | montagem + paginação |
| GET | `/decks/{deck_id}/sync?since_release=X` | montagem + seleção de from_release |
| GET | `/cards?public_id={ref}&page_size=1` | ao adicionar card por public_id |
| POST | `/decks/{deck_id}/cards` | botão "Adicionar cartão" |
| POST | `/decks/{deck_id}/cards/{card_id}/remove` | botão "Remover" |
| POST | `/decks/{deck_id}/publish-release` | botão "Publicar release" |
| GET | `/decks/{deck_id}/releases/{release_id}/export.csv` | botão "Exportar CSV" (download) |

---

### `/reports` — ReportsPage

**Arquivo:** `admin/src/pages/ListPages.tsx`  
**Acesso:** admin/reviewer

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/admin/reports?page=X&page_size=20[&status&report_type]` | montagem + filtros |

---

### `/reports/:reportId` — ReportDetailPage

**Arquivo:** `admin/src/pages/ReportDetailPage.tsx`  
**Acesso:** admin/reviewer

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/admin/reports/{report_id}` | montagem |
| GET | `/cards/{card_id}` | após carregar report (para mostrar versões) |
| POST | `/admin/reports/{report_id}/review` | submit da revisão |

---

### `/users` — UsersPage

**Arquivo:** `admin/src/pages/ListPages.tsx`  
**Acesso:** admin

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/admin/users?page=X&page_size=20` | montagem + paginação |

---

### `/users/new` — NewUserPage

**Arquivo:** `admin/src/pages/UserPages.tsx`  
**Acesso:** admin

| Método | Endpoint | Quando |
|--------|----------|--------|
| POST | `/admin/users` | submit do formulário |

---

### `/users/:userId` — EditUserPage

**Arquivo:** `admin/src/pages/UserPages.tsx`  
**Acesso:** admin

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/admin/users?page=1&page_size=100` | montagem (busca usuário por ID no resultado) |
| PATCH | `/admin/users/{user_id}` | submit do formulário de edição |
| POST | `/admin/users/{user_id}/reset-password` | submit do formulário de senha |

---

### `/addon` — AddonPage

**Arquivo:** `admin/src/pages/AddonPage.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/subscriptions/decks?page=1&page_size=100` | montagem |
| GET | `/subscriptions` | montagem |
| GET | `/addon/decks/{deck_id}/manifest` | ao selecionar deck |
| GET | `/addon/decks/{deck_id}/sync?since_release=X` | ao selecionar deck |
| POST | `/subscriptions/{deck_id}` | botão "Assinar" |
| POST | `/subscriptions/{deck_id}/cancel` | botão "Cancelar inscrição" |

---

### `/operation` — OperationPage

**Arquivo:** `admin/src/pages/OperationPage.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/health` | montagem |
| GET | `/ready` | montagem |

---

### `/` — ExplorePage (Community)

**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/subscriptions/decks?page=1&page_size=100` | montagem |
| POST | `/subscriptions/{deck_id}` | botão "Assinar" (SubscriptionButton) |
| **DELETE** | `/subscriptions/{deck_id}` | botão "Desinscrever" (SubscriptionButton) — **⚠️ endpoint inexistente** |

---

### `/my-decks` — MyDecksPage (Community)

**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/subscriptions/decks?page=1&page_size=100` | montagem (filtra `subscribed=true` no cliente) |

---

### `/deck/:deckId` — DeckPage (Community)

**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx`  
**Acesso:** autenticado

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/subscriptions/decks?page=1&page_size=100` | montagem |
| GET | `/addon/decks/{deck_id}/sync?since_release=0&page=1&page_size=1000` | ao abrir deck com inscrição ativa |
| POST | `/subscriptions/{deck_id}` | botão "Assinar" |
| **DELETE** | `/subscriptions/{deck_id}` | botão "Desinscrever" — **⚠️ endpoint inexistente** |

---

### `/deck/:deckId/suggestions` — CommunitySuggestionHistoryPage

**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx`  
**Acesso:** autenticado  
**Chamadas à API:** nenhuma — usa apenas `localStorage` (`anki-concursos-suggestions`)

---

### `/admin` — AdminDashboardPage (Community)

**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx`  
**Acesso:** admin/curator/reviewer  
**Chamadas à API:** nenhuma — métricas são **hardcoded** ("12", "25", "3")

---

### `/admin/decks` — AdminDecksPage (Community)

**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx`  
**Acesso:** admin/curator

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/subscriptions/decks?page=1&page_size=100` | montagem |

---

### `/admin/suggestions` — AdminSuggestionsPage (Community)

**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx`  
**Acesso:** admin/reviewer  
**Estado:** lê sugestões do `localStorage`; chamadas à API são opcionais (quando `token` presente)

| Método | Endpoint | Quando |
|--------|----------|--------|
| GET | `/cards/public/{public_id}` | ao converter sugestão sem `cardId` |
| POST | `/cards/{card_id}/versions` | ao converter sugestão |
| POST | `/cards/{card_id}/versions/{version_id}/approve` | imediatamente após criar versão |
| POST | `/cards/{card_id}/versions/{version_id}/publish` | imediatamente após aprovar |
| POST | `/decks/{deck_id}/cards` | adiciona card ao deck da sugestão |
| POST | `/decks/{deck_id}/publish-release` | publica release após adicionar card |

---

### `/community` — CommunityFuturePage

**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx`  
**Acesso:** autenticado  
**Chamadas à API:** nenhuma — conteúdo estático (placeholder)

---

## 8. Contrato do add-on Anki

O add-on usa exclusivamente os endpoints do prefixo `/addon/`. Fluxo típico:

```
1. GET /addon/status
   → verifica api_version, min_addon_version, supported_note_types

2. GET /addon/decks/{deck_id}/manifest
   → obtém note_types, fields, field_mapping, latest_release, templates

3. GET /addon/decks/{deck_id}/templates/sync?since_version={local_version}
   → sincroniza templates de note type (HTML/CSS)

4. GET /addon/decks/{deck_id}/sync?since_release={local_release}&page=X&page_size=Y
   → incrementalmente obtém changes com fields prontos para criar/atualizar notas Anki

5. POST /addon/decks/upload
   → faz upload de deck existente do Anki para a plataforma
   → aceita templates + notes em um único payload
```

**Note types suportados (hardcoded em `DeckService.ANKI_NOTE_TYPES`):**
- `basic` → `"Anki Concursos Basic"` — fields: `[Front, Back, Answer, Explanation]`
- `cloze` → `"Anki Concursos Cloze"` — fields: `[Text, Extra, Answer, Explanation]`

**Autenticação do add-on:** Bearer token (role `student` é suficiente para todos os endpoints `/addon/`)

---

## 9. Inconsistências encontradas

### 9.1 `DELETE /subscriptions/{deck_id}` — endpoint inexistente

**Severidade:** Alta (quebra silenciosa de funcionalidade)  
**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx:1276`  
**Problema:** O componente `SubscriptionButton` (usado em `ExplorePage` e `DeckPage`) faz:

```ts
mutationFn: () => apiRequest(`/subscriptions/${deck.deck_id}`, { method: 'DELETE' }, token)
```

O backend **não tem** nenhum endpoint `DELETE /subscriptions/{id}`. O endpoint correto é `POST /subscriptions/{deck_id}/cancel`.

A `AddonPage.tsx:81` usa corretamente `POST /subscriptions/${deckId}/cancel`.

**Impacto:** Botão "Desinscrever" nas telas `/` (ExplorePage) e `/deck/:deckId` (DeckPage) retorna 405 Method Not Allowed.  
**Correção:** Substituir `{ method: 'DELETE' }` por `{ method: 'POST' }` e a URL para `/subscriptions/${deck.deck_id}/cancel`.

---

### 9.2 Status `"draft"` no filtro de cards — valor não existe no enum

**Severidade:** Média (filtro inoperante)  
**Arquivo:** `admin/src/pages/ListPages.tsx:156`

```tsx
<option value="draft">Rascunho</option>
```

O enum `CardStatus` não tem valor `draft`. Os valores são: `generated`, `needs_review`, `approved`, `published`, `reported`, `revised`, `deprecated`, `archived`.

**Impacto:** Selecionar "Rascunho" envia `?status=draft` para a API, que retorna validação 422 (Unprocessable Entity) ou lista vazia, dependendo de como o backend trata o enum.  
**Correção:** Substituir `"draft"` por `"generated"` ou remover a opção.

---

### 9.3 `AdminDashboardPage` — métricas hardcoded

**Severidade:** Baixa (UX enganosa)  
**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx:710–712`

```tsx
<MetricCard label="Baralhos publicados" value="12" />
<MetricCard label="Versões em revisão" value="25" />
<MetricCard label="Releases pendentes" value="3" />
```

Os números são hardcoded. A API tem todos os dados necessários para preencher estas métricas dinamicamente.

---

### 9.4 `EditUserPage` — lista usuários por paginação de 100 sem cursor

**Severidade:** Baixa (risco ao crescer base de usuários)  
**Arquivo:** `admin/src/pages/UserPages.tsx:166`

```ts
apiRequest<Paginated<User>>('/admin/users?page=1&page_size=100', {}, token)
```

Para encontrar o usuário pelo ID passado na rota, a página carrega os primeiros 100 usuários e faz um `.find()` no cliente. Se houver mais de 100 usuários, o usuário pode não ser encontrado.  
**Correção ideal:** Criar endpoint `GET /admin/users/{user_id}` no backend.

---

### 9.5 Tabelas de ingestão sem API (`raw_documents`, `exams`, `questions`, `question_alternatives`, `processing_jobs`)

**Severidade:** Informativo  
Estas tabelas estão no schema e nas migrations mas não têm endpoints na API REST. Fazem parte do pipeline interno de extração de questões. Se houver ferramenta administrativa para esse fluxo, ela opera fora desta API.

---

### 9.6 `CommunitySuggestionHistoryPage` e `AdminSuggestionsPage` — estado local não persistido

**Severidade:** Média (perda de dados entre sessões)  
Sugestões da comunidade são armazenadas apenas em `localStorage` (`anki-concursos-suggestions`). Não há endpoint de persistência para sugestões no backend. Ao limpar o localStorage ou trocar de dispositivo, o histórico se perde.

---

### 9.7 `GET /cards/public/{public_id}` — rota pública sem autenticação exposta ao frontend admin

**Severidade:** Informativo  
O endpoint não requer autenticação (proposital — é para o add-on e embed público), mas também é chamado em `AdminSuggestionsPage` quando a sugestão não tem `cardId`. Não é um problema de segurança, mas é relevante documentar que esta rota é a única que expõe dados de cards sem autenticação.

---

### 9.8 CORS restringe métodos a GET/POST/OPTIONS

**Severidade:** Informativo (consistente com as rotas atuais)  
**Arquivo:** `app/main.py:56`

```python
allow_methods=["GET", "POST", "OPTIONS"],
```

A tentativa de usar `DELETE` em `CommunityInterfacePages.tsx:1276` (inconsistência 9.1) seria bloqueada pelo CORS antes mesmo de chegar ao backend, em requisições cross-origin.

---

### 9.9 `DeckPage` usa `since_release=0&page_size=1000` no addon sync

**Severidade:** Baixa (performance)  
**Arquivo:** `admin/src/pages/CommunityInterfacePages.tsx:107`

```ts
`/addon/decks/${deckId}/sync?since_release=0&page=1&page_size=1000`
```

Carrega até 1000 notas de uma vez para preview do deck. Para decks grandes isso pode ser lento. O endpoint suporta paginação incremental.

---

*Fim do documento*
