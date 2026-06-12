# Regras de Qualidade

## Objetivo

Garantir que cartões publicados sejam úteis, confiáveis, rastreáveis e corrigíveis.

## Regras para flashcards

Um flashcard deve ser:

- atômico;
- objetivo;
- autoexplicativo;
- fundamentado;
- classificado;
- versionado;
- rastreável.

## Checklist antes da publicação

O cartão só pode ser publicado se:

- possui frente;
- possui verso;
- possui resposta;
- possui explicação;
- possui disciplina válida;
- possui assunto válido;
- passou por revisão ou validação mínima;
- não é duplicata evidente;
- está em status permitido.

## Checks determinísticos sugeridos

### Conteúdo

- `front_not_empty`
- `back_not_empty`
- `answer_not_empty`
- `explanation_not_empty`

### Classificação

- `valid_discipline`
- `valid_topic`

### Evidência

Quando a política do deck exigir fundamentação:

- `has_evidence`
- `evidence_is_valid`
- `source_is_current`
- `citation_exists`

### Versionamento

- `card_has_stable_id`
- `card_has_immutable_public_id`
- `version_number_incremented`
- `content_hash_changed`
- `previous_version_preserved`

### Publicação

- `status_allows_publication`
- `deck_exists`
- `release_created`

### Exportação CSV

- `release_is_published`
- `stable_ids_present`
- `exported_version_matches_release`
- `valid_utf8`
- `csv_escaping_is_valid`
- `row_count_matches_release_snapshot`
- `content_hash_is_reproducible`
- `removed_cards_are_not_exported`
- `deprecated_cards_are_not_exported`

### Sincronização

- `since_release_exists_or_is_zero`
- `changes_are_release_ordered`
- `stable_ids_are_present`
- `old_version_matches_previous_state`
- `new_version_matches_release_item`
- `removed_and_deprecated_are_explicit`
- `current_client_receives_no_changes`

### Curadoria

- `report_targets_published_version`
- `reported_version_belongs_to_card`
- `decision_is_auditable`
- `rejection_preserves_content`
- `duplicate_preserves_content`
- `converted_report_creates_new_version`
- `resulting_version_belongs_to_reported_card`
- `change_reason_is_present`
- `outdated_law_has_evidence_review`
- `published_version_remains_current`
- `completed_review_is_immutable`

### Segurança e operação

- `password_is_salted_and_hashed`
- `inactive_user_cannot_authenticate`
- `token_has_expiration`
- `role_is_checked_against_database`
- `legacy_api_key_is_disabled_in_production`
- `production_secret_is_not_default`
- `readiness_checks_database`
- `migration_chain_reaches_head`
- `public_report_is_rate_limited`
- `login_is_rate_limited`
- `request_has_correlation_id`
- `backup_restore_is_periodically_tested`

## Tipos de report

```text
typo
wrong_answer
outdated_law
bad_explanation
classification_error
duplicate_card
suggestion
```

## Regra final

Nenhum cartão manual ou importado pode ser publicado sem validação
determinística e revisão humana. Um sistema externo nunca pode definir
diretamente o status `published`.

A consulta pública por `public_id` não pode retornar cartão em estado de
rascunho, revisão, rejeição ou arquivamento.

Decks só podem referenciar a versão atual publicada. Releases devem falhar
quando não houver mudanças e não podem ser alteradas após publicação.
